#!/bin/bash
# GitLab CI/CD Creator - Script de Verificación
# Valida que la instalación funcione correctamente

set -e

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  🔍 GitLab CI/CD Creator - Verificación"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Colores
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

success() {
    echo -e "${GREEN}✓${NC} $1"
}

error() {
    echo -e "${RED}✗${NC} $1"
}

warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# 1. Verificar Python
echo "1. Verificando Python..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
    PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)
    
    if [ "$PYTHON_MAJOR" -ge 3 ] && [ "$PYTHON_MINOR" -ge 8 ]; then
        success "Python $PYTHON_VERSION (>= 3.8 requerido)"
    else
        error "Python $PYTHON_VERSION (se requiere >= 3.8)"
        exit 1
    fi
else
    error "Python 3 no instalado"
    exit 1
fi

# 2. Verificar comando gitlab-cicd
echo ""
echo "2. Verificando comando gitlab-cicd..."
if command -v gitlab-cicd &> /dev/null; then
    success "Comando 'gitlab-cicd' disponible"
    CLI_VERSION=$(gitlab-cicd --version 2>&1 || echo "unknown")
    echo "   Versión: $CLI_VERSION"
else
    error "Comando 'gitlab-cicd' no encontrado"
    echo ""
    echo "   Solución:"
    echo "   1. Ejecuta: ./install.sh"
    echo "   2. Si ya instalaste, cierra y abre tu terminal"
    echo "   3. Verifica que la ruta esté en PATH"
    exit 1
fi

# 3. Verificar módulos Python
echo ""
echo "3. Verificando dependencias Python..."
MODULES=("gitlab" "click" "jinja2" "rich" "keyring")
MISSING_MODULES=()

for module in "${MODULES[@]}"; do
    if python3 -c "import $module" 2>/dev/null; then
        success "$module instalado"
    else
        error "$module NO instalado"
        MISSING_MODULES+=("$module")
    fi
done

