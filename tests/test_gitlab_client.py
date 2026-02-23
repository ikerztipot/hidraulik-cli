"""
Tests para el módulo GitLabClient
"""

import pytest
import gitlab
from unittest.mock import Mock, patch, MagicMock, call
from hidraulik.gitlab_client import GitLabClient


@pytest.fixture
def mock_gitlab():
    """Fixture que proporciona un mock de GitLab"""
    with patch('hidraulik.gitlab_client.gitlab.Gitlab') as mock_gl:
        mock_instance = Mock()
        mock_gl.return_value = mock_instance
        mock_instance.auth.return_value = None
        mock_instance.user = Mock()
        mock_instance.user.__dict__ = {'_attrs': {'username': 'testuser', 'id': 1}}
        yield mock_instance


def _make_project_mock(id=123, name='test-project', web_url='https://gitlab.com/test/test-project'):
    """Helper para crear un mock de proyecto con los _attrs correctos."""
    p = Mock()
    p.__dict__ = {'_attrs': {'id': id, 'name': name, 'web_url': web_url}}
    return p


def test_gitlab_client_init(mock_gitlab):
    """Test de inicialización del cliente"""
    client = GitLabClient('https://gitlab.com', 'test-token')
    assert client is not None
    mock_gitlab.auth.assert_called_once()


def test_get_current_user(mock_gitlab):
    """Test de obtención del usuario actual"""
    client = GitLabClient('https://gitlab.com', 'test-token')
    user = client.get_current_user()
    assert user['username'] == 'testuser'
    assert user['id'] == 1


def test_get_project(mock_gitlab):
    """Test de obtención de proyecto"""
    mock_project = Mock()
    mock_project.__dict__ = {
        '_attrs': {
            'id': 123,
            'name': 'test-project',
            'web_url': 'https://gitlab.com/test/test-project'
        }
    }
    mock_gitlab.projects = Mock()
    mock_gitlab.projects.get = Mock(return_value=mock_project)
    
    client = GitLabClient('https://gitlab.com', 'test-token')
    project = client.get_project('test/test-project')
    
    assert project['id'] == 123
    assert project['name'] == 'test-project'
    # GitLabClient hace URL-encoding del path (/ -> %2F)
    mock_gitlab.projects.get.assert_called_once_with('test%2Ftest-project')


def test_create_or_update_variable(mock_gitlab):
    """Test de creación/actualización de variable"""
    import gitlab
    
    mock_project = Mock()
    mock_project.variables = Mock()
    mock_project.variables.get = Mock(side_effect=gitlab.exceptions.GitlabGetError())
    mock_project.variables.create = Mock()
    mock_gitlab.projects = Mock()
    mock_gitlab.projects.get = Mock(return_value=mock_project)
    
    client = GitLabClient('https://gitlab.com', 'test-token')
    client.create_or_update_variable(123, 'TEST_VAR', 'test-value')
    
    mock_project.variables.create.assert_called_once()


def test_get_available_runners(mock_gitlab):
    """Test de obtención de runners disponibles"""
    mock_runner1 = Mock()
    mock_runner1.id = 1
    mock_runner1.description = "Runner 1"
    mock_runner1.active = True
    mock_runner1.is_shared = True
    mock_runner1.online = True
    mock_runner1.status = "online"
    mock_runner1.tag_list = ["docker", "linux"]
    
    mock_runner2 = Mock()
    mock_runner2.id = 2
    mock_runner2.description = "Runner 2"
    mock_runner2.active = True
    mock_runner2.is_shared = False
    mock_runner2.online = True
    mock_runner2.status = "online"
    mock_runner2.tag_list = ["buildkit", "scaleway"]
    
    # Mock para _enrich_runner_details - simula gl.runners.get()
    mock_runner_detail1 = Mock()
    mock_runner_detail1._attrs = {'tag_list': ["docker", "linux"]}
    
    mock_runner_detail2 = Mock()
    mock_runner_detail2._attrs = {'tag_list': ["buildkit", "scaleway"]}
    
    mock_gitlab.runners = Mock()
    mock_gitlab.runners.list = Mock(return_value=[mock_runner1, mock_runner2])
    mock_gitlab.runners.get = Mock(side_effect=[mock_runner_detail1, mock_runner_detail2])
    
    client = GitLabClient('https://gitlab.com', 'test-token')
    runners = client.get_available_runners(scope='active')
    
    assert len(runners) == 2
    assert runners[0]['id'] == 1
    assert runners[0]['tags'] == ["docker", "linux"]
    assert runners[1]['id'] == 2
    assert runners[1]['tags'] == ["buildkit", "scaleway"]


