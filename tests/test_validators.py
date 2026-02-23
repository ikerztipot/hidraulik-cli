"""
Tests para el módulo de validadores
"""

import pytest
from hidraulik.validators import (
    validate_k8s_namespace,
    validate_project_path,
    validate_component_name,
    validate_variable_name,
    validate_port,
    validate_storage_size,
    validate_runner_tags,
    sanitize_file_path
)
from hidraulik.exceptions import ValidationError


class TestK8sNamespaceValidation:
    """Tests para validación de namespaces de Kubernetes"""
    
    def test_valid_namespaces(self):
        """Namespaces válidos según RFC 1123"""
        valid_names = [
            'production',
            'dev-environment',
            'staging123',
            'test-ns-01',
            'a',
            'a' * 63  # máximo permitido
        ]
        for name in valid_names:
            assert validate_k8s_namespace(name) is True
    
    def test_invalid_namespace_empty(self):
        """Namespace vacío debe fallar"""
        with pytest.raises(ValidationError) as exc:
            validate_k8s_namespace('')
        assert 'No puede estar vacío' in str(exc.value)
    
    def test_invalid_namespace_too_long(self):
        """Namespace > 63 caracteres debe fallar"""
        with pytest.raises(ValidationError) as exc:
            validate_k8s_namespace('a' * 64)
        assert 'Máximo 63 caracteres' in str(exc.value)
    
    def test_invalid_namespace_uppercase(self):
        """Namespace con mayúsculas debe fallar"""
        with pytest.raises(ValidationError) as exc:
            validate_k8s_namespace('Production')
        assert 'DNS-1123' in str(exc.value)
    
    def test_invalid_namespace_special_chars(self):
        """Namespace con caracteres especiales debe fallar"""
        invalid_names = ['prod_env', 'test@prod', 'stage.env', 'dev/test']
        for name in invalid_names:
            with pytest.raises(ValidationError):
                validate_k8s_namespace(name)
    
    def test_invalid_namespace_starts_with_hyphen(self):
        """Namespace que empieza con guión debe fallar"""
        with pytest.raises(ValidationError) as exc:
            validate_k8s_namespace('-production')
        assert 'DNS-1123' in str(exc.value)
    
    def test_invalid_namespace_ends_with_hyphen(self):
        """Namespace que termina con guión debe fallar"""
        with pytest.raises(ValidationError) as exc:
            validate_k8s_namespace('production-')
        assert 'DNS-1123' in str(exc.value)


class TestProjectPathValidation:
    """Tests para validación de rutas de proyectos GitLab"""
    
    def test_valid_project_paths(self):
        """Rutas válidas de proyectos"""
        valid_paths = [
            'grupo/proyecto',
            'grupo/subgrupo/proyecto',
            'clients/internal-infrastructure/cicd-templates',
            'org/team/app/backend',
            'test-group/my-project-123'
        ]
        for path in valid_paths:
            assert validate_project_path(path) is True
    
    def test_invalid_project_path_empty(self):
        """Ruta vacía debe fallar"""
        with pytest.raises(ValidationError) as exc:
            validate_project_path('')
        assert 'vacío' in str(exc.value).lower() or 'vac' in str(exc.value).lower()
    
    def test_invalid_project_path_no_slash(self):
        """Ruta sin separador debe fallar"""
        with pytest.raises(ValidationError) as exc:
            validate_project_path('proyecto')
        assert 'namespace' in str(exc.value).lower()
    
    def test_invalid_project_path_starts_with_slash(self):
        """Ruta que empieza con / debe fallar"""
        with pytest.raises(ValidationError) as exc:
            validate_project_path('/grupo/proyecto')
        assert 'No puede' in str(exc.value)
    
    def test_invalid_project_path_ends_with_slash(self):
        """Ruta que termina con / debe fallar"""
        with pytest.raises(ValidationError) as exc:
            validate_project_path('grupo/proyecto/')
        assert 'No puede' in str(exc.value)
    
    def test_invalid_project_path_special_chars(self):
        """Ruta con caracteres no permitidos debe fallar"""
        invalid_paths = [
            'grupo@test/proyecto',
            'grupo/proyecto$test',
            'grupo test/proyecto',
            'grupo#/proyecto'
        ]
        for path in invalid_paths:
            with pytest.raises(ValidationError):
                validate_project_path(path)


