# Backend Specification - Strategy Monitor

## 📊 Base de données SQL

### Tables

```sql
-- Utilisateurs
CREATE TABLE users (
    id TEXT PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Pages de stratégies
CREATE TABLE pages (
    id TEXT PRIMARY KEY,
    owner_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Stratégies (legs stockés en JSON)
CREATE TABLE strategies (
    id TEXT PRIMARY KEY,
    page_id TEXT NOT NULL REFERENCES pages(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    client TEXT,
    action TEXT,
    status TEXT DEFAULT 'En cours',  -- 'En cours', 'Fait', 'Annulé'
    target_price REAL,
    target_condition TEXT DEFAULT 'inferieur',  -- 'inferieur' ou 'superieur'
    legs TEXT,  -- JSON array: [{"id": "...", "ticker": "...", "position": "long", "quantity": 1}]
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Groupes
CREATE TABLE groups (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    owner_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Membres des groupes
CREATE TABLE group_members (
    group_id TEXT NOT NULL REFERENCES groups(id) ON DELETE CASCADE,
    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    PRIMARY KEY (group_id, user_id)
);

-- Permissions sur les pages
CREATE TABLE page_permissions (
    id TEXT PRIMARY KEY,
    page_id TEXT NOT NULL REFERENCES pages(id) ON DELETE CASCADE,
    subject_type TEXT NOT NULL CHECK(subject_type IN ('user', 'group')),
    subject_id TEXT NOT NULL,
    can_view BOOLEAN DEFAULT TRUE,
    can_edit BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(page_id, subject_type, subject_id)
);
```

---

## 🔐 Authentification

### POST /register
Créer un compte utilisateur.

**Request:**
```json
{
    "username": "john",
    "password": "secret123"
}
```

**Response (200):**
```json
{
    "id": "uuid-...",
    "username": "john"
}
```

**Errors:**
- `400` - Username déjà pris: `{"detail": "Username already registered"}`

---

### POST /login
Connexion et obtention du token JWT.

**Request (form-data):**
```
username=john
password=secret123
```

**Response (200):**
```json
{
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "token_type": "bearer"
}
```

**Errors:**
- `401` - Identifiants invalides

---

### GET /me
Infos de l'utilisateur connecté.

**Headers:** `Authorization: Bearer <token>`

**Response (200):**
```json
{
    "id": "uuid-...",
    "username": "john"
}
```

---

## 📄 Pages API

### GET /pages
Récupère toutes les pages accessibles (owned + shared).

**Headers:** `Authorization: Bearer <token>`

**Response (200):**
```json
[
    {
        "id": "page-uuid-1",
        "name": "Mes Stratégies",
        "owner_id": "user-uuid",
        "owner_name": "john",
        "is_owner": true,
        "group_id": null,
        "group_name": null,
        "shared_by": null,
        "can_edit": true
    },
    {
        "id": "page-uuid-2",
        "name": "Page Partagée",
        "owner_id": "other-user-uuid",
        "owner_name": "alice",
        "is_owner": false,
        "group_id": null,
        "group_name": null,
        "shared_by": "alice",
        "can_edit": false
    }
]
```

---

### POST /pages
Crée une nouvelle page.

**Request:**
```json
{
    "name": "Ma Nouvelle Page",
    "id": "optional-custom-uuid"  // optionnel
}
```

**Response (200):**
```json
{
    "id": "page-uuid",
    "name": "Ma Nouvelle Page",
    "owner_id": "user-uuid"
}
```

---

### PUT /pages/{page_id}
Met à jour une page.

**Request:**
```json
{
    "name": "Nouveau Nom"
}
```

**Response (200):** `{"success": true}`

---

### DELETE /pages/{page_id}
Supprime une page (owner only).

**Response (200):** `{"success": true}`

---

## 📊 Permissions API

### GET /pages/{page_id}/permissions
Liste les permissions d'une page.

