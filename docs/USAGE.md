# Guía de Uso

## Instalación

### Requisitos Previos
- Python 3.8+
- pip
- Git

### Pasos de Instalación

1. **Clonar el repositorio**
```bash
git clone https://github.com/ikerztipot/gitlab-repo-cicd-creator-cli.git
cd gitlab-repo-cicd-creator-cli
```

2. **Crear entorno virtual**
```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

3. **Instalar el CLI**
```bash
pip install -e .
```

## Configuración Inicial

### 1. Obtener Token de GitLab

1. Accede a tu cuenta de GitLab
2. Ve a **Settings** → **Access Tokens**
3. Crea un nuevo token con los siguientes scopes:
   - `api`
   - `read_repository`
   - `write_repository`
4. Copia el token generado

### 2. Configurar el CLI

```bash
gitlab-cicd init
```

El CLI te solicitará:
- **URL de GitLab**: Por ejemplo, `https://gitlab.com`
- **Token de Acceso**: El token que generaste anteriormente
- **Repositorio de Plantillas**: URL del repositorio con tus plantillas personalizadas (opcional)

## Casos de Uso

### Caso 1: Crear CI/CD para Proyecto Existente

```bash
gitlab-cicd create mi-grupo/mi-proyecto \
  --k8s-cluster production \
  --namespace mi-app-prod \
  --environment prod
```

### Caso 2: Crear Proyecto Nuevo con CI/CD

```bash
gitlab-cicd create mi-grupo/nueva-app \
  --k8s-cluster staging \
  --namespace nueva-app-staging \
  --environment staging \
  --create-project
```

### Caso 3: Configurar Variables Sensibles

```bash
# Variable enmascarada
gitlab-cicd set-variable mi-grupo/mi-proyecto \
  DATABASE_PASSWORD "mi-password-secreto" \
  --masked

# Variable protegida
gitlab-cicd set-variable mi-grupo/mi-proyecto \
  PRODUCTION_API_KEY "api-key-secreta" \
  --protected --masked
```

### Caso 4: Ver Estado del Pipeline

```bash
gitlab-cicd status mi-grupo/mi-proyecto
```

## Personalización de Plantillas

### Estructura de Repositorio de Plantillas

Crea un repositorio en GitLab con la siguiente estructura:

```
plantillas-cicd/
├── .gitlab-ci.yml.j2
├── k8s/
│   ├── deployment.yaml.j2
│   ├── service.yaml.j2
│   ├── ingress.yaml.j2
│   └── configmap.yaml.j2
├── docker/
│   └── Dockerfile.j2
└── README.md
```

### Variables Disponibles en Plantillas

Las plantillas tienen acceso a las siguientes variables:

| Variable | Descripción | Ejemplo |
|----------|-------------|---------|
| `project_name` | Nombre del proyecto | `mi-app` |
| `project_path` | Ruta completa | `grupo/mi-app` |
| `k8s_cluster` | Cluster K8s | `production` |
| `namespace` | Namespace K8s | `mi-app-prod` |
| `environment` | Ambiente | `prod` |
| `docker_registry` | Registry Docker | `registry.gitlab.com` |
| `docker_image` | Imagen Docker | `grupo/mi-app` |

### Ejemplo de Plantilla

```yaml
# .gitlab-ci.yml.j2
stages:
  - build
  - deploy

build:
  stage: build
  script:
    - docker build -t {{ docker_registry }}/{{ docker_image }}:$CI_COMMIT_SHA .
    - docker push {{ docker_registry }}/{{ docker_image }}:$CI_COMMIT_SHA

deploy:
  stage: deploy
  script:
    - kubectl set image deployment/{{ project_name }} \
        {{ project_name }}={{ docker_registry }}/{{ docker_image }}:$CI_COMMIT_SHA \
        -n {{ namespace }}
  only:
    - main
  environment:
    name: {{ environment }}
```

## Flujo de Trabajo Recomendado

