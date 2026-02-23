"""
Tests para el módulo TemplateManager
"""

import pytest
import gitlab
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
from hidraulik.template_manager import TemplateManager


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def manager():
    return TemplateManager('grupo/plantillas-cicd')


@pytest.fixture
def mock_gitlab_module():
    """Parchea gitlab.Gitlab dentro de template_manager"""
    with patch('hidraulik.template_manager.gitlab.Gitlab') as mock_gl:
        inst = Mock()
        mock_gl.return_value = inst
        inst.auth.return_value = None
        yield inst


# ─────────────────────────────────────────────────────────────────────────────
# Init & deprecated load_templates
# ─────────────────────────────────────────────────────────────────────────────

def test_template_manager_init(manager):
    assert manager.template_repo_path == 'grupo/plantillas-cicd'
    assert manager.templates_cache == {}


def test_load_templates(manager):
    templates = manager.load_templates()
    assert isinstance(templates, dict)
    assert templates == {}


# ─────────────────────────────────────────────────────────────────────────────
# list_available_templates & get_template
# ─────────────────────────────────────────────────────────────────────────────

def test_list_available_templates_empty(manager):
    assert manager.list_available_templates() == []


def test_list_available_templates_with_cache(manager):
    manager.templates_cache = {'a.yaml': 'content', 'b.yaml': 'content2'}
    result = manager.list_available_templates()
    assert set(result) == {'a.yaml', 'b.yaml'}


def test_get_template_missing(manager):
    assert manager.get_template('nonexistent.yaml') == ''


def test_get_template_from_cache(manager):
    manager.templates_cache = {'ci.yaml': 'stage: build'}
    assert manager.get_template('ci.yaml') == 'stage: build'


# ─────────────────────────────────────────────────────────────────────────────
# get_templates_by_type
# ─────────────────────────────────────────────────────────────────────────────

def test_get_templates_by_type(manager):
    manager.templates_cache = {
        '.gitlab-ci.yml': 'pipeline content',
        'k8s/deployment.yaml': 'deployment content',
    }
    manager.template_types = {
        '.gitlab-ci.yml': 'pipeline',
        'k8s/deployment.yaml': 'k8s',
    }
    result = manager.get_templates_by_type('pipeline')
    assert result == {'.gitlab-ci.yml': 'pipeline content'}
    result_k8s = manager.get_templates_by_type('k8s')
    assert result_k8s == {'k8s/deployment.yaml': 'deployment content'}


# ─────────────────────────────────────────────────────────────────────────────
# _detect_template_type
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("path,expected", [
    ('pipeline/.gitlab-ci.yml.j2', 'pipeline'),
    ('k8s/04-deployment.yaml.j2', 'k8s'),
    ('helm/values.yaml.j2', 'helm'),
    ('config/app.conf.j2', 'config'),
    ('README.md', 'unknown'),
    ('unknown_folder/foo.j2', 'unknown'),
])
def test_detect_template_type(manager, path, expected):
    assert manager._detect_template_type(path) == expected


# ─────────────────────────────────────────────────────────────────────────────
# _calculate_dest_path
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("file_path,tpl_type,expected", [
    ('pipeline/.gitlab-ci.yml.j2', 'pipeline', '.gitlab-ci.yml'),
    ('k8s/04-deployment.yaml.j2', 'k8s', 'k8s/04-deployment.yaml'),
    ('helm/values.yaml.j2', 'helm', 'helm/values.yaml'),
    ('config/app.conf.j2', 'config', 'config/app.conf'),
    ('standalone.yaml.j2', 'unknown', 'standalone.yaml'),
])
def test_calculate_dest_path(manager, file_path, tpl_type, expected):
    result = manager._calculate_dest_path(file_path, tpl_type)
    assert result == expected


# ─────────────────────────────────────────────────────────────────────────────
# _should_include_file
# ─────────────────────────────────────────────────────────────────────────────

def test_should_include_file_no_filter(manager):
    assert manager._should_include_file('k8s/02-secrets.yaml.j2') is True


def test_should_include_file_non_k8s(manager):
    filt = {'app': ['deployment']}
    assert manager._should_include_file('pipeline/.gitlab-ci.yml.j2', filt) is True


def test_should_include_file_k8s_included(manager):
    filt = {'app': ['secrets', 'deployment']}
    assert manager._should_include_file('k8s/02-secrets.yaml.j2', filt) is True
    assert manager._should_include_file('k8s/04-deployment.yaml.j2', filt) is True


def test_should_include_file_k8s_excluded(manager):
    filt = {'app': ['deployment']}
    # pvc no está en el filtro
    assert manager._should_include_file('k8s/07-pvc.yaml.j2', filt) is False


# ─────────────────────────────────────────────────────────────────────────────
# extract_variables
# ─────────────────────────────────────────────────────────────────────────────