**Response (200):**
```json
[
    {
        "id": "perm-uuid",
        "subject_type": "user",
        "subject_id": "user-uuid",
        "subject_name": "alice",
        "can_view": true,
        "can_edit": false
    },
    {
        "id": "perm-uuid-2",
        "subject_type": "group",
        "subject_id": "group-uuid",
        "subject_name": "Trading Team",
        "can_view": true,
        "can_edit": true
    }
]
```

---

### POST /pages/{page_id}/permissions
Ajoute une permission.

**Request:**
```json
{
    "subject_type": "user",  // ou "group"
    "subject_id": "uuid-...",
    "can_view": true,
    "can_edit": false
}
```

**Response (200):** `{"success": true, "id": "perm-uuid"}`

---

### DELETE /pages/{page_id}/permissions/{permission_id}
Supprime une permission.

**Response (200):** `{"success": true}`

---

## 👥 Groups API

### GET /groups
Liste les groupes de l'utilisateur (owned + member).

**Response (200):**
```json
[
    {
        "id": "group-uuid",
        "name": "Trading Team",
        "owner_id": "user-uuid",
        "members": [
            {"id": "user-uuid-1", "username": "alice"},
            {"id": "user-uuid-2", "username": "bob"}
        ]
    }
]
```

---

### GET /groups/{group_id}
Détails d'un groupe.

**Response (200):**
```json
{
    "id": "group-uuid",
    "name": "Trading Team",
    "owner_id": "user-uuid",
    "members": [
        {"id": "user-uuid-1", "username": "alice"},
        {"id": "user-uuid-2", "username": "bob"}
    ]
}
```

---

### POST /groups
Crée un groupe.

**Request:**
```json
{
    "name": "Mon Groupe"
}
```

**Response (200):**
```json
{
    "id": "group-uuid",
    "name": "Mon Groupe"
}
```

---

### DELETE /groups/{group_id}
Supprime un groupe (owner only).

**Response (200):** `{"success": true}`

---

### POST /groups/{group_id}/members/{user_id}
Ajoute un membre au groupe.

**Response (200):** `{"success": true}`

---

### DELETE /groups/{group_id}/members/{user_id}
Retire un membre du groupe.

**Response (200):** `{"success": true}`

---

## 🔍 Search API

### GET /users/search?username={name}
Recherche un utilisateur par nom.

**Response (200):**
```json
{
    "id": "user-uuid",
    "username": "alice"
}
```

**Response (404):** `{"detail": "User not found"}`

---

### GET /groups/search?name={name}
Recherche un groupe par nom.

**Response (200):**
```json
{
    "id": "group-uuid",
    "name": "Trading Team"
}
```

---

## 🔌 WebSocket Protocol

### Connexion
```
ws://server:8080/ws?token=<jwt_token>
```

### Messages Client → Serveur

#### Créer une page
```json
{
    "type": "page.create",
    "payload": {
        "id": "optional-uuid",
        "name": "Ma Page"
    }
}
```

#### Mettre à jour une page
```json
{
    "type": "page.update",
    "payload": {
        "id": "page-uuid",
        "name": "Nouveau Nom"
    }
}
```

#### Supprimer une page
```json
{
    "type": "page.delete",
    "payload": {
        "id": "page-uuid"
    }
}
```

#### Créer une stratégie
```json
{
    "type": "strategy.create",
    "payload": {
        "page_id": "page-uuid",
        "id": "strategy-uuid",
        "name": "Butterfly SOFR",
        "client": "Client XYZ",
        "action": "Buy",
        "status": "En cours",
        "target_price": 0.05,
        "target_condition": "inferieur",
        "legs": "[{\"id\":\"leg-1\",\"ticker\":\"SFRH6C 98.00 COMDTY\",\"position\":\"long\",\"quantity\":1}]"
    }
}
```

