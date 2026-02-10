# Gestión de Variables en GitLab CI/CD Creator

## Tipos de Variables

Este CLI gestiona dos tipos de variables en las plantillas Jinja2:

### 1. Variables de Plantilla (Template Variables)

Son variables que se **sustituyen directamente** en los archivos generados durante la creación del CI/CD.

**Características:**
- Se solicitan al usuario durante la ejecución de `gitlab-cicd create`
- Sus valores se escriben directamente en los archivos `.gitlab-ci.yml` y configuraciones de Kubernetes
- Son visibles en el código del repositorio
- **Convención:** Cualquier variable que NO empiece con `CICD_`

**Ejemplos:**
```yaml
# En la plantilla .j2
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ project_name }}
  namespace: {{ namespace }}
spec:
  replicas: {{ replicas }}
```

**Resultado después de procesar:**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mi-aplicacion
  namespace: production
spec:
  replicas: 3
```

### 2. Variables CI/CD (GitLab Variables)

Son variables que se **guardan en la configuración de GitLab** y se mantienen como referencias en los archivos generados.

**Características:**
- Se solicitan al usuario durante la ejecución de `gitlab-cicd create`
- Se guardan como variables CI/CD en la configuración del proyecto de GitLab
- NO se sustituyen en los archivos, se mantienen como `${{ VARIABLE }}`
- Pueden ser marcadas como protegidas y/o enmascaradas
- Ideales para credenciales, tokens, URLs sensibles
- **Convención:** Deben empezar con el prefijo `CICD_`

**Ejemplos:**
```yaml
# En la plantilla .j2
build:
  script:
    - docker login -u $CI_REGISTRY_USER -p $CICD_REGISTRY_TOKEN }}
    - docker build -t $CICD_IMAGE_URL }}:$CI_COMMIT_SHA .
    
deploy:
  script:
    - kubectl set image deployment/app app=$CICD_IMAGE_URL }}
  environment:
    url: $CICD_APP_URL }}
```

**Resultado después de procesar:**
```yaml
# Las variables CICD_ NO se sustituyen, se mantienen como referencias
build:
  script:
    - docker login -u $CI_REGISTRY_USER -p $CICD_REGISTRY_TOKEN }}
    - docker build -t $CICD_IMAGE_URL }}:$CI_COMMIT_SHA .
    
deploy:
  script:
    - kubectl set image deployment/app app=$CICD_IMAGE_URL }}
  environment:
    url: $CICD_APP_URL }}
```

Y las variables se crean en GitLab Settings → CI/CD → Variables:
- `CICD_REGISTRY_TOKEN` = `ghp_xxxxxxxxxxxxx` (enmascarada)
- `CICD_IMAGE_URL` = `registry.gitlab.com/mi-org/mi-app`
- `CICD_APP_URL` = `https://mi-app.production.example.com`

## Flujo de Trabajo

### 1. Crear Plantillas en el Repositorio Central

```yaml
# .gitlab-ci.yml.j2
# Incluir bloques reutilizables
include:
  - project: '{{ template_repo }}'
    ref: main
    file: '/includes/.build-buildkit-scaleway.yml'

stages:
  - build
  - deploy

variables:
  DOCKER_IMAGE: {{ docker_registry }}/{{ project_name }}
  ENVIRONMENT: {{ environment }}

build:
  extends: .build-buildkit  # Del include remoto
  stage: build
  script:
    - docker login -u $CI_REGISTRY_USER -p $CICD_DOCKER_TOKEN }}
    - docker build -t $DOCKER_IMAGE:$CI_COMMIT_SHA .
    - docker push $DOCKER_IMAGE:$CI_COMMIT_SHA

deploy:
  stage: deploy
  script:
    - kubectl config use-context $CICD_K8S_CONTEXT }}
    - kubectl set image deployment/{{ project_name }} app=$DOCKER_IMAGE:$CI_COMMIT_SHA
  environment:
    name: {{ environment }}
    url: $CICD_APP_URL }}
```

## Variables Proporcionadas Automáticamente

