# Bloomberg Alarm - Intégration Serveur

## Installation

### Dépendances

```bash
pip install -r requirements.txt
```

### Configuration

Éditez `src/config.py` pour configurer l'URL du serveur:

```python
# Serveur local
ALARM_SERVER_URL = "http://localhost:8080"

# Serveur de production (Fly.io)
# ALARM_SERVER_URL = "https://alarm-server.fly.dev"
```

## Utilisation

### Mode en ligne (avec serveur)

1. **Démarrer le serveur** (voir `server.md`)
   ```bash
   cd alarm-server
   uvicorn app.main:app --reload --port 8080
   ```

2. **Lancer le client**
   ```bash
   python main.py
   ```

3. **Première connexion**
   - Une fenêtre de login s'affiche automatiquement
   - Créez un compte dans l'onglet "Inscription"
   - Ou connectez-vous si vous avez déjà un compte

4. **Synchronisation automatique**
   - Les stratégies sont automatiquement sauvegardées sur le serveur
   - Les modifications sont synchronisées en temps réel avec tous les clients connectés
   - Le token de connexion est sauvegardé localement

### Mode hors ligne

Si le serveur n'est pas accessible:
- Cliquez sur "Continuer hors ligne" dans le dialog de login
- Les stratégies seront sauvegardées localement uniquement
- Utilisez le menu "Fichier > Sauvegarder" pour créer des fichiers `.baw`

## Fonctionnalités

### Synchronisation

- ✅ Authentification JWT avec token persistant
- ✅ Connexion WebSocket en temps réel
- ✅ Reconnexion automatique en cas de perte de connexion
- ⏳ Synchronisation des stratégies (en développement)
- ⏳ Synchronisation des alarmes (en développement)
- ⏳ Partage de pages entre utilisateurs (en développement)

### Mode hybride

Le client supporte deux modes:
- **Mode en ligne**: Toutes les données synchronisées avec le serveur
- **Mode hors ligne**: Données locales uniquement (fichiers `.baw`)

Vous pouvez basculer entre les modes à tout moment.

## Architecture

```
Client (Qt/PySide6)
    │
    ├─ AuthService         → Login/Register (HTTP)
    ├─ AlarmServerService  → WebSocket en temps réel
    └─ FileHandler         → Sauvegarde locale de secours

           ↕ WebSocket (wss://)
           
Serveur (FastAPI)
    │
    ├─ API HTTP           → /login, /register, /pages, /alarms
    ├─ WebSocket          → Broadcast temps réel
    └─ SQLite DB          → Stockage persistant
```

## Données stockées

### Serveur
- Utilisateurs (passwords hashés bcrypt)
- Pages et permissions
- Stratégies (alarmes Bloomberg)
- Historique des déclenchements

### Client
- Token d'authentification (`~/.bloomberg_alarm/auth_token.json`)
- Fichiers de backup locaux (`.baw`)

## Sécurité

- 🔒 Passwords hashés avec bcrypt
- 🔒 JWT tokens avec expiration
- 🔒 WebSocket sécurisé (WSS en production)
- 🔒 Permissions par page
- 🔒 Token stocké localement de manière sécurisée

## Déploiement serveur

Voir `server.md` pour les détails de déploiement sur:
- Fly.io (gratuit)
- VPS / Docker
- Serveur local

## Commandes utiles

### Réinitialiser l'authentification

```bash
# Windows
del "%USERPROFILE%\.bloomberg_alarm\auth_token.json"

# Linux/Mac
rm ~/.bloomberg_alarm/auth_token.json
```

### Changer d'URL serveur

Éditez `src/config.py` ou définissez la variable d'environnement:

```bash
set ALARM_SERVER_URL=https://votre-serveur.com
python main.py
```

## Troubleshooting

### "Connexion refusée"
- Vérifiez que le serveur est démarré
- Vérifiez l'URL dans `src/config.py`
- Testez avec: `curl http://localhost:8080/health`

### "Token invalide"
- Supprimez le token stocké (voir ci-dessus)
- Reconnectez-vous

### Mode hors ligne forcé
- Le client continue de fonctionner même sans serveur
- Les données sont sauvegardées localement
- Synchronisation automatique à la reconnexion (futur)

## Développement

### Ajouter une synchronisation

1. Ajouter un signal dans `AlarmServerService`
2. Connecter le signal dans `MainWindow._start_server_sync()`
3. Implémenter le handler `_on_server_*`

Exemple:
```python
# Dans AlarmServerService
strategy_updated = Signal(dict)

# Dans MainWindow
self.alarm_server.strategy_updated.connect(self._on_server_strategy_updated)

def _on_server_strategy_updated(self, data: dict):
    # Mettre à jour la stratégie locale
    pass
```

## TODO

- [ ] Synchronisation complète stratégies
- [ ] Synchronisation alarmes déclenchées
- [ ] Partage de pages entre utilisateurs
- [ ] Gestion des conflits de synchronisation
- [ ] Mode offline-first avec queue de synchronisation
- [ ] Notifications push depuis le serveur
- [ ] Historique des modifications
