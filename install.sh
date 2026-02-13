#!/bin/bash
# GitLab CI/CD Creator - Instalador
# Detecta automáticamente el entorno e instala correctamente

set -e

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  🚀 GitLab CI/CD Creator - Instalador"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Verificar Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 no está instalado"
    echo ""
    echo "Instala Python 3.8 o superior:"
    echo "  • macOS:        brew install python3"
    echo "  • Ubuntu/Debian: sudo apt install python3 python3-pip python3-venv"
    echo "  • Fedora/RHEL:  sudo dnf install python3 python3-pip"
    echo ""
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo "✓ Python $PYTHON_VERSION detectado"

# Instalar dependencia de sistema para keyring (almacenamiento seguro)
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo ""
    echo "📦 Verificando dependencias del sistema (keyring)..."
    if ! dpkg -s python3-dbus &> /dev/null 2>&1 && ! rpm -q python3-dbus &> /dev/null 2>&1; then
        echo "⚠️  Recomendado: Instalar python3-dbus para almacenamiento seguro de tokens"
        echo "   Ubuntu/Debian: sudo apt install python3-dbus"
        echo "   Fedora/RHEL:   sudo dnf install python3-dbus"
        echo ""
    fi
fi

# Detectar e instalar con pipx (recomendado)
if command -v pipx &> /dev/null; then
    echo "✓ pipx detectado"
    echo ""
    echo "📦 Instalando gitlab-cicd con pipx..."
    pipx install . --force
    
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  ✅ ¡Instalación completada!"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "El comando 'gitlab-cicd' está disponible globalmente."
    echo ""
    echo "Próximos pasos:"
    echo "  1️⃣  gitlab-cicd init         # Configurar credenciales"
    echo "  2️⃣  gitlab-cicd --help       # Ver todos los comandos"
    echo "  3️⃣  gitlab-cicd create --help # Ver opciones de creación"
    echo ""
    
else
    # pipx no disponible, usar pip install --user
    echo ""
    echo "⚙️  pipx no detectado. Usando instalación con pip..."
    echo "   💡 Tip: Instala pipx para mejor gestión: python3 -m pip install --user pipx"
    echo ""
    echo "📦 Instalando gitlab-cicd..."
    
    # Detectar si estamos en un virtualenv
    if [[ -n "$VIRTUAL_ENV" ]]; then
        # Dentro de virtualenv: instalar sin --user
        echo "   (virtualenv detectado: $VIRTUAL_ENV)"
        python3 -m pip install . --quiet
    else
        # Fuera de virtualenv: instalar con --user para evitar conflictos con el sistema
        # --break-system-packages es seguro cuando se combina con --user
        python3 -m pip install --user --break-system-packages . --quiet
    fi
    
    # Detectar ruta de instalación
    USER_BIN=""
    if [[ -n "$VIRTUAL_ENV" ]]; then
        # Dentro de virtualenv: el binario está en $VIRTUAL_ENV/bin
        USER_BIN="$VIRTUAL_ENV/bin"
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS (fuera de virtualenv)
        USER_BIN="$HOME/Library/Python/$PYTHON_VERSION/bin"
    else
        # Linux (fuera de virtualenv)
        USER_BIN="$HOME/.local/bin"
    fi
    
    # Verificar si la ruta está en PATH
    if [[ ":$PATH:" != *":$USER_BIN:"* ]]; then
        echo ""
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "  ✅ ¡Instalación completada!"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo ""
        echo "⚠️  CONFIGURACIÓN NECESARIA:"
        echo ""
        echo "Añade esta línea a tu ~/.zshrc (o ~/.bashrc):"
        echo ""
        echo "  export PATH=\"$USER_BIN:\$PATH\""
        echo ""
        echo "Luego ejecuta:"
        echo ""
        echo "  source ~/.zshrc"
        echo ""
        echo "O cierra y abre tu terminal."
        echo ""
        echo "Después podrás usar:"
        echo "  gitlab-cicd init"
        echo "  gitlab-cicd --help"
        echo ""
        
        # Intentar añadir automáticamente
        read -p "¿Deseas que añada la ruta automáticamente a ~/.zshrc? (s/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Ss]$ ]]; then
            echo "" >> ~/.zshrc
            echo "# GitLab CI/CD Creator" >> ~/.zshrc
            echo "export PATH=\"$USER_BIN:\$PATH\"" >> ~/.zshrc
            echo ""
            echo "✓ Añadido a ~/.zshrc"
            echo ""
            echo "Ejecuta: source ~/.zshrc"
            echo "O cierra y abre tu terminal."
            echo ""
        fi
    else
        echo ""
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "  ✅ ¡Instalación completada!"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo ""
        echo "El comando 'gitlab-cicd' está disponible."
        echo ""
        echo "Próximos pasos:"
        echo "  1️⃣  gitlab-cicd init      # Configurar credenciales"
        echo "  2️⃣  gitlab-cicd --help    # Ver comandos disponibles"
        echo ""
    fi
fi
