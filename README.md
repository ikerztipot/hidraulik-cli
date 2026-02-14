# Hidraulik

> CLI profesional para automatizar la creación de pipelines CI/CD en GitLab con despliegues en Kubernetes

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

## 🚀 Características Principales

### Automatización Inteligente
- ✅ **Cero Configuración Manual**: Genera pipelines completos con una sola línea
- ✅ **Detección Automática de Runners**: Obtiene runners disponibles desde GitLab API
- ✅ **Descubrimiento de Clusters K8s**: Encuentra GitLab Kubernetes Agents en grupos padres
- ✅ **Plantillas Jinja2**: Sistema flexible desde repositorios remotos de GitLab
- ✅ **Validación Robusta**: Valida inputs antes de comunicarse con GitLab

### Seguridad y Confiabilidad
- 🔒 **Almacenamiento Seguro**: Tokens en keyring del sistema (macOS/Linux/Windows)
- 🔒 **Variables Protegidas**: Soporte para variables enmascaradas y protegidas
- 📝 **Logging Estructurado**: Logs rotatorios con niveles configurables
- ⚠️ **Manejo de Errores**: Excepciones específicas con contexto completo

### Arquitectura Limpia
- 🏗️ **Capa de Servicios**: Separación de responsabilidades (VariableService, RunnerService, K8sConfigService)
- 🧪 **Alta Cobertura de Tests**: Suite completa con pytest
- 📦 **Código Modular**: Validadores, excepciones y utilidades separadas
- 📖 **Documentación Completa**: Guías de uso y desarrollo

---

## 📋 Tabla de Contenidos

