# 🧪 Guide de test du module C2C

## Préparation

1. **Créer les migrations et les appliquer**
```bash
cd gabomazone-app
python manage.py makemigrations c2c
python manage.py migrate c2c
```

2. **Créer les paramètres par défaut**
```bash
python manage.py shell
```
```python
from c2c.models import PlatformSettings
PlatformSettings.objects.create()
```

3. **Créer des utilisateurs de test**
- Vendeur : `seller@test.com`
- Acheteur : `buyer@test.com`

4. **Créer un produit peer-to-peer de test**
- Via l'admin ou via `/sell-product/`

## Tests du workflow complet

### Test 1 : Création d'intention d'achat

1. Se connecter en tant qu'acheteur
2. Aller sur une page de produit peer-to-peer
3. Cliquer sur "Proposer une offre"
4. **Résultat attendu** : Redirection vers `/c2c/purchase-intent/{product_id}/`
5. Cliquer sur "Créer une intention d'achat"
6. **Résultat attendu** : 
   - Redirection vers la messagerie
   - Conversation ouverte avec le vendeur
   - Notification au vendeur

### Test 2 : Négociation

1. Dans la messagerie, proposer un prix
2. **Résultat attendu** :
   - Création d'une `Negotiation`
   - Mise à jour du statut de `PurchaseIntent` à "NEGOTIATING"

### Test 3 : Acceptation du prix final

1. Les deux parties acceptent un prix
2. **Résultat attendu** :
   - Création d'une `C2COrder`
   - Calcul automatique des commissions
   - Création d'une `DeliveryVerification` avec codes
   - Redirection vers le paiement

### Test 4 : Paiement

1. Cliquer sur "Procéder au paiement"
2. **Résultat attendu** :
   - Initialisation SingPay (ou simulation en sandbox)
   - Mise à jour du statut de la commande à "PAID"

### Test 5 : Vérification double code

1. **En tant que vendeur** :
   - Saisir le code acheteur (A-CODE)
   - **Résultat attendu** : Code vérifié, statut mis à jour

2. **En tant qu'acheteur** :
   - Saisir le code vendeur (V-CODE)
   - **Résultat attendu** : 
     - Code vérifié
     - Transaction complétée
     - Statistiques vendeur mises à jour

## Tests de l'admin

### Test 6 : Gestion des commissions

1. Aller sur `/admin/c2c/platformsettings/`
2. Modifier les commissions
3. **Résultat attendu** : Changements sauvegardés

### Test 7 : Visualisation des commandes

1. Aller sur `/admin/c2c/c2corder/`
2. **Résultat attendu** : Liste de toutes les commandes C2C

## Tests des dashboards

### Test 8 : Dashboard vendeur

1. Aller sur `/c2c/seller/dashboard/`
2. **Résultat attendu** :
   - Statistiques affichées
   - Intentions d'achat récentes
   - Liens vers les commandes

### Test 9 : Dashboard acheteur

1. Aller sur `/c2c/buyer/orders/`
2. **Résultat attendu** : Liste des commandes de l'acheteur

## Tests de validation

### Test 10 : Vérifier les permissions

1. Essayer d'accéder à une commande qui ne nous appartient pas
2. **Résultat attendu** : Message d'erreur, redirection

### Test 11 : Vérifier les calculs de commissions

1. Créer une commande avec un prix de 100 000 FCFA
2. **Résultat attendu** :
   - Commission acheteur : 5 900 FCFA
   - Commission vendeur : 9 900 FCFA
   - Total acheteur : 105 900 FCFA
   - Net vendeur : 90 100 FCFA

## Checklist de validation

- [ ] Les migrations s'appliquent sans erreur
- [ ] Les paramètres par défaut sont créés
- [ ] L'intention d'achat se crée correctement
- [ ] La négociation fonctionne
- [ ] La commande C2C est créée avec les bonnes commissions
- [ ] Le paiement s'initialise (ou se simule)
- [ ] Les codes de vérification sont générés
- [ ] La vérification double code fonctionne
- [ ] Les statistiques vendeur sont mises à jour
- [ ] L'admin fonctionne correctement
- [ ] Les dashboards s'affichent
- [ ] Les permissions sont respectées

## 🐛 Problèmes courants

### Erreur : "no such table: c2c_platformsettings"
**Solution** : Exécutez `python manage.py migrate c2c`

### Erreur : "ModuleNotFoundError: No module named 'c2c'"
**Solution** : Vérifiez que `c2c` est dans `INSTALLED_APPS`

### Les templates ne s'affichent pas
**Solution** : Vérifiez que le dossier `c2c/templates/c2c/` existe

### Les codes de vérification ne sont pas générés
**Solution** : Vérifiez que `DeliveryVerification` est créée lors de la création de `C2COrder`

## 📝 Notes

- En mode sandbox, le paiement SingPay est simulé
- Les codes de vérification sont générés automatiquement
- Les badges vendeurs sont attribués automatiquement selon les performances


