#!/bin/bash
# Script d'installation de WeasyPrint pour GabomaZone

echo "Installation de WeasyPrint pour la génération de PDFs..."

# Activer l'environnement virtuel si disponible
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
    echo "Environnement virtuel activé"
elif [ -f ".venv/Scripts/activate" ]; then
    source .venv/Scripts/activate
    echo "Environnement virtuel activé (Windows)"
fi

# Installer WeasyPrint
echo "Installation de WeasyPrint..."
pip install weasyprint

# Vérifier l'installation
echo "Vérification de l'installation..."
python -c "import weasyprint; print('✓ WeasyPrint installé avec succès! Version:', weasyprint.__version__)" 2>&1

if [ $? -eq 0 ]; then
    echo ""
    echo "✓ Installation réussie!"
    echo "Vous pouvez maintenant générer des PDFs depuis les factures."
else
    echo ""
    echo "✗ Erreur lors de l'installation."
    echo ""
    echo "Sur Linux/WSL, vous devrez peut-être installer les dépendances système :"
    echo "  sudo apt-get update"
    echo "  sudo apt-get install -y python3-dev python3-pip python3-setuptools python3-wheel python3-cffi libcairo2 libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf2.0-0 libffi-dev shared-mime-info"
    echo ""
    echo "Sur Windows, utilisez l'installeur Windows de WeasyPrint ou installez GTK+."
fi

