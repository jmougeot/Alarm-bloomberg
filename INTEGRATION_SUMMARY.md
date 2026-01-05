# Intégration Serveur - Résumé des modifications

## 📋 Fichiers créés

### Services
1. **`src/services/auth_service.py`**
   - Gestion authentification (login/register)
   - Sauvegarde persistante du token JWT
   - Génération URL WebSocket

2. **`src/services/alarm_server_service.py`**
   - Client WebSocket Qt pour synchronisation temps réel
   - Signaux Qt pour les événements serveur
   - Reconnexion automatique
   - API de synchronisation (create/update/delete)

### UI
3. **`src/ui/login_dialog.py`**
   - Dialog de connexion/inscription
   - Onglets login et register
   - Option "Continuer hors ligne"
   - Validation des champs

### Configuration
4. **`src/config.py`**
   - Configuration centralisée du serveur
   - URL modifiable (local/production)
   - Paramètres de connexion

### Documentation
5. **`SERVER_INTEGRATION.md`**
   - Guide complet d'utilisation
   - Architecture
   - Instructions de déploiement
   - Troubleshooting

6. **`test_server.py`**
   - Script de test de connexion
   - Validation santé du serveur
   - Test authentification

## 📝 Fichiers modifiés

### 1. **`requirements.txt`**
```diff
+ websockets>=12.0
+ httpx>=0.25.0
+ aiofiles>=23.0.0
```

### 2. **`main.py`**
- Import de la configuration serveur
- Passage de `server_url` au MainWindow

### 3. **`src/ui/main_window.py`**
#### Nouveaux imports
- `AuthService`, `AlarmServerService`, `LoginDialog`
- `asyncio` pour les appels async

#### Nouvelles propriétés
```python
self.auth_service = AuthService(server_url)
self.alarm_server: Optional[AlarmServerService] = None
self._online_mode = False
```

#### Nouvelles méthodes
- `_attempt_server_connection()` - Connexion auto au démarrage
- `_show_login_dialog()` - Affiche le dialog
- `_on_login_attempt()` - Gère login/register
- `_start_server_sync()` - Démarre WebSocket
- `_on_server_connected()` - Callback connexion
- `_on_server_disconnected()` - Callback déconnexion
- `_on_server_error()` - Gestion erreurs
- `_on_initial_state()` - État initial du serveur
- `_on_server_alarm_*()` - Callbacks alarmes
- `_on_server_page_*()` - Callbacks pages

#### Modifications closeEvent
- Arrêt propre du service WebSocket

## 🔄 Flux d'authentification

```
Démarrage app
    │
    ├─ Token existe localement?
    │   ├─ OUI → Connexion WebSocket automatique
    │   └─ NON → Afficher dialog login
    │
Login/Register
    │
    ├─ HTTP POST /login ou /register
    ├─ Récupération JWT token
    ├─ Sauvegarde locale du token
    └─ Connexion WebSocket
    
WebSocket
    │
    ├─ Envoi token dans URL: ws://...?token=XXX
    ├─ Réception initial_state
    └─ Écoute événements en temps réel
```

## 📊 Architecture de synchronisation

```
MainWindow
    │
    ├─ auth_service (AuthService)
    │   ├─ login() / register()
    │   ├─ load_saved_token()
    │   └─ get_ws_url()
    │
    └─ alarm_server (AlarmServerService)
        ├─ Signaux Qt:
        │   ├─ connected
        │   ├─ disconnected
        │   ├─ initial_state_received
        │   ├─ alarm_created/updated/deleted
        │   └─ page_created/updated/deleted
        │
        └─ Méthodes sync:
            ├─ create_alarm_sync()
            ├─ update_alarm_sync()
            ├─ delete_alarm_sync()
            ├─ create_page_sync()
            └─ share_page_sync()
```

## 🎯 Fonctionnalités implémentées

✅ **Authentification**
- Login/Register avec JWT
- Token persistant local
- Auto-login au démarrage

✅ **WebSocket**
- Connexion temps réel
- Reconnexion automatique
- Gestion des déconnexions

✅ **Mode hybride**
- Mode en ligne avec serveur
- Mode hors ligne (fallback)
- Choix utilisateur

✅ **UI**
- Dialog de login/register
- Indicateurs de connexion
- Messages d'erreur

✅ **Infrastructure**
- Services séparés et testables
- Configuration centralisée
- Documentation complète

## 🔨 TODO - Synchronisation

Les méthodes suivantes sont des stubs à implémenter:

```python
def _on_initial_state(self, state: dict):
    # TODO: Charger pages et alarmes du serveur
    pass

def _on_server_alarm_created(self, alarm_data: dict):
    # TODO: Créer l'alarme localement
    pass

def _on_server_alarm_updated(self, alarm_data: dict):
    # TODO: Mettre à jour l'alarme locale
    pass

def _on_server_alarm_deleted(self, alarm_id: str):
    # TODO: Supprimer l'alarme locale
    pass

def _on_server_page_created(self, page_data: dict):
    # TODO: Créer la page localement
    pass
```

### Plan de synchronisation complète

1. **Mapping Server ↔ Client**
   - Alarme serveur → Strategy client
   - Page serveur → PageWidget client

2. **Stratégies de conflit**
   - Last-write-wins
   - Ou: Merge intelligent

3. **Queue offline**
   - Stocker modifications pendant déconnexion
   - Rejouer à la reconnexion

4. **Bidirectionnel**
   - Client → Serveur: Sur chaque modification locale
   - Serveur → Client: Via WebSocket

## 🧪 Tests

### Test connexion
```bash
python test_server.py
```

### Test complet
1. Démarrer le serveur (voir `server.md`)
2. Lancer `python main.py`
3. Créer un compte
4. Vérifier la connexion dans la statusbar

### Test mode offline
1. Ne pas démarrer le serveur
2. Lancer `python main.py`
3. Cliquer "Continuer hors ligne"
4. Vérifier que l'app fonctionne normalement

## 📦 Déploiement

### Local
```bash
pip install -r requirements.txt
python main.py
```

### Production
1. Modifier `src/config.py`:
   ```python
   ALARM_SERVER_URL = "https://your-server.com"
   ```

2. Rebuild et distribuer

## 🔐 Sécurité

- Passwords JAMAIS stockés en clair
- Token JWT avec expiration
- WebSocket sécurisé (WSS) en production
- Permissions par page sur le serveur

## 📞 Support

- Documentation: `SERVER_INTEGRATION.md`
- Architecture serveur: `server.md`
- Test connexion: `python test_server.py`