if [ ${#MISSING_MODULES[@]} -ne 0 ]; then
    echo ""
    error "Faltan módulos: ${MISSING_MODULES[*]}"
    echo "   Ejecuta: pip install ${MISSING_MODULES[*]}"
    exit 1
fi

# 4. Verificar keyring (para almacenamiento seguro)
echo ""
echo "4. Verificando almacenamiento seguro (keyring)..."
if python3 -c "import keyring; keyring.get_keyring()" &>/dev/null; then
    KEYRING_BACKEND=$(python3 -c "import keyring; print(keyring.get_keyring().__class__.__name__)")
    success "Keyring disponible: $KEYRING_BACKEND"
else
    warning "Keyring no disponible (se usará fallback seguro)"
    echo "   Opcional: Instala soporte para tu sistema"
    
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        echo "   • Ubuntu/Debian: sudo apt install python3-dbus"
        echo "   • Fedora/RHEL:   sudo dnf install python3-dbus"
    fi
fi

# 5. Verificar estructura de directorios
echo ""
echo "5. Verificando estructura del proyecto..."
REQUIRED_FILES=(
    "src/gitlab_cicd_creator/__init__.py"
    "src/gitlab_cicd_creator/cli.py"
    "src/gitlab_cicd_creator/config.py"
    "src/gitlab_cicd_creator/gitlab_client.py"
    "src/gitlab_cicd_creator/exceptions.py"
    "src/gitlab_cicd_creator/validators.py"
    "src/gitlab_cicd_creator/services/variable_service.py"
    "pyproject.toml"
    "README.md"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$file" ]; then
        success "$file"
    else
        error "$file NO ENCONTRADO"
    fi
done

# 6. Verificar configuración (si existe)
echo ""
echo "6. Verificando configuración..."
CONFIG_DIR="$HOME/.gitlab-cicd-creator"
if [ -d "$CONFIG_DIR" ]; then
    success "Directorio de configuración existe: $CONFIG_DIR"
    
    if [ -f "$CONFIG_DIR/config.json" ]; then
        success "config.json encontrado"
        
        # Verificar campos requeridos
        if command -v jq &> /dev/null; then
            GITLAB_URL=$(jq -r '.gitlab_url // empty' "$CONFIG_DIR/config.json" 2>/dev/null)
            TEMPLATE_REPO=$(jq -r '.template_repo // empty' "$CONFIG_DIR/config.json" 2>/dev/null)
            
            if [ -n "$GITLAB_URL" ]; then
                success "gitlab_url configurado: $GITLAB_URL"
            else
                warning "gitlab_url no configurado"
            fi
            
            if [ -n "$TEMPLATE_REPO" ]; then
                success "template_repo configurado: $TEMPLATE_REPO"
            else
                warning "template_repo no configurado"
            fi
        fi
    else
        warning "config.json no encontrado (ejecuta 'gitlab-cicd init')"
    fi
    
    # Verificar token
    TOKEN_EXISTS=false
    if python3 -c "import keyring; keyring.get_password('gitlab-cicd-creator', 'gitlab_token')" &>/dev/null 2>&1; then
        success "Token almacenado en keyring (seguro)"
        TOKEN_EXISTS=true
    elif [ -f "$CONFIG_DIR/.token" ]; then
        success "Token en fallback file (permisos: $(stat -f '%Lp' "$CONFIG_DIR/.token" 2>/dev/null || stat -c '%a' "$CONFIG_DIR/.token" 2>/dev/null))"
        TOKEN_EXISTS=true
    else
        warning "Token no configurado (ejecuta 'gitlab-cicd init')"
    fi
    
    # Verificar logs
    if [ -d "$CONFIG_DIR/logs" ]; then
        LOG_COUNT=$(ls -1 "$CONFIG_DIR/logs"/*.log 2>/dev/null | wc -l)
        if [ $LOG_COUNT -gt 0 ]; then
            success "Logs: $LOG_COUNT archivo(s)"
        fi
    fi
else
    warning "Directorio de configuración no existe"
    echo "   Primera vez: Ejecuta 'gitlab-cicd init'"
fi

# 7. Test de funcionalidad básica
echo ""
echo "7. Probando comandos básicos..."

# Test --help
if gitlab-cicd --help &>/dev/null; then
    success "gitlab-cicd --help funciona"
else
    error "gitlab-cicd --help falla"
fi

# Test comandos disponibles
COMMANDS=("init" "create" "status" "set-variable" "list-templates")
for cmd in "${COMMANDS[@]}"; do
    if gitlab-cicd $cmd --help &>/dev/null; then
        success "gitlab-cicd $cmd disponible"
    else
        error "gitlab-cicd $cmd NO disponible"
    fi
done

# 8. Verificar tests (si estamos en desarrollo)
echo ""
echo "8. Verificando entorno de desarrollo (opcional)..."
if [ -d "tests" ]; then
    success "Directorio tests/ encontrado"
    
    if command -v pytest &> /dev/null; then
        success "pytest instalado"
        
        # Contar tests
        TEST_COUNT=$(find tests -name "test_*.py" | wc -l)
        success "$TEST_COUNT archivo(s) de test"
    else
        warning "pytest no instalado (solo necesario para desarrollo)"
        echo "   Instala con: pip install -e \".[dev]\""
    fi
else
    warning "tests/ no encontrado (normal si se instaló desde pip/pipx)"
fi

# 9. Resumen final
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  📋 Resumen de Verificación"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

ISSUES=false

if ! command -v gitlab-cicd &> /dev/null; then
    error "CLI no instalado correctamente"
    ISSUES=true
fi

if [ ${#MISSING_MODULES[@]} -ne 0 ]; then
    error "Faltan dependencias Python"
    ISSUES=true
fi

if [ ! -d "$CONFIG_DIR" ] || [ ! -f "$CONFIG_DIR/config.json" ]; then
    warning "Configuración pendiente (ejecuta 'gitlab-cicd init')"
fi

if [ "$ISSUES" = true ]; then
    echo ""
    error "Se encontraron problemas. Revisa los errores arriba."
    echo ""
    echo "Para reinstalar:"
    echo "  ./uninstall.sh"
    echo "  ./install.sh"
    exit 1
else
    echo ""
    success "¡Verificación completada!"
    echo ""
    echo "Próximos pasos:"
    echo "  1️⃣  gitlab-cicd init         # Configurar credenciales (si no lo has hecho)"
    echo "  2️⃣  gitlab-cicd --help       # Ver todos los comandos"
    echo "  3️⃣  gitlab-cicd create --help # Ver opciones de creación"
    echo ""
    echo "Documentación completa: README.md"
    echo ""
fi
