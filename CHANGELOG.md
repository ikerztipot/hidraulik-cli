# Hidraulik - Changelog

Todos los cambios notables en este proyecto serán documentados en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.0.0/),
y este proyecto adhiere a [Semantic Versioning](https://semver.org/lang/es/).

## [Unreleased]

### Añadido
- **Configuración de Docker por componente**: Ahora el CLI pregunta si el proyecto usa Docker
- **Rutas de Dockerfile personalizadas**: Permite especificar la ruta del Dockerfile para cada componente
- Nueva variable de plantilla `use_docker` (booleana) que indica si el proyecto usa Docker
- Nueva variable de plantilla `dockerfile_paths` (diccionario) con rutas de Dockerfile por componente
- Prompt interactivo para configurar Dockerfile path por cada componente con valores por defecto inteligentes
  - Un componente: default `Dockerfile`
  - Múltiples componentes: default `{component}/Dockerfile`

### Mejorado
- **Mensajes de error mejorados**: Ahora los errores de autenticación y otros errores comunes muestran mensajes claros con soluciones paso a paso en lugar de tracebacks técnicos
- Documentación actualizada en README con las nuevas variables `use_docker` y `dockerfile_paths`
- Ejemplos de plantillas actualizados para mostrar el uso condicional de `DOCKERFILE_PATH`
- Flujo interactivo mejorado con preguntas sobre Docker antes de la selección de runners

### Corregido
- **Extensión .j2 en archivos generados**: Ahora los archivos procesados se guardan con su extensión correcta (`.gitlab-ci.yml` en lugar de `.gitlab-ci.yml.j2`)
- Los archivos de plantilla del repositorio remoto ahora se mapean correctamente a sus rutas de destino sin la extensión `.j2`
- **Error 409 al crear variables con múltiples scopes**: Mejorado el manejo de variables CI/CD cuando existen múltiples variables con el mismo nombre pero diferentes `environment_scope`. Ahora busca y actualiza correctamente la variable específica por scope.

## [0.4.0] - 2026-02-10

### Añadido
- **Detección automática de runners de GitLab**: Obtiene tags de runners disponibles desde la instancia
- Método `get_available_runners()` en GitLabClient para obtener runners de la instancia
- Método `get_group_runners()` para obtener runners de grupos específicos
- Método `get_project_runners()` para obtener runners de proyectos
- Función helper `get_available_runner_tags()` que recopila todos los tags de runners disponibles
- **Selección interactiva de runner tags** con múltiples métodos:
  - Por números (ej: `1,3,5`)
  - Por nombres (ej: `buildkit,scaleway,worko-internal`)
  - Usando valores sugeridos por defecto
- Función `select_runner_tags_interactive()` con interfaz visual mejorada
- Nueva variable de plantilla `components` para proyectos multi-componente (web, cms, api, etc.)
- Nueva variable `tag_prefix` para prefijos de tags de release (wkhs, acme, etc.)
- Plantilla `.gitlab-ci.yml.j2` multi-componente dinámica con loops Jinja2
- Include remoto `.build-buildkit-scaleway.yml` para builds con BuildKit
- Documentación completa en `docs/TEMPLATE_REPO_STRUCTURE.md`
- Documentación de ejemplo interactivo en `docs/INTERACTIVE_EXAMPLE.md`
- Tests unitarios para funciones de runners
- Archivo de ejemplo `examples/includes/.build-buildkit-scaleway.yml`
- Archivo de ejemplo `examples/.gitlab-ci.yml.example` con pipeline completo

### Cambiado
- El comando `create` ahora solicita componentes a desplegar de forma interactiva
- La selección de runner tags es visual e interactiva (no manual)
- Las variables `runner_tags` se obtienen dinámicamente de GitLab (no hardcodeadas)
- Feedback visual mejorado durante `init` con mensajes de progreso
- Búsqueda de proyectos similares ahora es opcional y limitada (optimización de performance)

### Mejorado
- Mensajes de progreso claros durante `init`: "Conectando...", "Verificando...", etc.
- Mejor manejo de errores con sugerencias contextuales
- Experiencia de usuario más fluida con selección visual de opciones
- Mayor flexibilidad para arquitecturas multi-componente
- Documentación expandida con ejemplos reales de uso

### Técnico
- Separación de lógica de obtención de runners en funciones reutilizables
- Manejo robusto de fallos de permisos al obtener runners
- Soporte para runners a nivel de instancia, grupo y proyecto
- Agregación automática de tags únicos desde múltiples fuentes

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

[0.1.0]: https://github.com/ikerztipot/hidraulik-cli/releases/tag/v0.1.0
