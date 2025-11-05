# GitLab CI/CD Creator - Changelog

Todos los cambios notables en este proyecto serán documentados en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.0.0/),
y este proyecto adhiere a [Semantic Versioning](https://semver.org/lang/es/).

## [0.3.0] - 2025-11-05

### Añadido
- **Sistema de clasificación de variables**: Distinción automática entre variables de plantilla y variables CI/CD
- **Convención `CICD_` prefix**: Variables que empiezan con `CICD_` se guardan como variables CI/CD en GitLab
- Método `extract_variables()` en TemplateManager para detectar y clasificar variables
- Parámetro `preserve_cicd_vars` en `process_templates()` para preservar variables CI/CD sin sustituir
- Solicitud interactiva de flags protected/masked para cada variable CI/CD
- Nueva documentación completa: `docs/VARIABLES.md`
- Tests para la nueva funcionalidad de clasificación de variables
- Tests para verificar que variables CI/CD no se sustituyen en plantillas
- Método `set_cicd_vars()` en K8sGenerator

### Cambiado
- El comando `create` ahora analiza y clasifica variables automáticamente
- Variables con prefijo `CICD_` ya NO se sustituyen en archivos, se mantienen como `${{ CICD_* }}`
- Las variables CI/CD se guardan en la configuración de GitLab con sus flags configurados
- Proceso interactivo mejorado que muestra claramente qué variables son de plantilla y cuáles son CI/CD

### Mejorado
- Mejor separación de responsabilidades entre sustitución y almacenamiento de variables
- Experiencia de usuario más clara durante la configuración de variables
- Mayor seguridad al manejar credenciales y secretos
- Documentación extendida con ejemplos prácticos y casos de uso

## [0.2.0] - 2025-11-05

### Cambiado
- **BREAKING CHANGE**: El repositorio de plantillas ahora es **obligatorio**
- Las plantillas se cargan exclusivamente desde un repositorio GitLab central
- `template_repo` ahora es un campo obligatorio en la configuración
- Mejorada la validación durante `init` para verificar acceso al repositorio de plantillas
- El comando `list-templates` ahora carga plantillas directamente desde GitLab

### Eliminado
- **BREAKING CHANGE**: Eliminado directorio `templates/` local
- Ya no se soportan plantillas locales
- Las plantillas **deben** estar en un repositorio GitLab

### Añadido
- Verificación automática del repositorio de plantillas durante `init`
- Contador de plantillas encontradas en el repositorio
- Mensajes de progreso al cargar plantillas desde GitLab
- Nueva documentación: `docs/TEMPLATE_REPO_SETUP.md` con guía completa
- Validación de formato de ruta del repositorio (grupo/proyecto)
- Verificación de permisos de lectura en el repositorio

### Mejorado
- Mejor manejo de errores al acceder al repositorio de plantillas
- Mensajes más claros sobre requisitos del repositorio
- Feedback visual durante la carga de plantillas
- Documentación actualizada con énfasis en el repositorio obligatorio

## [0.1.0] - 2025-11-05

### Añadido
- Implementación inicial del CLI
- Comando `init` para configuración inicial
- Comando `create` para generar CI/CD en proyectos
- Comando `status` para ver estado de pipelines
- Comando `set-variable` para gestionar variables CI/CD
- Comando `list-templates` para listar plantillas disponibles
- Cliente para interactuar con GitLab API
- Gestor de plantillas con soporte para Jinja2
- Generador de configuraciones para Kubernetes
- Plantillas de ejemplo para:
  - `.gitlab-ci.yml`
  - Deployment de Kubernetes
  - Service de Kubernetes
  - Ingress de Kubernetes
  - Dockerfile
- Suite de tests unitarios
- Documentación completa en README
- Guía de uso detallada
- Guía de contribución

### Características
- Soporte para múltiples ambientes (dev, staging, prod)
- Integración completa con API de GitLab
- Gestión automática de variables CI/CD
- Plantillas personalizables desde repositorios GitLab
- Configuración persistente
- Interfaz de usuario rica con colores en terminal

[0.1.0]: https://github.com/ikerztipot/gitlab-repo-cicd-creator-cli/releases/tag/v0.1.0
