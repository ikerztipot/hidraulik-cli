"""
Generador de configuraciones para Kubernetes
"""

from typing import Dict, Any, List
from jinja2 import Environment, BaseLoader, Template


class K8sGenerator:
    """Generador de configuraciones CI/CD para Kubernetes"""
    
    def __init__(self):
        """Inicializa el generador"""
        self.jinja_env = Environment(loader=BaseLoader())
        # Variables que no deben ser sustituidas (se guardarán como variables CI/CD)
        self.cicd_vars = []
    
    def set_cicd_vars(self, cicd_vars: List[str]):
        """
        Establece la lista de variables que deben guardarse como variables CI/CD
        (no serán sustituidas en las plantillas)
        
        Args:
            cicd_vars: Lista de nombres de variables CI/CD
        """
        self.cicd_vars = cicd_vars
    
    def process_templates(
        self,
        templates: Dict[str, str],
        variables: Dict[str, Any],
        preserve_cicd_vars: bool = True
    ) -> Dict[str, str]:
        """
        Procesa las plantillas sustituyendo solo las variables de plantilla.
        Las variables CI/CD (que empiezan con CICD_) se mantienen sin sustituir.
        
        Args:
            templates: Diccionario con plantillas
            variables: Variables para sustituir
            preserve_cicd_vars: Si True, preserva variables CICD_ sin sustituir
            
        Returns:
            Diccionario con archivos procesados
        """
        processed = {}
        
        # Filtrar variables: solo sustituir las que NO son variables CI/CD
        template_variables = {
            k: v for k, v in variables.items() 
            if not (preserve_cicd_vars and k.startswith('CICD_'))
        }
        
        for file_path, content in templates.items():
            try:
                template = self.jinja_env.from_string(content)
                processed_content = template.render(**template_variables)
                processed[file_path] = processed_content
            except Exception as e:
                print(f"Error procesando {file_path}: {str(e)}")
                # En caso de error, usar el contenido original
                processed[file_path] = content
        
        return processed
    
    def generate_gitlab_ci(self, variables: Dict[str, Any]) -> str:
        """
        Genera un archivo .gitlab-ci.yml básico
        
        Args:
            variables: Variables de configuración
            
        Returns:
            Contenido del archivo .gitlab-ci.yml
        """
        template_content = """
# GitLab CI/CD para {{ project_name }}
# Generado automáticamente por gitlab-cicd-creator

stages:
  - build
  - test
  - deploy

variables:
  DOCKER_REGISTRY: {{ docker_registry }}
  DOCKER_IMAGE: {{ docker_image }}
  K8S_NAMESPACE: {{ namespace }}
  ENVIRONMENT: {{ environment }}

# Build de la imagen Docker
build:
  stage: build
  image: docker:latest
  services:
    - docker:dind
  script:
    - docker login -u $CI_REGISTRY_USER -p $CI_REGISTRY_PASSWORD $DOCKER_REGISTRY
    - docker build -t $DOCKER_REGISTRY/$DOCKER_IMAGE:$CI_COMMIT_SHORT_SHA .
    - docker tag $DOCKER_REGISTRY/$DOCKER_IMAGE:$CI_COMMIT_SHORT_SHA $DOCKER_REGISTRY/$DOCKER_IMAGE:latest
    - docker push $DOCKER_REGISTRY/$DOCKER_IMAGE:$CI_COMMIT_SHORT_SHA
    - docker push $DOCKER_REGISTRY/$DOCKER_IMAGE:latest
  only:
    - main
    - develop

# Tests
test:
  stage: test
  image: $DOCKER_REGISTRY/$DOCKER_IMAGE:$CI_COMMIT_SHORT_SHA
  script:
    - echo "Running tests..."
    # Añade tus comandos de test aquí
  only:
    - main
    - develop

# Deploy a Kubernetes
deploy:
  stage: deploy
  image: bitnami/kubectl:latest
  script:
    - kubectl config use-context {{ k8s_cluster }}
    - kubectl set image deployment/{{ project_name }} {{ project_name }}=$DOCKER_REGISTRY/$DOCKER_IMAGE:$CI_COMMIT_SHORT_SHA -n $K8S_NAMESPACE
    - kubectl rollout status deployment/{{ project_name }} -n $K8S_NAMESPACE
  only:
    - main
  environment:
    name: {{ environment }}
    url: https://{{ project_name }}.{{ environment }}.example.com
"""
        template = Template(template_content)
        return template.render(**variables)
    
    def generate_kubernetes_deployment(self, variables: Dict[str, Any]) -> str:
        """
        Genera un archivo de deployment de Kubernetes
        
        Args:
            variables: Variables de configuración
            
        Returns:
            Contenido del archivo deployment.yaml
        """
        template_content = """
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ project_name }}
  namespace: {{ namespace }}
  labels:
    app: {{ project_name }}
    environment: {{ environment }}
spec:
  replicas: 2
  selector:
    matchLabels:
      app: {{ project_name }}
  template:
    metadata:
      labels:
        app: {{ project_name }}
        environment: {{ environment }}
    spec:
      containers:
      - name: {{ project_name }}
        image: {{ docker_registry }}/{{ docker_image }}:latest
        ports:
        - containerPort: 8080
        env:
        - name: ENVIRONMENT
          value: "{{ environment }}"
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: {{ project_name }}
  namespace: {{ namespace }}
spec:
  selector:
    app: {{ project_name }}
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8080
  type: ClusterIP
"""
        template = Template(template_content)
        return template.render(**variables)