### Para Nuevos Proyectos

1. **Crear repositorio en GitLab**
   ```bash
   gitlab-cicd create grupo/nuevo-proyecto \
     --k8s-cluster dev \
     --namespace nuevo-proyecto-dev \
     --environment dev \
     --create-project
   ```

2. **Clonar y añadir código**
   ```bash
   git clone git@gitlab.com:grupo/nuevo-proyecto.git
   cd nuevo-proyecto
   # Añadir tu código aquí
   ```

3. **Commit y push**
   ```bash
   git add .
   git commit -m "Initial commit"
   git push origin main
   ```

4. **Verificar pipeline**
   ```bash
   gitlab-cicd status grupo/nuevo-proyecto
   ```

### Para Proyectos Existentes

1. **Añadir CI/CD**
   ```bash
   gitlab-cicd create grupo/proyecto-existente \
     --k8s-cluster production \
     --namespace proyecto-prod \
     --environment prod
   ```

2. **Verificar cambios localmente** (opcional)
   ```bash
   cd proyecto-existente
   git pull origin main
   ```

3. **Ajustar configuración**
   - Revisa el `.gitlab-ci.yml` generado
   - Ajusta las configuraciones de Kubernetes según tus necesidades
   - Añade variables específicas

4. **Activar pipeline**
   - Haz un commit en la rama `main`
   - El pipeline se ejecutará automáticamente

## Solución de Problemas

### Error: "No se ha inicializado la configuración"

**Solución**: Ejecuta `gitlab-cicd init` y proporciona tus credenciales.

### Error: "Token de acceso inválido"

**Solución**: 
1. Verifica que el token tenga los permisos correctos (`api`, `read_repository`, `write_repository`)
2. Asegúrate de que el token no haya expirado
3. Ejecuta `gitlab-cicd init` nuevamente con un nuevo token

### Error: "Proyecto no encontrado"

**Solución**:
- Verifica que la ruta del proyecto sea correcta (formato: `grupo/proyecto`)
- Si el proyecto no existe, usa la opción `--create-project`

### Pipeline falla en build

**Solución**:
1. Verifica que el Dockerfile esté presente en el repositorio
2. Revisa los logs del pipeline en GitLab
3. Asegúrate de que las variables de CI/CD estén correctamente configuradas

### Error de despliegue en Kubernetes

**Solución**:
1. Verifica que el cluster K8s esté configurado en GitLab
2. Confirma que el namespace existe o puede ser creado
3. Revisa los permisos del service account usado por GitLab CI

## Tips y Mejores Prácticas

### 1. Usar Ambientes Separados

```bash
# Desarrollo
gitlab-cicd create grupo/app --k8s-cluster dev --namespace app-dev --environment dev

# Staging
gitlab-cicd create grupo/app --k8s-cluster staging --namespace app-staging --environment staging

# Producción
gitlab-cicd create grupo/app --k8s-cluster prod --namespace app-prod --environment prod
```

### 2. Gestión de Secrets

Usa siempre `--masked` para secretos:

```bash
gitlab-cicd set-variable grupo/app SECRET_KEY "valor-secreto" --masked
```

### 3. Variables por Ambiente

GitLab permite variables específicas por ambiente. Puedes configurarlas manualmente en la UI de GitLab después de usar el CLI.

### 4. Plantillas Versionadas

Mantén tus plantillas en un repositorio versionado y usa tags:

```bash
gitlab-cicd init --template-repo grupo/plantillas@v1.0.0
```

### 5. Validación Local

Antes de hacer push, valida tu configuración localmente:

```bash
# Validar sintaxis YAML
yamllint .gitlab-ci.yml

# Validar configuración K8s
kubectl apply --dry-run=client -f k8s/
```

## Soporte

Para más ayuda:
- Consulta la documentación completa en el README
- Abre un issue en GitHub: https://github.com/ikerztipot/gitlab-repo-cicd-creator-cli/issues
- Contacta al equipo de desarrollo
