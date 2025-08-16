#!/bin/bash

# ================================
# Gabomazone Launcher - CLI Style
# ================================

clear
echo "==================================="
echo "   🚀 Bienvenue dans"
echo "  ██████████████████████████████████████████████"
echo "  █                                            █"
echo "  █               GABOMAZONE                   █"
echo "  █                                            █"
echo "  ██████████████████████████████████████████████"
echo "==================================="
echo " Gabomazone Django Launcher - v1.0"
echo "==================================="
echo



# 1. Demande si on veut créer un nouvel environnement
read -p "Voulez-vous créer un nouvel environnement Python ? (y/n) : " create_env

if [ "$create_env" == "y" ] || [ "$create_env" == "Y" ]; then
    read -p "Entrez le nom de l'environnement : " env_name
    
    # Création de l'environnement
    python3 -m venv "$env_name"
    
    # Activation de l'environnement
    source "$env_name/bin/activate"
    
    echo "✅ Environnement '$env_name' créé et activé. \n"
else
    echo "⚠️ Aucun nouvel environnement créé. \n"
    
    # Vérifie si un environnement est déjà actif
    if [ -z "$VIRTUAL_ENV" ]; then
        echo "⚠️ Aucun environnement activé. Pense à activer ton venv avant d’installer. \n"
    else
        echo "➡️ Environnement déjà actif : $VIRTUAL_ENV \n"
    fi
fi

# 2. Installation des dépendances
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
    echo "✅ Dépendances installées. \n"
else
    echo "⚠️ Fichier requirements.txt introuvable. \n"
fi

# 3. Demande si on veut lancer le serveur Django
read -p "Voulez-vous lancer le serveur Django ? (y/n) : " run_server

if [ "$run_server" == "y" ] || [ "$run_server" == "Y" ]; then
    # Demande du port
    read -p "Entrez le port (par défaut 8000) : " port
    port=${port:-8000}  # Si vide, on met 8000 par défaut
    
    if [ -f "manage.py" ]; then
        echo "🚀 Lancement du serveur Django sur le port $port ..."
        python manage.py runserver "0.0.0.0:$port"
    else
        echo "❌ Fichier manage.py introuvable. Es-tu dans le bon dossier ?"
    fi
else
    echo "⏹️ Serveur non lancé."
fi