def test_get_group_runners(mock_gitlab):
    """Test de obtención de runners de grupo"""
    mock_runner = Mock()
    mock_runner.id = 10
    mock_runner.description = "Group Runner"
    mock_runner.active = True
    mock_runner.is_shared = False
    mock_runner.online = True
    mock_runner.status = "online"
    mock_runner.tag_list = ["worko-internal", "kubernetes"]
    
    # Mock para _enrich_runner_details
    mock_runner_detail = Mock()
    mock_runner_detail._attrs = {'tag_list': ["worko-internal", "kubernetes"]}
    
    mock_group = Mock()
    mock_group.runners = Mock()
    mock_group.runners.list = Mock(return_value=[mock_runner])
    
    mock_gitlab.groups = Mock()
    mock_gitlab.groups.get = Mock(return_value=mock_group)
    mock_gitlab.runners = Mock()
    mock_gitlab.runners.get = Mock(return_value=mock_runner_detail)
    
    client = GitLabClient('https://gitlab.com', 'test-token')
    runners = client.get_group_runners('clients')
    
    assert len(runners) == 1
    assert runners[0]['id'] == 10
    assert runners[0]['tags'] == ["worko-internal", "kubernetes"]


def test_get_project_runners(mock_gitlab):
    """Test de obtención de runners de proyecto"""
    mock_runner = Mock()
    mock_runner.id = 20
    mock_runner.description = "Project Runner"
    mock_runner.active = True
    mock_runner.is_shared = False
    mock_runner.online = True
    mock_runner.status = "online"
    mock_runner.tag_list = ["staging", "testing"]
    
    # Mock para _enrich_runner_details
    mock_runner_detail = Mock()
    mock_runner_detail._attrs = {'tag_list': ["staging", "testing"]}
    
    mock_project = Mock()
    mock_project.runners = Mock()
    mock_project.runners.list = Mock(return_value=[mock_runner])
    
    mock_gitlab.projects = Mock()
    mock_gitlab.projects.get = Mock(return_value=mock_project)
    mock_gitlab.runners = Mock()
    mock_gitlab.runners.get = Mock(return_value=mock_runner_detail)
    
    client = GitLabClient('https://gitlab.com', 'test-token')
    runners = client.get_project_runners('test/project')
    
    assert len(runners) == 1
    assert runners[0]['id'] == 20
    assert runners[0]['tags'] == ["staging", "testing"]
    assert runners[0]['id'] == 20
    assert runners[0]['tags'] == ["staging", "testing"]


# ─────────────────────────────────────────────────────────────────────────────
# Auth / init errors
# ─────────────────────────────────────────────────────────────────────────────

def test_gitlab_client_auth_error():
    """Test que lanza excepción cuando el token es inválido"""
    with patch('hidraulik.gitlab_client.gitlab.Gitlab') as mock_gl:
        mock_instance = Mock()
        mock_gl.return_value = mock_instance
        mock_instance.auth.side_effect = gitlab.exceptions.GitlabAuthenticationError(
            "401 Unauthorized", 401
        )
        with pytest.raises(Exception, match="Error de autenticación"):
            GitLabClient('https://gitlab.com', 'bad-token')


def test_gitlab_client_connection_error():
    """Test que lanza excepción cuando no puede conectar"""
    with patch('hidraulik.gitlab_client.gitlab.Gitlab') as mock_gl:
        mock_instance = Mock()
        mock_gl.return_value = mock_instance
        mock_instance.auth.side_effect = Exception("Connection refused")
        with pytest.raises(Exception, match="Error al conectar"):
            GitLabClient('https://gitlab.com', 'token')


# ─────────────────────────────────────────────────────────────────────────────
# get_project – fallback por búsqueda
# ─────────────────────────────────────────────────────────────────────────────

def test_get_project_fallback_search(mock_gitlab):
    """Test que si la ruta falla, busca por nombre"""
    # Objeto proyecto con path_with_namespace para la búsqueda por lista
    found_project = Mock()
    found_project.path_with_namespace = 'test/test-project'
    found_project.id = 123

    # Proyecto final retornado por get(id)
    project_final = _make_project_mock()
    mock_gitlab.projects = Mock()
    mock_gitlab.projects.get = Mock(
        side_effect=[gitlab.exceptions.GitlabGetError("404", 404), project_final]
    )
    mock_gitlab.projects.list = Mock(return_value=[found_project])

    client = GitLabClient('https://gitlab.com', 'test-token')
    result = client.get_project('test/test-project')
    assert result['id'] == 123


