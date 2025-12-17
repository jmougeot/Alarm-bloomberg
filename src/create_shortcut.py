"""Script pour créer les raccourcis Windows"""
import os
import sys

def create_shortcuts():
    try:
        import winshell
        from win32com.client import Dispatch
    except ImportError:
        print("    [!] winshell/pywin32 non installe")
        return False
    
    # On est dans src/, remonter à la racine du projet
    script_dir = os.path.dirname(os.path.abspath(__file__))
    app_dir = os.path.dirname(script_dir)
    
    # Trouver pythonw.exe
    python_dir = os.path.dirname(sys.executable)
    pythonw = os.path.join(python_dir, "pythonw.exe")
    if not os.path.exists(pythonw):
        pythonw = sys.executable
    
    main_script = os.path.join(app_dir, "main.py")
    icon_path = os.path.join(app_dir, "assets", "icon.ico")
    
    print(f"    App: {app_dir}")
    print(f"    Main: {main_script} (exists: {os.path.exists(main_script)})")
    print(f"    Icon: {icon_path} (exists: {os.path.exists(icon_path)})")
    
    try:
        shell = Dispatch("WScript.Shell")
        
        # Raccourci Bureau
        desktop = winshell.desktop()
        shortcut_path = os.path.join(desktop, "Strategy Monitor.lnk")
        print(f"    Desktop: {shortcut_path}")
        
        shortcut = shell.CreateShortCut(shortcut_path)
        shortcut.Targetpath = pythonw
        shortcut.Arguments = f'"{main_script}"'
        shortcut.WorkingDirectory = app_dir
        shortcut.Description = "Strategy Price Monitor"
        if os.path.exists(icon_path):
            shortcut.IconLocation = f"{icon_path},0"
        shortcut.save()
        print("    [OK] Raccourci Bureau cree")
        
        # Raccourci Menu Demarrer
        start_menu = winshell.start_menu()
        shortcut_path2 = os.path.join(start_menu, "Programs", "Strategy Monitor.lnk")
        shortcut2 = shell.CreateShortCut(shortcut_path2)
        shortcut2.Targetpath = pythonw
        shortcut2.Arguments = f'"{main_script}"'
        shortcut2.WorkingDirectory = app_dir
        shortcut2.Description = "Strategy Price Monitor"
        if os.path.exists(icon_path):
            shortcut2.IconLocation = f"{icon_path},0"
        shortcut2.save()
        print("    [OK] Raccourci Menu Demarrer cree")
        
        return True
    except Exception as e:
        print(f"    [!] Erreur: {e}")
        return False

if __name__ == "__main__":
    create_shortcuts()