El CLI inyecta automáticamente estas variables en todas las plantillas:

| Variable | Descripción | Ejemplo |
|----------|-------------|---------|
| `project_name` | Nombre del proyecto GitLab | `mi-app` |
| `project_path` | Ruta completa del proyecto | `clients/acme/mi-app` |
| `namespace` | Namespace de Kubernetes | `production` |
| `environments` | Lista de entornos | `['pre', 'prod']` |
| `template_repo` | Ruta del repositorio de plantillas | `clients/infrastructure` |

**Uso típico:**
```yaml
# Include dinámico
include:
  - project: '{{ template_repo }}'
    file: '/includes/.build.yml'

# Deployment
metadata:
  name: {{ project_name }}
  namespace: {{ namespace }}
```

### 2. Ejecutar el CLI

```bash
gitlab-cicd create mi-grupo/mi-proyecto \
  --k8s-cluster prod-cluster \
  --namespace production \
  --environment prod
```

### 3. El CLI Analiza las Variables

```
✓ Plantillas cargadas: 2 archivos

Analizando variables de las plantillas...
  • Variables de plantilla: docker_registry, environment, project_name
  • Variables CI/CD (se guardarán en GitLab): CICD_APP_URL, CICD_DOCKER_TOKEN, CICD_K8S_CONTEXT
```

### 4. Solicita Valores para Variables de Plantilla

```
Información requerida para las plantillas:
docker_registry: registry.gitlab.com
project_name [mi-proyecto]: 
environment [prod]: 
```

### 5. Solicita Valores para Variables CI/CD

```
Valores para variables CI/CD:
Estas variables se guardarán en la configuración de GitLab

CICD_DOCKER_TOKEN: ghp_xxxxxxxxxxxx
  ¿Marcar CICD_DOCKER_TOKEN como protegida? [y/N]: y
  ¿Marcar CICD_DOCKER_TOKEN como enmascarada? [Y/n]: y

CICD_K8S_CONTEXT: arn:aws:eks:us-east-1:123456:cluster/prod
  ¿Marcar CICD_K8S_CONTEXT como protegida? [y/N]: y
  ¿Marcar CICD_K8S_CONTEXT como enmascarada? [Y/n]: n

CICD_APP_URL: https://mi-app.production.example.com
  ¿Marcar CICD_APP_URL como protegida? [y/N]: n
  ¿Marcar CICD_APP_URL como enmascarada? [Y/n]: n
```

### 6. Genera y Guarda

```
Generando archivos CI/CD...
✓ 2 archivos procesados
  ✓ .gitlab-ci.yml
  ✓ k8s/deployment.yaml

Configurando variables CI/CD en GitLab...
  ✓ CICD_DOCKER_TOKEN (protegida, enmascarada)
  ✓ CICD_K8S_CONTEXT (protegida)
  ✓ CICD_APP_URL

✓ CI/CD configurado exitosamente!

Puedes ver el pipeline en: https://gitlab.com/mi-grupo/mi-proyecto/-/pipelines
```

## Convenciones y Buenas Prácticas

### Nomenclatura

| Tipo | Prefijo | Ejemplo | Uso |
|------|---------|---------|-----|
| Template | Ninguno | `{{ project_name }}` | Valores que se escriben en archivos |
| CI/CD | `CICD_` | `$CICD_API_KEY }}` | Valores sensibles o configurables |

### Cuándo usar Variables de Plantilla

✅ **Usar para:**
- Nombres de proyecto, namespace, ambiente
- Configuraciones de estructura (replicas, puertos)
- Referencias a recursos (nombres de deployments, services)
- Valores que no cambian después del setup inicial

### Cuándo usar Variables CI/CD

✅ **Usar para:**
- Credenciales (tokens, passwords, API keys)
- URLs de servicios externos
- Configuraciones que pueden cambiar sin modificar archivos
- Secretos y datos sensibles
- Referencias a clusters, contextos, registros

### Protegida vs Enmascarada

**Variables Protegidas:**
- Solo disponibles en ramas/tags protegidos
- Útil para producción
- Ejemplo: `CICD_PROD_TOKEN`