class TestComponentNameValidation:
    """Tests para validación de nombres de componentes"""
    
    def test_valid_component_names(self):
        """Nombres válidos de componentes"""
        valid_names = [
            'api-backend',
            'frontend-app',
            'database-service',
            'worker-01',
            'app123'
        ]
        for name in valid_names:
            assert validate_component_name(name) is True
    
    def test_invalid_component_name_uppercase(self):
        """Nombre con mayúsculas debe fallar"""
        with pytest.raises(ValidationError):
            validate_component_name('API-Backend')
    
    def test_invalid_component_name_underscore(self):
        """Nombre con guiones bajos debe fallar"""
        with pytest.raises(ValidationError):
            validate_component_name('api_backend')
    
    def test_invalid_component_name_too_long(self):
        """Nombre > 63 caracteres debe fallar"""
        with pytest.raises(ValidationError) as exc:
            validate_component_name('a' * 64)
        assert 'Máximo 63 caracteres' in str(exc.value)


class TestVariableNameValidation:
    """Tests para validación de nombres de variables"""
    
    def test_valid_variable_names(self):
        """Nombres válidos de variables"""
        valid_names = [
            'DATABASE_URL',
            'API_KEY',
            'CICD_TOKEN',
            '_PRIVATE_VAR',
            'VAR123',
            'MY_APP_CONFIG'
        ]
        for name in valid_names:
            assert validate_variable_name(name) is True
    
    def test_invalid_variable_name_lowercase(self):
        """Nombre con minúsculas debe fallar"""
        with pytest.raises(ValidationError):
            validate_variable_name('database_url')
    
    def test_invalid_variable_name_special_chars(self):
        """Nombre con caracteres especiales debe fallar"""
        invalid_names = ['API-KEY', 'VAR.NAME', 'VAR@NAME', 'VAR NAME']
        for name in invalid_names:
            with pytest.raises(ValidationError):
                validate_variable_name(name)
    
    def test_invalid_variable_name_starts_with_number(self):
        """Nombre que empieza con número debe fallar"""
        with pytest.raises(ValidationError):
            validate_variable_name('123VAR')
    
    def test_invalid_variable_name_reserved(self):
        """Nombres reservados deben fallar"""
        reserved_names = ['PATH', 'HOME', 'USER', 'SHELL']
        for name in reserved_names:
            with pytest.raises(ValidationError) as exc:
                validate_variable_name(name)
            assert 'reservado' in str(exc.value).lower()


class TestDockerRegistryValidation:
    """Tests para validación de registros Docker"""
    
    # Estas funciones no existen en el código actual, comentamos los tests
    pass


class TestPortNumberValidation:
    """Tests para validación de números de puerto"""
    
    def test_valid_ports(self):
        """Puertos válidos"""
        valid_ports = ['80', '443', '8080', '3000', '5432', '27017', '65535']
        for port in valid_ports:
            assert validate_port(port) is True
    
    def test_invalid_port_non_numeric(self):
        """Puerto no numérico debe fallar"""
        with pytest.raises(ValidationError) as exc:
            validate_port('abc')
        assert 'número entero' in str(exc.value).lower()
    
    def test_invalid_port_too_low(self):
        """Puerto < 1 debe fallar"""
        with pytest.raises(ValidationError) as exc:
            validate_port('0')
        assert '1 y 65535' in str(exc.value) or 'entre' in str(exc.value).lower()
    
    def test_invalid_port_too_high(self):
        """Puerto > 65535 debe fallar"""
        with pytest.raises(ValidationError) as exc:
            validate_port('65536')
        assert '1 y 65535' in str(exc.value) or 'entre' in str(exc.value).lower()


class TestStorageSizeValidation:
    """Tests para validación de tamaños de almacenamiento"""
    
    def test_valid_storage_sizes(self):
        """Tamaños válidos de almacenamiento"""
        valid_sizes = ['100Mi', '1Gi', '10Gi', '500Gi', '1Ti', '50Mi', '1.5Gi']
        for size in valid_sizes:
            assert validate_storage_size(size) is True
    
    def test_invalid_storage_size_format(self):
        """Formato inválido debe fallar"""
        invalid_sizes = ['100MB', '500', 'abc', '10Gb', '-5Gi', 'Gi10']
        for size in invalid_sizes:
            with pytest.raises(ValidationError):
                validate_storage_size(size)


