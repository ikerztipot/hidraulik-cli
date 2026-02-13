"""
setup.py - Compatibilidad hacia atrás

Este proyecto usa pyproject.toml (PEP 517/518) para toda su configuración.
setup.py existe solo para compatibilidad con pip < 20.0 y herramientas legacy.

Configuración real: pyproject.toml
Documentación: README.md
"""
from setuptools import setup

if __name__ == "__main__":
    setup()
