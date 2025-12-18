#!/usr/bin/env python
"""
Script de diagnostic pour le système C2C de Gabomazone
Vérifie l'état de la base de données et identifie les problèmes potentiels
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

from accounts.models import PeerToPeerProduct, ProductConversation, ProductMessage
from c2c.models import PurchaseIntent, Negotiation
from django.contrib.auth.models import User
from django.db import connection

def check_tables():
    """Vérifie que toutes les tables nécessaires existent"""
    print("\n🔍 VÉRIFICATION DES TABLES")
    print("-" * 60)
    
    required_tables = [
        'accounts_peertopeerproduct',
        'accounts_productconversation',
        'accounts_productmessage',
        'c2c_purchaseintent',
        'c2c_negotiation',
    ]
    
    with connection.cursor() as cursor:
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        existing_tables = [row[0] for row in cursor.fetchall()]
    
    missing = []
    for table in required_tables:
        if table in existing_tables:
            print(f"  ✅ {table}")
        else:
            print(f"  ❌ {table} - MANQUANTE!")
            missing.append(table)
    
    if missing:
        print(f"\n⚠️ {len(missing)} table(s) manquante(s). Exécutez:")
        print("  python manage.py migrate")
        return False
    return True

def check_users():
    """Affiche les utilisateurs"""
    print("\n👥 UTILISATEURS")
    print("-" * 60)
    users = User.objects.all()
    for u in users[:10]:  # Afficher les 10 premiers
        print(f"  - {u.username} (ID: {u.id}, Email: {u.email or '(vide)'})")
    
    total = users.count()
    if total > 10:
        print(f"  ... et {total - 10} autres")
    print(f"\n📊 Total: {total} utilisateur(s)")
    
    if total < 2:
        print("⚠️ Vous avez besoin d'au moins 2 utilisateurs (1 vendeur + 1 acheteur) pour tester le C2C")
    
    return total

def check_products():
    """Affiche les articles d'occasion"""
    print("\n🛍️ ARTICLES D'OCCASION")
    print("-" * 60)
    
    try:
        peer_products = PeerToPeerProduct.objects.all()
        for p in peer_products[:10]:  # Afficher les 10 premiers
            status_icon = "✅" if p.status == PeerToPeerProduct.APPROVED else "⏳"
            print(f"  {status_icon} [{p.status}] {p.product_name}")
            print(f"     ID: {p.id}, Vendeur: {p.seller.username}, Prix: {p.PRDPrice:,.0f} FCFA")
        
        total = peer_products.count()
        approved = PeerToPeerProduct.objects.filter(status=PeerToPeerProduct.APPROVED).count()
        
        if total > 10:
            print(f"  ... et {total - 10} autres")
        
        print(f"\n📊 Total: {total} article(s)")
        print(f"📊 Approuvés: {approved} article(s)")
        
        if approved == 0:
            print("⚠️ Aucun article approuvé. Créez un article et approuvez-le pour tester le C2C.")
        
        return total, approved
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return 0, 0

def check_intents():
    """Affiche les intentions d'achat"""
    print("\n💡 INTENTIONS D'ACHAT")
    print("-" * 60)
    
    try:
        intents = PurchaseIntent.objects.all().select_related('product', 'buyer', 'seller')
        
        if intents.count() == 0:
            print("  (Aucune intention d'achat)")
            print("\n⚠️ Aucune intention d'achat trouvée. C'est normal si vous n'avez pas encore cliqué sur 'Négocier'.")
            return 0
        
        for intent in intents:
            status_map = {
                PurchaseIntent.PENDING: "⏳ EN ATTENTE",
                PurchaseIntent.NEGOTIATING: "💬 NÉGOCIATION",
                PurchaseIntent.ACCEPTED: "✅ ACCEPTÉ",
                PurchaseIntent.REJECTED: "❌ REFUSÉ",
                PurchaseIntent.CANCELLED: "🚫 ANNULÉ",
                PurchaseIntent.EXPIRED: "⌛ EXPIRÉ",
                PurchaseIntent.COMPLETED: "✅ TERMINÉ",
            }
            status_label = status_map.get(intent.status, intent.status)
            
            print(f"\n  📋 Intention #{intent.id}: {intent.product.product_name}")
            print(f"     Statut: {status_label}")
            print(f"     Acheteur: {intent.buyer.username}")
            print(f"     Vendeur: {intent.seller.username}")
            print(f"     Prix initial: {intent.initial_price:,.0f} FCFA")
            if intent.negotiated_price:
                print(f"     Prix négocié: {intent.negotiated_price:,.0f} FCFA")
            if intent.final_price:
                print(f"     Prix final: {intent.final_price:,.0f} FCFA")
            print(f"     Vendeur notifié: {'✅ Oui' if intent.seller_notified else '❌ Non'}")
            print(f"     Expire le: {intent.expires_at.strftime('%d/%m/%Y %H:%M')}")
            
            # Vérifier s'il y a des négociations
            negs = intent.negotiations.all()
            if negs.exists():
                print(f"     Négociations: {negs.count()}")
                for neg in negs:
                    print(f"       - {neg.proposer.username}: {neg.proposed_price:,.0f} FCFA ({neg.status})")
        
        print(f"\n📊 Total: {intents.count()} intention(s) d'achat")
        return intents.count()
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return 0

