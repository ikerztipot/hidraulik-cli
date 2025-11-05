#!/bin/bash
# Script de instalación rápida

set -e

echo "🚀 Instalando GitLab CI/CD Creator..."

# Verificar Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 no está instalado"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo "✓ Python $PYTHON_VERSION detectado"

# Crear entorno virtual
echo "📦 Creando entorno virtual..."
python3 -m venv venv

# Activar entorno virtual
source venv/bin/activate

# Actualizar pip
echo "📦 Actualizando pip..."
pip install --upgrade pip

# Instalar dependencias
echo "📦 Instalando dependencias..."
pip install -e .

echo ""
echo "✅ Instalación completada!"
echo ""
echo "Para usar el CLI:"
echo "  1. Activa el entorno virtual: source venv/bin/activate"
echo "  2. Inicializa la configuración: gitlab-cicd init"
echo "  3. Usa el CLI: gitlab-cicd --help"
echo ""
