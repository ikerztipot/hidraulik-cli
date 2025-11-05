#!/bin/bash

# Script de verificación del setup del proyecto
# Ejecuta: chmod +x verify_setup.sh && ./verify_setup.sh

echo "🔍 Verificando el setup del proyecto GitLab CI/CD Creator..."
echo ""

# Colores
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Contadores
errors=0
warnings=0

# Función para verificar
check() {
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓${NC} $1"
    else
        echo -e "${RED}✗${NC} $1"
        ((errors++))
    fi
}

check_warning() {
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓${NC} $1"
    else
        echo -e "${YELLOW}⚠${NC} $1"
        ((warnings++))
    fi
}

echo "📦 Verificando archivos de configuración..."

# Verificar archivos principales
[ -f "pyproject.toml" ]; check "pyproject.toml existe"
[ -f "setup.py" ]; check "setup.py existe"
[ -f "requirements.txt" ]; check "requirements.txt existe"
[ -f "requirements-dev.txt" ]; check "requirements-dev.txt existe"
[ -f "README.md" ]; check "README.md existe"
[ -f "LICENSE" ]; check "LICENSE existe"
[ -f ".gitignore" ]; check ".gitignore existe"
[ -f "Makefile" ]; check "Makefile existe"

echo ""
echo "📁 Verificando estructura de directorios..."

[ -d "src/gitlab_cicd_creator" ]; check "Directorio src/gitlab_cicd_creator existe"
[ -d "tests" ]; check "Directorio tests existe"
[ -d "docs" ]; check "Directorio docs existe"

echo ""
echo "🐍 Verificando módulos Python..."

[ -f "src/gitlab_cicd_creator/__init__.py" ]; check "__init__.py existe"
[ -f "src/gitlab_cicd_creator/cli.py" ]; check "cli.py existe"
[ -f "src/gitlab_cicd_creator/gitlab_client.py" ]; check "gitlab_client.py existe"
[ -f "src/gitlab_cicd_creator/template_manager.py" ]; check "template_manager.py existe"
[ -f "src/gitlab_cicd_creator/k8s_generator.py" ]; check "k8s_generator.py existe"
[ -f "src/gitlab_cicd_creator/config.py" ]; check "config.py existe"

echo ""
echo "🧪 Verificando tests..."

[ -f "tests/__init__.py" ]; check "tests/__init__.py existe"
[ -f "tests/test_cli.py" ]; check "test_cli.py existe"
[ -f "tests/test_gitlab_client.py" ]; check "test_gitlab_client.py existe"
[ -f "tests/test_template_manager.py" ]; check "test_template_manager.py existe"
[ -f "tests/test_k8s_generator.py" ]; check "test_k8s_generator.py existe"
[ -f "tests/test_config.py" ]; check "test_config.py existe"

echo ""
echo "📄 Verificando documentación de plantillas..."

[ -f "docs/TEMPLATE_REPO_SETUP.md" ]; check "Guía TEMPLATE_REPO_SETUP.md existe"
echo "  ℹ️  Las plantillas se cargan desde tu repositorio GitLab"
echo "  ℹ️  Ver docs/TEMPLATE_REPO_SETUP.md para configurar el repositorio"

echo ""
echo "📚 Verificando documentación..."

[ -f "README.md" ]; check "README.md existe"
[ -f "QUICKSTART.md" ]; check "QUICKSTART.md existe"
[ -f "NEXT_STEPS.md" ]; check "NEXT_STEPS.md existe"
[ -f "PROJECT_SUMMARY.md" ]; check "PROJECT_SUMMARY.md existe"
[ -f "CHANGELOG.md" ]; check "CHANGELOG.md existe"
[ -f "docs/USAGE.md" ]; check "docs/USAGE.md existe"
[ -f "docs/CONTRIBUTING.md" ]; check "docs/CONTRIBUTING.md existe"

echo ""
echo "🔧 Verificando herramientas..."

[ -f "install.sh" ]; check "install.sh existe"
[ -x "install.sh" ]; check "install.sh es ejecutable"
[ -f "pytest.ini" ]; check "pytest.ini existe"
[ -f ".flake8" ]; check ".flake8 existe"

echo ""
echo "🖥️  Verificando configuración de VSCode..."

[ -f ".vscode/settings.json" ]; check_warning ".vscode/settings.json existe"
[ -f ".vscode/launch.json" ]; check_warning ".vscode/launch.json existe"
[ -f ".vscode/extensions.json" ]; check_warning ".vscode/extensions.json existe"

echo ""
echo "🐍 Verificando Python..."

if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo -e "${GREEN}✓${NC} Python instalado: $PYTHON_VERSION"
else
    echo -e "${RED}✗${NC} Python 3 no encontrado"
    ((errors++))
fi

echo ""
echo "📊 Conteo de líneas de código..."

if command -v wc &> /dev/null; then
    PYTHON_LINES=$(find src tests -name '*.py' 2>/dev/null | xargs wc -l 2>/dev/null | tail -1 | awk '{print $1}')
    if [ ! -z "$PYTHON_LINES" ]; then
        echo -e "${GREEN}✓${NC} Líneas de código Python: $PYTHON_LINES"
    fi
fi

MODULE_COUNT=$(find src/gitlab_cicd_creator -name '*.py' -not -name '__init__.py' 2>/dev/null | wc -l | tr -d ' ')
echo -e "${GREEN}✓${NC} Módulos principales: $MODULE_COUNT"

TEST_COUNT=$(find tests -name 'test_*.py' 2>/dev/null | wc -l | tr -d ' ')
echo -e "${GREEN}✓${NC} Archivos de test: $TEST_COUNT"

DOC_COUNT=$(find docs -name '*.md' 2>/dev/null | wc -l | tr -d ' ')
echo -e "${GREEN}✓${NC} Documentos: $DOC_COUNT"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ $errors -eq 0 ]; then
    echo -e "${GREEN}✅ Setup completado exitosamente!${NC}"
    echo ""
    echo "Próximos pasos:"
    echo "  1. ./install.sh"
    echo "  2. source venv/bin/activate"
    echo "  3. gitlab-cicd init"
    echo ""
    echo "Para más información, lee:"
    echo "  - QUICKSTART.md (inicio rápido)"
    echo "  - NEXT_STEPS.md (próximos pasos)"
    echo "  - docs/USAGE.md (guía completa)"
else
    echo -e "${RED}❌ Se encontraron $errors errores${NC}"
    exit 1
fi

if [ $warnings -gt 0 ]; then
    echo -e "${YELLOW}⚠️  $warnings advertencias (no críticas)${NC}"
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
