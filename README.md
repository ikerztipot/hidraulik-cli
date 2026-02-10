# GitLab CI/CD Creator

Un CLI potente y flexible para generar automáticamente configuraciones de CI/CD en repositorios de GitLab para despliegues en Kubernetes.

## � Tabla de Contenidos

- [Características](#-características)
- [Requisitos](#-requisitos)
- [Instalación](#-instalación)
- [Uso Rápido](#-uso-rápido)
- [Comandos Disponibles](#-comandos-disponibles)
- [Repositorio de Plantillas](#-repositorio-de-plantillas)
- [Variables en Plantillas](#-variables-en-plantillas)- [Ejemplos Completos](#-ejemplos-completos)- [Configuración de GitLab](#-configuración-de-gitlab)
- [Desarrollo](#-desarrollo)
- [Contribuir](#-contribuir)

## �🚀 Características

- **Automatización Completa**: Genera pipelines CI/CD listos para producción
- **Kubernetes Native**: Configuraciones optimizadas para clusters K8s con GitLab Agents
- **Plantillas Personalizables**: Usa plantillas Jinja2 desde repositorios de GitLab
- **Remote Includes**: Bloques reutilizables centralizados (sin duplicación)
- **Variables CI/CD**: Gestión automática de variables de entorno y secretos
- **Múltiples Ambientes**: Soporte para dev, staging y producción con KUBE_CONTEXT por entorno
- **Detección de Clusters**: Integración automática con GitLab Agents para Kubernetes
- **Organización por Tipos**: Pipeline, K8s, Helm, Config e Includes
- **Integración GitLab**: Comunicación directa con la API de GitLab

## 📋 Requisitos

- Python 3.8 o superior
- Cuenta de GitLab con token de acceso personal (permisos: `api`, `read_repository`, `write_repository`)
- **Repositorio central de plantillas en GitLab** (obligatorio)
- GitLab Agents configurados para acceso a clusters de Kubernetes

## 🔧 Instalación

```bash
# 1. Clonar el repositorio
git clone https://github.com/ikerztipot/gitlab-repo-cicd-creator-cli.git
cd gitlab-repo-cicd-creator-cli

# 2. Ejecutar el instalador
./install.sh
```

El instalador:
- ✅ Detecta tu sistema operativo
- ✅ Instala las dependencias necesarias
- ✅ Hace que `gitlab-cicd` esté disponible globalmente

**Nota:** Cierra y abre tu terminal después de la instalación.

### Desinstalación

```bash
./uninstall.sh
```

## 🎯 Uso Rápido

### 1. Inicializar configuración

```bash
gitlab-cicd init
```

El CLI te pedirá:
- URL de GitLab (ej: `https://gitlab.workoholics.es`)
- Token de acceso personal
- **Ruta del repositorio de plantillas** (ej: `clients/infrastructure`)

### 2. Crear CI/CD para un proyecto

```bash
gitlab-cicd create clients/acme/mi-app \
  --namespace production \
  --environments pre,prod \
  --create-project
```

El CLI:
1. Detecta automáticamente los clusters disponibles (GitLab Agents)
2. Carga las plantillas desde el repositorio
3. **Obtiene runners disponibles de GitLab** (tags de runners activos)
4. Solicita configuración interactiva:
   - Componentes a desplegar (web, cms, api, etc.)
   - **Selección de runner tags** (desde lista de runners disponibles)
   - Prefijo para tags de release (wkhs, acme, etc.)
   - Cluster para cada entorno
5. Solicita valores para variables personalizadas
6. Genera y commit los archivos al proyecto

### 3. Listar plantillas disponibles

```bash
gitlab-cicd list-templates
```

### 4. Ver estado del CI/CD

```bash
gitlab-cicd status clients/acme/mi-app
```

### 5. Configurar variables CI/CD

```bash
gitlab-cicd set-variable clients/acme/mi-app API_KEY "valor-secreto" --masked --protected
```

## 📚 Comandos Disponibles

### `init` - Inicializar configuración

```bash
gitlab-cicd init
```

Configura el CLI con URL de GitLab, token y repositorio de plantillas.

### `create` - Crear CI/CD para un proyecto

```bash
gitlab-cicd create PROJECT_PATH [OPTIONS]
```

**Argumentos:**
- `PROJECT_PATH`: Ruta del proyecto en GitLab (ej: `clients/acme/mi-app`)

**Opciones:**
- `--namespace`: Namespace de Kubernetes (requerido)
- `--environments`: Entornos separados por coma (default: `dev,pre,pro`)
- `--create-project`: Crear el proyecto si no existe

**Ejemplo:**
```bash
gitlab-cicd create clients/workoholics/web-app \
  --namespace workoholics-web \
  --environments pre,prod \
  --create-project
```

### `status` - Ver estado del CI/CD

```bash
gitlab-cicd status PROJECT_PATH
```

### `set-variable` - Configurar variable CI/CD

```bash
gitlab-cicd set-variable PROJECT_PATH KEY VALUE [OPTIONS]
```

**Opciones:**
- `--protected`: Variable solo disponible en ramas protegidas
- `--masked`: Enmascarar valor en logs

**Ejemplo:**
```bash
gitlab-cicd set-variable clients/acme/app DB_PASSWORD "secreto" --masked --protected
```

### `list-templates` - Listar plantillas

```bash
gitlab-cicd list-templates
```

Muestra todas las plantillas disponibles en el repositorio configurado.

## � Repositorio de Plantillas

### Estructura Requerida

El repositorio de plantillas debe seguir esta organización:

```
clients/infrastructure/          # Tu repositorio de plantillas
├── pipeline/                    # Plantillas de CI/CD (procesadas con Jinja2)
│   ├── .gitlab-ci.yml.j2       # Pipeline principal
│   └── build-stage.yml.j2      # Stages adicionales (opcional)
│
├── includes/                    # Bloques reutilizables (NO procesados, incluidos remotamente)
│   ├── .build-buildkit-scaleway.yml
│   ├── .deploy-k8s.yml
│   └── .test-python.yml
│
├── k8s/                         # Manifiestos de Kubernetes
│   ├── deployment.yaml.j2
│   ├── service.yaml.j2
│   └── ingress.yaml.j2
│
├── helm/                        # Charts de Helm (opcional)
│   └── values.yaml.j2
│
└── config/                      # Configuraciones (opcional)
    └── env.j2
```

### Tipos de Archivos

| Carpeta | Extensión | Procesado | Destino | Uso |
|---------|-----------|-----------|---------|-----|
| `pipeline/` | `.j2` | ✅ Sí | Raíz proyecto | Archivos CI/CD procesados con variables |
| `includes/` | `.yml` | ❌ No | No se copian | Bloques incluidos remotamente |
| `k8s/` | `.j2` | ✅ Sí | `k8s/` | Manifiestos Kubernetes |
| `helm/` | `.j2` | ✅ Sí | `helm/` | Charts Helm |
| `config/` | `.j2` | ✅ Sí | `config/` | Configuraciones |

### Ejemplo de Plantilla Principal

**`pipeline/.gitlab-ci.yml.j2`**:
```yaml
# GitLab CI/CD para {{ project_name }}

# Incluir bloques reutilizables desde el repositorio de plantillas
include:
  - project: '{{ template_repo }}'
    ref: main
    file: 
      - '/includes/.build-buildkit-scaleway.yml'
      - '/includes/.deploy-k8s.yml'

stages:
  - build
  - deploy

variables:
  PROJECT_PATH: {{ project_path }}
  NAMESPACE: {{ namespace }}

build:
  extends: .build-buildkit  # Definido en includes/.build-buildkit-scaleway.yml
  only:
    - main

# Deploy por cada entorno
{% for env in environments %}
deploy:{{ env }}:
  extends: .deploy-k8s  # Definido en includes/.deploy-k8s.yml
  variables:
    KUBE_CONTEXT: $KUBE_CONTEXT
  environment:
    name: {{ env }}
  only:
    - main
{% endfor %}
```

### Ejemplo de Remote Include

**`includes/.build-buildkit-scaleway.yml`** (sin extensión `.j2`):
```yaml
# @requires: PACKAGE_NAME, DOCKERFILE_PATH

.build-buildkit:
  stage: build
  image:
    name: moby/buildkit:latest
    entrypoint: [""]
  script:
    - buildctl build --frontend dockerfile.v0 \
        --local context=. \
        --output type=image,name=$DOCKER_REGISTRY/$PROJECT_PATH:$CI_COMMIT_SHORT_SHA,push=true
  tags:
    - scaleway
```

**Ventajas de Remote Includes:**
- ✅ Mantenimiento centralizado
- ✅ Sin duplicación de código
- ✅ Actualiza una vez, afecta todos los proyectos
- ✅ Versionado con tags/branches

**Detección Automática de Variables:**

El CLI analiza automáticamente los archivos de remote includes para detectar variables requeridas mediante el comentario especial `# @requires:`.

Cuando se encuentra este comentario, el CLI:
1. Descarga el archivo desde el repositorio de plantillas
2. Extrae las variables listadas después de `@requires:`
3. Las solicita al usuario durante la creación del pipeline
4. Las configura automáticamente como variables CI/CD en GitLab

## 🔑 Variables en Plantillas

El CLI maneja dos tipos de variables:

### 1. Variables de Plantilla (sustituidas directamente)

Estas variables se procesan y sustituyen en los archivos generados:

| Variable | Descripción | Ejemplo |
|----------|-------------|---------|
| `project_name` | Nombre del proyecto | `mi-app` |
| `project_path` | Ruta completa del proyecto | `clients/acme/mi-app` |
| `namespace` | Namespace de Kubernetes | `production` |
| `environments` | Lista de entornos | `['pre', 'prod']` |
| `template_repo` | Repositorio de plantillas | `clients/infrastructure` |

**Uso en plantillas:**
```yaml
metadata:
  name: {{ project_name }}
  namespace: {{ namespace }}

include:
  - project: '{{ template_repo }}'
    file: '/includes/.build.yml'

{% for env in environments %}
deploy:{{ env }}:
  environment:
    name: {{ env }}
{% endfor %}
```

### 2. Variables CI/CD (guardadas en GitLab)

Variables que empiezan con `CICD_` se guardan como variables CI/CD en GitLab y **NO** se sustituyen en los archivos.

**En la plantilla:**
```yaml
build:
  script:
    - docker login -u $CI_REGISTRY_USER -p $CICD_REGISTRY_TOKEN
    - curl -H "Authorization: Bearer $CICD_API_KEY" $CICD_API_URL
```

**Durante la ejecución**, el CLI:
1. Detecta automáticamente las variables `CICD_*`
2. Solicita sus valores al usuario
3. Las guarda como variables CI/CD en GitLab
4. Opcionalmente las marca como protegidas/enmascaradas
5. Las mantiene como `$CICD_*` en los archivos generados (NO las sustituye)

**Ejemplo interactivo:**
```bash
Valores para variables CI/CD:
CICD_REGISTRY_TOKEN: ghp_xxxxxxxxxxxx
  ¿Marcar CICD_REGISTRY_TOKEN como protegida? [y/N]: y
  ¿Marcar CICD_REGISTRY_TOKEN como enmascarada? [Y/n]: y

CICD_API_KEY: sk_live_xxxxx
  ¿Marcar CICD_API_KEY como protegida? [y/N]: y
  ¿Marcar CICD_API_KEY como enmascarada? [Y/n]: y
```

### Variables Automáticas Proporcionadas por el CLI

El CLI inyecta automáticamente estas variables en todas las plantillas sin solicitar al usuario:

| Variable | Descripción | Ejemplo | Origen |
|----------|-------------|---------|--------|
| `project_name` | Nombre del proyecto GitLab | `web-app` | Extraído del último segmento de `project_path` |
| `project_path` | Ruta completa del proyecto | `clients/workoholics/web-app` | Argumento del comando `create` |
| `namespace` | Namespace de Kubernetes | `wkhs` | Opción `--namespace` |
| `environments` | Lista de entornos | `['pre', 'prod']` | Opción `--environments` |
| `template_repo` | Repositorio de plantillas | `clients/infrastructure` | Configuración almacenada en `config.json` |
| `components` | Componentes a desplegar | `['web', 'cms']` | Prompt interactivo |
| `runner_tags` | Tags de runners GitLab | `['buildkit', 'scaleway']` | Selección interactiva desde GitLab API |
| `tag_prefix` | Prefijo para tags de releases | `wkhs` | Prompt interactivo con smart default |

### Buenas Prácticas

**Variables de Plantilla - Usar para:**
- ✅ Nombres de proyecto, namespace, ambiente
- ✅ Configuraciones de estructura (réplicas, puertos)
- ✅ Referencias a recursos (nombres de deployments, services)
- ✅ Valores que no cambian después del setup inicial

**Variables CI/CD - Usar para:**
- ✅ Credenciales (tokens, passwords, API keys)
- ✅ URLs de servicios externos
- ✅ Configuraciones que pueden cambiar sin modificar archivos
- ✅ Secretos y datos sensibles
- ✅ Referencias a clusters, contextos, registros

**Protección de Variables:**
- **Protegidas:** Solo disponibles en ramas/tags protegidos (recomendado para producción)
- **Enmascaradas:** Su valor se oculta en los logs (recomendado para todos los secretos)

## 📖 Ejemplos Completos

### Ejemplo 1: Sesión Interactiva Completa

Este ejemplo muestra una sesión completa de uso del CLI con todas las interacciones.

#### Comando Inicial

```bash
gitlab-cicd create clients/workoholics/web-app \
  --namespace wkhs \
  --environments pre,prod \
  --create-project
```

#### Salida del CLI

```
╭────────────────────────────────────────╮
│ Creando CI/CD para clients/workoholics/web-app │
╰────────────────────────────────────────╯

✓ Conectado a GitLab
✓ Proyecto listo: https://gitlab.workoholics.es/clients/workoholics/web-app

Obteniendo clusters disponibles...
  ✓ clients/internal-infrastructure/cicd-templates:scaleway-internal-worko-pre
  ✓ clients/internal-infrastructure/cicd-templates:scaleway-internal-worko-prod

Cargando plantillas desde: clients/internal-infrastructure/cicd-templates
✓ Plantillas cargadas: 8 archivos

Analizando variables de las plantillas...
  • Variables de plantilla: project_name, project_path, namespace, environments, components, runner_tags, tag_prefix
  • Variables CI/CD (se guardarán en GitLab): CICD_DOCKER_REGISTRY, CICD_REGISTRY_USER, CICD_REGISTRY_PASSWORD

Obteniendo runners disponibles...
✓ Encontrados 5 runners con 8 tags

Configuración del Pipeline

Componentes a desplegar (separados por coma) [web]: web,cms

Runners disponibles:
  1. Runner #97 - Scaleway BuildKit
     Tags: buildkit, scaleway, worko-internal
  2. Runner #85 - Docker Production
     Tags: docker, production
  3. Runner #72 - Kubernetes Staging
     Tags: kubernetes, staging

Selecciona un runner (número) [1]: 1
✓ Runner seleccionado: Runner #97
✓ Tags del runner: buildkit, scaleway, worko-internal

Prefijo para tags de release (ej: wkhs, acme) [web]: wkhs

Configuración de KUBE_CONTEXT por entorno:

Entorno: pre
Clusters disponibles:
  1. clients/internal-infrastructure/cicd-templates:scaleway-internal-worko-pre
  2. clients/internal-infrastructure/cicd-templates:scaleway-internal-worko-prod
Selecciona el cluster para pre (número o ingresa manualmente) [1]: 1
✓ KUBE_CONTEXT para pre: clients/internal-infrastructure/cicd-templates:scaleway-internal-worko-pre

Entorno: prod
Clusters disponibles:
  1. clients/internal-infrastructure/cicd-templates:scaleway-internal-worko-pre
  2. clients/internal-infrastructure/cicd-templates:scaleway-internal-worko-prod
Selecciona el cluster para prod (número o ingresa manualmente) [2]: 2
✓ KUBE_CONTEXT para prod: clients/internal-infrastructure/cicd-templates:scaleway-internal-worko-prod

Analizando includes remotos...
  ✓ Analizado: includes/.build-buildkit-scaleway.yml
  • Variables en includes remotos: PACKAGE_NAME, DOCKERFILE_PATH

Información requerida para las plantillas:
(No hay variables adicionales requeridas)

Valores para variables CI/CD:
Estas variables se guardarán en la configuración de GitLab

CICD_DOCKER_REGISTRY: registry.workoholics.es
  ¿Marcar CICD_DOCKER_REGISTRY como protegida? [y/N]: n
  ¿Marcar CICD_DOCKER_REGISTRY como enmascarada? [y/N]: n

CICD_REGISTRY_USER: ci-deployer
  ¿Marcar CICD_REGISTRY_USER como protegida? [y/N]: y
  ¿Marcar CICD_REGISTRY_USER como enmascarada? [y/N]: n

CICD_REGISTRY_PASSWORD: ••••••••
  ¿Marcar CICD_REGISTRY_PASSWORD como protegida? [y/N]: y
  ¿Marcar CICD_REGISTRY_PASSWORD como enmascarada? [y/N]: y

Generando archivos del CI/CD...
✓ Procesadas 1 plantillas de pipeline
✓ Procesadas 8 plantillas de Kubernetes
✓ Procesadas 0 plantillas de Helm
✓ Procesadas 0 configuraciones adicionales

Commiteando archivos al repositorio...
✓ .gitlab-ci.yml
✓ k8s/web/02-secrets.yaml
✓ k8s/web/03-configs.yaml
✓ k8s/web/04-deployment.yaml
✓ k8s/web/05-ingress.yaml
✓ k8s/cms/02-secrets.yaml
✓ k8s/cms/03-configs.yaml
✓ k8s/cms/04-deployment.yaml
✓ k8s/cms/05-ingress.yaml

Configurando variables CI/CD en GitLab...
✓ Variable CICD_DOCKER_REGISTRY configurada
✓ Variable CICD_REGISTRY_USER configurada (protegida)
✓ Variable CICD_REGISTRY_PASSWORD configurada (protegida, enmascarada)

Configurando variables KUBE_CONTEXT por entorno...
✓ Variable KUBE_CONTEXT configurada para entorno: pre
✓ Variable KUBE_CONTEXT configurada para entorno: prod

╭───────────────────────────────────────╮
│ ✅ CI/CD configurado exitosamente     │
╰───────────────────────────────────────╯

Pipeline generado con:
  • 2 componentes: web, cms
  • 2 ambientes: pre, prod
  • 6 stages: build-web, deploy-web-pre, deploy-web-prod, build-cms, deploy-cms-pre, deploy-cms-prod
  • 3 runner tags: buildkit, scaleway, worko-internal

Ver pipeline en:
  https://gitlab.workoholics.es/clients/workoholics/web-app/-/pipelines

Próximos pasos:
  1️⃣  Revisa los archivos generados en el repositorio
  2️⃣  Crea un tag para activar el pipeline:
      git tag wkhs-web-v1.0.0 && git push --tags
      git tag wkhs-cms-v1.0.0 && git push --tags
  3️⃣  Verifica el estado del pipeline con:
      gitlab-cicd status clients/workoholics/web-app
```

### Ejemplo 2: Plantilla Completa con Variables y Remote Includes

#### Plantilla: `pipeline/.gitlab-ci.yml.j2`

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

default:
  tags:
{%- for tag in runner_tags %}
    - {{ tag }}
{%- endfor %}

stages:
{%- for component in components %}
  - build-{{ component }}
{%- for env in environments %}
  - deploy-{{ component }}-{{ env }}
{%- endfor %}
{%- endfor %}

variables:
  PROJECT_PATH: {{ project_path }}
  NAMESPACE: {{ namespace }}
  TAG_PREFIX: {{ tag_prefix }}

# ============================================
# BUILD STAGES - Por cada componente
# ============================================
{%- for component in components %}

build-{{ component }}:
  extends: .build-buildkit-scaleway  # Definido en includes/
  stage: build-{{ component }}
  variables:
    PACKAGE_NAME: {{ component }}
    DOCKERFILE_PATH: docker/{{ component }}/Dockerfile
  only:
    refs:
      - tags
    variables:
      - $CI_COMMIT_TAG =~ /^${TAG_PREFIX}-{{ component }}-v.*/

{%- endfor %}

# ============================================
# DEPLOY STAGES - Por cada componente y entorno
# ============================================
{%- for component in components %}
{%- for env in environments %}

deploy-{{ component }}-{{ env }}:
  extends: .deploy-k8s  # Definido en includes/
  stage: deploy-{{ component }}-{{ env }}
  variables:
    COMPONENT: {{ component }}
    ENVIRONMENT: {{ env }}
    MANIFESTS_PATH: k8s/{{ component }}
  environment:
    name: {{ env }}/{{ component }}
    url: https://{{ component }}.{{ env }}.$DOMAIN
  only:
    refs:
      - tags
    variables:
      - $CI_COMMIT_TAG =~ /^${TAG_PREFIX}-{{ component }}-v.*/
  {%- if env == environments[-1] %}
  when: manual
  {%- endif %}

{%- endfor %}
{%- endfor %}
```

#### Archivo Generado: `.gitlab-ci.yml`

```yaml
# GitLab CI/CD para web-app
# Generado con gitlab-cicd-creator
# Repositorio: clients/workoholics/web-app

include:
  - project: 'clients/internal-infrastructure/cicd-templates'
    ref: main
    file: 
      - '/includes/.build-buildkit-scaleway.yml'
      - '/includes/.deploy-k8s.yml'

default:
  tags:
    - buildkit
    - scaleway
    - worko-internal

stages:
  - build-web
  - deploy-web-pre
  - deploy-web-prod
  - build-cms
  - deploy-cms-pre
  - deploy-cms-prod

variables:
  PROJECT_PATH: clients/workoholics/web-app
  NAMESPACE: wkhs
  TAG_PREFIX: wkhs

# BUILD STAGES
build-web:
  extends: .build-buildkit-scaleway
  stage: build-web
  variables:
    PACKAGE_NAME: web
    DOCKERFILE_PATH: docker/web/Dockerfile
  only:
    refs:
      - tags
    variables:
      - $CI_COMMIT_TAG =~ /^${TAG_PREFIX}-web-v.*/

build-cms:
  extends: .build-buildkit-scaleway
  stage: build-cms
  variables:
    PACKAGE_NAME: cms
    DOCKERFILE_PATH: docker/cms/Dockerfile
  only:
    refs:
      - tags
    variables:
      - $CI_COMMIT_TAG =~ /^${TAG_PREFIX}-cms-v.*/

# DEPLOY STAGES
deploy-web-pre:
  extends: .deploy-k8s
  stage: deploy-web-pre
  variables:
    COMPONENT: web
    ENVIRONMENT: pre
    MANIFESTS_PATH: k8s/web
  environment:
    name: pre/web
    url: https://web.pre.$DOMAIN
  only:
    refs:
      - tags
    variables:
      - $CI_COMMIT_TAG =~ /^${TAG_PREFIX}-web-v.*/

deploy-web-prod:
  extends: .deploy-k8s
  stage: deploy-web-prod
  variables:
    COMPONENT: web
    ENVIRONMENT: prod
    MANIFESTS_PATH: k8s/web
  environment:
    name: prod/web
    url: https://web.prod.$DOMAIN
  only:
    refs:
      - tags
    variables:
      - $CI_COMMIT_TAG =~ /^${TAG_PREFIX}-web-v.*/
  when: manual

# ... (deploy-cms-pre, deploy-cms-prod similar)
```

### Ejemplo 3: Detección Automática de Runners

El CLI obtiene automáticamente los runners disponibles desde GitLab en tres niveles:

1. **Runners de la instancia** (si tienes permisos de admin)
2. **Runners del grupo** (ancestros del proyecto)
3. **Runners del proyecto** (específicos del proyecto)

```bash
Obteniendo runners disponibles...
  • Buscando runners de la instancia...
    ✓ Encontrados 3 runners
  • Buscando runners del grupo clients/...
    ✓ Encontrados 2 runners
  • Buscando runners del proyecto...
    ✓ Encontrados 0 runners

Runners disponibles:
  1. Runner #97 - Scaleway BuildKit (instancia)
     Tags: buildkit, scaleway, worko-internal
     
  2. Runner #85 - Docker Prod (instancia)
     Tags: docker, production, linux
     
  3. Runner #72 - K8s Staging (grupo)
     Tags: kubernetes, staging, scaleway
     
  4. Runner #58 - General Purpose (grupo)
     Tags: docker, general

Selecciona un runner (número) [1]: 1
```

**Ventajas:**
- ✅ No necesitas conocer los tags de antemano
- ✅ Solo muestra runners activos y disponibles
- ✅ Garantiza compatibilidad con la infraestructura existente
- ✅ Sel eccionas un runner completo con todos sus tags al mismo tiempo

## ⚙️ Configuración de GitLab

### Obtener Token de Acceso

1. Ve a GitLab → Settings → Access Tokens
2. Crea un nuevo token con permisos:
   - `api` - Acceso completo a la API
   - `read_repository` - Leer repositorios
   - `write_repository` - Escribir en repositorios
3. Guarda el token de forma segura
4. Úsalo durante `gitlab-cicd init`

### GitLab Agents para Kubernetes

El CLI detecta automáticamente los GitLab Agents configurados en tu repositorio de plantillas.

**Configuración:**
1. Los agents deben estar en el proyecto del repositorio de plantillas (ej: `clients/infrastructure`)
2. El CLI los lista automáticamente al crear un proyecto
3. Puedes seleccionar el cluster para cada entorno

**Formato de KUBE_CONTEXT:**
```
<template_repo>:<agent_name>
```

**Ejemplo:**
```
clients/infrastructure:scaleway-internal-worko-prod
```

## 🧪 Desarrollo

### Ejecutar tests

```bash
pytest
pytest --cov=gitlab_cicd_creator --cov-report=html  # Con cobertura
```

### Formatear código

```bash
make format    # black + isort
make lint      # flake8 + mypy
```

## 📦 Estructura del Proyecto

```
gitlab-repo-cicd-creator-cli/
├── src/gitlab_cicd_creator/
│   ├── cli.py              # CLI principal con Click
│   ├── config.py           # Gestión de configuración (~/.gitlab-cicd-creator/config.json)
│   ├── gitlab_client.py    # Cliente GitLab API con soporte multi-nivel
│   ├── template_manager.py # Carga plantillas desde GitLab, detecta tipos
│   └── k8s_generator.py    # Procesador Jinja2, preserva CICD_ vars
├── tests/                  # Suite de tests con pytest
├── pyproject.toml         # Configuración del proyecto
└── README.md              # Esta documentación
```

## 🤝 Contribuir

¡Gracias por tu interés en contribuir a GitLab CI/CD Creator!

### Proceso de Contribución

1. **Fork** el repositorio
2. **Clona** tu fork:
   ```bash
   git clone https://github.com/TU-USUARIO/gitlab-repo-cicd-creator-cli.git
   cd gitlab-repo-cicd-creator-cli
   ```
3. **Crea una rama** para tu feature:
   ```bash
   git checkout -b feature/mi-feature
   ```
4. **Haz cambios** siguiendo las guías de estilo
5. **Ejecuta tests** y verifica que pasen:
   ```bash
   make test
   make lint
   ```
6. **Commit** tus cambios con un mensaje descriptivo:
   ```bash
   git commit -m 'Add: mi feature'
   ```
7. **Push** a tu fork:
   ```bash
   git push origin feature/mi-feature
   ```
8. **Abre un Pull Request** desde GitHub/GitLab

### Configuración de Desarrollo

```bash
# Crear y activar entorno virtual
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# Instalar en modo desarrollo con dependencias de testing
pip install -e ".[dev]"
```

### Estándares de Código

**Python:**
- Estilo: PEP 8
- Longitud de línea: 100 caracteres
- Formateador: Black
- Organización de imports: isort
- Type hints: Requeridos para funciones públicas

**Formateo:**
```bash
make format  # Ejecuta black + isort automáticamente
make lint    # Verifica con flake8 + mypy
```

### Tests

```bash
make test          # Ejecutar todos los tests
make test-cov      # Tests con reporte de cobertura en htmlcov/
```

**Escribir Tests:**
- Usa `pytest` como framework
- Mock las llamadas a GitLab API usando `unittest.mock`
- Usa `click.testing.CliRunner` para tests del CLI
- Cobertura mínima esperada: 80%

**Ejemplo:**
```python
from click.testing import CliRunner
from gitlab_cicd_creator.cli import cli

def test_init_command():
    runner = CliRunner()
    result = runner.invoke(cli, ['init'], input='https://gitlab.com\ntoken\norg/repo\n')
    assert result.exit_code == 0
    assert 'Configuración guardada' in result.output
```

### Estructura de Commits

Usa el siguiente formato para mensajes de commit:

```
<tipo>: <descripción corta>

<descripción detallada opcional>
```

**Tipos de commit:**
- `Add:` Nueva funcionalidad
- `Fix:` Corrección de bugs
- `Docs:` Cambios en documentación
- `Style:` Formateo, sin cambios en lógica
- `Refactor:` Refactorización de código
- `Test:` Añadir o modificar tests
- `Chore:` Actualización de dependencias, builds

**Ejemplos:**
```
Add: soporte para remote includes dinámicos

- Añadida variable template_repo a variables automáticas
- Actualizada documentación con ejemplos
- Tests añadidos para nueva funcionalidad

Fix: corrección en detección de runner tags

El método runners.list() no incluía tags en la respuesta.
Cambiado a runners.get(id) individual para obtener tag_list.

Docs: actualización de README con ejemplos de uso
```

### Reportar Issues

Al reportar un bug, incluye:
- Versión de Python: `python --version`
- Versión del CLI: `gitlab-cicd --version`
- Comando ejecutado
- Output completo del error
- Pasos para reproducir el problema

**Ejemplo de issue:**
```markdown
## Bug: Error al crear proyecto con namespace especial

**Ambiente:**
- Python: 3.11.2
- CLI: v1.2.3
- GitLab: self-hosted 15.8

**Comando:**
```bash
gitlab-cicd create my-group/my-project --namespace my_namespace
```

**Error:**
```
ValueError: Invalid namespace format
```

**Pasos para reproducir:**
1. Ejecutar `gitlab-cicd init` con configuración válida
2. Ejecutar comando de create con namespace que contiene underscore
3. Error aparece

**Comportamiento esperado:**
El namespace debería aceptarse o mostrar un mensaje de error más claro.
```

### Preguntas y Sugerencias

Si tienes preguntas o sugerencias:
- Abre un issue con la etiqueta `question` o `enhancement`
- Describe claramente tu caso de uso
- Si es una nueva funcionalidad, explica por qué sería útil

## 📄 Licencia

MIT License - Ver archivo `LICENSE`

## 🙏 Agradecimientos

- [python-gitlab](https://python-gitlab.readthedocs.io/) - Cliente Python para GitLab API
- [Click](https://click.palletsprojects.com/) - Framework para CLIs
- [Rich](https://rich.readthedocs.io/) - Formateo de texto en terminal
- [Jinja2](https://jinja.palletsprojects.com/) - Motor de plantillas

---

**Made with ❤️ for the DevOps community**
