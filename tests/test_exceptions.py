"""
Tests para el módulo de excepciones
"""

import pytest
from hidraulik.exceptions import (
    GitLabCICDError,
    AuthenticationError,
    ProjectNotFoundError,
    ValidationError,
    ConfigurationError,
    TemplateError,
    TemplateNotFoundError,
    GitLabAPIError
)


class TestGitLabCICDError:
    """Tests para la excepción base"""
    
    def test_base_exception_with_message(self):
        """Test excepción base con mensaje"""
        error = GitLabCICDError("Error genérico")
        assert str(error) == "Error genérico"
        assert error.message == "Error genérico"
        assert error.details == {}
    
    def test_base_exception_with_details(self):
        """Test excepción base con detalles"""
        details = {'code': 500, 'reason': 'Internal error'}
        error = GitLabCICDError("Error con detalles", details=details)
        assert error.message == "Error con detalles"
        assert error.details == details
        assert error.details['code'] == 500


class TestAuthenticationError:
    """Tests para errores de autenticación"""
    
    def test_authentication_error_basic(self):
        """Test error de autenticación básico"""
        error = AuthenticationError("Token inválido")
        assert "Token inválido" in str(error)
        assert isinstance(error, GitLabCICDError)
        assert isinstance(error, GitLabAPIError)
    
    def test_authentication_error_default_message(self):
        """Test error de autenticación con mensaje por defecto"""
        error = AuthenticationError()
        assert "Token inválido" in str(error) or "expirado" in str(error)
        assert error.status_code == 401
    
    def test_authentication_error_inheritance(self):
        """Test que hereda correctamente de la base"""
        error = AuthenticationError("Test")
        assert isinstance(error, GitLabCICDError)
        assert isinstance(error, GitLabAPIError)
        assert isinstance(error, Exception)


class TestProjectNotFoundError:
    """Tests para errores de proyecto no encontrado"""
    
    def test_project_not_found_basic(self):
        """Test error básico de proyecto no encontrado"""
        error = ProjectNotFoundError("grupo/proyecto")
        assert "grupo/proyecto" in str(error)
        assert error.project_path == "grupo/proyecto"
        assert error.status_code == 404
    
    def test_project_not_found_inheritance(self):
        """Test que hereda correctamente"""
        error = ProjectNotFoundError("test/project")
        assert isinstance(error, GitLabAPIError)
        assert isinstance(error, GitLabCICDError)


class TestValidationError:
    """Tests para errores de validación"""
    
    def test_validation_error_basic(self):
        """Test error de validación básico"""
        error = ValidationError('namespace', 'Production', 'Debe ser minúsculas')
        assert 'namespace' in str(error)
        assert 'Production' in error.value
        assert 'minúsculas' in error.reason
    
    def test_validation_error_attributes(self):
        """Test que los atributos se almacenan correctamente"""
        error = ValidationError('port', '99999', 'Puerto inválido')
        assert error.field == 'port'
        assert error.value == '99999'
        assert error.reason == 'Puerto inválido'


class TestConfigurationError:
    """Tests para errores de configuración"""
    
    def test_configuration_error_missing_config(self):
        """Test error de configuración faltante"""
        error = ConfigurationError("Configuración no inicializada")
        assert "no inicializada" in str(error)
    
    def test_configuration_error_with_details(self):
        """Test error con detalles de campos faltantes"""
        details = {
            'missing_fields': ['gitlab_url', 'gitlab_token'],
            'config_file': '~/.hidraulik/config.json'
        }
        error = ConfigurationError("Faltan campos", details=details)
        assert 'gitlab_url' in error.details['missing_fields']
        assert 'gitlab_token' in error.details['missing_fields']


