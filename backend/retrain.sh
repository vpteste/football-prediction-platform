#!/bin/bash

# Ce script automatise le processus de ré-entraînement du modèle de prédiction.
# Il peut maintenant être exécuté depuis n'importe où.

# Arrête le script si une commande échoue
set -e

# Se place dans le dossier du script pour garantir que les chemins sont corrects
cd "$(dirname "$0")"

echo "--- Début du processus de ré-entraînement automatique ---"

# Étape 1: Mettre à jour la base de données historiques
echo "
[1/2] Lancement de la collecte des données (data_collector.py)..."
./.venv/bin/python data_collector.py

echo "
[2/2] Lancement de l'entraînement du modèle (trainer.py)..."
./.venv/bin/python trainer.py

echo "
--- Processus de ré-entraînement terminé avec succès! ---"
echo "N'oubliez pas de redémarrer le serveur web (uvicorn) pour qu'il charge le nouveau modèle."