def test_get_project_fallback_not_found(mock_gitlab):
    """Test que re-lanza si no encuentra el proyecto en la búsqueda"""
    mock_gitlab.projects = Mock()
    mock_gitlab.projects.get = Mock(
        side_effect=gitlab.exceptions.GitlabGetError("404", 404)
    )
    # Devuelve proyecto con ruta diferente
    mock_result = Mock()
    mock_result.path_with_namespace = 'other/project'
    mock_gitlab.projects.list = Mock(return_value=[mock_result])

    client = GitLabClient('https://gitlab.com', 'test-token')
    with pytest.raises(gitlab.exceptions.GitlabGetError):
        client.get_project('test/test-project')


# ─────────────────────────────────────────────────────────────────────────────
# create_or_update_file
# ─────────────────────────────────────────────────────────────────────────────

def test_create_or_update_file_creates_new(mock_gitlab):
    """Test que crea un archivo cuando no existe"""
    mock_project = Mock()
    mock_file = Mock()
    mock_project.files.get = Mock(
        side_effect=gitlab.exceptions.GitlabGetError("404", 404)
    )
    mock_project.files.create = Mock()
    mock_gitlab.projects.get = Mock(return_value=mock_project)

    client = GitLabClient('https://gitlab.com', 'test-token')
    client.create_or_update_file(123, '.gitlab-ci.yml', 'content', 'init commit')

    mock_project.files.create.assert_called_once()
    call_kwargs = mock_project.files.create.call_args[0][0]
    assert call_kwargs['file_path'] == '.gitlab-ci.yml'
    assert call_kwargs['content'] == 'content'


def test_create_or_update_file_updates_existing(mock_gitlab):
    """Test que actualiza un archivo cuando ya existe"""
    mock_project = Mock()
    mock_file = Mock()
    mock_project.files.get = Mock(return_value=mock_file)
    mock_gitlab.projects.get = Mock(return_value=mock_project)

    client = GitLabClient('https://gitlab.com', 'test-token')
    client.create_or_update_file(
        'group/proj', '.gitlab-ci.yml', 'new content', 'update commit', branch='develop'
    )

    assert mock_file.content == 'new content'
    mock_file.save.assert_called_once_with(branch='develop', commit_message='update commit')


# ─────────────────────────────────────────────────────────────────────────────
# create_or_update_variable – escenario de actualización
# ─────────────────────────────────────────────────────────────────────────────

def test_create_or_update_variable_updates_existing(mock_gitlab):
    """Test que actualiza variable cuando ya existe con mismo scope"""
    mock_project = Mock()
    mock_var = Mock()
    mock_var.key = 'MY_VAR'
    mock_var.environment_scope = '*'
    mock_project.variables.list = Mock(return_value=[mock_var])
    mock_gitlab.projects.get = Mock(return_value=mock_project)

    client = GitLabClient('https://gitlab.com', 'test-token')
    client.create_or_update_variable(123, 'MY_VAR', 'new-value', masked=True)

    assert mock_var.value == 'new-value'
    assert mock_var.masked is True
    mock_var.save.assert_called_once()


def test_create_or_update_variable_409_fallback(mock_gitlab):
    """Test que si create lanza 409, busca y actualiza manualmente"""
    mock_project = Mock()
    mock_var = Mock()
    mock_var.key = 'X'
    mock_var.environment_scope = '*'

    # Primera lista: no encuentra la variable
    # create lanza 409
    mock_project.variables.list = Mock(side_effect=[[], [mock_var]])
    mock_project.variables.create = Mock(
        side_effect=gitlab.exceptions.GitlabCreateError("409", 409)
    )
    mock_gitlab.projects.get = Mock(return_value=mock_project)

    client = GitLabClient('https://gitlab.com', 'test-token')
    client.create_or_update_variable(123, 'X', 'val')

    # El fallback debe haber actualizado la variable
    assert mock_var.value == 'val'
    mock_var.save.assert_called_once()


def test_create_or_update_variable_other_error_raises(mock_gitlab):
    """Test que errores distintos a 409 se re-lanzan"""
    mock_project = Mock()
    mock_project.variables.list = Mock(return_value=[])
    mock_project.variables.create = Mock(
        side_effect=gitlab.exceptions.GitlabCreateError("500 Server Error", 500)
    )
    mock_gitlab.projects.get = Mock(return_value=mock_project)

    client = GitLabClient('https://gitlab.com', 'test-token')
    with pytest.raises(gitlab.exceptions.GitlabCreateError):
        client.create_or_update_variable(123, 'FAIL', 'val')


# ─────────────────────────────────────────────────────────────────────────────
# get_variables
# ─────────────────────────────────────────────────────────────────────────────

