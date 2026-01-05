"""
Script de test pour vérifier la connexion au serveur
"""
import asyncio
import sys
from src.services.auth_service import AuthService
from src.config import ALARM_SERVER_URL


async def test_server_connection():
    """Test la connexion au serveur"""
    print(f"🔍 Test de connexion à {ALARM_SERVER_URL}...")
    
    auth = AuthService(ALARM_SERVER_URL)
    
    # Test 1: Health check
    print("\n1️⃣ Test health check...")
    try:
        import httpx
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{ALARM_SERVER_URL}/health", timeout=5.0)
            if response.status_code == 200:
                print("   ✅ Serveur accessible")
            else:
                print(f"   ❌ Erreur {response.status_code}")
                return False
    except Exception as e:
        print(f"   ❌ Serveur inaccessible: {e}")
        return False
    
    # Test 2: Login (avec compte test)
    print("\n2️⃣ Test authentification...")
    username = "test_user"
    password = "test123"
    
    # Tenter de créer un compte
    print(f"   Création du compte {username}...")
    success = await auth.register(username, password)
    
    if success:
        print(f"   ✅ Compte créé et authentifié")
    else:
        # Le compte existe déjà, tenter login
        print(f"   Compte existe déjà, login...")
        success = await auth.login(username, password)
        if success:
            print(f"   ✅ Authentification réussie")
        else:
            print(f"   ❌ Échec authentification")
            return False
    
    # Test 3: WebSocket URL
    print("\n3️⃣ Test génération URL WebSocket...")
    try:
        ws_url = auth.get_ws_url()
        print(f"   ✅ URL WebSocket: {ws_url}")
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        return False
    
    print("\n✅ Tous les tests passés!")
    print(f"\n📝 Infos utilisateur:")
    print(f"   Username: {auth.user_info.get('username')}")
    print(f"   User ID: {auth.user_info.get('id')}")
    
    return True


def main():
    print("=" * 60)
    print("Test de connexion serveur Bloomberg Alarm")
    print("=" * 60)
    
    try:
        result = asyncio.run(test_server_connection())
        
        if result:
            print("\n✨ Configuration serveur OK!")
            print("Vous pouvez lancer l'application: python main.py")
            sys.exit(0)
        else:
            print("\n⚠️  Problèmes de connexion détectés")
            print("Vérifiez que le serveur est démarré:")
            print("  cd alarm-server")
            print("  uvicorn app.main:app --reload --port 8080")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrompu")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
