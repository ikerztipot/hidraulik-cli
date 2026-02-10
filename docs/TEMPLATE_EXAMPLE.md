# Ejemplo de Plantilla con Variables CI/CD y Remote Includes

Este archivo muestra cómo crear plantillas que usen:
- Variables de plantilla (se sustituyen directamente)
- Variables CI/CD (se guardan en GitLab)
- Remote includes dinámicos (bloques reutilizables)

## `.gitlab-ci.yml.j2`

```yaml
# GitLab CI/CD para {{ project_name }}
# Generado con gitlab-cicd-creator
# Repositorio: {{ project_path }}

# Incluir bloques reutilizables desde el repositorio de plantillas
include:
  - project: '{{ template_repo }}'
    ref: main
    file: 
      - '/includes/.build-buildkit-scaleway.yml'
      - '/includes/.deploy-k8s.yml'

stages:
  - build
  - test
  - deploy

variables:
  PROJECT_NAME: {{ project_name }}
  ENVIRONMENT: {{ environment }}
  DOCKER_REGISTRY: {{ docker_registry }}
  DOCKER_IMAGE: $DOCKER_REGISTRY/$PROJECT_NAME
  NAMESPACE: {{ namespace }}

# ============================================
# BUILD STAGE - Usando bloque remoto
# ============================================
build-image:
  extends: .build-buildkit  # Definido en includes/.build-buildkit-scaleway.yml
  stage: build
  variables:
    IMAGE_NAME: $DOCKER_IMAGE
    IMAGE_TAG: $CI_COMMIT_SHORT_SHA
  script:
    - echo "Building Docker image for $ENVIRONMENT"
    # Usar variable CI/CD para autenticación (CICD_DOCKER_TOKEN)
    - docker login -u $CI_REGISTRY_USER -p $CICD_DOCKER_TOKEN $DOCKER_REGISTRY
    - docker build -t $DOCKER_IMAGE:$CI_COMMIT_SHORT_SHA .
    - docker tag $DOCKER_IMAGE:$CI_COMMIT_SHORT_SHA $DOCKER_IMAGE:latest
    - docker push $DOCKER_IMAGE:$CI_COMMIT_SHORT_SHA
    - docker push $DOCKER_IMAGE:latest
  only:
    - main
    - develop

# ============================================
# TEST STAGE
# ============================================
unit-tests:
  stage: test
  image: $DOCKER_IMAGE:$CI_COMMIT_SHORT_SHA
  script:
    - echo "Running tests..."
    # Usar variable CI/CD para conexión a base de datos de prueba
    - export DATABASE_URL=$CICD_TEST_DB_URL
    - npm install
    - npm test
  coverage: '/Coverage: \d+\.\d+%/'
  artifacts:
    reports:
      coverage_report:
        coverage_format: cobertura
        path: coverage/cobertura-coverage.xml
  only:
    - main
    - develop

integration-tests:
  stage: test
  image: $DOCKER_IMAGE:$CI_COMMIT_SHORT_SHA
  script:
    - echo "Running integration tests..."
    # Usar variables CI/CD para servicios externos
    - export API_KEY=$CICD_API_KEY
    - export API_URL=$CICD_API_URL
    - npm run test:integration
  only:
    - main

# ============================================
# DEPLOY STAGE
# ============================================
deploy-{{ environment }}:
  stage: deploy
  image: bitnami/kubectl:latest
  script:
    - echo "Deploying to {{ environment }} environment"
    # Configurar kubectl usando variable CI/CD de contexto K8s
    - kubectl config use-context $CICD_K8S_CONTEXT
    # Deploy en namespace específico
    - kubectl set image deployment/$PROJECT_NAME $PROJECT_NAME=$DOCKER_IMAGE:$CI_COMMIT_SHORT_SHA -n {{ namespace }}
    - kubectl rollout status deployment/$PROJECT_NAME -n {{ namespace }}
    # Verificar deployment
    - kubectl get pods -n {{ namespace }} -l app=$PROJECT_NAME
  environment:
    name: {{ environment }}
    # Usar variable CI/CD para URL de la aplicación
    url: $CICD_APP_URL
  only:
    - main
  when: manual
```

## `k8s/deployment.yaml.j2`

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ project_name }}
  namespace: {{ namespace }}
  labels:
    app: {{ project_name }}
    environment: {{ environment }}
