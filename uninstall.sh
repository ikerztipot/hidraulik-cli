#!/bin/bash
# Desinstalador de GitLab CI/CD Creator

set -e

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  🗑️  GitLab CI/CD Creator - Desinstalador"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if command -v pipx &> /dev/null; then
    # Instalado con pipx
    echo "📦 Desinstalando gitlab-cicd-creator..."
    pipx uninstall gitlab-cicd-creator || true
    
    echo ""
    echo "✅ Desinstalación completada"
    echo ""
else
    # Instalado con pip
    echo "📦 Desinstalando gitlab-cicd-creator..."
    pip uninstall -y gitlab-cicd-creator 2>/dev/null || true
    python3 -m pip uninstall -y gitlab-cicd-creator 2>/dev/null || true
    
    echo ""
    echo "✅ Desinstalación completada"
    echo ""
fi

# Preguntar si eliminar configuración
read -p "¿Deseas eliminar la configuración guardada? (s/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Ss]$ ]]; then
    rm -rf ~/.gitlab-cicd-creator
    echo "✓ Configuración eliminada"
fi

echo ""
echo "¡Hasta pronto! 👋"
echo ""
