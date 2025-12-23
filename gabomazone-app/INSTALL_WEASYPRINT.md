# Installation de WeasyPrint pour la génération de PDFs

WeasyPrint permet de générer des PDFs à partir des factures HTML.

## Installation sur Linux/WSL (Ubuntu/Debian)

### 1. Installer les dépendances système

```bash
sudo apt-get update
sudo apt-get install -y \
    python3-dev \
    python3-pip \
    python3-setuptools \
    python3-wheel \
    python3-cffi \
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 \
    libffi-dev \
    shared-mime-info
```

### 2. Installer WeasyPrint dans l'environnement virtuel

```bash
cd gabomazone-app
source .venv/bin/activate  # ou .venv/Scripts/activate sur Windows
pip install weasyprint
```

### 3. Vérifier l'installation

```bash
python -c "import weasyprint; print('WeasyPrint installé! Version:', weasyprint.__version__)"
```

## Installation sur Windows

### Option 1 : Utiliser l'installeur Windows

1. Télécharger GTK+ pour Windows depuis : https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer
2. Installer GTK+
3. Installer WeasyPrint :
   ```bash
   pip install weasyprint
   ```

### Option 2 : Utiliser WSL (recommandé)

Si vous utilisez WSL, suivez les instructions pour Linux ci-dessus.

## Installation rapide (script)

Un script d'installation est disponible :

```bash
cd gabomazone-app
bash install_weasyprint.sh
```

## Alternative : Utiliser l'impression du navigateur

Si l'installation de WeasyPrint pose problème, vous pouvez toujours :
1. Cliquer sur "Voir la facture" pour ouvrir la facture dans le navigateur
2. Utiliser l'impression du navigateur (Ctrl+P ou Cmd+P)
3. Choisir "Enregistrer au format PDF" dans les options d'impression

Le design de la facture est optimisé pour l'impression et fonctionne parfaitement avec cette méthode.

## Dépannage

### Erreur : "No module named 'weasyprint'"
- Vérifiez que vous êtes dans l'environnement virtuel : `which python` doit pointer vers `.venv/bin/python`
- Réinstallez : `pip install --upgrade weasyprint`

### Erreur : "cairo" ou dépendances système manquantes
- Sur Linux/WSL : Installez les dépendances système listées ci-dessus
- Sur Windows : Installez GTK+ pour Windows

### Erreur lors de la génération PDF
- Vérifiez que toutes les dépendances sont installées
- Consultez les logs Django pour plus de détails
- Utilisez l'impression du navigateur en alternative