spec:
  replicas: {{ replicas | default(2) }}
  selector:
    matchLabels:
      app: {{ project_name }}
  template:
    metadata:
      labels:
        app: {{ project_name }}
        environment: {{ environment }}
        version: latest
    spec:
      containers:
      - name: {{ project_name }}
        image: {{ docker_registry }}/{{ project_name }}:latest
        ports:
        - containerPort: {{ app_port | default(8080) }}
          name: http
          protocol: TCP
        env:
        # Variables de entorno estáticas
        - name: ENVIRONMENT
          value: "{{ environment }}"
        - name: PROJECT_NAME
          value: "{{ project_name }}"
        
        # Variables CI/CD - Se referencian como secrets de Kubernetes
        # Estas deben estar configuradas como variables CI/CD en GitLab
        - name: DATABASE_URL
          value: $CICD_DATABASE_URL
        - name: REDIS_URL
          value: $CICD_REDIS_URL
        - name: API_KEY
          value: $CICD_API_KEY
        - name: SECRET_KEY
          value: $CICD_SECRET_KEY
        
        resources:
          requests:
            memory: "{{ memory_request | default('256Mi') }}"
            cpu: "{{ cpu_request | default('250m') }}"
          limits:
            memory: "{{ memory_limit | default('512Mi') }}"
            cpu: "{{ cpu_limit | default('500m') }}"
        
        livenessProbe:
          httpGet:
            path: /health
            port: {{ app_port | default(8080) }}
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
        
        readinessProbe:
          httpGet:
            path: /ready
            port: {{ app_port | default(8080) }}
          initialDelaySeconds: 10
          periodSeconds: 5
          timeoutSeconds: 3
          failureThreshold: 2
---
apiVersion: v1
kind: Service
metadata:
  name: {{ project_name }}
  namespace: {{ namespace }}
  labels:
    app: {{ project_name }}
spec:
  selector:
    app: {{ project_name }}
  ports:
  - protocol: TCP
    port: 80
    targetPort: {{ app_port | default(8080) }}
    name: http
  type: ClusterIP
```

## `k8s/ingress.yaml.j2`

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: {{ project_name }}
  namespace: {{ namespace }}
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
spec:
  tls:
  - hosts:
    # Usar variable CI/CD para el dominio
    - $CICD_APP_DOMAIN
    secretName: {{ project_name }}-tls
  rules:
  - host: $CICD_APP_DOMAIN
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: {{ project_name }}
            port:
              number: 80
```

## Resumen de Variables

### Variables de Plantilla (se sustituyen con valores reales)

- `{{ project_name }}` - Nombre del proyecto
- `{{ environment }}` - Ambiente (dev/staging/prod)
- `{{ namespace }}` - Namespace de Kubernetes
- `{{ docker_registry }}` - Registro de Docker
- `{{ replicas }}` - Número de réplicas (con default)
- `{{ app_port }}` - Puerto de la aplicación (con default)
- `{{ memory_request }}`, `{{ cpu_request }}` - Recursos
- `{{ memory_limit }}`, `{{ cpu_limit }}` - Límites

### Variables CI/CD (se guardan en GitLab, prefijo CICD_)

**Credenciales:**
- `$CICD_DOCKER_TOKEN` - Token de autenticación de Docker
- `$CICD_API_KEY` - API key para servicios externos
- `$CICD_SECRET_KEY` - Clave secreta de la aplicación

**URLs y Conexiones:**
- `$CICD_DATABASE_URL` - URL de conexión a base de datos
- `$CICD_REDIS_URL` - URL de conexión a Redis
- `$CICD_TEST_DB_URL` - URL de base de datos para tests
- `$CICD_API_URL` - URL de API externa
- `$CICD_APP_URL` - URL pública de la aplicación
- `$CICD_APP_DOMAIN` - Dominio de la aplicación

**Configuración de Infraestructura:**
- `$CICD_K8S_CONTEXT` - Contexto de Kubernetes a usar

## Uso

Al ejecutar:

```bash
gitlab-cicd create mi-grupo/mi-app \
  --k8s-cluster production-cluster \
  --namespace mi-app-prod \
  --environment prod
```

El CLI:

1. **Detecta automáticamente** las variables de plantilla y CI/CD
2. **Solicita valores** para variables de plantilla:
   ```
   docker_registry: registry.gitlab.com
   replicas: 3
   app_port: 3000
   ```

3. **Solicita valores y configuración** para variables CI/CD:
   ```
   CICD_DOCKER_TOKEN: ghp_xxxxxxxxxxxxx
     ¿Marcar como protegida? [y/N]: y
     ¿Marcar como enmascarada? [Y/n]: y
   
   CICD_DATABASE_URL: postgres://user:pass@host:5432/db
     ¿Marcar como protegida? [y/N]: y
     ¿Marcar como enmascarada? [Y/n]: y
   
   CICD_APP_URL: https://mi-app.production.example.com
     ¿Marcar como protegida? [y/N]: n
     ¿Marcar como enmascarada? [Y/n]: n
   ```

4. **Genera archivos** sustituyendo variables de plantilla
5. **Guarda variables CI/CD** en la configuración de GitLab con flags apropiados

## Ventajas de este Enfoque

✅ **Seguridad**: Credenciales nunca se escriben en archivos del repositorio
✅ **Flexibilidad**: Variables CI/CD pueden cambiarse sin modificar código
✅ **Claridad**: Distinción clara entre configuración estática y dinámica
✅ **GitLab Native**: Aprovecha las capacidades nativas de CI/CD de GitLab
✅ **Reusabilidad**: Mismas plantillas para múltiples proyectos
