# Guide de Test - Gabomazone Redesign

## ✅ Problème mysqlclient résolu

Le package `mysqlclient` est **déjà commenté** dans `requirements.txt` (ligne 34). 
Le projet utilise **SQLite par défaut**, donc mysqlclient n'est pas nécessaire.

## 🚀 Commandes pour tester l'application

### 1. Activer l'environnement virtuel

**Sur Linux/WSL:**
```bash
cd gabomazone-app
source .venv/bin/activate
```

**Sur Windows PowerShell:**
```powershell
cd gabomazone-app
.venv\Scripts\Activate.ps1
```

### 2. Vérifier que les dépendances sont installées

```bash
pip list | grep Django
```

Vous devriez voir `Django 3.2.14` installé.

### 3. Vérifier la configuration Django

```bash
python manage.py check
```

Cette commande vérifie que la configuration Django est correcte.

### 4. Appliquer les migrations (si nécessaire)

```bash
python manage.py migrate
```

### 5. Créer un superutilisateur (si nécessaire)

```bash
python manage.py createsuperuser
```

### 6. Lancer le serveur de développement

```bash
python manage.py runserver
```

Ou sur un port spécifique:
```bash
python manage.py runserver 8000
```

### 7. Accéder à l'application

- **Client app**: http://127.0.0.1:8000/
- **Admin**: http://127.0.0.1:8000/admin/
- **Vendor Dashboard**: http://127.0.0.1:8000/supplier/panel/ (après connexion vendeur)

## 🎨 Vérifications du Redesign

### Client App (White/Orange)
- [ ] Vérifier que le thème orange/blanc s'affiche
- [ ] Tester la navigation mobile (bottom nav)
- [ ] Vérifier les prix en XOF
- [ ] Tester la recherche
- [ ] Vérifier le panier

### Vendor Dashboard (Purple Glassmorphism)
- [ ] Vérifier le design purple/glass
- [ ] Tester la sidebar
- [ ] Vérifier les statistiques
- [ ] Tester la gestion des produits

### Français
- [ ] Vérifier que tous les textes sont en français
- [ ] Pas de langue switcher visible
- [ ] Tous les boutons en français

### Currency XOF
- [ ] Tous les prix affichés en XOF
- [ ] Format: `{{price|floatformat:0}} XOF`

## 🐛 Problèmes courants

### Si mysqlclient pose problème
Le package est déjà commenté. Si vous voyez encore des erreurs:
1. Vérifiez que la ligne 34 de `requirements.txt` est bien commentée: `#mysqlclient>=2.1.0`
2. Le projet utilise SQLite, mysqlclient n'est pas nécessaire

### Si les fichiers statiques ne s'affichent pas
```bash
python manage.py collectstatic --noinput
```

### Si erreur de migration
```bash
python manage.py makemigrations
python manage.py migrate
```

## 📝 Notes

- Le projet utilise SQLite par défaut (pas besoin de MySQL)
- Tous les textes doivent être en français
- Tous les prix en XOF
- Design mobile-first avec bottom navigation

