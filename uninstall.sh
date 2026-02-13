#!/bin/bash
# GitLab CI/CD Creator - Desinstalador
# Elimina el CLI y opcionalmente la configuración

set -e

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  🗑️  GitLab CI/CD Creator - Desinstalador"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

UNINSTALL_SUCCESS=false

if command -v pipx &> /dev/null; then
    # Instalado con pipx
    echo "📦 Desinstalando con pipx..."
    if pipx uninstall gitlab-cicd-creator 2>/dev/null; then
        UNINSTALL_SUCCESS=true
    fi
fi

# Intentar con pip si pipx falló o no está disponible
if [ "$UNINSTALL_SUCCESS" = false ]; then
    echo "📦 Desinstalando con pip..."
    if pip uninstall -y gitlab-cicd-creator 2>/dev/null || python3 -m pip uninstall -y gitlab-cicd-creator 2>/dev/null; then
        UNINSTALL_SUCCESS=true
    fi
fi

if [ "$UNINSTALL_SUCCESS" = true ]; then
    echo ""
    echo "✅ Paquete desinstalado correctamente"
else
    echo ""
    echo "⚠️  No se encontró gitlab-cicd-creator instalado"
fi

echo ""

# Preguntar si eliminar configuración
if [ -d ~/.gitlab-cicd-creator ]; then
    echo "Se encontró configuración en ~/.gitlab-cicd-creator"
    echo "Contiene:"
    echo "  • Configuración de GitLab (URL, plantillas)"
    echo "  • Tokens almacenados (keyring o fallback)"
    echo "  • Logs de ejecución"
    echo ""
    read -p "¿Eliminar configuración completa? (s/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Ss]$ ]]; then
        rm -rf ~/.gitlab-cicd-creator
        echo "✓ Configuración eliminada"
        
        # Limpiar token del keyring si existe
        if command -v python3 &> /dev/null; then
            python3 -c "import keyring; keyring.delete_password('gitlab-cicd-creator', 'gitlab_token')" 2>/dev/null || true
        fi
    else
        echo "✓ Configuración conservada"
    fi
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  ✅ Desinstalación completada"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "¡Hasta pronto! 👋"
echo ""
