# Guía de Contribución

¡Gracias por tu interés en contribuir a GitLab CI/CD Creator!

## Proceso de Contribución

1. **Fork** el repositorio
2. **Clona** tu fork: `git clone https://github.com/TU-USUARIO/gitlab-repo-cicd-creator-cli.git`
3. **Crea una rama**: `git checkout -b feature/mi-feature`
4. **Haz cambios** siguiendo las guías de estilo
5. **Ejecuta tests**: `make test`
6. **Commit**: `git commit -m 'Add: mi feature'`
7. **Push**: `git push origin feature/mi-feature`
8. **Abre un Pull Request**

## Configuración de Desarrollo

```bash
# Entorno virtual
python -m venv venv
source venv/bin/activate

# Instalar en modo desarrollo
pip install -e ".[dev]"
```

## Estándares de Código

### Python
- **Estilo**: PEP 8
- **Longitud de línea**: 100 caracteres
- **Formateador**: Black
- **Imports**: isort
- **Type hints**: Requeridos

### Formateo

```bash
make format  # black + isort
make lint    # flake8 + mypy
```

## Tests

```bash
make test          # Ejecutar tests
make test-cov      # Con cobertura
```

### Escribir Tests
- Usa `pytest` y `click.testing.CliRunner`
- Mock las llamadas a GitLab API
- Cobertura mínima: 80%

## Estructura de Commits

```
<tipo>: <descripción corta>

<descripción detallada opcional>
```

**Tipos:**
- `Add:` Nueva funcionalidad
- `Fix:` Corrección de bugs
- `Docs:` Cambios en documentación
- `Style:` Formateo, sin cambios en lógica
- `Refactor:` Refactorización de código
- `Test:` Añadir o modificar tests

**Ejemplo:**
```
Add: soporte para remote includes dinámicos

- Añadida variable template_repo a variables automáticas
- Actualizada documentación con ejemplos
- Tests añadidos para nueva funcionalidad
```

## Reportar Issues

Al reportar un bug, incluye:
- Versión de Python
- Comando ejecutado
- Output completo del error
- Pasos para reproducir

## Preguntas

Si tienes preguntas, abre un issue con la etiqueta `question`.
