# 🔄 Resumen de Cambios - v0.2.0

## Ajustes Implementados

He realizado los cambios solicitados para que el CLI funcione exclusivamente con un repositorio central de plantillas en GitLab.

---

## ✅ Cambios Principales

### 1. **Repositorio de Plantillas Obligatorio**

**Antes:**
- El repositorio de plantillas era opcional
- Podía usar plantillas locales por defecto

**Ahora:**
- ✅ El repositorio de plantillas es **OBLIGATORIO**
- ✅ Debe configurarse durante `gitlab-cicd init`
- ✅ Se valida que el repositorio existe y es accesible
- ✅ Se verifica que contiene archivos `.j2`

### 2. **Validación Durante Inicialización**

El comando `gitlab-cicd init` ahora:
- ✅ Verifica la conexión con GitLab
- ✅ Valida que el repositorio de plantillas existe
- ✅ Comprueba permisos de lectura
- ✅ Cuenta las plantillas disponibles
- ✅ Muestra advertencias si no hay plantillas `.j2`
- ✅ No guarda la configuración si algo falla

### 3. **Carga de Plantillas desde GitLab**

**Antes:**
```python
templates = template_manager.load_templates()  # Local
```

**Ahora:**
```python
templates = template_manager.load_from_gitlab(
    gitlab_url,
    token,
    template_repo_path
)
```

El CLI ahora:
- ✅ Carga plantillas directamente desde GitLab
- ✅ Solo procesa archivos con extensión `.j2`
- ✅ Busca recursivamente en todo el repositorio
- ✅ Muestra progreso durante la carga
- ✅ Cachea las plantillas cargadas

### 4. **Sustitución de Variables**

El proceso de sustitución de variables funciona así:

1. **Usuario ejecuta**: `gitlab-cicd create grupo/proyecto --k8s-cluster prod --namespace app`
2. **CLI pide datos adicionales**: Docker registry, imagen, etc.
3. **CLI carga plantillas** desde el repositorio GitLab configurado
4. **Motor Jinja2 sustituye** las variables en cada plantilla:
   ```jinja2
   name: {{ project_name }}           → name: mi-proyecto
   namespace: {{ namespace }}         → namespace: app
   environment: {{ environment }}     → environment: prod
   cluster: {{ k8s_cluster }}        → cluster: prod
   ```
5. **CLI crea archivos** en el proyecto de GitLab con el contenido procesado

---

## 📁 Archivos Modificados

### Código Principal

1. **`src/gitlab_cicd_creator/config.py`**
   - Agregado `template_repo` como campo obligatorio en `is_configured()`

2. **`src/gitlab_cicd_creator/cli.py`**
   - Validación obligatoria del repositorio en `init`
   - Verificación de existencia y acceso al repositorio
   - Carga de plantillas desde GitLab en `create`
   - Actualizado `list-templates` para cargar desde GitLab

3. **`src/gitlab_cicd_creator/template_manager.py`**
   - Método `load_templates()` marcado como deprecated
   - Mejorado `load_from_gitlab()` con:
     - Mejor manejo de errores
     - Filtrado por extensión `.j2`
     - Mensajes de progreso
     - Caché de plantillas

### Documentación

4. **`README.md`**
   - Sección sobre repositorio obligatorio
   - Enlace a guía de configuración
   - Requisitos actualizados

5. **`docs/TEMPLATE_REPO_SETUP.md`** (NUEVO)
   - Guía completa paso a paso
   - Estructura recomendada
   - Ejemplos de plantillas
   - Uso de variables Jinja2
   - Solución de problemas

6. **`QUICKSTART.md`**
   - Advertencia sobre repositorio obligatorio

7. **`CHANGELOG.md`**
   - Nueva versión 0.2.0 con cambios detallados

8. **`.env.example`**
   - Comentarios sobre repositorio obligatorio

9. **`WELCOME.txt`**
   - Enlace a guía de configuración de plantillas

---

## 🎯 Flujo de Trabajo Actualizado

### Configuración Inicial (Una Vez)

```bash
# 1. Crear repositorio de plantillas en GitLab
# En GitLab UI: Nuevo proyecto → tu-grupo/plantillas-cicd

# 2. Añadir plantillas al repositorio
git clone git@gitlab.com:tu-grupo/plantillas-cicd.git
cd plantillas-cicd
# ... crear archivos .j2 ...
git add .
git commit -m "Plantillas iniciales"
git push

# 3. Configurar el CLI
cd /ruta/al/cli
./install.sh
source venv/bin/activate
gitlab-cicd init
# Proporcionar:
#   - URL: https://gitlab.com
#   - Token: glpat-xxxxx
#   - Repo plantillas: tu-grupo/plantillas-cicd
```

### Uso Diario