class TestTemplateError:
    """Tests para errores de plantillas"""
    
    def test_template_error_not_found(self):
        """Test error de plantilla no encontrada"""
        error = TemplateError("Plantilla deployment.yaml no encontrada")
        assert "deployment.yaml" in str(error)
    
    def test_template_error_with_details(self):
        """Test error con detalles de sintaxis"""
        details = {
            'template': 'gitlab-ci.yml',
            'line': 42,
            'syntax_error': 'Invalid Jinja2 syntax'
        }
        error = TemplateError("Error de sintaxis", details=details)
        assert error.details['line'] == 42


class TestTemplateNotFoundError:
    """Tests para errores de plantilla no encontrada"""
    
    def test_template_not_found_basic(self):
        """Test error básico de plantilla no encontrada"""
        error = TemplateNotFoundError("deployment.yaml.j2")
        assert "deployment.yaml.j2" in str(error)
        assert error.template_path == "deployment.yaml.j2"
    
    def test_template_not_found_inheritance(self):
        """Test que hereda de TemplateError"""
        error = TemplateNotFoundError("template.j2")
        assert isinstance(error, TemplateError)
        assert isinstance(error, GitLabCICDError)


class TestGitLabAPIError:
    """Tests para errores de API de GitLab"""
    
    def test_gitlab_api_error_with_status_code(self):
        """Test error de API con código de estado"""
        error = GitLabAPIError("Error API", status_code=500)
        assert "Error API" in str(error)
        assert error.status_code == 500
    
    def test_gitlab_api_error_with_response_data(self):
        """Test error de API con datos de respuesta"""
        response_data = {'message': 'Internal error', 'error_code': 'E500'}
        error = GitLabAPIError("Error API", status_code=500, response_data=response_data)
        assert error.response_data['message'] == 'Internal error'


class TestExceptionHierarchy:
    """Tests para verificar la jerarquía de excepciones"""
    
    def test_all_inherit_from_base(self):
        """Test que todas las excepciones heredan de la base"""
        exceptions = [
            AuthenticationError("test"),
            ProjectNotFoundError("grupo/test"),
            ValidationError("field", "value", "reason"),
            ConfigurationError("test"),
            TemplateError("test"),
            TemplateNotFoundError("template.j2"),
            GitLabAPIError("test")
        ]
        
        for exc in exceptions:
            assert isinstance(exc, GitLabCICDError)
            assert isinstance(exc, Exception)
    
    def test_exception_catching_hierarchy(self):
        """Test que se pueden capturar por tipo base"""
        try:
            raise ValidationError("test", "value", "reason")
        except GitLabCICDError as e:
            assert isinstance(e, ValidationError)
    
    def test_specific_exception_catching(self):
        """Test que se pueden capturar específicamente"""
        try:
            raise AuthenticationError("Token inválido")
        except AuthenticationError as e:
            assert "Token inválido" in str(e)
        except GitLabCICDError:
            pytest.fail("Should have caught specific AuthenticationError")


class TestExceptionUsagePatterns:
    """Tests para patrones de uso comunes"""
    
    def test_exception_with_context_manager(self):
        """Test usar excepciones en context managers"""
        with pytest.raises(ValidationError) as exc_info:
            raise ValidationError("port", "99999", "Fuera de rango")
        
        assert "port" in str(exc_info.value)
        assert "99999" in exc_info.value.value
    
    def test_exception_chaining(self):
        """Test encadenar excepciones"""
        try:
            try:
                raise ValueError("Error original")
            except ValueError as e:
                raise ConfigurationError("Error de config") from e
        except ConfigurationError as e:
            assert e.__cause__ is not None
            assert isinstance(e.__cause__, ValueError)
    
    def test_exception_with_rich_details(self):
        """Test excepciones con detalles ricos para debugging"""
        details = {
            'timestamp': '2026-02-14T10:30:00Z',
            'user': 'testuser',
            'project': 'grupo/proyecto',
            'operation': 'create_pipeline',
            'environment': 'production'
        }
        
        error = GitLabCICDError("Operación falló", details=details)
        
        # Verificar que todos los detalles están disponibles
        assert error.details['user'] == 'testuser'
        assert error.details['project'] == 'grupo/proyecto'
        assert error.details['operation'] == 'create_pipeline'
