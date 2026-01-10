# Variables d'environnement - Configuration

Ce fichier documente les variables d'environnement nécessaires pour Gabomazone.

## Fichier .env

Créez un fichier `.env` à la racine du projet (`gabomazone-app/.env`) avec le contenu suivant :

```bash
# Variables d'environnement pour Gabomazone
# Ce fichier contient des informations sensibles et ne doit PAS être commité sur Git

## SingPay API Configuration
# Obtenez ces valeurs depuis votre compte SingPay : https://client.singpay.ga
# Documentation : https://client.singpay.ga/doc/reference/index.html
SINGPAY_API_KEY=votre_api_key_ici
SINGPAY_API_SECRET=votre_api_secret_ici
SINGPAY_MERCHANT_ID=votre_merchant_id_ici
SINGPAY_ENVIRONMENT=sandbox
# SINGPAY_BYPASS_API n'est pas nécessaire si les credentials sont présents
# Le système désactivera automatiquement le mode bypass si les credentials sont configurés
# Pour forcer le mode bypass même avec des credentials, décommentez la ligne suivante :
# SINGPAY_BYPASS_API=True
SINGPAY_PRODUCTION_DOMAIN=gabomazone.pythonanywhere.com
```

## Installation

1. Installez `python-decouple` :
   ```bash
   pip install python-decouple
   ```

2. Créez le fichier `.env` à partir de ce template

3. Remplissez les valeurs réelles de vos clés API SingPay

## Mode Bypass automatique

Le système détecte automatiquement si les credentials SingPay sont présents :

- **Si les credentials sont présents** (SINGPAY_API_KEY, SINGPAY_API_SECRET, SINGPAY_MERCHANT_ID) :
  - Le mode bypass est **automatiquement désactivé**
  - L'API réelle SingPay sera utilisée
  - Vous n'avez pas besoin de définir `SINGPAY_BYPASS_API=False`

- **Si les credentials sont absents** :
  - Le mode bypass est **automatiquement activé**
  - Les paiements seront simulés pour les tests

- **Pour forcer le mode bypass** même avec des credentials :
  - Ajoutez `SINGPAY_BYPASS_API=True` dans votre fichier `.env`

## Sécurité

- ⚠️ **NE JAMAIS** commiter le fichier `.env` sur Git
- Le fichier `.env` est déjà dans `.gitignore`
- Utilisez des valeurs différentes pour le développement et la production

