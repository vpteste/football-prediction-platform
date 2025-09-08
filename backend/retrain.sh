#!/bin/bash

# Ce script automatise le processus de ré-entraînement du modèle de prédiction.
# Il doit être exécuté depuis le dossier 'backend'.

# Arrête le script si une commande échoue
set -e

echo "--- Début du processus de ré-entraînement automatique ---"

# Étape 1: Mettre à jour la base de données historiques
echo "\n[1/2] Lancement de la collecte des données (data_collector.py)..."
./.venv/bin/python data_collector.py

echo "\n[2/2] Lancement de l'entraînement du modèle (trainer.py)..."
./.venv/bin/python trainer.py

echo "\n--- Processus de ré-entraînement terminé avec succès! ---"
echo "N'oubliez pas de redémarrer le serveur web (uvicorn) pour qu'il charge le nouveau modèle."
