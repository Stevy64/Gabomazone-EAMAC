# Guide de Test du Workflow C2C

## ✅ Workflow Complet (étape par étape)

### Étape 1: Créer un article d'occasion (Vendeur)
1. Connectez-vous en tant que **Vendeur**
2. Allez sur `/accounts/sell-product/`
3. Ajoutez un article (nom, prix, images, etc.)
4. Attendez la validation (statut = APPROVED)

### Étape 2: Lancer une négociation (Acheteur)
1. **Déconnectez-vous** et **connectez-vous** avec un compte **Acheteur** différent
2. Trouvez l'article sur la page boutique (`/shop/`)
3. Cliquez sur le bouton orange avec icône "Tag" (🏷️)
4. **Vérifiez**: Vous devriez être redirigé vers une page de confirmation
5. **Cliquez sur "Confirmer l'intention d'achat"**
6. **Vérifiez**: Vous devriez être redirigé vers `/accounts/my-messages/` avec le chatbot ouvert

### Étape 3: Notification du vendeur
1. **Déconnectez-vous** et **reconnectez-vous** en tant que **Vendeur**
2. Allez sur `/accounts/my-messages/`
3. **Vérifiez**: Un encadré orange "Intentions d'achat reçues" devrait apparaître en haut
4. **Cliquez sur "Accepter"**
5. **Vérifiez**: Le chatbot devrait s'ouvrir automatiquement

### Étape 4: Négociation du prix
1. Dans le chatbot, une section **jaune** "Négocier le prix" doit être visible
2. **Acheteur**: Propose un nouveau prix (ex: 45000 au lieu de 50000)
3. **Vendeur**: Voit la proposition et peut:
   - **Accepter** (le prix devient final)
   - **Refuser** (nouvelle proposition demandée)
   - **Contre-proposer** (nouveau prix suggéré)
4. Continuez jusqu'à ce qu'un prix soit **accepté par les deux parties**

### Étape 5: Accepter le prix final
1. Quand un prix est accepté, un bouton vert "Accepter le prix final" apparaît
2. **Cliquez dessus**
3. **Vérifiez**: Vous êtes redirigé vers la page de paiement (`/c2c/order/<id>/payment/`)

### Étape 6: Paiement
1. Sur la page de paiement, vous voyez:
   - Prix final négocié
   - Commission acheteur (5.9%)
   - Total à payer
   - Net vendeur (prix - 9.9%)
2. **Cliquez sur "Payer avec SingPay"**
3. *(En mode sandbox, le paiement sera simulé)*

### Étape 7: Vérification double code
1. Après paiement, allez sur `/c2c/order/<id>/detail/`
2. **Vendeur**: Entre le **A-CODE** (code acheteur) pour confirmer la remise
3. **Acheteur**: Entre le **V-CODE** (code vendeur) pour confirmer la réception
4. **Vérifiez**: La transaction passe à "Complétée"

---

## 🐛 Diagnostic: Que faire si ça ne marche pas?

### Problème 1: Le bouton "Négocier" ne s'affiche pas
**Cause possible**: Les articles ne sont pas détectés comme "peer-to-peer"

**Vérification**:
```bash
cd gabomazone-app
python manage.py shell
```
```python
from accounts.models import PeerToPeerProduct
print(f"Nombre d'articles d'occasion: {PeerToPeerProduct.objects.count()}")
print(f"Nombre approuvés: {PeerToPeerProduct.objects.filter(status='APPROVED').count()}")

# Lister les articles approuvés
for p in PeerToPeerProduct.objects.filter(status='APPROVED'):
    print(f"ID: {p.id}, Nom: {p.product_name}, Vendeur: {p.seller.username}")
```

### Problème 2: Le bouton "Négocier" ne fait rien
**Cause possible**: Erreur JavaScript

**Vérification**:
1. Ouvrez la console du navigateur (F12 → Console)
2. Cliquez sur le bouton "Négocier"
3. Notez toute erreur affichée

### Problème 3: Erreur "no such table: c2c_purchaseintent"
**Cause**: Migrations non appliquées

**Solution**:
```bash
cd gabomazone-app
python manage.py migrate c2c
python manage.py migrate accounts
```

### Problème 4: Le vendeur ne reçoit pas de notification
**Cause possible**: `seller_notified` est déjà à True

**Vérification**:
```python
from c2c.models import PurchaseIntent
intents = PurchaseIntent.objects.filter(status='PENDING')
for intent in intents:
    print(f"Intent {intent.id}: Vendeur={intent.seller.username}, Notifié={intent.seller_notified}")
    # Forcer la notification
    intent.seller_notified = False
    intent.save()
```

### Problème 5: Le chatbot est vide
**Cause possible**: La conversation n'a pas été créée

**Vérification**:
```python
from accounts.models import ProductConversation, ProductMessage
from c2c.models import PurchaseIntent

# Vérifier les intentions d'achat
intents = PurchaseIntent.objects.all()
print(f"Intentions d'achat: {intents.count()}")

# Vérifier les conversations
convs = ProductConversation.objects.all()
print(f"Conversations: {convs.count()}")

for conv in convs:
    msgs = conv.messages.all()
    print(f"Conversation {conv.id}: Vendeur={conv.seller.username}, Acheteur={conv.buyer.username}, Messages={msgs.count()}")
```

### Problème 6: La négociation ne fonctionne pas
**Cause possible**: Polling désactivé ou erreur réseau

