# GabomaZone
Marketplace multi-vendeur (B2C et C2C) avec paiement SingPay.

## Prérequis
- Python 3.10+
- pip / virtualenv
- PostgreSQL ou SQLite (défaut local)

## Installation rapide (local)
1) Créer et activer un venv
```
python -m venv venv-gabomazone
venv-gabomazone\Scripts\activate   # Windows
source venv-gabomazone/bin/activate # Linux/Mac
```

2) Installer les dépendances
```
pip install -r requirements.txt
```

3) Créer le fichier `.env` dans `gabomazone-app/`
```
SINGPAY_API_KEY=...
SINGPAY_API_SECRET=...
SINGPAY_MERCHANT_ID=...
SINGPAY_ENVIRONMENT=sandbox   # ou production
SINGPAY_PRODUCTION_DOMAIN=gabomazone.pythonanywhere.com
```

4) Migrations + serveur
```
python manage.py migrate
python manage.py runserver 8001
```

## Paiement SingPay (unique moyen de paiement)
Le flux de paiement utilise uniquement l’API SingPay.

Endpoints clés:
- Initialisation: `/payments/singpay/init/`
- Webhook: `/payments/singpay/callback/`
- Return URL: `/payments/singpay/return/`

En production, configure les URLs de callback chez SingPay avec ton domaine public:
```
https://<ton-domaine>/payments/singpay/callback/
https://<ton-domaine>/payments/singpay/return/
```

## Workflow C2C (négociation → paiement → validation)
1) L’acheteur crée une intention d’achat.
2) Négociation du prix jusqu’à acceptation.
3) Paiement via SingPay (transaction C2C).
4) Génération et validation des codes de livraison (acheteur/vendeur).
5) Libération des fonds + commissions via SingPay.

## Troubleshooting SingPay
- **Erreur 401/403**: vérifier `SINGPAY_API_KEY`, `SINGPAY_API_SECRET`, `SINGPAY_MERCHANT_ID`.
- **Callback non reçu**: vérifier l’URL webhook côté SingPay et l’accessibilité publique.
- **URL de paiement invalide**: vérifier `SINGPAY_PRODUCTION_DOMAIN` et l’environnement.
- **Paiement bloqué**: consulter les logs serveur et `SingPayWebhookLog` dans l’admin.

## Check-list mise en production
- Définir `DEBUG=False` et configurer les hosts autorisés.
- Configurer les variables d’environnement SingPay en production.
- Renseigner `SINGPAY_PRODUCTION_DOMAIN` avec le domaine public.
- Déclarer les URLs webhook/return chez SingPay.
- Exécuter `python manage.py migrate` et `python manage.py collectstatic`.
- Vérifier SSL/HTTPS et accessibilité publique des callbacks.

## Docker (optionnel)
```
docker build -t gabomazone-app -f Dockerfile.gabomazone .
docker run -it --rm --name gabomazone-app gabomazone-app
```

## Déploiement
- PythonAnywhere (Django): https://help.pythonanywhere.com/pages/DeployExistingDjangoProject/
- Static files: https://help.pythonanywhere.com/pages/DjangoStaticFiles

### Si /contact/, /faq/, /pages/… renvoient 404 en production
1. **Test** : ouvrir `https://<ton-domaine>/_urls_ok/`  
   - Si tu vois « OK », Django reçoit les requêtes ; les routes sont en tête dans `project/urls.py`.  
   - Si 404 aussi : le proxy (Nginx, Apache, PythonAnywhere) ne transmet pas ces URLs à Django.

2. **Nginx** : ne pas utiliser `try_files $uri $uri/ =404` pour tout le site.  
   Transmettre à Django tout ce qui n’est pas `/static/` ni `/media/` :
   ```nginx
   location / {
       proxy_pass http://127.0.0.1:8000;  # ou ton socket gunicorn/uwsgi
       proxy_set_header Host $host;
       proxy_set_header X-Real-IP $remote_addr;
       proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
       proxy_set_header X-Forwarded-Proto $scheme;
   }
   location /static/ { alias /chemin/vers/static/; }
   location /media/  { alias /chemin/vers/media/; }
   ```

3. **PythonAnywhere** : dans la configuration WSGI, s’assurer que l’application Django est bien chargée pour le domaine et que les chemins comme `/contact/` ne sont pas interceptés par une règle statique.

## Retirer un module
1) Revenir à zéro sur les migrations: `python manage.py migrate <app_name> zero`
2) Retirer l’app de `INSTALLED_APPS` et des URLs
3) `python manage.py makemigrations` puis `python manage.py migrate`
4) Supprimer le dossier de l’app
