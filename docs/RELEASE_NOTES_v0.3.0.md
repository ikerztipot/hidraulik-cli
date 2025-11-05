# Resumen de Cambios - Sistema de Variables CI/CD

## 📋 Resumen Ejecutivo

Se ha implementado un sistema inteligente de clasificación de variables que distingue automáticamente entre:

1. **Variables de Plantilla** → Se sustituyen directamente en los archivos
2. **Variables CI/CD** → Se guardan en la configuración de GitLab

## 🎯 Convención Adoptada

### Variables de Plantilla (sin prefijo)

```jinja2
{{ project_name }}
{{ environment }}
{{ namespace }}
{{ docker_registry }}
```

**Comportamiento:** 
- Se solicitan al usuario durante `gitlab-cicd create`
- Se sustituyen en los archivos `.gitlab-ci.yml` y manifiestos K8s
- Sus valores quedan "hard-coded" en el repositorio

### Variables CI/CD (prefijo `CICD_`)

```yaml
$CICD_DOCKER_TOKEN
$CICD_DATABASE_URL
$CICD_API_KEY
$CICD_K8S_CONTEXT
```

**Comportamiento:**
- Se detectan automáticamente por el prefijo `CICD_`
- Se solicitan al usuario con opciones de protected/masked
- Se guardan como variables CI/CD en GitLab
- **NO se sustituyen** en los archivos (quedan como `$CICD_*`)
- Disponibles en tiempo de ejecución del pipeline

## 🔧 Cambios en el Código

### 1. template_manager.py

**Nuevo método:**
```python
def extract_variables(templates: Dict[str, str]) -> Tuple[List[str], List[str]]:
    """
    Extrae y clasifica variables de las plantillas.
    Retorna (template_vars, cicd_vars)
    """
```

- Usa regex para detectar variables Jinja2
- Clasifica por prefijo `CICD_`
- Retorna dos listas separadas

### 2. k8s_generator.py

**Nuevo método:**
```python
def set_cicd_vars(cicd_vars: List[str]):
    """Establece lista de variables CI/CD"""
```

**Parámetro añadido:**
```python
def process_templates(templates, variables, preserve_cicd_vars=True):
    """
    Si preserve_cicd_vars=True, filtra variables CICD_ 
    para que NO se sustituyan
    """
```

### 3. cli.py (comando `create`)

**Flujo mejorado:**

1. Cargar plantillas desde GitLab
2. **Extraer y clasificar variables** ← NUEVO
3. Mostrar al usuario qué variables son de plantilla y cuáles CI/CD
4. Solicitar valores para variables de plantilla
5. **Solicitar valores y flags para variables CI/CD** ← NUEVO
6. Procesar plantillas (preservando CICD_*)
7. Crear archivos en repositorio
8. **Guardar variables CI/CD en GitLab** ← NUEVO

### 4. Tests Actualizados

- `test_extract_variables()` - Verifica clasificación
- `test_set_cicd_vars()` - Verifica configuración
- `test_process_templates_preserve_cicd_vars()` - Verifica preservación
- `test_config_is_configured()` - Actualizado para incluir template_repo
- `test_create_or_update_variable()` - Corregido para usar GitlabGetError

## 📚 Documentación Creada

### docs/VARIABLES.md (8.5 KB)

Documentación completa sobre:
- Tipos de variables y convenciones
- Flujo de trabajo completo
- Cuándo usar cada tipo
- Diferencia entre protected y masked
- Ejemplo completo paso a paso
- Guía de migración

### docs/TEMPLATE_EXAMPLE.md (5.2 KB)

Plantillas de ejemplo con:
- `.gitlab-ci.yml.j2` completo con ambos tipos de variables
- `deployment.yaml.j2` con configuración mixta
- `ingress.yaml.j2` usando dominio de variable CI/CD
- Lista de variables usadas
- Explicación del flujo

### README.md - Actualizado

- Nueva sección "Gestión de Variables"
- Explicación de ambos tipos
- Enlace a documentación detallada
- Ejemplos actualizados

### CHANGELOG.md - v0.3.0

- Documentación de todos los cambios
- Breaking changes (ninguno - retrocompatible)
- Nuevas características

## 🎬 Ejemplo de Uso

### Plantilla: `.gitlab-ci.yml.j2`

```yaml
stages:
  - build
  - deploy

build:
  script:
    - docker login -u $CI_REGISTRY_USER -p $CICD_DOCKER_TOKEN
    - docker build -t {{ docker_registry }}/{{ project_name }}:$CI_COMMIT_SHA .

deploy:
  script:
    - kubectl config use-context $CICD_K8S_CONTEXT
    - kubectl set image deployment/{{ project_name }} app=...
  environment:
    url: $CICD_APP_URL
```

### Ejecución:

