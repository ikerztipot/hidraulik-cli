"""
Tests para el módulo GitLabClient
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
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
