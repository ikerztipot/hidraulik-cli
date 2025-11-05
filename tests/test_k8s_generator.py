"""
Tests para el módulo K8sGenerator
"""

import pytest
from gitlab_cicd_creator.k8s_generator import K8sGenerator


def test_k8s_generator_init():
    """Test de inicialización del generador K8s"""
    generator = K8sGenerator()
    assert generator is not None
    assert generator.jinja_env is not None
    assert generator.cicd_vars == []


def test_process_templates():
    """Test de procesamiento de plantillas"""
    generator = K8sGenerator()
    templates = {
        'test.yaml': 'name: {{ project_name }}\nenvironment: {{ environment }}'
    }
    variables = {
        'project_name': 'my-app',
        'environment': 'prod'
    }
    
    result = generator.process_templates(templates, variables)
    
    assert 'test.yaml' in result
    assert 'name: my-app' in result['test.yaml']
    assert 'environment: prod' in result['test.yaml']


def test_generate_gitlab_ci():
    """Test de generación de .gitlab-ci.yml"""
    generator = K8sGenerator()
    variables = {
        'project_name': 'test-app',
        'docker_registry': 'registry.gitlab.com',
        'docker_image': 'test/app',
        'namespace': 'production',
        'environment': 'prod',
        'k8s_cluster': 'prod-cluster'
    }
    
    result = generator.generate_gitlab_ci(variables)
    
    assert 'test-app' in result
    assert 'stages:' in result
    assert 'build' in result
    assert 'deploy' in result


def test_generate_kubernetes_deployment():
    """Test de generación de deployment de K8s"""
    generator = K8sGenerator()
    variables = {
        'project_name': 'test-app',
        'namespace': 'production',
        'environment': 'prod',
        'docker_registry': 'registry.gitlab.com',
        'docker_image': 'test/app'
    }
    
    result = generator.generate_kubernetes_deployment(variables)
    
    assert 'kind: Deployment' in result
    assert 'kind: Service' in result
    assert 'test-app' in result
    assert 'production' in result


def test_set_cicd_vars():
    """Test de configuración de variables CI/CD"""
    generator = K8sGenerator()
    cicd_vars = ['CICD_DATABASE_URL', 'CICD_API_KEY', 'CICD_SECRET_TOKEN']
    
    generator.set_cicd_vars(cicd_vars)
    
    assert generator.cicd_vars == cicd_vars


def test_process_templates_preserve_cicd_vars():
    """Test de procesamiento preservando variables CI/CD"""
    generator = K8sGenerator()
    
    templates = {
        'config.yaml': '''
app: {{ project_name }}
environment: {{ environment }}
database: {{ CICD_DATABASE_URL }}
api_key: {{ CICD_API_KEY }}
'''
    }
    
    variables = {
        'project_name': 'my-app',
        'environment': 'prod',
        'CICD_DATABASE_URL': 'postgres://localhost/db',
        'CICD_API_KEY': 'secret123'
    }
    
    # Procesar preservando variables CI/CD
    result = generator.process_templates(templates, variables, preserve_cicd_vars=True)
    
    # Las variables de plantilla deben estar sustituidas
    assert 'app: my-app' in result['config.yaml']
    assert 'environment: prod' in result['config.yaml']
    
    # Las variables CI/CD deben mantenerse como variables Jinja2 sin sustituir
    # (aparecerán vacías porque no se pasan los valores)
    assert 'database: ' in result['config.yaml']
    assert 'api_key: ' in result['config.yaml']
    
    # NO deben aparecer los valores reales de las variables CI/CD
    assert 'postgres://localhost/db' not in result['config.yaml']
    assert 'secret123' not in result['config.yaml']
def test_process_templates_without_preserve():
    """Test de procesamiento sin preservar variables CI/CD"""
    generator = K8sGenerator()
    
    templates = {
        'config.yaml': 'app: {{ project_name }}\nkey: {{ CICD_API_KEY }}'
    }
    
    variables = {
        'project_name': 'my-app',
        'CICD_API_KEY': 'secret123'
    }
    
    # Procesar sin preservar (modo antiguo)
    result = generator.process_templates(templates, variables, preserve_cicd_vars=False)
    
    # Todas las variables deben estar sustituidas
    assert 'app: my-app' in result['config.yaml']
    assert 'key: secret123' in result['config.yaml']
