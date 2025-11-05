"""
Tests para el módulo GitLabClient
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from gitlab_cicd_creator.gitlab_client import GitLabClient


@pytest.fixture
def mock_gitlab():
    """Fixture que proporciona un mock de GitLab"""
    with patch('gitlab_cicd_creator.gitlab_client.gitlab.Gitlab') as mock_gl:
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
    mock_gitlab.projects.get.assert_called_once_with('test/test-project')


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
