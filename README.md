# GitLab CI/CD Creator

Un CLI potente y flexible para generar automáticamente configuraciones de CI/CD en repositorios de GitLab para despliegues en Kubernetes.

## 🚀 Características

- **Automatización Completa**: Genera pipelines CI/CD listos para producción
- **Kubernetes Native**: Configuraciones optimizadas para clusters K8s
- **Plantillas Personalizables**: Usa plantillas desde repositorios de GitLab
- **Variables CI/CD**: Gestión automática de variables de entorno
- **Múltiples Ambientes**: Soporte para dev, staging y producción
- **Integración GitLab**: Comunicación directa con la API de GitLab

## 📋 Requisitos

- Python 3.8 o superior
- Cuenta de GitLab con token de acceso personal
- **Repositorio central de plantillas en GitLab** (obligatorio)
- Acceso a un cluster de Kubernetes (para despliegues)

## 🔧 Instalación

### Desde el código fuente

```bash
# Clonar el repositorio
git clone https://github.com/ikerztipot/gitlab-repo-cicd-creator-cli.git
cd gitlab-repo-cicd-creator-cli

# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# Instalar dependencias
pip install -e .

# O instalar con dependencias de desarrollo
pip install -e ".[dev]"
```

### Usando pip (cuando esté publicado)

```bash
pip install gitlab-cicd-creator
```

## 🎯 Uso Rápido

### 1. Inicializar configuración

```bash
gitlab-cicd init
```

