# 📦 Guía de Configuración del Repositorio de Plantillas

El CLI **GitLab CI/CD Creator** requiere un repositorio central en GitLab que contenga las plantillas de CI/CD. Esta guía te ayudará a configurarlo.

---

## 🎯 Requisitos del Repositorio

### Ubicación
- Debe estar en GitLab (gitlab.com o tu instancia privada)
- Debe ser accesible con tu token de acceso personal
- Formato de ruta: `grupo/nombre-proyecto` (ej: `acme/plantillas-cicd`)

### Contenido
- **SOLO** archivos con extensión `.j2` (plantillas Jinja2)
- El CLI carga automáticamente todos los archivos `.j2` de forma recursiva
- Puedes organizar las plantillas en carpetas

---

## 📁 Estructura Recomendada

```
tu-grupo/plantillas-cicd/
│
├── .gitlab-ci.yml.j2              # Pipeline principal
│
├── k8s/                           # Manifiestos Kubernetes
│   ├── deployment.yaml.j2
│   ├── service.yaml.j2
│   ├── ingress.yaml.j2
│   ├── configmap.yaml.j2
│   └── secret.yaml.j2
│
├── docker/                        # Dockerfiles
│   ├── Dockerfile.j2
│   └── Dockerfile.multi-stage.j2
│
└── scripts/                       # Scripts opcionales
    ├── build.sh.j2
    └── deploy.sh.j2
```

---

## 🚀 Paso a Paso: Crear el Repositorio

### 1. Crear Repositorio en GitLab

```bash
# Opción A: Crear desde la UI de GitLab
# 1. Ve a GitLab → New Project → Create blank project
# 2. Nombre: plantillas-cicd
# 3. Visibility: Private (recomendado)
# 4. Initialize with README: No

# Opción B: Crear desde CLI (si tienes glab instalado)
glab repo create plantillas-cicd --private
```

### 2. Clonar el Repositorio

```bash
git clone git@gitlab.com:tu-grupo/plantillas-cicd.git
cd plantillas-cicd
```

### 3. Crear Estructura de Carpetas

```bash
mkdir -p k8s docker scripts
```

### 4. Crear Plantilla Base de GitLab CI/CD

Crea el archivo `.gitlab-ci.yml.j2`:

```yaml
# GitLab CI/CD para {{ project_name }}
# Auto-generado por gitlab-cicd-creator

stages:
  - build
  - test
  - deploy

variables:
  DOCKER_REGISTRY: {{ docker_registry }}
  DOCKER_IMAGE: {{ docker_image }}
  K8S_NAMESPACE: {{ namespace }}
  ENVIRONMENT: {{ environment }}
  DOCKER_DRIVER: overlay2

# Build de imagen Docker
build:
  stage: build
  image: docker:24-git
  services:
    - docker:24-dind
  before_script:
    - echo "$CI_REGISTRY_PASSWORD" | docker login -u "$CI_REGISTRY_USER" --password-stdin $DOCKER_REGISTRY
  script:
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
    - echo "Ejecutando tests..."
    # Añade tus comandos de test aquí
  only:
    - main
    - develop

# Deploy a Kubernetes
deploy:{{ environment }}:
  stage: deploy
  image: bitnami/kubectl:latest
  script:
    - kubectl config use-context {{ k8s_cluster }}
    - kubectl apply -f k8s/
    - kubectl set image deployment/{{ project_name }} {{ project_name }}=$DOCKER_REGISTRY/$DOCKER_IMAGE:$CI_COMMIT_SHORT_SHA -n $K8S_NAMESPACE
    - kubectl rollout status deployment/{{ project_name }} -n $K8S_NAMESPACE
  only:
    - main
  environment:
    name: {{ environment }}
```

### 5. Crear Plantilla de Kubernetes Deployment

Crea `k8s/deployment.yaml.j2`:

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
```

### 6. Crear Plantilla de Kubernetes Service

Crea `k8s/service.yaml.j2`:

```yaml
apiVersion: v1
kind: Service
metadata:
  name: {{ project_name }}
  namespace: {{ namespace }}
spec:
  selector:
    app: {{ project_name }}
  ports:
  - port: 80
    targetPort: 8080
  type: ClusterIP
```

### 7. Crear Plantilla de Dockerfile

Crea `docker/Dockerfile.j2`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8080

CMD ["python", "app.py"]
```

### 8. Crear README del Repositorio

Crea `README.md`:

```markdown
# Plantillas CI/CD

Repositorio central de plantillas para GitLab CI/CD Creator.

## Contenido

- `.gitlab-ci.yml.j2` - Pipeline principal de GitLab CI/CD
- `k8s/` - Manifiestos de Kubernetes
- `docker/` - Dockerfiles

## Variables Disponibles

Las plantillas tienen acceso a las siguientes variables:

- `{{ project_name }}` - Nombre del proyecto
- `{{ project_path }}` - Ruta completa del proyecto
- `{{ k8s_cluster }}` - Cluster de Kubernetes
- `{{ namespace }}` - Namespace de Kubernetes
- `{{ environment }}` - Ambiente (dev/staging/prod)
- `{{ docker_registry }}` - Registro de Docker
- `{{ docker_image }}` - Nombre de la imagen Docker

## Uso

Estas plantillas son utilizadas automáticamente por el CLI `gitlab-cicd-creator`.
```

### 9. Commit y Push

```bash
git add .
git commit -m "Initial commit: Plantillas base de CI/CD"
git push origin main
```

---

## ✅ Verificar el Repositorio

### Desde GitLab UI
1. Ve a tu repositorio en GitLab
2. Verifica que todos los archivos `.j2` estén presentes
3. Confirma que tienes permisos de lectura

### Desde el CLI

```bash
# Configurar el CLI con tu repositorio
gitlab-cicd init

# Listar plantillas disponibles
gitlab-cicd list-templates
```

Deberías ver una lista de todas tus plantillas `.j2`.

---

## 🎨 Personalizar Plantillas

### Variables Jinja2

Usa la sintaxis `{{ variable }}` para variables que serán sustituidas:

```yaml
# Ejemplo
name: {{ project_name }}
namespace: {{ namespace }}
environment: {{ environment }}
```

### Condicionales

Puedes usar condicionales en tus plantillas:

```yaml
{% if environment == 'prod' %}
replicas: 3
{% else %}
replicas: 1
{% endif %}
```

### Loops

También puedes usar loops:

```yaml
env:
{% for key, value in env_vars.items() %}
- name: {{ key }}
  value: "{{ value }}"
{% endfor %}
```

---

## 🔒 Seguridad

### Permisos Recomendados
- **Lectura**: Todos los usuarios que usarán el CLI
- **Escritura**: Solo administradores del equipo DevOps
- **Visibility**: Private (para proteger tu infraestructura)

### Token de Acceso
- Asegúrate de que tu token tenga el scope `read_repository`
- No compartas tu token
- Rota el token periódicamente

---

## 📚 Ejemplos Adicionales

### Plantilla con Múltiples Ambientes

```yaml
{% if environment == 'prod' %}
resources:
  limits:
    memory: "1Gi"
    cpu: "1000m"
{% elif environment == 'staging' %}
resources:
  limits:
    memory: "512Mi"
    cpu: "500m"
{% else %}
resources:
  limits:
    memory: "256Mi"
    cpu: "250m"
{% endif %}
```

### Plantilla con Valores por Defecto

```yaml
replicas: {{ replicas | default(2) }}
image: {{ docker_image | default('app:latest') }}
```

---

## 🆘 Solución de Problemas

### "No se encontraron plantillas"
- Verifica que los archivos tengan extensión `.j2`
- Confirma que el repositorio existe y es accesible
- Revisa los permisos de tu token

### "Error al acceder al repositorio"
- Verifica el formato de la ruta: `grupo/proyecto`
- Confirma que tienes permisos de lectura
- Asegúrate de que la rama `main` existe

### "Variable no definida"
- Revisa que estés usando `{{ variable }}` correctamente
- Consulta la lista de variables disponibles en el README

---

## 🔄 Actualizar Plantillas

Para actualizar las plantillas:

1. Edita los archivos `.j2` en tu repositorio
2. Commit y push los cambios
3. El CLI usará automáticamente la versión más reciente

**Tip**: Usa tags de Git para versionar tus plantillas:

```bash
git tag -a v1.0.0 -m "Primera versión estable"
git push origin v1.0.0
```

---

## 📞 Recursos

- [Documentación de Jinja2](https://jinja.palletsprojects.com/)
- [GitLab CI/CD Docs](https://docs.gitlab.com/ee/ci/)
- [Kubernetes Docs](https://kubernetes.io/docs/)

---

✨ ¡Listo! Ahora tienes un repositorio central de plantillas configurado y listo para usar con el CLI.