- [Requisitos](#-requisitos)
- [Instalación](#-instalación)
- [Inicio Rápido](#-inicio-rápido)
- [Comandos](#-comandos)
- [Configuración de GitLab](#%EF%B8%8F-configuración-de-gitlab)
- [Arquitectura del Proyecto](#-arquitectura-del-proyecto)
- [Repositorio de Plantillas](#-repositorio-de-plantillas)
- [Variables y Seguridad](#-variables-y-seguridad)
- [Desarrollo](#-desarrollo)
- [Contribuir](#-contribuir)

---

## 📋 Requisitos

### Sistema
- **Python 3.8+** (requerido)
- **Git** (recomendado)

### GitLab
- Instancia de GitLab (Cloud o self-hosted)
- **Token de Acceso Personal** con permisos:
  - `api` - Acceso completo a la API
  - `read_repository` - Leer repositorios
  - `write_repository` - Escribir en repositorios
- **Repositorio de plantillas** configurado en GitLab (obligatorio)
- **GitLab Kubernetes Agents** configurados (opcional, pero recomendado)

---

## 🔧 Instalación

### Instalación Automática (Recomendada)

```bash
# Clonar repositorio
git clone https://github.com/ikerztipot/hidraulik.git
cd hidraulik

# Ejecutar instalador
./install.sh
```

El instalador detecta automáticamente:
- ✓ Python y versión requerida
- ✓ Instala con `pipx` (aislado) o `pip` (usuario)
- ✓ Configura PATH si es necesario
- ✓ Verifica dependencias del sistema (keyring)

**Nota:** Cierra y abre tu terminal después de la instalación.

### Instalación Manual

```bash
# Con pipx (aislado, recomendado)
pipx install .

# Con pip (usuario)
pip install --user .

# Verificar instalación
hidraulik --version
```

### Desinstalación

```bash
./uninstall.sh
```

Elimina el CLI y opcionalmente la configuración en `~/.hidraulik/`.

---

## ⚡ Inicio Rápido

### 1. Configurar Credenciales

```bash
hidraulik init
```

El CLI solicitará:
- **URL de GitLab**: `https://gitlab.workoholics.es`
- **Token**: `glpat-xxxxxxxxxxxx` (almacenado de forma segura en keyring)
- **Repositorio de plantillas**: `clients/internal-infrastructure/cicd-templates`

**Almacenamiento:**
- Config: `~/.hidraulik/config.json` (sin token)
- Token: Keyring del sistema (seguro) o fallback `~/.hidraulik/.token` (permisos 0o600)
- Logs: `~/.hidraulik/logs/` (rotación 10MB, 5 archivos)

### 2. Crear CI/CD para un Proyecto

```bash
hidraulik create clients/acme/mi-app \\
  --namespace production \\
  --environments pre,prod \\
  --create-project
```

**El CLI ejecutará automáticamente:**

1. **Conexión**
   - Valida credenciales con GitLab
   - Crea proyecto si no existe

2. **Descubrimiento**
   - Busca Kubernetes Agents en grupos padres
   - Obtiene runners disponibles (instancia + grupo + proyecto)

3. **Configuración Interactiva**
   - Componentes (ej: `web`, `api`, `cms`)
   - Docker (Dockerfiles y puertos)
   - Runner (desde lista con tags)
   - Perfiles K8s (xsmall → xlarge)
   - Clusters por entorno

4. **Generación**
   - Procesa plantillas Jinja2
   - Genera manifiestos K8s
   - Commitea archivos
   - Configura variables CI/CD

### 3. Verificar

```bash
# Ver estado
hidraulik status clients/acme/mi-app

# Listar plantillas
hidraulik list-templates

# Añadir variable
hidraulik set-variable clients/acme/mi-app API_KEY "secreto" --masked --protected
```

---

## 📚 Comandos

### `init` - Configuración Inicial

```bash
hidraulik init
```

Configura URL, token (almacenado en keyring) y repositorio de plantillas.

**Keyring por plataforma:**
- **macOS**: Keychain
- **Linux**: Secret Service (GNOME Keyring/KWallet)
- **Windows**: Windows Credential Manager
- **Fallback**: `~/.hidraulik/.token` (permisos 0o600)

---

### `create` - Crear CI/CD

```bash
hidraulik create PROJECT_PATH --namespace NAMESPACE [OPTIONS]
```

**Argumentos:**
- `PROJECT_PATH`: Ruta GitLab (ej: `clients/acme/app`)

**Opciones:**
- `--namespace TEXT` *(requerido)*: Namespace K8s (RFC 1123)
- `--environments TEXT`: Entornos (default: `dev,pre,prod`)
- `--create-project`: Crear proyecto si no existe

**Validaciones automáticas:**
- Namespace: RFC 1123 (lowercase, max 63 chars)
- Project path: Formato `grupo/proyecto`
- Puertos: Rango 1-65535
- Variables: Formato `A-Z`, `0-9`, `_`

**Ejemplo:**
```bash
hidraulik create clients/workoholics/backend \\
  --namespace wkhs-api \\
  --environments staging,production \\
  --create-project
```

**Flujo de ejecución:**
```
→ Configurando CI/CD

Descubriendo recursos GitLab...
✓ 5 runner(s) disponible(s)
✓ 4 cluster(s) encontrado(s):
  1. clients/infrastructure:k3s-slots-caprabo
  2. clients/infrastructure:scaleway-worko-pre
  3. clients/infrastructure:scaleway-worko-prod
  4. clients/infrastructure:scaleway-basquetour

Componentes: api,worker
¿Usa Docker? [y/n]: y
Dockerfile 'api': 
Puerto 'api' (80): 8000
  ✓ api: Dockerfile (puerto 8000)

Selecciona runner (1-5): 2
✓ Runner: gcp-docker (tags: docker, gcp)

Cluster para staging (1-4) o Enter: 2
Cluster para production (1-4) o Enter: 3

Variables para 'api':
Nombre: DATABASE_URL
¿Es secret? [y/n]: y
  🔒 DATABASE_URL → Secret

Generando archivos...
✓ .gitlab-ci.yml
✓ k8s/api/01-namespace.yaml
✓ k8s/api/02-secrets.yaml
✓ k8s/api/04-deployment.yaml

✅ CI/CD configurado exitosamente
```

---

### `status` - Estado del Proyecto

```bash
hidraulik status PROJECT_PATH
```

Muestra:
- Estado del repositorio
- Último pipeline
- Variables CI/CD
- Clusters por entorno

---

### `set-variable` - Configurar Variable CI/CD

```bash
hidraulik set-variable PROJECT_PATH KEY VALUE [OPTIONS]
```

**Opciones:**
- `--protected`: Solo en branches/tags protegidos
- `--masked`: Ocultar en logs
- `--environment-scope`: Limitar a entorno

**Ejemplos:**
```bash
# Variable simple
hidraulik set-variable clients/acme/app API_URL "https://api.acme.com"

# Secret protegido
hidraulik set-variable clients/acme/app DB_PASS "secret" --masked --protected

# Por entorno
hidraulik set-variable clients/acme/app REPLICAS "3" --environment-scope production
```

---

### `list-templates` - Listar Plantillas

```bash
hidraulik list-templates
```

Muestra plantillas disponibles del repositorio configurado, organizadas por tipo (Pipeline, K8s, Helm, Config).

---

## ⚙️ Configuración de GitLab

### 1. Token de Acceso Personal

1. GitLab → **Preferences → Access Tokens**
2. Crear token con permisos:
   - ✅ `api`
   - ✅ `read_repository`
   - ✅ `write_repository`
3. Copiar token (`glpat-xxxxxxxxxxxx`)
4. Usar en `hidraulik init`

### 2. GitLab Kubernetes Agents

**Ubicación:** Grupos padres o proyecto de infraestructura

**Configuración en GitLab UI:**
```
Operate → Kubernetes clusters → Connect a cluster (agent)
```

**Nombres sugeridos:**
- `scaleway-internal-worko-prod`
- `k3s-slots-caprabo`
- `gke-production-us`

**Búsqueda automática del CLI:**
1. Proyecto del repositorio de plantillas
2. Grupos padres del repositorio de plantillas  
3. Grupos padres del proyecto destino

**Formato generado:** `<project_path>:<agent_name>`

**Ejemplo:** `clients/infrastructure:scaleway-worko-prod`

### 3. Runners de GitLab

El CLI descubre automáticamente:
1. **Runners de instancia** (si eres admin)
2. **Runners del grupo**
3. **Runners del proyecto**

**Selección interactiva:**
```
Runners disponibles:
  1. ● gcp-ci-cd-gitlab-runner-docker
     docker, gcp
  2. ● Runner autoescalado cluster
     buildkit, scaleway, worko-internal

Selecciona (1-2): 2
✓ Tags: buildkit, scaleway, worko-internal
```

---

## 🏗 Arquitectura del Proyecto

### Estructura de Directorios

```
hidraulik/
├── src/hidraulik/
│   ├── cli.py                      # CLI principal (orquestación)
│   ├── config.py                   # Config con keyring
│   ├── exceptions.py               # Excepciones personalizadas
│   ├── validators.py               # Validadores de input
│   ├── logging_config.py           # Logging estructurado
│   ├── gitlab_client.py            # Cliente GitLab API
│   ├── template_manager.py         # Carga de plantillas
│   ├── k8s_generator.py            # Procesamiento Jinja2
│   └── services/
│       ├── variable_service.py     # Gestión de variables
│       ├── runner_service.py       # Descubrimiento runners
│       └── k8s_config_service.py   # Configuración K8s
│
├── tests/                          # Suite pytest
│   ├── test_cli.py
│   ├── test_config.py
│   ├── test_gitlab_client.py
│   ├── test_k8s_generator.py
│   └── test_template_manager.py
│
├── docs/                           # Documentación
│   ├── CONTRIBUTING.md
│   ├── TEMPLATE_EXAMPLE.md
│   └── VARIABLES.md
│
├── install.sh                      # Instalador
├── uninstall.sh                    # Desinstalador
├── pyproject.toml                  # Configuración proyecto
└── Makefile                        # Tareas (test, lint, format)
```

### Capas de Abstracción

#### 1. CLI Layer (`cli.py`)
- Interfaz Click
- Orquestación de flujo
- Manejo de errores

#### 2. Service Layer (`services/`)
- **VariableService**: Variables (template + CI/CD + CICD_*)
- **RunnerService**: Runners y tags
- **K8sConfigService**: Recursos K8s (perfiles, manifiestos, PVCs)

#### 3. Client Layer (`gitlab_client.py`)
- Wrapper `python-gitlab`
- CRUD en GitLab
- Runners multi-nivel
- Variables protegidas/enmascaradas

#### 4. Processing Layer (`k8s_generator.py`, `template_manager.py`)
- Carga plantillas (recursivo)
- Procesamiento Jinja2
- Preservación `CICD_*`

#### 5. Validation Layer (`validators.py`)
- K8s namespace (RFC 1123)
- Project path
- Puertos, storage, variables
- Sanitización paths

#### 6. Exception Layer (`exceptions.py`)
- Excepciones context-aware
- Jerarquía personalizada

### Excepciones Personalizadas

```
GitLabCICDError                 # Base
├── ConfigurationError          # Error config.json
├── ValidationError             # Input inválido
├── GitLabAPIError              # Error API GitLab
├── TemplateError               # Error plantillas
├── ProjectNotFoundError        # Proyecto no existe
└── VariableRequiredError       # Variable faltante
```

### Validadores Disponibles

```python
from hidraulik.validators import (
    validate_k8s_namespace,      # RFC 1123
    validate_project_path,        # namespace/project
    validate_port,                # 1-65535
    validate_storage_size,        # 1Gi, 10Gi
    validate_variable_name,       # A-Z, 0-9, _
    sanitize_file_path,           # Path traversal
)
```

---

## 📦 Repositorio de Plantillas

### Estructura Requerida

```
clients/internal-infrastructure/cicd-templates/
│
├── pipeline/                    # CI/CD (procesados Jinja2)
│   └── .gitlab-ci.yml.j2
│
├── includes/                    # Reutilizables (NO procesados)
│   ├── .build-buildkit.yml
│   ├── .deploy-k8s.yml
│   └── .test-python.yml
│
├── k8s/                         # Manifiestos K8s (procesados)
│   ├── 01-namespace.yaml.j2
│   ├── 02-secrets.yaml.j2
│   ├── 03-configs.yaml.j2
│   ├── 04-deployment.yaml.j2
│   ├── 05-ingress.yaml.j2
│   ├── 06-service.yaml.j2
│   └── 07-pvc.yaml.j2
│
└── helm/                        # Charts Helm (opcional)
    └── values.yaml.j2
```

### Tipos de Archivos

| Carpeta | Extensión | Procesado | Destino |
|---------|-----------|-----------|---------|
| `pipeline/` | `.j2` | ✅ Sí | Raíz proyecto |
| `includes/` | `.yml` | ❌ No | Remote include |
| `k8s/` | `.j2` | ✅ Sí | `k8s/<component>/` |
| `helm/` | `.j2` | ✅ Sí | `helm/` |

### Ejemplo Plantilla Principal

**`pipeline/.gitlab-ci.yml.j2`:**
```yaml
# CI/CD para {{ project_name }}

include:
  - project: '{{ template_repo }}'
    ref: main
    file: 
      - '/includes/.build-buildkit.yml'
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

{%- for component in components %}

build-{{ component }}:
  extends: .build-buildkit
  stage: build-{{ component }}
  variables:
    COMPONENT: {{ component }}
{%- if use_docker %}
    DOCKERFILE_PATH: {{ dockerfile_paths[component] }}
{%- endif %}

{%- for env in environments %}
deploy-{{ component }}-{{ env }}:
  extends: .deploy-k8s
  stage: deploy-{{ component }}-{{ env }}
  environment: {{ env }}/{{ component }}
{%- if env == 'prod' %}
  when: manual
{%- endif %}
{%- endfor %}
{%- endfor %}
```

### Remote Include: Build

**`includes/.build-buildkit.yml`:**
```yaml
# @requires: COMPONENT, DOCKERFILE_PATH

.build-buildkit:
  stage: build
  image:
    name: moby/buildkit:latest
    entrypoint: [""]
  script:
    - buildctl build \\
        --frontend dockerfile.v0 \\
        --local context=. \\
        --opt filename=$DOCKERFILE_PATH \\
        --output type=image,push=true
```

**Comentario `@requires`:** El CLI detecta automáticamente variables en includes remotos.

---

## 🔑 Variables y Seguridad

### Tipos de Variables

#### 1. Variables de Plantilla (Sustituidas)

Procesadas por Jinja2:

| Variable | Generación | Valor ejemplo |
|----------|------------|---------------|
| `project_name` | Automático | `mi-app` |
| `project_path` | Automático | `clients/acme/mi-app` |
| `namespace` | Automático | `production` |
| `environments` | Automático | `['pre', 'prod']` |
| `components` | Interactivo | `['web', 'api']` |
| `runner_tags` | Interactivo | `['docker', 'gcp']` |
| `use_docker` | Interactivo | `True` |

**Uso:**
```yaml
metadata:
  name: {{ component }}-{{ project_name }}
  namespace: {{ namespace }}
```

#### 2. Variables de Entorno (K8s)

**Prompt:**
```
Variables para 'api':
Nombre: DATABASE_URL
¿Secret? [y/n]: y
  🔒 DATABASE_URL → Secret
Nombre: LOG_LEVEL
¿Secret? [y/n]: n
  ✓ LOG_LEVEL → ConfigMap
```

**Destino:**
- Secrets: `k8s/<component>/02-secrets.yaml`
- ConfigMaps: `k8s/<component>/03-configs.yaml`

#### 3. Variables CI/CD (Prefijo `CICD_*`)

**En plantilla:**
```yaml
script:
  - docker login -u $CI_REGISTRY_USER -p $CICD_REGISTRY_TOKEN
```

**Durante ejecución:**
```
CICD_REGISTRY_TOKEN: ••••••••
  ¿Protegida? [y/N]: y
  ¿Enmascarada? [Y/n]: y
```

Las variables `CICD_*` **NO** se sustituyen, se guardan en GitLab.

### Buenas Prácticas

#### Variables de Plantilla
✅ Nombres de recursos, configuración estructural  
❌ Credenciales, datos sensibles

#### Variables CI/CD
✅ Tokens, credenciales, URLs externas  
✅ Marcar como protegidas (producción)  
✅ Marcar como enmascaradas (TODAS las credenciales)

#### Almacenamiento del CLI
- Token en keyring (recomendado)
- Fallback: `~/.hidraulik/.token` (permisos 0o600)

---

## 🧪 Desarrollo

### Setup

```bash
git clone https://github.com/ikerztipot/hidraulik.git
cd hidraulik

python3 -m venv venv
source venv/bin/activate

pip install -e ".[dev]"
```

### Tests

```bash
make test          # Todos los tests
make test-cov      # Con cobertura (htmlcov/)
pytest tests/test_cli.py -v     # Test específico
```

### Formatear y Lint

```bash
make format        # black + isort
make lint          # flake8 + mypy
make all           # format + lint + test
```

**Estándares:**
- Línea: 100 caracteres
- Formateador: Black
- Type hints requeridos

### Añadir Funcionalidad

1. **Validador** (`validators.py`)
2. **Servicio** (`services/*.py`)
3. **CLI** (`cli.py`)
4. **Tests** (`tests/`)
5. **Docs** (`README.md`)

---

## 🤝 Contribuir

### Proceso

1. Fork y clone
2. Branch: `feature/mi-feature` o `fix/mi-bugfix`
3. Desarrollar + formatear + tests
4. Commit: [Conventional Commits](https://www.conventionalcommits.org/)
   ```bash
   git commit -m "feat: añadir soporte Helm"
   git commit -m "fix: corregir validación namespace"
   ```
5. Push y Pull Request

### Tipos de Commit

- `feat`: Nueva funcionalidad
- `fix`: Bug fix
- `docs`: Documentación
- `refactor`: Refactorización
- `test`: Tests
- `chore`: Mantenimiento

### Reportar Bugs

Issue con:
- Entorno (Python, SO, versión CLI)
- Comando ejecutado
- Output/Error
- Pasos para reproducir

---

## 📄 Licencia

MIT License - Ver [LICENSE](LICENSE)

---

## 🙏 Agradecimientos

- [python-gitlab](https://python-gitlab.readthedocs.io/) - Cliente GitLab API
- [Click](https://click.palletsprojects.com/) - Framework CLI
- [Rich](https://rich.readthedocs.io/) - Terminal UI
- [Jinja2](https://jinja.palletsprojects.com/) - Motor de plantillas
- [keyring](https://github.com/jaraco/keyring) - Almacenamiento seguro

---

## 📮 Soporte

- **Issues**: [GitHub Issues](https://github.com/ikerztipot/hidraulik/issues)
- **Email**: soporte@workoholics.es

---

**Made with ❤️ for DevOps by Workoholics**

*Automatiza tu infraestructura, libera tu tiempo* 🚀