def test_extract_variables(manager):
    templates = {
        'ci.yaml': '{{ docker_registry }}/{{ project_name }} ${{ CICD_DOCKER_TOKEN }}',
        'deploy.yaml': '{{ namespace }} {{ replicas }} ${{ CICD_IMAGE_URL }}',
    }
    template_vars, cicd_vars = manager.extract_variables(templates)

    assert 'docker_registry' in template_vars
    assert 'project_name' in template_vars
    assert 'namespace' in template_vars
    assert 'replicas' in template_vars
    assert 'CICD_DOCKER_TOKEN' in cicd_vars
    assert 'CICD_IMAGE_URL' in cicd_vars

    # CICD_ vars no en template_vars
    assert 'CICD_DOCKER_TOKEN' not in template_vars
    assert 'CICD_IMAGE_URL' not in template_vars


def test_extract_variables_filters_jinja_internals(manager):
    """Variables internas de Jinja2 (env, item, etc.) se ignoran"""
    templates = {
        'tmpl.yaml': '{% for item in items %}{{ item }}{% endfor %} {{ project_name }}'
    }
    template_vars, cicd_vars = manager.extract_variables(templates)
    # 'item' es variable interna de Jinja2, debe filtrarse
    assert 'item' not in template_vars


# ─────────────────────────────────────────────────────────────────────────────
# load_from_gitlab – flujo completo (mock)
# ─────────────────────────────────────────────────────────────────────────────

def test_load_from_gitlab_success(mock_gitlab_module):
    """Test del flujo completo de carga desde GitLab"""
    mock_project = Mock()
    mock_project.name = 'plantillas-cicd'

    tree_items = [
        {'type': 'blob', 'name': 'ci.yaml.j2',         'path': 'pipeline/ci.yaml.j2'},
        {'type': 'blob', 'name': 'deployment.yaml.j2',  'path': 'k8s/deployment.yaml.j2'},
        {'type': 'blob', 'name': 'includes.yaml',       'path': 'includes/base.yaml'},  # excluido
    ]
    mock_project.repository_tree = Mock(return_value=tree_items)

    file_mock = Mock()
    file_mock.decode.return_value = b'hello {{ project_name }}'
    mock_project.files.get = Mock(return_value=file_mock)

    mock_gitlab_module.projects.get = Mock(return_value=mock_project)

    manager = TemplateManager('grupo/plantillas-cicd')
    result = manager.load_from_gitlab(
        'https://gitlab.com', 'token', 'grupo/plantillas-cicd'
    )

    assert '.gitlab-ci.yml' in result or 'ci.yaml' in result or len(result) > 0
    assert 'includes/base.yaml' not in result


def test_load_from_gitlab_auth_error(mock_gitlab_module):
    """Test que retorna vacío en error de autenticación"""
    mock_gitlab_module.auth.side_effect = gitlab.exceptions.GitlabAuthenticationError(
        "401", 401
    )
    manager = TemplateManager('grupo/plantillas-cicd')
    result = manager.load_from_gitlab('https://gitlab.com', 'bad-token', 'grupo/plantillas-cicd')
    assert result == {}


def test_load_from_gitlab_get_error(mock_gitlab_module):
    """Test que retorna vacío si el proyecto no existe"""
    mock_gitlab_module.projects.get = Mock(
        side_effect=gitlab.exceptions.GitlabGetError("404", 404)
    )
    manager = TemplateManager('grupo/plantillas-cicd')
    result = manager.load_from_gitlab('https://gitlab.com', 'token', 'no/project')
    assert result == {}


def test_load_from_gitlab_unexpected_error(mock_gitlab_module):
    """Test que retorna vacío en error inesperado"""
    mock_gitlab_module.projects.get = Mock(side_effect=RuntimeError("boom"))
    manager = TemplateManager('grupo/plantillas-cicd')
    result = manager.load_from_gitlab('https://gitlab.com', 'token', 'any/project')
    assert result == {}


# ─────────────────────────────────────────────────────────────────────────────
# get_remote_includes
# ─────────────────────────────────────────────────────────────────────────────

def test_get_remote_includes_success(mock_gitlab_module):
    """Test que retorna archivos de includes/"""
    mock_project = Mock()
    tree = [
        {'type': 'blob', 'path': 'includes/base.yaml'},
        {'type': 'blob', 'path': 'includes/common.yaml'},
        {'type': 'blob', 'path': 'pipeline/ci.yaml.j2'},  # excluido
    ]
    mock_project.repository_tree = Mock(return_value=tree)
    mock_gitlab_module.projects.get = Mock(return_value=mock_project)

    manager = TemplateManager('grupo/plantillas-cicd')
    result = manager.get_remote_includes('https://gitlab.com', 'token')

    assert 'includes/base.yaml' in result
    assert 'includes/common.yaml' in result
    # pipeline file excluded
    assert all(p.startswith('includes/') for p in result)


