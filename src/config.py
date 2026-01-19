"""
Configuration du serveur d'alarmes
"""

# URL du serveur d'alarmes
# Peut être modifié pour pointer vers le serveur de production
ALARM_SERVER_URL = "http://localhost:8080"

# Pour utiliser le serveur déployé sur Fly.io, décommenter:
# ALARM_SERVER_URL = "https://alarm-server.fly.dev"

# Paramètres de connexion
CONNECTION_RETRY_DELAY = 5.0  # Délai entre les tentatives de reconnexion (secondes)
CONNECTION_TIMEOUT = 10.0  # Timeout des requêtes HTTP (secondes)

# Mode de fonctionnement
AUTO_CONNECT = True  # Se connecter automatiquement au démarrage si un token existe
OFFLINE_MODE_ALLOWED = True  # Permettre de continuer en mode hors ligne
