# Guía de Contribución

¡Gracias por tu interés en contribuir a GitLab CI/CD Creator!

## Cómo Contribuir

### 1. Fork y Clonar

```bash
# Fork el repositorio en GitHub
# Luego clona tu fork
git clone https://github.com/TU-USUARIO/gitlab-repo-cicd-creator-cli.git
cd gitlab-repo-cicd-creator-cli
```

### 2. Configurar Entorno de Desarrollo

```bash
# Crear entorno virtual
python -m venv venv
source venv/bin/activate

# Instalar dependencias de desarrollo
pip install -e ".[dev]"

# O usar Make
make dev-setup
```

### 3. Crear Rama de Feature

```bash
git checkout -b feature/mi-nueva-feature
```

### 4. Hacer Cambios

- Escribe código limpio y bien documentado
- Sigue las convenciones de estilo de Python (PEP 8)
- Añade tests para nuevas funcionalidades
- Actualiza la documentación si es necesario

### 5. Ejecutar Tests

```bash
# Ejecutar tests
make test

# Con cobertura
make test-cov

# Linting
make lint

# Formatear código
make format
```

### 6. Commit

Usa mensajes de commit descriptivos siguiendo la convención:

```
tipo(ámbito): descripción breve

Descripción más detallada si es necesario.

Fixes #123
```

Tipos de commit:
- `feat`: Nueva funcionalidad
- `fix`: Corrección de bug
- `docs`: Cambios en documentación
- `style`: Cambios de formato
- `refactor`: Refactorización de código
- `test`: Añadir o modificar tests
- `chore`: Tareas de mantenimiento

### 7. Push y Pull Request

```bash
git push origin feature/mi-nueva-feature
```

Luego crea un Pull Request en GitHub con:
- Descripción clara de los cambios
- Referencias a issues relacionados
- Capturas de pantalla si aplica

## Estándares de Código

### Python Style Guide

Seguimos PEP 8 con algunas modificaciones:

- Longitud máxima de línea: 100 caracteres
- Usar black para formateo automático
- Usar isort para ordenar imports
- Usar type hints donde sea posible

### Ejemplo

```python
from typing import Dict, List, Optional

def procesar_plantilla(
    template: str,
    variables: Dict[str, str],
    strict: bool = True
) -> Optional[str]:
    """
    Procesa una plantilla con las variables proporcionadas.
    
    Args:
        template: Contenido de la plantilla
        variables: Diccionario de variables
        strict: Si se debe fallar en variables faltantes
        
    Returns:
        Plantilla procesada o None si hay error
        
    Raises:
        ValueError: Si strict=True y faltan variables
    """
    pass
```

## Testing

### Escribir Tests

- Un test por funcionalidad
- Usar fixtures de pytest
- Mockear dependencias externas
- Nombres descriptivos

Ejemplo:

```python
def test_gitlab_client_obtiene_proyecto():
    """Test que verifica que el cliente obtiene un proyecto correctamente"""
    client = GitLabClient('https://gitlab.com', 'token')
    project = client.get_project('grupo/proyecto')
    assert project['id'] is not None
```

### Ejecutar Tests

```bash
# Todos los tests
pytest

# Un archivo específico
pytest tests/test_gitlab_client.py

# Una función específica
pytest tests/test_gitlab_client.py::test_gitlab_client_obtiene_proyecto

# Con cobertura
pytest --cov=gitlab_cicd_creator --cov-report=html
```

## Documentación

### Docstrings

Usa docstrings estilo Google:

```python
def funcion(param1: str, param2: int) -> bool:
    """
    Descripción breve de la función.
    
    Descripción más detallada si es necesario.
    
    Args:
        param1: Descripción del primer parámetro
        param2: Descripción del segundo parámetro
        
    Returns:
        Descripción del valor de retorno
        
    Raises:
        ValueError: Cuándo se lanza esta excepción
        
    Example:
        >>> funcion("test", 42)
        True
    """
    pass
```

### README y Docs

- Actualiza README.md si cambias funcionalidad pública
- Añade ejemplos de uso
- Mantén la documentación sincronizada con el código

## Proceso de Review

### Checklist antes de PR

- [ ] Tests pasan localmente
- [ ] Código formateado con black
- [ ] Sin errores de linting
- [ ] Documentación actualizada
- [ ] Commits con mensajes descriptivos
- [ ] Branch actualizado con main

### Durante el Review

- Responde a comentarios de manera constructiva
- Haz cambios solicitados
- Mantén la conversación profesional

## Reportar Bugs

### Antes de Reportar

1. Busca si el bug ya fue reportado
2. Intenta reproducir en la última versión
3. Recopila información relevante

### Crear Issue

Incluye:
- **Descripción**: Qué esperabas vs qué pasó
- **Steps to Reproduce**: Pasos para reproducir
- **Environment**: Sistema operativo, versión de Python, etc.
- **Logs**: Mensajes de error relevantes

Ejemplo:

```markdown
## Descripción
El comando `gitlab-cicd create` falla al intentar crear un proyecto nuevo.

## Pasos para Reproducir
1. Ejecutar `gitlab-cicd init` con credenciales válidas
2. Ejecutar `gitlab-cicd create test/nuevo --create-project`
3. Ver error

## Ambiente
- OS: macOS 14.0
- Python: 3.11.5
- gitlab-cicd-creator: 0.1.0

## Error
\`\`\`
Error: Project creation failed: 404 Not Found
\`\`\`
```

## Sugerir Features

### Template de Feature Request

```markdown
## Problema que Resuelve
Descripción del problema o necesidad

## Solución Propuesta
Cómo podría implementarse

## Alternativas Consideradas
Otras formas de resolver el problema

## Información Adicional
Contexto adicional, ejemplos, etc.
```

## Preguntas

Si tienes preguntas:
- Abre un issue con la etiqueta `question`
- Contacta a los maintainers
- Revisa discusiones previas

¡Gracias por contribuir! 🎉
