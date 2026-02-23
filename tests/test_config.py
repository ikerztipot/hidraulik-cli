"""
Tests para el módulo Config
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from hidraulik.config import Config


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


# ─────────────────────────────────────────────────────────────────────────────
# Token seguro – keyring disponible
# ─────────────────────────────────────────────────────────────────────────────

def test_save_token_secure_with_keyring(temp_config_dir):
    """Test que guarda el token en keyring cuando está disponible"""
    import unittest.mock as mock

    with mock.patch('hidraulik.config.KEYRING_AVAILABLE', True):
        with mock.patch('hidraulik.config.keyring') as mock_keyring:
            config = Config(config_dir=temp_config_dir)
            config.set('gitlab_url', 'https://gitlab.com')
            config.set('gitlab_token', 'my-token')
            config.set('template_repo', 'g/t')
            config.save()

            mock_keyring.set_password.assert_called_once_with(
                Config.KEYRING_SERVICE, Config.KEYRING_TOKEN_KEY, 'my-token'
            )


def test_get_token_secure_from_keyring(temp_config_dir):
    """Test que obtiene el token desde keyring cuando está disponible"""
    import unittest.mock as mock

    with mock.patch('hidraulik.config.KEYRING_AVAILABLE', True):
        with mock.patch('hidraulik.config.keyring') as mock_keyring:
            mock_keyring.get_password.return_value = 'keyring-token'
            config = Config(config_dir=temp_config_dir)
            token = config.get('gitlab_token')
            assert token == 'keyring-token'


def test_get_token_secure_keyring_none_falls_to_file(temp_config_dir):
    """Test que si keyring retorna None, usa el archivo fallback"""
    import unittest.mock as mock

    with mock.patch('hidraulik.config.KEYRING_AVAILABLE', True):
        with mock.patch('hidraulik.config.keyring') as mock_keyring:
            mock_keyring.get_password.return_value = None

            # Crear archivo de token fallback
            token_file = Path(temp_config_dir) / '.token'
            token_file.write_text('file-token')

            config = Config(config_dir=temp_config_dir)
            token = config.get('gitlab_token')
            assert token == 'file-token'


def test_save_token_secure_keyring_fails_fallback(temp_config_dir):
    """Test que si keyring.set_password falla, usa archivo fallback"""
    import unittest.mock as mock

    with mock.patch('hidraulik.config.KEYRING_AVAILABLE', True):
        with mock.patch('hidraulik.config.keyring') as mock_keyring:
            mock_keyring.set_password.side_effect = Exception("keyring unavailable")

            config = Config(config_dir=temp_config_dir)
            config.set('gitlab_url', 'https://gitlab.com')
            config.set('gitlab_token', 'fallback-token')
            config.set('template_repo', 'g/t')
            config.save()

            # El token debe haberse guardado en el archivo
            token_file = Path(temp_config_dir) / '.token'
            assert token_file.exists()
            assert token_file.read_text() == 'fallback-token'


def test_clear_removes_keyring_token(temp_config_dir):
    """Test que clear elimina el token del keyring"""
    import unittest.mock as mock

    with mock.patch('hidraulik.config.KEYRING_AVAILABLE', True):
        with mock.patch('hidraulik.config.keyring') as mock_keyring:
            config = Config(config_dir=temp_config_dir)
            config.set('test', 'val')
            config.save()
            config.clear()

            mock_keyring.delete_password.assert_called_once()


def test_clear_keyring_delete_exception_ignored(temp_config_dir):
    """Test que clear no falla si delete_password lanza excepción"""
    import unittest.mock as mock

    with mock.patch('hidraulik.config.KEYRING_AVAILABLE', True):
        with mock.patch('hidraulik.config.keyring') as mock_keyring:
            mock_keyring.delete_password.side_effect = Exception("not found")
            config = Config(config_dir=temp_config_dir)
            config.clear()  # No debe lanzar excepción


def test_delete_nonexistent_key_no_error(temp_config_dir):
    """Test que delete de una clave inexistente no lanza error"""
    config = Config(config_dir=temp_config_dir)
    config.delete('key_that_does_not_exist')  # No debe lanzar


def test_config_token_not_saved_in_json(temp_config_dir):
    """Test que el token no se guarda en el JSON del archivo"""
    config = Config(config_dir=temp_config_dir)
    config.set('gitlab_url', 'https://gitlab.com')
    config.set('gitlab_token', 'secret-token')
    config.set('template_repo', 'g/t')
    config.save()

    import json
    with open(config.config_file) as f:
        data = json.load(f)
    assert 'gitlab_token' not in data


def test_get_token_returns_default_when_no_token(temp_config_dir):
    """Test que get('gitlab_token') retorna default cuando no hay token guardado"""
    import unittest.mock as mock

    with mock.patch('hidraulik.config.KEYRING_AVAILABLE', True):
        with mock.patch('hidraulik.config.keyring') as mock_keyring:
            mock_keyring.get_password.return_value = None  # Sin token en keyring
            config = Config(config_dir=temp_config_dir)
            result = config.get('gitlab_token', 'my-default')
            assert result == 'my-default'


def test_get_token_secure_keyring_exception_falls_to_file(temp_config_dir):
    """Test que si keyring.get_password lanza excepción, usa el archivo"""
    import unittest.mock as mock

    # Crear archivo de token fallback
    token_file = Path(temp_config_dir) / '.token'
    token_file.write_text('file-token')

    with mock.patch('hidraulik.config.KEYRING_AVAILABLE', True):
        with mock.patch('hidraulik.config.keyring') as mock_keyring:
            mock_keyring.get_password.side_effect = Exception("keyring backend error")

            config = Config(config_dir=temp_config_dir)
            token = config.get('gitlab_token')
            assert token == 'file-token'


def test_clear_removes_token_file(temp_config_dir):
    """Test que clear elimina el archivo .token si existe"""
    token_file = Path(temp_config_dir) / '.token'
    token_file.write_text('my-secret-token')

    config = Config(config_dir=temp_config_dir)
    config.clear()

    assert not token_file.exists()