**Variables Enmascaradas:**
- Su valor se oculta en los logs del pipeline
- Recomendado para todos los secretos
- Ejemplo: Todos los tokens, passwords, API keys

## Ejemplo Completo

### Plantilla: `.gitlab-ci.yml.j2`

```yaml
stages:
  - build
  - test
  - deploy

variables:
  PROJECT_NAME: {{ project_name }}
  ENVIRONMENT: {{ environment }}
  DOCKER_IMAGE: {{ docker_registry }}/$PROJECT_NAME

# Build
build-image:
  stage: build
  script:
    - echo "Building for $ENVIRONMENT"
    - docker login -u $CI_REGISTRY_USER -p $CICD_REGISTRY_TOKEN }}
    - docker build -t $DOCKER_IMAGE:$CI_COMMIT_SHA .
    - docker push $DOCKER_IMAGE:$CI_COMMIT_SHA

# Test
unit-tests:
  stage: test
  script:
    - npm install
    - npm test
  environment:
    DATABASE_URL: $CICD_TEST_DB_URL }}

# Deploy
deploy-k8s:
  stage: deploy
  script:
    - kubectl config use-context $CICD_K8S_CONTEXT }}
    - kubectl set image deployment/$PROJECT_NAME app=$DOCKER_IMAGE:$CI_COMMIT_SHA -n {{ namespace }}
    - kubectl rollout status deployment/$PROJECT_NAME -n {{ namespace }}
  environment:
    name: $ENVIRONMENT
    url: $CICD_APP_URL }}
  only:
    - main
```

### Ejecución

```bash
gitlab-cicd create acme/web-app \
  --k8s-cluster prod-cluster \
  --namespace production \
  --environment prod
```

### Resultado

**Variables de Plantilla (sustituidas):**
- `project_name` → `web-app`
- `environment` → `prod`
- `docker_registry` → `registry.gitlab.com`
- `namespace` → `production`

**Variables CI/CD (guardadas en GitLab):**
- `CICD_REGISTRY_TOKEN` (protegida, enmascarada)
- `CICD_TEST_DB_URL` (enmascarada)
- `CICD_K8S_CONTEXT` (protegida)
- `CICD_APP_URL`

**Archivo generado `.gitlab-ci.yml`:**
```yaml
stages:
  - build
  - test
  - deploy

variables:
  PROJECT_NAME: web-app
  ENVIRONMENT: prod
  DOCKER_IMAGE: registry.gitlab.com/web-app

build-image:
  stage: build
  script:
    - echo "Building for prod"
    - docker login -u $CI_REGISTRY_USER -p $CICD_REGISTRY_TOKEN }}
    - docker build -t $DOCKER_IMAGE:$CI_COMMIT_SHA .
    - docker push $DOCKER_IMAGE:$CI_COMMIT_SHA

# ... resto del archivo con CICD_ variables sin sustituir
```

## Migración desde Versiones Anteriores

Si tienes plantillas que no usan la convención `CICD_`, todas las variables se tratarán como variables de plantilla (comportamiento anterior).

Para migrar:

1. Identifica variables sensibles en tus plantillas
2. Renómbralas con el prefijo `CICD_`
3. Ajusta las referencias en las plantillas de `{{ var }}` a `$CICD_VAR }}`

**Antes:**
```yaml
script:
  - docker login -u $CI_REGISTRY_USER -p {{ docker_token }}
```

**Después:**
```yaml
script:
  - docker login -u $CI_REGISTRY_USER -p $CICD_DOCKER_TOKEN }}
```

## Referencias

- [GitLab CI/CD Variables Documentation](https://docs.gitlab.com/ee/ci/variables/)
- [Jinja2 Template Documentation](https://jinja.palletsprojects.com/)
- [GitLab Protected Variables](https://docs.gitlab.com/ee/ci/variables/#protected-cicd-variables)
- [GitLab Masked Variables](https://docs.gitlab.com/ee/ci/variables/#mask-a-cicd-variable)