#### Mettre à jour une stratégie
```json
{
    "type": "strategy.update",
    "payload": {
        "id": "strategy-uuid",
        "name": "Butterfly SOFR Updated",
        "client": "Client XYZ",
        "action": "Sell",
        "status": "Fait",
        "target_price": 0.03,
        "target_condition": "superieur",
        "legs": "[...]"
    }
}
```

#### Supprimer une stratégie
```json
{
    "type": "strategy.delete",
    "payload": {
        "id": "strategy-uuid"
    }
}
```

---

### Messages Serveur → Client

#### État initial (envoyé à la connexion)
```json
{
    "type": "initial_state",
    "payload": {
        "pages": [
            {
                "id": "page-uuid",
                "name": "Mes Stratégies",
                "owner_id": "user-uuid",
                "owner_name": "john",
                "is_owner": true,
                "can_edit": true
            }
        ],
        "strategies": [
            {
                "id": "strategy-uuid",
                "page_id": "page-uuid",
                "name": "Butterfly SOFR",
                "client": "Client XYZ",
                "action": "Buy",
                "status": "En cours",
                "target_price": 0.05,
                "target_condition": "inferieur",
                "legs": "[{\"id\":\"leg-1\",\"ticker\":\"SFRH6C 98.00 COMDTY\",\"position\":\"long\",\"quantity\":1}]"
            }
        ]
    }
}
```

#### Notification de création/update/delete
```json
{
    "type": "page",
    "payload": {
        "action": "created",  // ou "updated", "deleted"
        "data": { ... },      // données de la page (absent si deleted)
        "id": "page-uuid"     // présent si deleted
    }
}
```

```json
{
    "type": "strategy",
    "payload": {
        "action": "created",
        "data": { ... }
    }
}
```

#### Ping/Pong (keep-alive)
```json
// Serveur envoie:
{"type": "ping"}

// Client répond:
{"type": "pong"}
```

#### Erreur
```json
{
    "type": "error",
    "payload": {
        "message": "Page not found"
    }
}
```

---

## 📋 Format des Legs (JSON)

Les legs sont stockés comme une string JSON dans la colonne `strategies.legs`:

```json
[
    {
        "id": "leg-uuid-1",
        "ticker": "SFRH6C 98.00 COMDTY",
        "position": "long",
        "quantity": 1
    },
    {
        "id": "leg-uuid-2", 
        "ticker": "SFRH6C 98.125 COMDTY",
        "position": "short",
        "quantity": 2
    },
    {
        "id": "leg-uuid-3",
        "ticker": "SFRH6C 98.25 COMDTY",
        "position": "long",
        "quantity": 1
    }
]
```

**Champs:**
- `id` (string): UUID unique du leg
- `ticker` (string): Ticker Bloomberg (ex: "SFRH6C 98.00 COMDTY")
- `position` (string): "long" ou "short"
- `quantity` (int): Nombre de contrats (≥ 1)

---

## 🔒 Sécurité

1. **Tokens JWT** - Expiration recommandée: 24h
2. **Password Hashing** - Utiliser bcrypt ou argon2
3. **HTTPS** - Obligatoire en production
4. **WebSocket Auth** - Valider le token à chaque connexion
5. **Permissions** - Vérifier `can_edit` avant modification

---

## 🚀 Stack recommandée

- **Framework**: FastAPI (Python) ou Express (Node.js)
- **Base de données**: PostgreSQL ou SQLite
- **WebSocket**: Built-in FastAPI ou ws (Node.js)
- **Auth**: python-jose (JWT) ou jsonwebtoken

---

## 📦 Exemple FastAPI (structure)

```
backend/
├── main.py              # Point d'entrée FastAPI
├── database.py          # Configuration SQLAlchemy
├── models.py            # Modèles ORM
├── schemas.py           # Pydantic schemas
├── auth.py              # JWT utilities
├── routers/
│   ├── auth.py          # /login, /register, /me
│   ├── pages.py         # /pages, /pages/{id}/permissions
│   ├── groups.py        # /groups
│   └── websocket.py     # /ws
└── requirements.txt
```
