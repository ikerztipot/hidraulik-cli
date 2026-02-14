"""
Tests para el módulo TemplateManager
"""

import pytest
from pathlib import Path
from hidraulik.template_manager import TemplateManager


def test_template_manager_init():
    """Test de inicialización del gestor de plantillas"""
    manager = TemplateManager('grupo/plantillas-cicd')
    assert manager.template_repo_path == 'grupo/plantillas-cicd'
    assert manager.templates_cache == {}


def test_load_templates():
    """Test de carga de plantillas (deprecado)"""
    manager = TemplateManager('grupo/plantillas-cicd')
    templates = manager.load_templates()
    assert isinstance(templates, dict)
    assert templates == {}  # Debe retornar vacío (deprecado)


def test_list_available_templates():
    """Test de listado de plantillas disponibles"""
    manager = TemplateManager('grupo/plantillas-cicd')
    templates = manager.list_available_templates()
    assert isinstance(templates, list)


def test_get_template():
    """Test de obtención de plantilla específica"""
    manager = TemplateManager('grupo/plantillas-cicd')
    template = manager.get_template('test.yaml')
    assert isinstance(template, str)


def test_extract_variables():
    """Test de extracción y clasificación de variables"""
    manager = TemplateManager('grupo/plantillas-cicd')
    
    templates = {
        'ci.yaml': '''
stages:
  - build
  - deploy

build:
  script:
    - docker build -t {{ docker_registry }}/{{ project_name }}:{{ version }} .
    - echo "Token: ${{ CICD_DOCKER_TOKEN }}"
    
deploy:
  script:
    - kubectl set image deployment/{{ project_name }} app=${{ CICD_IMAGE_URL }}
    - kubectl rollout status deployment/{{ project_name }} -n {{ namespace }}
''',
        'deployment.yaml': '''
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ project_name }}
  namespace: {{ namespace }}
spec:
  replicas: {{ replicas }}
  template:
    spec:
      containers:
      - name: app
        image: ${{ CICD_IMAGE_URL }}
        env:
        - name: DATABASE_URL
          value: ${{ CICD_DATABASE_URL }}
        - name: ENVIRONMENT
          value: {{ environment }}
'''
    }
    
    template_vars, cicd_vars = manager.extract_variables(templates)
    
    # Verificar que se detectaron las variables de plantilla
    assert 'docker_registry' in template_vars
    assert 'project_name' in template_vars
    assert 'version' in template_vars
    assert 'namespace' in template_vars
    assert 'replicas' in template_vars
    assert 'environment' in template_vars
    
    # Verificar que se detectaron las variables CI/CD (con prefijo CICD_)
    assert 'CICD_DOCKER_TOKEN' in cicd_vars
    assert 'CICD_IMAGE_URL' in cicd_vars
    assert 'CICD_DATABASE_URL' in cicd_vars
    
    # Verificar que las variables CI/CD NO están en template_vars
    assert 'CICD_DOCKER_TOKEN' not in template_vars
    assert 'CICD_IMAGE_URL' not in template_vars