def test_get_variables(mock_gitlab):
    """Test que retorna variables del proyecto"""
    mock_project = Mock()
    var1 = Mock()
    var1.__dict__ = {'_attrs': {'key': 'A', 'value': '1'}}
    var2 = Mock()
    var2.__dict__ = {'_attrs': {'key': 'B', 'value': '2'}}
    mock_project.variables.list = Mock(return_value=[var1, var2])
    mock_gitlab.projects.get = Mock(return_value=mock_project)

    client = GitLabClient('https://gitlab.com', 'test-token')
    result = client.get_variables(123)

    assert len(result) == 2
    assert result[0]['key'] == 'A'
    assert result[1]['key'] == 'B'


# ─────────────────────────────────────────────────────────────────────────────
# get_pipelines
# ─────────────────────────────────────────────────────────────────────────────

def test_get_pipelines(mock_gitlab):
    """Test que retorna pipelines del proyecto"""
    mock_project = Mock()
    pipe1 = Mock()
    pipe1.__dict__ = {'_attrs': {'id': 10, 'status': 'success'}}
    mock_project.pipelines.list = Mock(return_value=[pipe1])
    mock_gitlab.projects.get = Mock(return_value=mock_project)

    client = GitLabClient('https://gitlab.com', 'test-token')
    result = client.get_pipelines(123, per_page=5, page=2)

    mock_project.pipelines.list.assert_called_once_with(per_page=5, page=2)
    assert result[0]['id'] == 10


# ─────────────────────────────────────────────────────────────────────────────
# get_file_content
# ─────────────────────────────────────────────────────────────────────────────

def test_get_file_content(mock_gitlab):
    """Test que retorna el contenido de un archivo"""
    mock_project = Mock()
    mock_file = Mock()
    mock_file.decode.return_value = b'hello world'
    mock_project.files.get = Mock(return_value=mock_file)
    mock_gitlab.projects.get = Mock(return_value=mock_project)

    client = GitLabClient('https://gitlab.com', 'test-token')
    content = client.get_file_content(123, 'README.md', ref='develop')

    assert content == 'hello world'
    mock_project.files.get.assert_called_once_with(file_path='README.md', ref='develop')


# ─────────────────────────────────────────────────────────────────────────────
# list_repository_tree
# ─────────────────────────────────────────────────────────────────────────────

def test_list_repository_tree(mock_gitlab):
    """Test que retorna el árbol del repositorio"""
    mock_project = Mock()
    items = [
        {'type': 'blob', 'path': 'README.md'},
        {'type': 'tree', 'path': 'src'},
    ]
    mock_project.repository_tree = Mock(return_value=items)
    mock_gitlab.projects.get = Mock(return_value=mock_project)

    client = GitLabClient('https://gitlab.com', 'test-token')
    result = client.list_repository_tree(123, path='', ref='main', recursive=True)

    assert len(result) == 2
    mock_project.repository_tree.assert_called_once_with(
        path='', ref='main', recursive=True, get_all=True
    )


# ─────────────────────────────────────────────────────────────────────────────
# create_project_if_not_exists – personal namespace
# ─────────────────────────────────────────────────────────────────────────────

def test_create_project_if_not_exists_returns_existing(mock_gitlab):
    """Test que retorna el proyecto si ya existe"""
    mock_project = _make_project_mock()
    mock_gitlab.projects.get = Mock(return_value=mock_project)

    client = GitLabClient('https://gitlab.com', 'test-token')
    result = client.create_project_if_not_exists('test/test-project')

    assert result['id'] == 123


def test_create_project_if_not_exists_personal_namespace(mock_gitlab):
    """Test creación de proyecto en namespace personal"""
    # get lanza 404, luego create funciona
    new_project = _make_project_mock(id=200, name='newproj')
    mock_gitlab.projects.get = Mock(
        side_effect=gitlab.exceptions.GitlabGetError("404", 404)
    )
    mock_gitlab.projects.list = Mock(return_value=[])
    mock_gitlab.projects.create = Mock(return_value=new_project)

    client = GitLabClient('https://gitlab.com', 'test-token')
    result = client.create_project_if_not_exists('newproj')

    mock_gitlab.projects.create.assert_called_once_with({'name': 'newproj'})
    assert result['id'] == 200


