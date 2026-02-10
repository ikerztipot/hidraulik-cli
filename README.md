# GitLab CI/CD Creator

Un CLI potente y flexible para generar automáticamente configuraciones de CI/CD en repositorios de GitLab para despliegues en Kubernetes.

## � Tabla de Contenidos

- [Características](#-características)
- [Requisitos](#-requisitos)
- [Instalación](#-instalación)
- [Uso Rápido](#-uso-rápido)
- [Comandos Disponibles](#-comandos-disponibles)
- [Repositorio de Plantillas](#-repositorio-de-plantillas)
- [Variables en Plantillas](#-variables-en-plantillas)
- [Configuración de GitLab](#-configuración-de-gitlab)
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
2. Te permite seleccionar el cluster para cada entorno
3. Carga las plantillas desde el repositorio
4. Solicita valores para variables
5. Genera y commit los archivos al proyecto

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

Las contribuciones son bienvenidas:

1. Fork del proyecto
2. Crea una rama (`git checkout -b feature/AmazingFeature`)
3. Commit cambios (`git commit -m 'Add AmazingFeature'`)
4. Push (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📄 Licencia

MIT License - Ver archivo `LICENSE`

## 🙏 Agradecimientos

- [python-gitlab](https://python-gitlab.readthedocs.io/) - Cliente Python para GitLab API
- [Click](https://click.palletsprojects.com/) - Framework para CLIs
- [Rich](https://rich.readthedocs.io/) - Formateo de texto en terminal
- [Jinja2](https://jinja.palletsprojects.com/) - Motor de plantillas

---

**Made with ❤️ for the DevOps community**
