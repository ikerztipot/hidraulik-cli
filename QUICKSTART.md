# Inicio Rápido - GitLab CI/CD Creator

## Instalación en 3 Pasos

### 1. Instalar
```bash
./install.sh
# o manualmente:
python -m venv venv
source venv/bin/activate
pip install -e .
```

### 2. Configurar
```bash
source venv/bin/activate
gitlab-cicd init
```

Proporciona:
- URL de GitLab (ej: `https://gitlab.com`)
- Token de acceso personal (créalo en GitLab → Settings → Access Tokens)
- **Repositorio de plantillas** (ej: `grupo/plantillas-cicd`) - **OBLIGATORIO**

⚠️ **Importante**: Debes tener un repositorio en GitLab con las plantillas antes de continuar.

### 3. Usar
```bash
# Crear CI/CD para un proyecto
gitlab-cicd create mi-grupo/mi-proyecto \
  --k8s-cluster mi-cluster \
  --namespace mi-app-prod \
  --environment prod

# Ver estado
gitlab-cicd status mi-grupo/mi-proyecto

# Configurar variable
gitlab-cicd set-variable mi-grupo/mi-proyecto \
  DATABASE_URL "postgresql://..." \
  --masked
```

## Ejemplos Prácticos

### Ejemplo 1: App Python en Desarrollo
```bash
gitlab-cicd create acme/api-python \
  --k8s-cluster dev-cluster \
  --namespace acme-dev \
  --environment dev \
  --create-project
```

### Ejemplo 2: App Node.js en Staging
```bash
gitlab-cicd create acme/frontend-react \
  --k8s-cluster staging-cluster \
  --namespace acme-staging \
  --environment staging
```

### Ejemplo 3: Microservicio en Producción
```bash
gitlab-cicd create acme/users-service \
  --k8s-cluster prod-cluster \
  --namespace acme-prod \
  --environment prod

# Configurar variables sensibles
gitlab-cicd set-variable acme/users-service JWT_SECRET "secret123" --masked --protected
gitlab-cicd set-variable acme/users-service DB_PASSWORD "pass123" --masked --protected
```

## Comandos Útiles

```bash
# Ver todos los comandos
gitlab-cicd --help

# Ayuda de un comando específico
gitlab-cicd create --help

# Listar plantillas disponibles
gitlab-cicd list-templates

# Ver versión
gitlab-cicd --version
```

## Siguiente Paso

Lee la [Guía de Uso Completa](docs/USAGE.md) para casos de uso avanzados.

## Solución Rápida de Problemas

**Error de autenticación**: Verifica tu token en GitLab → Settings → Access Tokens

**Proyecto no encontrado**: Usa `--create-project` para crear el proyecto

**Pipeline no se ejecuta**: Verifica que haya un commit en la rama `main`

Para más ayuda, consulta [USAGE.md](docs/USAGE.md) o abre un issue.