def test_create_project_if_not_exists_with_group(mock_gitlab):
    """Test creación de proyecto dentro de un grupo existente"""
    new_project = _make_project_mock(id=300, name='myapp')

    # projects.get falla (proyecto no existe), luego projects.list tampoco lo encuentra
    mock_gitlab.projects.get = Mock(
        side_effect=gitlab.exceptions.GitlabGetError("404", 404)
    )
    mock_gitlab.projects.list = Mock(return_value=[])

    # group existe
    mock_group = Mock()
    mock_group.id = 10
    mock_gitlab.groups = Mock()
    mock_gitlab.groups.get = Mock(return_value=mock_group)

    # project.create exitoso
    mock_gitlab.projects.create = Mock(return_value=new_project)

    client = GitLabClient('https://gitlab.com', 'test-token')
    result = client.create_project_if_not_exists('mygroup/myapp')

    mock_gitlab.projects.create.assert_called_once()
    assert result['id'] == 300


def test_create_project_if_not_exists_creates_group(mock_gitlab):
    """Test creación de grupo nuevo cuando no existe"""
    new_project = _make_project_mock(id=400, name='app')

    # projects.get falla
    mock_gitlab.projects.get = Mock(
        side_effect=gitlab.exceptions.GitlabGetError("404", 404)
    )
    mock_gitlab.projects.list = Mock(return_value=[])

    # group no existe, lo crea
    mock_new_group = Mock()
    mock_new_group.id = 20
    mock_gitlab.groups = Mock()
    mock_gitlab.groups.get = Mock(
        side_effect=gitlab.exceptions.GitlabGetError("404", 404)
    )
    mock_gitlab.groups.create = Mock(return_value=mock_new_group)

    mock_gitlab.projects.create = Mock(return_value=new_project)

    client = GitLabClient('https://gitlab.com', 'test-token')
    result = client.create_project_if_not_exists('newgroup/app')

    mock_gitlab.groups.create.assert_called_once()
    assert result['id'] == 400


def test_create_or_update_variable_list_exception_continues(mock_gitlab):
    """Test que si variables.list falla, intenta crear directamente"""
    mock_project = Mock()
    mock_project.variables.list = Mock(side_effect=Exception("forbidden"))
    mock_project.variables.create = Mock()
    mock_gitlab.projects.get = Mock(return_value=mock_project)

    client = GitLabClient('https://gitlab.com', 'test-token')
    client.create_or_update_variable(123, 'MY_VAR', 'value')

    mock_project.variables.create.assert_called_once()


# ─────────────────────────────────────────────────────────────────────────────
# _enrich_runner_details – fallback sin tags
# ─────────────────────────────────────────────────────────────────────────────

def test_enrich_runner_details_no_tags(mock_gitlab):
    """Test que maneja runners sin tags en los detalles"""
    mock_runner = Mock()
    mock_runner.id = 99
    mock_runner.description = 'no tags runner'
    mock_runner.active = True
    mock_runner.is_shared = True
    mock_runner.online = False
    mock_runner.status = 'offline'

    mock_gitlab.runners = Mock()
    mock_gitlab.runners.list = Mock(return_value=[mock_runner])
    mock_gitlab.runners.get = Mock(
        side_effect=gitlab.exceptions.GitlabGetError("403", 403)
    )

    client = GitLabClient('https://gitlab.com', 'test-token')
    runners = client.get_available_runners()

    # Se enriquece sin lanzar excepción, tags vacíos
    assert runners[0]['id'] == 99
    assert runners[0]['tags'] == []


# ─────────────────────────────────────────────────────────────────────────────
# get_available_runners / get_group_runners / get_project_runners – errores
# ─────────────────────────────────────────────────────────────────────────────

def test_get_available_runners_error_returns_empty(mock_gitlab):
    """Test que retorna lista vacía si falla listar runners"""
    mock_gitlab.runners = Mock()
    mock_gitlab.runners.list = Mock(
        side_effect=gitlab.exceptions.GitlabListError("403", 403)
    )

    client = GitLabClient('https://gitlab.com', 'test-token')
    result = client.get_available_runners()
    assert result == []


def test_get_group_runners_error_returns_empty(mock_gitlab):
    """Test que retorna lista vacía si el grupo no existe"""
    mock_gitlab.groups = Mock()
    mock_gitlab.groups.get = Mock(
        side_effect=gitlab.exceptions.GitlabGetError("404", 404)
    )

    client = GitLabClient('https://gitlab.com', 'test-token')
    result = client.get_group_runners('no/group')
    assert result == []


def test_get_project_runners_error_returns_empty(mock_gitlab):
    """Test que retorna lista vacía si el proyecto no existe"""
    mock_gitlab.projects = Mock()
    mock_gitlab.projects.get = Mock(
        side_effect=gitlab.exceptions.GitlabGetError("404", 404)
    )

    client = GitLabClient('https://gitlab.com', 'test-token')
    result = client.get_project_runners('no/project')
    assert result == []