class TestRunnerTagsValidation:
    """Tests para validación de tags de runner"""
    
    def test_valid_runner_tags(self):
        """Tags válidos de runner"""
        valid_tags = [
            ['docker'],
            ['linux', 'docker'],
            ['buildkit', 'scaleway'],
            ['kubernetes', 'production']
        ]
        for tags in valid_tags:
            assert validate_runner_tags(tags) is True
    
    def test_invalid_runner_tags_empty_list(self):
        """Lista vacía debe fallar"""
        with pytest.raises(ValidationError) as exc:
            validate_runner_tags([])
        assert 'al menos un tag' in str(exc.value).lower()
    
    def test_invalid_runner_tags_empty_tag(self):
        """Tag vacío debe fallar"""
        with pytest.raises(ValidationError):
            validate_runner_tags(['docker', '', 'linux'])
    
    def test_invalid_runner_tags_special_chars(self):
        """Tags con caracteres especiales deben fallar"""
        invalid_tags_list = [
            ['docker@latest'],
            ['linux/ubuntu'],
            ['tag with spaces']
        ]
        for tags in invalid_tags_list:
            with pytest.raises(ValidationError):
                validate_runner_tags(tags)


class TestCpuRequestValidation:
    """Tests para validación de solicitudes de CPU"""
    pass  # Función no existe en código actual


class TestMemoryRequestValidation:
    """Tests para validación de solicitudes de memoria"""
    pass  # Función no existe en código actual


class TestSanitizeFilePath:
    """Tests para sanitización de rutas de archivos"""
    
    def test_sanitize_prevents_path_traversal(self):
        """Prevenir path traversal"""
        dangerous_paths = [
            '../../../etc/passwd',
            'config/../../../secret'
        ]
        for path in dangerous_paths:
            with pytest.raises(ValidationError) as exc:
                sanitize_file_path(path)
            assert 'path traversal' in str(exc.value).lower() or '..' in str(exc.value)
    
    def test_sanitize_prevents_absolute_paths(self):
        """Prevenir rutas absolutas"""
        with pytest.raises(ValidationError) as exc:
            sanitize_file_path('/etc/config')
        assert 'relativa' in str(exc.value).lower() or 'absolut' in str(exc.value).lower()
    
    def test_sanitize_normal_relative_paths(self):
        """Rutas relativas normales"""
        safe_paths = [
            'config/deployment.yaml',
            '.gitlab-ci.yml',
            'k8s/service.yaml'
        ]
        for path in safe_paths:
            result = sanitize_file_path(path)
            assert result == path or result == path.replace('\\', '/')


class TestEnvironmentNameValidation:
    """Tests para validación de nombres de entornos"""
    pass  # Función no existe en código actual


# ─────────────────────────────────────────────────────────────────────────────
# normalize_k8s_label / normalize_to_k8s_namespace – líneas sin cobertura
# ─────────────────────────────────────────────────────────────────────────────

from hidraulik.validators import normalize_k8s_label, normalize_to_k8s_namespace


class TestNormalizeK8sLabel:
    def test_truncates_long_name(self):
        """Nombres > 63 chars se truncan"""
        long_name = 'a' * 70
        result = normalize_k8s_label(long_name)
        assert len(result) <= 63

    def test_empty_string_returns_default(self):
        """Cadena vacía retorna el default"""
        result = normalize_k8s_label('', default='fallback')
        assert result == 'fallback'

    def test_all_special_chars_returns_default(self):
        """Solo chars especiales retorna default"""
        result = normalize_k8s_label('!!!---', default='safe')
        assert result == 'safe'


class TestNormalizeToK8sNamespace:
    def test_basic_normalization(self):
        result = normalize_to_k8s_namespace('My_App Name')
        assert result.islower()
        assert ' ' not in result
        assert '_' not in result

    def test_empty_returns_default(self):
        result = normalize_to_k8s_namespace('')
        assert result == 'default'


# ─────────────────────────────────────────────────────────────────────────────
# validate_project_path – slash doble (//), slash inicial/final
# ─────────────────────────────────────────────────────────────────────────────

class TestProjectPathEdgeCases:
    def test_double_slash_raises(self):
        with pytest.raises(ValidationError):
            validate_project_path('grupo//proyecto')

    def test_leading_slash_raises(self):
        with pytest.raises(ValidationError):
            validate_project_path('/grupo/proyecto')

    def test_trailing_slash_raises(self):
        with pytest.raises(ValidationError):
            validate_project_path('grupo/proyecto/')


# ─────────────────────────────────────────────────────────────────────────────
# validate_variable_name / validate_component_name / sanitize_file_path – vacíos
# ─────────────────────────────────────────────────────────────────────────────

class TestValidateVariableNameEdge:
    def test_empty_raises(self):
        with pytest.raises(ValidationError):
            validate_variable_name('')


class TestValidateComponentNameEdge:
    def test_empty_raises(self):
        with pytest.raises(ValidationError):
            validate_component_name('')


class TestSanitizeFilePathEdge:
    def test_empty_raises(self):
        with pytest.raises(ValidationError):
            sanitize_file_path('')