```bash
# Crear CI/CD para un proyecto
gitlab-cicd create mi-grupo/mi-app \
  --k8s-cluster production \
  --namespace mi-app-prod \
  --environment prod

# El CLI automáticamente:
# 1. Carga plantillas desde tu-grupo/plantillas-cicd
# 2. Sustituye variables con los datos proporcionados
# 3. Crea archivos en mi-grupo/mi-app
# 4. Configura variables CI/CD
```

---

## 🔍 Validaciones Implementadas

### Durante `gitlab-cicd init`:
- ✅ URL de GitLab no vacía
- ✅ Token no vacío
- ✅ Repositorio de plantillas no vacío
- ✅ Conexión exitosa a GitLab
- ✅ Usuario autenticado correctamente
- ✅ Repositorio de plantillas existe
- ✅ Permisos de lectura en el repositorio
- ✅ Hay archivos `.j2` en el repositorio

### Durante `gitlab-cicd create`:
- ✅ Configuración completa (`init` ejecutado)
- ✅ Plantillas cargadas exitosamente desde GitLab
- ✅ Al menos una plantilla disponible
- ✅ Variables proporcionadas por el usuario

---

## 📊 Ejemplo de Sustitución de Variables

### Plantilla (en GitLab: tu-grupo/plantillas-cicd)

**Archivo**: `.gitlab-ci.yml.j2`
```yaml
stages:
  - build
  - deploy

variables:
  IMAGE: {{ docker_registry }}/{{ docker_image }}
  NAMESPACE: {{ namespace }}

build:
  stage: build
  script:
    - docker build -t $IMAGE:{{ project_name }}-$CI_COMMIT_SHA .

deploy:
  stage: deploy
  script:
    - kubectl set image deployment/{{ project_name }} \
        app=$IMAGE:{{ project_name }}-$CI_COMMIT_SHA \
        -n {{ namespace }}
  environment:
    name: {{ environment }}
```

### Comando del Usuario
```bash
gitlab-cicd create acme/api \
  --k8s-cluster prod-k8s \
  --namespace acme-prod \
  --environment prod
# CLI pide: docker_registry=registry.gitlab.com, docker_image=acme/api
```

### Resultado (en GitLab: acme/api)

**Archivo**: `.gitlab-ci.yml`
```yaml
stages:
  - build
  - deploy

variables:
  IMAGE: registry.gitlab.com/acme/api
  NAMESPACE: acme-prod

build:
  stage: build
  script:
    - docker build -t $IMAGE:api-$CI_COMMIT_SHA .

deploy:
  stage: deploy
  script:
    - kubectl set image deployment/api \
        app=$IMAGE:api-$CI_COMMIT_SHA \
        -n acme-prod
  environment:
    name: prod
```

---

## 📚 Nueva Documentación

### `docs/TEMPLATE_REPO_SETUP.md`

Esta nueva guía incluye:
- ✅ Requisitos del repositorio de plantillas
- ✅ Estructura recomendada
- ✅ Paso a paso para crear el repositorio
- ✅ Ejemplos de plantillas completas
- ✅ Uso de variables Jinja2
- ✅ Condicionales y loops en plantillas
- ✅ Recomendaciones de seguridad
- ✅ Solución de problemas comunes
- ✅ Cómo versionar plantillas con Git tags

---

## ✨ Características Clave

### 1. **Centralización**
- Una única fuente de verdad para las plantillas
- Fácil de mantener y actualizar
- Versionamiento con Git

### 2. **Seguridad**
- Control de acceso mediante permisos de GitLab
- Auditoría de cambios en plantillas
- Tokens con permisos específicos

### 3. **Flexibilidad**
- Organización libre de plantillas en carpetas
- Soporte para múltiples tipos de plantillas
- Variables personalizables

### 4. **Validación**
- Verificación automática de acceso
- Detección de problemas de permisos
- Feedback claro de errores

---

## 🧪 Cómo Probar

### 1. Crear Repositorio de Prueba

```bash
# En GitLab, crear: tu-usuario/test-templates
# Clonar y añadir un archivo de prueba:
echo "name: {{ project_name }}" > test.yaml.j2
git add test.yaml.j2
git commit -m "Test template"
git push
```

### 2. Configurar CLI

```bash
gitlab-cicd init
# URL: https://gitlab.com
# Token: tu-token
# Repo: tu-usuario/test-templates
```

### 3. Verificar Carga

```bash
gitlab-cicd list-templates
# Debería mostrar: test.yaml.j2
```

### 4. Probar Creación

```bash
gitlab-cicd create tu-usuario/test-project \
  --k8s-cluster test \
  --namespace test \
  --environment dev \
  --create-project
```

---

## 🎉 Resultado

Ahora el CLI:
- ✅ Requiere configuración completa antes de usar
- ✅ Carga plantillas exclusivamente desde GitLab
- ✅ Valida acceso y permisos automáticamente
- ✅ Sustituye variables correctamente
- ✅ Proporciona feedback claro al usuario

¡Listo para usar! 🚀