def test_get_remote_includes_error_returns_empty(mock_gitlab_module):
    """Test que retorna lista vacía ante cualquier error"""
    mock_gitlab_module.auth.side_effect = Exception("fail")
    manager = TemplateManager('grupo/plantillas-cicd')
    result = manager.get_remote_includes('https://gitlab.com', 'token')
    assert result == []


# ─────────────────────────────────────────────────────────────────────────────
# load_from_gitlab – con filtro de manifiestos k8s
# ─────────────────────────────────────────────────────────────────────────────

def test_load_from_gitlab_with_k8s_filter(mock_gitlab_module):
    """Test que el filtro de manifiestos excluye archivos k8s no requeridos"""
    mock_project = Mock()
    mock_project.name = 'plantillas'

    tree_items = [
        {'type': 'blob', 'name': '04-deployment.yaml.j2', 'path': 'k8s/04-deployment.yaml.j2'},
        {'type': 'blob', 'name': '07-pvc.yaml.j2',        'path': 'k8s/07-pvc.yaml.j2'},
        {'type': 'blob', 'name': 'ci.yaml.j2',            'path': 'pipeline/ci.yaml.j2'},
    ]
    mock_project.repository_tree = Mock(return_value=tree_items)
    file_mock = Mock()
    file_mock.decode.return_value = b'content'
    mock_project.files.get = Mock(return_value=file_mock)
    mock_gitlab_module.projects.get = Mock(return_value=mock_project)

    manager = TemplateManager('grupo/plantillas')
    k8s_filter = {'app': ['deployment']}  # solo deployment, no pvc
    result = manager.load_from_gitlab(
        'https://gitlab.com', 'token', 'grupo/plantillas',
        k8s_manifests_filter=k8s_filter
    )

    keys = list(result.keys())
    # pvc debe estar excluido
    assert not any('pvc' in k for k in keys)


# ─────────────────────────────────────────────────────────────────────────────
# extract_variables_from_includes
# ─────────────────────────────────────────────────────────────────────────────

def test_extract_variables_from_includes_success(mock_gitlab_module):
    """Extrae variables @requires desde archivos remote includes"""
    mock_project = Mock()

    # Árbol del repositorio
    tree = [
        {'type': 'blob', 'path': 'includes/base.yml'},
    ]
    mock_project.repository_tree = Mock(return_value=tree)

    # Contenido de un include con @requires (una variable por línea)
    include_content = b'# @requires: REGISTRY_URL\n# @requires: KUBE_SERVER\n'
    include_file = Mock()
    include_file.decode.return_value = include_content
    mock_project.files.get = Mock(return_value=include_file)

    mock_gitlab_module.projects.get = Mock(return_value=mock_project)

    manager = TemplateManager('grupo/plantillas')
    templates = {
        'ci.yaml': "include:\n  - file: '/includes/base.yml'"
    }
    result = manager.extract_variables_from_includes(
        templates, 'https://gitlab.com', 'token'
    )

    assert 'REGISTRY_URL' in result
    assert 'KUBE_SERVER' in result


def test_extract_variables_from_includes_no_includes(mock_gitlab_module):
    """Retorna lista vacía si las plantillas no tienen includes"""
    mock_project = Mock()
    mock_project.repository_tree = Mock(return_value=[])
    mock_gitlab_module.projects.get = Mock(return_value=mock_project)

    manager = TemplateManager('grupo/plantillas')
    templates = {'ci.yaml': 'stages: [build, deploy]'}
    result = manager.extract_variables_from_includes(
        templates, 'https://gitlab.com', 'token'
    )
    assert result == []


def test_extract_variables_from_includes_error_returns_empty(mock_gitlab_module):
    """Retorna lista vacía si hay error de conexión"""
    mock_gitlab_module.auth.side_effect = Exception("timeout")

    manager = TemplateManager('grupo/plantillas')
    result = manager.extract_variables_from_includes({}, 'https://gitlab.com', 'token')
    assert result == []


def test_extract_variables_from_includes_file_not_found(mock_gitlab_module):
    """Maneja error cuando el archivo include no existe en el repo"""
    mock_project = Mock()
    mock_project.repository_tree = Mock(return_value=[
        {'type': 'blob', 'path': 'includes/base.yml'}
    ])
    mock_project.files.get = Mock(side_effect=Exception("404 Not Found"))
    mock_gitlab_module.projects.get = Mock(return_value=mock_project)

    manager = TemplateManager('grupo/plantillas')
    templates = {"ci.yaml": "include:\n  - file: '/includes/base.yml'"}
    # No debe lanzar excepción
    result = manager.extract_variables_from_includes(
        templates, 'https://gitlab.com', 'token'
    )
    assert isinstance(result, list)
