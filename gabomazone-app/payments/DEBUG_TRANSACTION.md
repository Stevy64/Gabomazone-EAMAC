# Guide de débogage des transactions SingPay

## Problèmes courants et solutions

### 1. `transaction_id` manquant

**Symptôme**: `transaction_id manquant dans la réponse API, génération d'un ID: REF-UNKNOWN-...`

**Causes possibles**:
- L'API SingPay ne retourne pas de `transaction_id` dans la réponse JSON
- Le `transaction_id` n'est pas dans l'URL de paiement
- Le format de l'URL de paiement n'est pas reconnu

**Solutions**:
- Vérifier les logs pour voir la réponse complète de l'API
- Vérifier le format de l'URL de paiement retournée
- Le système génère automatiquement un `transaction_id` basé sur la référence

### 2. Transaction non trouvée

**Symptôme**: `No SingPayTransaction matches the given query`

**Causes possibles**:
- Le `transaction_id` utilisé pour chercher ne correspond pas à celui créé
- La transaction n'a pas été créée correctement
- Le `transaction_id` a été modifié entre la création et la recherche

**Solutions**:
- Vérifier les logs pour voir le `transaction_id` créé
- Vérifier que la transaction existe dans la base de données
- Vérifier que le `transaction_id` dans l'URL correspond à celui en base

### 3. Erreur lors de la création de la transaction

**Symptôme**: `UNIQUE constraint failed: payments_singpaytransaction.transaction_id`

**Causes possibles**:
- Tentative de créer une transaction avec un `transaction_id` déjà existant
- Double clic sur le bouton de paiement

**Solutions**:
- Le système détecte automatiquement les transactions existantes et les met à jour
- Vérifier les logs pour voir si une transaction existante a été trouvée

## Vérifications à faire

1. **Vérifier les logs Django**:
   ```bash
   # Chercher les logs de transaction
   grep "Transaction ID à utiliser" logs/django.log
   grep "transaction_id" logs/django.log
   ```

2. **Vérifier la base de données**:
   ```python
   from payments.models import SingPayTransaction
   # Voir les transactions récentes
   transactions = SingPayTransaction.objects.all().order_by('-id')[:10]
   for t in transactions:
       print(f"ID: {t.id}, Transaction ID: {t.transaction_id}, Statut: {t.status}")
   ```

3. **Vérifier la réponse de l'API SingPay**:
   - Les logs affichent la réponse complète de l'API
   - Vérifier le format de l'URL de paiement
   - Vérifier si `transaction_id` est présent dans la réponse

## Format attendu de la réponse SingPay

```json
{
  "link": "https://gateway.singpay.ga/ext/v1/payment/{transaction_id}",
  "exp": "1/9/2026, 11:41:11 PM",
  "reference": "REF-ORDER-123"
}
```

Ou:

```json
{
  "payment_url": "https://gateway.singpay.ga/payment/{transaction_id}",
  "transaction_id": "abc123...",
  "expires_at": "2026-01-09T23:41:11Z"
}
```