```bash
$ gitlab-cicd create acme/web-app \
    --k8s-cluster prod-cluster \
    --namespace production \
    --environment prod

✓ Plantillas cargadas: 2 archivos

Analizando variables de las plantillas...
  • Variables de plantilla: docker_registry, project_name
  • Variables CI/CD (se guardarán en GitLab): CICD_APP_URL, CICD_DOCKER_TOKEN, CICD_K8S_CONTEXT

Información requerida para las plantillas:
docker_registry: registry.gitlab.com
project_name [web-app]: 

Valores para variables CI/CD:
Estas variables se guardarán en la configuración de GitLab

CICD_DOCKER_TOKEN: ghp_xxxxxxxxxxxx
  ¿Marcar CICD_DOCKER_TOKEN como protegida? [y/N]: y
  ¿Marcar CICD_DOCKER_TOKEN como enmascarada? [Y/n]: y

CICD_K8S_CONTEXT: arn:aws:eks:us-east-1:123:cluster/prod
  ¿Marcar CICD_K8S_CONTEXT como protegida? [y/N]: y
  ¿Marcar CICD_K8S_CONTEXT como enmascarada? [Y/n]: n

CICD_APP_URL: https://web-app.production.acme.com
  ¿Marcar CICD_APP_URL como protegida? [y/N]: n
  ¿Marcar CICD_APP_URL como enmascarada? [Y/n]: n

Generando archivos CI/CD...
✓ 2 archivos procesados
  ✓ .gitlab-ci.yml
  ✓ k8s/deployment.yaml

Configurando variables CI/CD en GitLab...
  ✓ CICD_DOCKER_TOKEN (protegida, enmascarada)
  ✓ CICD_K8S_CONTEXT (protegida)
  ✓ CICD_APP_URL

✓ CI/CD configurado exitosamente!

Puedes ver el pipeline en: https://gitlab.com/acme/web-app/-/pipelines
```

### Archivo Generado: `.gitlab-ci.yml`

```yaml
stages:
  - build
  - deploy

build:
  script:
    # Valores sustituidos ↓
    - docker login -u $CI_REGISTRY_USER -p $CICD_DOCKER_TOKEN
    - docker build -t registry.gitlab.com/web-app:$CI_COMMIT_SHA .
                       ^^^^^^^^^^^^^^^^^^^^^^^^
                       Variable de plantilla sustituida

deploy:
  script:
    - kubectl config use-context $CICD_K8S_CONTEXT
                                  ^^^^^^^^^^^^^^^^
                                  Variable CI/CD (NO sustituida)
    - kubectl set image deployment/web-app app=...
                                    ^^^^^^^
                                    Variable de plantilla sustituida
  environment:
    url: $CICD_APP_URL
         ^^^^^^^^^^^^^
         Variable CI/CD (NO sustituida)
```

## ✅ Tests

Todos los tests pasan:

```
================================================================= test session starts =================================================================
platform darwin -- Python 3.13.4, pytest-8.4.2, pluggy-1.6.0
collected 30 items

tests/test_cli.py .......                                       [ 23%]
tests/test_config.py .......                                    [ 46%]
tests/test_gitlab_client.py ....                                [ 60%]
tests/test_k8s_generator.py .......                             [ 83%]
tests/test_template_manager.py .....                            [100%]

================================================================= 30 passed in 0.32s ==================================================================
```

## 🔐 Beneficios de Seguridad

1. **Credenciales fuera del código**: Tokens y passwords nunca se escriben en el repositorio
2. **Variables enmascaradas**: Los valores sensibles no aparecen en logs
3. **Variables protegidas**: Solo disponibles en ramas/tags protegidos
4. **Flexibilidad**: Cambiar credenciales sin modificar código
5. **Auditoría**: GitLab registra cambios en variables CI/CD

## 🚀 Próximos Pasos

Para usar esta funcionalidad:

1. **Actualiza tus plantillas** para usar `CICD_` en variables sensibles
2. **Ejecuta `gitlab-cicd create`** en tus proyectos
3. **Verifica en GitLab** que las variables CI/CD se crearon correctamente
4. **Ejecuta un pipeline** para confirmar que todo funciona

## 📖 Referencias

- [docs/VARIABLES.md](docs/VARIABLES.md) - Documentación completa
- [docs/TEMPLATE_EXAMPLE.md](docs/TEMPLATE_EXAMPLE.md) - Ejemplos de plantillas
- [docs/TEMPLATE_REPO_SETUP.md](docs/TEMPLATE_REPO_SETUP.md) - Configurar repo de plantillas
- [GitLab CI/CD Variables](https://docs.gitlab.com/ee/ci/variables/)
- [Jinja2 Documentation](https://jinja.palletsprojects.com/)

---

**Versión:** 0.3.0  
**Fecha:** 5 de noviembre de 2025  
**Estado:** ✅ Implementado y Testeado
