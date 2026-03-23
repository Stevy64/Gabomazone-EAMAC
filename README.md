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

---

## Architecture du projet

### Apps Django
| App | Rôle |
|-----|------|
| `home` | Page d'accueil, carousel, configuration du site |
| `accounts` | Authentification, profils, produits C2C, messagerie |
| `products` | Catalogue B2B, détails produit, wishlist, recherche |
| `categories` | Catégories hiérarchiques, listing HTMX avec scroll infini |
| `orders` | Panier, checkout, commandes B2B |
| `c2c` | Workflow C2C (intentions d'achat, négociation, vérification) |
| `payments` | Intégration SingPay, transactions, escrow |
| `suppliers` | Pages vendeurs PRO, listing, détails |
| `contact` | Formulaire de contact |
| `pages` | Pages CMS (à propos, CGV, FAQ) |
| `settings` | Configuration globale du site |
| `supplier_panel` | Panneau d'administration vendeur |

### Templates (`templates/`)
```
templates/
├── base.html                    # Squelette (~100 lignes)
├── components/
│   ├── header.html              # Header + navigation
│   ├── footer.html              # Footer
│   ├── alerts.html              # Toasts notifications
│   ├── bottom_nav.html          # Navigation mobile bas
│   ├── preloader.html           # Spinner de chargement
│   ├── product_card.html        # Carte produit réutilisable
│   ├── search_bar_mobile.html   # Barre recherche mobile
│   └── add_to_cart_sticky.html  # Bouton panier sticky
└── admin/                       # Surcharges admin Django
```

Chaque app a ses propres templates dans `<app>/templates/<app>/`.

**Conventions templates :**
- `{% extends 'base.html' %}` pour toutes les pages
- `{% include "components/..." %}` pour les composants partagés
- Blocs nommés : `{% block head %}`, `{% block body %}`, `{% block script %}`
- Noms de blocs dans les `{% endblock body %}` pour la lisibilité

### Static Files (`static/gabomazone-client/`)
```
gabomazone-client/
├── css/
│   ├── flavoriz-design.css      # Design system principal
│   ├── flavoriz-force.css       # Overrides prioritaires
│   ├── gabomazone-ux.css        # Styles UX spécifiques
│   ├── layout.css               # Layout global (header offset, footer)
│   ├── alerts.css               # Styles toasts
│   ├── modals.css               # Styles modals
│   └── pages/                   # CSS par page (46 fichiers)
│       ├── account.css          # Mon compte
│       ├── account-details.css  # Détails compte
│       ├── cart.css             # Panier
│       ├── cart-empty.css       # Panier vide
│       ├── category-list.css    # Liste catégories
│       ├── change-password.css  # Mot de passe
│       ├── checkout.css         # Paiement
│       ├── contact.css          # Contact
│       ├── faq.css              # FAQ
│       ├── login.css            # Connexion
│       ├── messages.css         # Messagerie
│       ├── pages.css            # Pages CMS
│       ├── product-detail-b2b.css
│       ├── product-detail-c2c.css
│       ├── product-search.css   # Recherche
│       ├── purchase-intent.css  # Intention d'achat C2C
│       ├── sell-product.css     # Vente C2C
│       ├── seller-profile.css   # Profil vendeur C2C
│       ├── success.css          # Confirmation commande
│       ├── vendor-details.css   # Détail vendeur PRO
│       ├── vendors-grid.css     # Grille vendeurs
│       ├── wishlist.css         # Liste souhaits
│       ├── c2c-*.css            # Pages C2C (6 fichiers)
│       └── supplier-panel/      # Panel vendeur (12 fichiers)
│           ├── base.css
│           ├── dashboard.css
│           ├── add-product.css
│           ├── payments-detail.css
│           └── ...
└── js/
    ├── smart-header.js          # Header scroll/sticky
    ├── custom-dropdown.js       # Dropdowns personnalisés
    ├── desktop-search-expand.js # Recherche desktop
    ├── mobile-search-expand.js  # Recherche mobile
    ├── account-dropdown-fix.js  # Fix dropdown compte
    ├── alerts.js                # Auto-dismiss toasts
    ├── modals.js                # Système modal (GMModal)
    └── pages/                   # JS par page (21 fichiers)
        ├── cart.js
        ├── category-list.js
        ├── my-published-products.js
        ├── order-archive.js
        ├── account-details.js
        ├── add-peer-product.js
        ├── cart-empty.js
        └── supplier-panel/         # JS panel vendeur
            ├── edit-product.js
            ├── subscriptions.js
            ├── store-settings.js
            ├── reviews.js
            ├── orders-list.js
            ├── login.js
            └── register.js
```

**Conventions CSS/JS :**
- Chaque page a son propre fichier CSS dans `css/pages/` et optionnellement un JS dans `js/pages/`
- Les classes CSS extraites des templates suivent la convention `gm-s-{hash}` (auto-générées)
- Les scripts Django-dépendants (contenant `{{ }}` ou `{% %}`) restent inline par nécessité
- Cache-busting via `?v=1.0` sur tous les liens statiques

### Logging
Configuré dans `settings.py` avec sortie console + fichier (`logs/gabomazone.log`).
Loggers par app : `accounts`, `orders`, `payments`, `products`, `c2c`, `categories`, `home`, `supplier_panel`, `suppliers`, `contact`.

---

## Paiement SingPay (unique moyen de paiement)
Le flux de paiement utilise uniquement l'API SingPay.

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
1) L'acheteur crée une intention d'achat.
2) Négociation du prix jusqu'à acceptation.
3) Paiement via SingPay (transaction C2C).
4) Génération et validation des codes de livraison (acheteur/vendeur).
5) Libération des fonds + commissions via SingPay.

## Troubleshooting SingPay
- **Erreur 401/403**: vérifier `SINGPAY_API_KEY`, `SINGPAY_API_SECRET`, `SINGPAY_MERCHANT_ID`.
- **Callback non reçu**: vérifier l'URL webhook côté SingPay et l'accessibilité publique.
- **URL de paiement invalide**: vérifier `SINGPAY_PRODUCTION_DOMAIN` et l'environnement.
- **Paiement bloqué**: consulter les logs serveur et `SingPayWebhookLog` dans l'admin.

## Check-list mise en production
- Définir `DEBUG=False` et configurer les hosts autorisés.
- Configurer les variables d'environnement SingPay en production.
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

### Production
```bash
source .venv/bin/activate
pip install gunicorn

# Après chaque modification
sudo systemctl daemon-reload
sudo systemctl restart gunicorn
sudo systemctl status gunicorn
```

## Retirer un module
1) Revenir à zéro sur les migrations: `python manage.py migrate <app_name> zero`
2) Retirer l'app de `INSTALLED_APPS` et des URLs
3) `python manage.py makemigrations` puis `python manage.py migrate`
4) Supprimer le dossier de l'app
