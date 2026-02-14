"""
Tests para el módulo K8sGenerator
"""

import pytest
from hidraulik.k8s_generator import K8sGenerator


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
    """Test de generación de .gitlab-ci.yml con plantilla"""
    generator = K8sGenerator()
    templates = {
        '.gitlab-ci.yml': '''
stages:
  - build
  - deploy

build:
  stage: build
  script:
    - echo "Building {{ project_name }}"
    - docker build -t {{ docker_image }} .

deploy:
  stage: deploy
  script:
    - kubectl apply -f deployment.yaml
  environment:
    name: {{ environment }}
'''
    }
    variables = {
        'project_name': 'test-app',
        'docker_image': 'test/app',
        'environment': 'prod'
    }
    
    result = generator.process_templates(templates, variables)
    
    assert 'test-app' in result['.gitlab-ci.yml']
    assert 'stages:' in result['.gitlab-ci.yml']
    assert 'build' in result['.gitlab-ci.yml']
    assert 'deploy' in result['.gitlab-ci.yml']


def test_generate_kubernetes_deployment():
    """Test de generación de deployment de K8s con plantilla"""
    generator = K8sGenerator()
    templates = {
        'deployment.yaml': '''
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ project_name }}
  namespace: {{ namespace }}
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: {{ project_name }}
        image: {{ docker_image }}
---
apiVersion: v1
kind: Service
metadata:
  name: {{ project_name }}
  namespace: {{ namespace }}
'''
    }
    variables = {
        'project_name': 'test-app',
        'namespace': 'production',
        'docker_image': 'registry.gitlab.com/test/app'
    }
    
    result = generator.process_templates(templates, variables)
    
    assert 'kind: Deployment' in result['deployment.yaml']
    assert 'kind: Service' in result['deployment.yaml']
    assert 'test-app' in result['deployment.yaml']
    assert 'production' in result['deployment.yaml']


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
