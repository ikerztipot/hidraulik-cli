"""
Tests para el módulo Config
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from gitlab_cicd_creator.config import Config


@pytest.fixture
def temp_config_dir():
    """Fixture que proporciona un directorio temporal para configuración"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


def test_config_init(temp_config_dir):
    """Test de inicialización de configuración"""
    config = Config(config_dir=temp_config_dir)
    assert config.config_dir == Path(temp_config_dir)
    # El archivo de config se crea al guardar, no en el init
    assert not config.config_file.exists()


def test_config_set_and_get(temp_config_dir):
    """Test de establecer y obtener valores"""
    config = Config(config_dir=temp_config_dir)
    config.set('test_key', 'test_value')
    assert config.get('test_key') == 'test_value'


def test_config_save_and_load(temp_config_dir):
    """Test de guardar y cargar configuración"""
    config = Config(config_dir=temp_config_dir)
    config.set('gitlab_url', 'https://gitlab.com')
    config.set('gitlab_token', 'test-token')
    config.save()
    
    # Crear nueva instancia y verificar que se cargó
    config2 = Config(config_dir=temp_config_dir)
    assert config2.get('gitlab_url') == 'https://gitlab.com'
    assert config2.get('gitlab_token') == 'test-token'


def test_config_delete(temp_config_dir):
    """Test de eliminación de clave"""
    config = Config(config_dir=temp_config_dir)
    config.set('test_key', 'test_value')
    assert config.get('test_key') == 'test_value'
    
    config.delete('test_key')
    assert config.get('test_key') is None


def test_config_is_configured(temp_config_dir):
    """Test de verificación de configuración completa"""
    config = Config(config_dir=temp_config_dir)
    assert not config.is_configured()
    
    config.set('gitlab_url', 'https://gitlab.com')
    assert not config.is_configured()
    
    config.set('gitlab_token', 'test-token')
    assert not config.is_configured()  # Aún falta template_repo
    
    config.set('template_repo', 'grupo/plantillas')
    assert config.is_configured()  # Ahora sí está completo


def test_config_clear(temp_config_dir):
    """Test de limpieza de configuración"""
    config = Config(config_dir=temp_config_dir)
    config.set('test_key', 'test_value')
    config.save()
    
    config.clear()
    assert config.get('test_key') is None
    assert not config.config_file.exists()


def test_config_get_with_default(temp_config_dir):
    """Test de obtención con valor por defecto"""
    config = Config(config_dir=temp_config_dir)
    assert config.get('nonexistent', 'default') == 'default'