def check_conversations():
    """Affiche les conversations"""
    print("\n💬 CONVERSATIONS")
    print("-" * 60)
    
    try:
        convs = ProductConversation.objects.all().select_related('product', 'buyer', 'seller')
        
        if convs.count() == 0:
            print("  (Aucune conversation)")
            print("\n⚠️ Aucune conversation trouvée. Vérifiez que les intentions d'achat créent bien des conversations.")
            return 0
        
        for conv in convs:
            msg_count = conv.messages.count()
            unread_seller = conv.get_unread_count_for_seller()
            unread_buyer = conv.get_unread_count_for_buyer()
            
            print(f"\n  💬 Conversation #{conv.id}: {conv.product.product_name}")
            print(f"     Acheteur: {conv.buyer.username}")
            print(f"     Vendeur: {conv.seller.username}")
            print(f"     Messages: {msg_count}")
            print(f"     Non lus (Vendeur: {unread_seller}, Acheteur: {unread_buyer})")
            print(f"     Dernier message: {conv.last_message_at.strftime('%d/%m/%Y %H:%M') if conv.last_message_at else '(jamais)'}")
            
            # Afficher les 3 derniers messages
            if msg_count > 0:
                print("     Derniers messages:")
                for msg in conv.messages.order_by('-created_at')[:3]:
                    sender_name = msg.sender.username
                    preview = msg.message[:50] + "..." if len(msg.message) > 50 else msg.message
                    read_icon = "📖" if msg.is_read else "📩"
                    print(f"       {read_icon} {sender_name}: {preview}")
        
        print(f"\n📊 Total: {convs.count()} conversation(s)")
        return convs.count()
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return 0

def check_negotiations():
    """Affiche les négociations"""
    print("\n🤝 NÉGOCIATIONS")
    print("-" * 60)
    
    try:
        negs = Negotiation.objects.all().select_related('purchase_intent', 'proposer')
        
        if negs.count() == 0:
            print("  (Aucune négociation)")
            print("\n⚠️ Aucune négociation trouvée. C'est normal si vous n'avez pas encore proposé de prix.")
            return 0
        
        for neg in negs:
            status_map = {
                Negotiation.PENDING: "⏳ EN ATTENTE",
                Negotiation.ACCEPTED: "✅ ACCEPTÉ",
                Negotiation.REJECTED: "❌ REFUSÉ",
            }
            status_label = status_map.get(neg.status, neg.status)
            
            print(f"\n  🤝 Négociation #{neg.id}")
            print(f"     Intention d'achat: #{neg.purchase_intent.id}")
            print(f"     Proposé par: {neg.proposer.username}")
            print(f"     Prix proposé: {neg.proposed_price:,.0f} FCFA")
            print(f"     Statut: {status_label}")
            if neg.message:
                print(f"     Message: {neg.message}")
            print(f"     Date: {neg.created_at.strftime('%d/%m/%Y %H:%M')}")
        
        print(f"\n📊 Total: {negs.count()} négociation(s)")
        return negs.count()
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return 0

def main():
    """Fonction principale"""
    print("=" * 60)
    print("🔍 DIAGNOSTIC C2C - Gabomazone")
    print("=" * 60)
    
    # Vérifier les tables
    if not check_tables():
        print("\n❌ Des tables sont manquantes. Exécutez les migrations d'abord.")
        sys.exit(1)
    
    # Vérifier les utilisateurs
    user_count = check_users()
    
    # Vérifier les produits
    product_count, approved_count = check_products()
    
    # Vérifier les intentions d'achat
    intent_count = check_intents()
    
    # Vérifier les conversations
    conv_count = check_conversations()
    
    # Vérifier les négociations
    neg_count = check_negotiations()
    
    # Résumé final
    print("\n" + "=" * 60)
    print("📊 RÉSUMÉ")
    print("=" * 60)
    print(f"  Utilisateurs:           {user_count}")
    print(f"  Articles d'occasion:    {product_count} ({approved_count} approuvés)")
    print(f"  Intentions d'achat:     {intent_count}")
    print(f"  Conversations:          {conv_count}")
    print(f"  Négociations:           {neg_count}")
    
    # Recommandations
    print("\n💡 RECOMMANDATIONS")
    print("-" * 60)
    
    if user_count < 2:
        print("  ⚠️ Créez au moins 2 comptes utilisateurs")
    
    if approved_count == 0:
        print("  ⚠️ Créez et approuvez au moins 1 article d'occasion")
    
    if intent_count == 0 and approved_count > 0:
        print("  ⚠️ Cliquez sur 'Négocier' sur un article pour créer une intention d'achat")
    
    if intent_count > 0 and conv_count == 0:
        print("  ⚠️ Problème: Des intentions d'achat existent mais aucune conversation n'a été créée")
        print("      → Vérifiez le service PurchaseIntentService.create_purchase_intent")
    
    if conv_count > 0 and neg_count == 0:
        print("  ⚠️ Les conversations existent mais aucune négociation n'a été faite")
        print("      → Essayez de proposer un prix dans le chatbot")
    
    if intent_count == 0 and conv_count == 0 and neg_count == 0:
        print("  ✅ Base de données vide - c'est normal si vous débutez")
        print("  📝 Suivez le guide TEST_C2C_WORKFLOW.md pour tester le système")
    
    print("\n" + "=" * 60)
    print("✅ DIAGNOSTIC TERMINÉ")
    print("=" * 60)

if __name__ == '__main__':
    main()