**Vérification**:
1. Ouvrez la console du navigateur (F12 → Réseau)
2. Proposez un prix
3. Vérifiez qu'une requête à `/c2c/make-offer/<id>/` est envoyée
4. Vérifiez la réponse (doit être `{"success": true, ...}`)

### Problème 7: "UNIQUE constraint failed"
**Cause**: Une intention existe déjà pour ce produit et cet acheteur

**Solution**:
```python
from c2c.models import PurchaseIntent

# Voir les intentions existantes
intents = PurchaseIntent.objects.all()
for i in intents:
    print(f"Intent {i.id}: Produit={i.product.product_name}, Acheteur={i.buyer.username}, Statut={i.status}")

# Supprimer une intention spécifique si nécessaire
intent = PurchaseIntent.objects.get(id=1)  # Remplacer 1 par l'ID
intent.delete()
```

---

## 🔄 Réinitialiser un produit pour retester

Si vous voulez retester avec un produit existant:

```bash
cd gabomazone-app
sqlite3 db.sqlite3 "DELETE FROM c2c_negotiation WHERE purchase_intent_id IN (SELECT id FROM c2c_purchaseintent WHERE product_id=<ID_PRODUIT>); DELETE FROM c2c_purchaseintent WHERE product_id=<ID_PRODUIT>; DELETE FROM accounts_productmessage WHERE conversation_id IN (SELECT id FROM accounts_productconversation WHERE product_id=<ID_PRODUIT>); DELETE FROM accounts_productconversation WHERE product_id=<ID_PRODUIT>;"
```

Remplacez `<ID_PRODUIT>` par l'ID du produit.

---

## 📊 Script de diagnostic complet

Créez un fichier `check_c2c.py` dans `gabomazone-app/`:

```python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

from accounts.models import PeerToPeerProduct, ProductConversation, ProductMessage
from c2c.models import PurchaseIntent, Negotiation
from django.contrib.auth.models import User

print("=" * 60)
print("DIAGNOSTIC C2C - État actuel de la base de données")
print("=" * 60)

print("\n1. UTILISATEURS")
print("-" * 60)
users = User.objects.all()
for u in users[:5]:  # Afficher les 5 premiers
    print(f"  - {u.username} (ID: {u.id}, Email: {u.email})")

print(f"\nTotal: {users.count()} utilisateurs")

print("\n2. ARTICLES D'OCCASION")
print("-" * 60)
peer_products = PeerToPeerProduct.objects.all()
for p in peer_products[:10]:  # Afficher les 10 premiers
    print(f"  - [{p.status}] {p.product_name} (ID: {p.id}, Vendeur: {p.seller.username}, Prix: {p.PRDPrice} FCFA)")

print(f"\nTotal: {peer_products.count()} articles")
print(f"Approuvés: {PeerToPeerProduct.objects.filter(status=PeerToPeerProduct.APPROVED).count()}")

print("\n3. INTENTIONS D'ACHAT")
print("-" * 60)
intents = PurchaseIntent.objects.all().select_related('product', 'buyer', 'seller')
for intent in intents:
    print(f"  - Intent #{intent.id}: {intent.product.product_name}")
    print(f"    Acheteur: {intent.buyer.username}, Vendeur: {intent.seller.username}")
    print(f"    Statut: {intent.status}, Prix initial: {intent.initial_price} FCFA")
    print(f"    Notifié: {intent.seller_notified}, Expire: {intent.expires_at}")
    print()

print(f"Total: {intents.count()} intentions d'achat")

print("\n4. CONVERSATIONS")
print("-" * 60)
convs = ProductConversation.objects.all().select_related('product', 'buyer', 'seller')
for conv in convs:
    msg_count = conv.messages.count()
    unread_seller = conv.get_unread_count_for_seller()
    unread_buyer = conv.get_unread_count_for_buyer()
    print(f"  - Conv #{conv.id}: {conv.product.product_name}")
    print(f"    Acheteur: {conv.buyer.username}, Vendeur: {conv.seller.username}")
    print(f"    Messages: {msg_count}, Non lus (Vendeur: {unread_seller}, Acheteur: {unread_buyer})")
    print()

print(f"Total: {convs.count()} conversations")

print("\n5. NÉGOCIATIONS")
print("-" * 60)
negs = Negotiation.objects.all().select_related('purchase_intent', 'proposer')
for neg in negs:
    print(f"  - Neg #{neg.id}: {neg.proposed_price} FCFA par {neg.proposer.username}")
    print(f"    Statut: {neg.status}, Message: {neg.message or '(vide)'}")
    print()

print(f"Total: {negs.count()} négociations")

print("\n" + "=" * 60)
print("FIN DU DIAGNOSTIC")
print("=" * 60)
```

**Exécution**:
```bash
cd gabomazone-app
python check_c2c.py
```

---

## 📞 Informations à fournir si le problème persiste

Si après tous ces tests, le workflow ne fonctionne toujours pas, fournissez-moi:

1. **Sortie du script `check_c2c.py`**
2. **Erreurs dans la console du navigateur** (F12 → Console)
3. **Étape exacte où ça bloque** (Étape 1, 2, 3, etc.)
4. **Capture d'écran** de l'interface à ce moment
5. **Logs Django** (dans votre terminal où `runserver` est lancé)

Cela me permettra de diagnostiquer précisément le problème.