El CLI te pedirá:
- URL de GitLab (ej: https://gitlab.com)
- Token de acceso personal
- **Ruta del repositorio de plantillas** (ej: grupo/plantillas-cicd) - **OBLIGATORIO**

### 2. Crear CI/CD para un proyecto

```bash
gitlab-cicd create grupo/proyecto \
  --k8s-cluster mi-cluster \
  --namespace production \
  --environment prod
```

### 3. Ver estado del CI/CD

```bash
gitlab-cicd status grupo/proyecto
```

### 4. Configurar variables CI/CD

```bash
gitlab-cicd set-variable grupo/proyecto API_KEY "tu-api-key" --masked
```

### 5. Listar plantillas disponibles

```bash
gitlab-cicd list-templates
```

## 📚 Comandos Disponibles

### `init`
Inicializa la configuración del CLI.

```bash
gitlab-cicd init [--gitlab-url URL] [--token TOKEN] [--template-repo REPO]
```

**Opciones:**
- `--gitlab-url`: URL de GitLab (por defecto: https://gitlab.com)
- `--token`: Token de acceso personal
- `--template-repo`: URL del repositorio de plantillas

### `create`
Crea la configuración CI/CD para un repositorio.

```bash
gitlab-cicd create PROJECT_PATH [OPTIONS]
```

**Argumentos:**
- `PROJECT_PATH`: Ruta del proyecto en GitLab (ej: grupo/proyecto)

**Opciones:**
- `--k8s-cluster`: Nombre del cluster de Kubernetes (requerido)
- `--namespace`: Namespace de Kubernetes (requerido)
- `--environment`: Ambiente (dev/staging/prod, por defecto: dev)
- `--create-project`: Crear el proyecto si no existe

**Ejemplo:**
```bash
gitlab-cicd create mi-grupo/mi-app \
  --k8s-cluster production-k8s \
  --namespace mi-app-prod \
  --environment prod \
  --create-project
```

### `status`
Muestra el estado del CI/CD de un proyecto.

```bash
gitlab-cicd status PROJECT_PATH
```

### `set-variable`
Establece una variable CI/CD en un proyecto.

```bash
gitlab-cicd set-variable PROJECT_PATH KEY VALUE [OPTIONS]
```

**Opciones:**
- `--protected`: Marcar como variable protegida
- `--masked`: Enmascarar el valor en los logs

**Ejemplo:**
```bash
gitlab-cicd set-variable mi-grupo/mi-app DATABASE_PASSWORD "secreto123" --masked --protected
```

### `list-templates`
Lista las plantillas disponibles.

```bash
gitlab-cicd list-templates
```

## 🔑 Configuración Inicial

### 1. Crear Repositorio de Plantillas

**⚠️ IMPORTANTE**: Antes de usar el CLI, debes crear un repositorio en GitLab con las plantillas.

📖 **[Ver Guía Completa de Configuración de Plantillas](docs/TEMPLATE_REPO_SETUP.md)**

Resumen rápido:
1. Crea un repositorio en GitLab (ej: `tu-grupo/plantillas-cicd`)
2. Añade archivos de plantilla con extensión `.j2`
3. Estructura recomendada: `.gitlab-ci.yml.j2`, `k8s/*.j2`, `docker/*.j2`

### 2. Obtener Token de GitLab

Para obtener un token de acceso personal:

1. Ve a GitLab → Settings → Access Tokens
2. Crea un nuevo token con los siguientes permisos:
   - `api` - Acceso completo a la API
   - `read_repository` - Leer repositorios
   - `write_repository` - Escribir en repositorios
3. Guarda el token de forma segura

## 📝 Repositorio Central de Plantillas (Obligatorio)

**IMPORTANTE**: Las plantillas deben estar en un repositorio de GitLab accesible. El CLI lee las plantillas directamente desde este repositorio.

### Estructura Recomendada

Crea un repositorio en GitLab (ej: `tu-grupo/plantillas-cicd`) con la siguiente estructura:

```
plantillas-cicd/
├── .gitlab-ci.yml.j2
├── k8s/
│   ├── deployment.yaml.j2
│   ├── service.yaml.j2
│   └── ingress.yaml.j2
└── docker/
    └── Dockerfile.j2
```

**Notas importantes:**
- Todos los archivos de plantilla deben tener extensión `.j2`
- El CLI carga automáticamente todas las plantillas `.j2` del repositorio
- Las plantillas usan sintaxis Jinja2 para sustitución de variables
- El repositorio debe ser accesible con tu token de GitLab

### Gestión de Variables

El CLI maneja dos tipos de variables en las plantillas:

#### 1. Variables de Plantilla (se sustituyen en archivos)

Variables que se solicitan y se escriben directamente en los archivos generados:

- `{{ project_name }}` - Nombre del proyecto
- `{{ project_path }}` - Ruta completa del proyecto
- `{{ k8s_cluster }}` - Nombre del cluster K8s
- `{{ namespace }}` - Namespace de Kubernetes
- `{{ environment }}` - Ambiente (dev/staging/prod)
- `{{ docker_registry }}` - Registro de Docker
- `{{ docker_image }}` - Nombre de la imagen

#### 2. Variables CI/CD (se guardan en GitLab)

Variables que se mantienen como referencias y se guardan en la configuración de GitLab:

**Convención**: Variables que empiezan con `CICD_` en las plantillas se guardan automáticamente como variables CI/CD en GitLab.

Ejemplo en plantilla:
```yaml
build:
  script:
    - docker login -u $CI_REGISTRY_USER -p $CICD_DOCKER_TOKEN }}
    - curl -H "Authorization: Bearer $CICD_API_KEY }}" $CICD_API_URL }}
```

Durante la ejecución, el CLI:
1. Detecta las variables `CICD_*`
2. Solicita sus valores al usuario
3. Las guarda como variables CI/CD en GitLab (protegidas/enmascaradas según se indique)
4. **NO las sustituye** en los archivos, se mantienen como `$CICD_* }}`

📖 **[Ver Documentación Completa de Variables](docs/VARIABLES.md)**

## 🧪 Desarrollo

### Ejecutar tests

```bash
pytest
```

### Con cobertura

```bash
pytest --cov=gitlab_cicd_creator --cov-report=html
```

### Formatear código

```bash
black src/
isort src/
```

### Linting

```bash
flake8 src/
mypy src/
```

## 📦 Estructura del Proyecto

```
gitlab-repo-cicd-creator-cli/
├── src/
│   └── gitlab_cicd_creator/
│       ├── __init__.py
│       ├── cli.py              # CLI principal
│       ├── config.py           # Gestión de configuración
│       ├── gitlab_client.py    # Cliente de GitLab API
│       ├── template_manager.py # Gestor de plantillas (carga desde GitLab)
│       └── k8s_generator.py    # Generador K8s
├── tests/
│   ├── __init__.py
│   ├── test_cli.py
│   ├── test_gitlab_client.py
│   └── test_template_manager.py
├── docs/
│   ├── USAGE.md                # Guía de uso completa
│   ├── CONTRIBUTING.md         # Guía de contribución
│   └── TEMPLATE_REPO_SETUP.md  # Configurar repositorio de plantillas
├── pyproject.toml
├── requirements.txt
└── README.md
```

**Nota**: Las plantillas se almacenan en tu **repositorio GitLab** (ver [docs/TEMPLATE_REPO_SETUP.md](docs/TEMPLATE_REPO_SETUP.md)).

## 🤝 Contribuir

Las contribuciones son bienvenidas! Por favor:

1. Haz fork del proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo `LICENSE` para más detalles.

## 🐛 Reportar Problemas

Si encuentras algún bug o tienes una sugerencia, por favor abre un [issue](https://github.com/ikerztipot/gitlab-repo-cicd-creator-cli/issues).

## 👥 Autores

- Tu Nombre - [@ikerztipot](https://github.com/ikerztipot)

## 🙏 Agradecimientos

- [python-gitlab](https://python-gitlab.readthedocs.io/) - Cliente Python para GitLab API
- [Click](https://click.palletsprojects.com/) - Framework para CLIs
- [Rich](https://rich.readthedocs.io/) - Formateo de texto en terminal
- [Jinja2](https://jinja.palletsprojects.com/) - Motor de plantillas

---

**Made with ❤️ for the DevOps community**
