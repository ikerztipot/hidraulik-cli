"""
Tests para el módulo CLI
"""

import pytest
from click.testing import CliRunner
from gitlab_cicd_creator.cli import main


@pytest.fixture
def runner():
    """Fixture que proporciona un runner de Click"""
    return CliRunner()


def test_main_help(runner):
    """Test del comando de ayuda principal"""
    result = runner.invoke(main, ['--help'])
    assert result.exit_code == 0
    assert 'GitLab CI/CD Creator' in result.output


def test_version(runner):
    """Test del comando de versión"""
    result = runner.invoke(main, ['--version'])
    assert result.exit_code == 0
    assert '0.1.0' in result.output


def test_init_help(runner):
    """Test del comando init --help"""
    result = runner.invoke(main, ['init', '--help'])
    assert result.exit_code == 0
    assert 'Inicializa la configuración' in result.output


def test_create_help(runner):
    """Test del comando create --help"""
    result = runner.invoke(main, ['create', '--help'])
    assert result.exit_code == 0
    assert 'Crea el CI/CD' in result.output


def test_status_help(runner):
    """Test del comando status --help"""
    result = runner.invoke(main, ['status', '--help'])
    assert result.exit_code == 0
    assert 'estado del CI/CD' in result.output


def test_set_variable_help(runner):
    """Test del comando set-variable --help"""
    result = runner.invoke(main, ['set-variable', '--help'])
    assert result.exit_code == 0
    assert 'variable CI/CD' in result.output


def test_list_templates_help(runner):
    """Test del comando list-templates --help"""
    result = runner.invoke(main, ['list-templates', '--help'])
    assert result.exit_code == 0
    assert 'plantillas disponibles' in result.output
