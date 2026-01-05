"""
Gestion des alertes (son, popup, état des alertes)
"""
import sys
from typing import TYPE_CHECKING

if sys.platform == 'win32':
    import winsound
else:
    import os

if TYPE_CHECKING:
    from ..ui.main_window import MainWindow


class AlertHandler:
    """Gère les alertes et notifications"""
    
    def __init__(self, main_window: 'MainWindow'):
        self.window = main_window
        self._alerted_strategies: set[str] = set()
    
    def on_target_reached(self, strategy_id: str):
        """Événement déclenché quand une cible est atteinte"""
        from ..models.strategy import TargetCondition
        
        # Éviter de spammer les alertes
        if strategy_id in self._alerted_strategies:
            return
        
        if strategy_id in self.window.strategies:
            strategy = self.window.strategies[strategy_id]
            self._alerted_strategies.add(strategy_id)
            
            current_price = strategy.calculate_strategy_price()
            is_inferior = strategy.target_condition == TargetCondition.INFERIEUR
            
            # Jouer le son d'alerte
            self.play_alert_sound()
            
            # Afficher le popup
            self.show_alert_popup(strategy.name, current_price, strategy.target_price, is_inferior)  # type: ignore
            
            condition_text = "inférieur" if is_inferior else "supérieur"
            self.window.statusbar.showMessage(
                f"🚨 ALARME! '{strategy.name}' - Prix {condition_text} à {strategy.target_price:.4f}!", 
                5000
            )
    
    def on_target_left(self, strategy_id: str):
        """Appelé quand le prix sort de la zone cible"""
        self._alerted_strategies.discard(strategy_id)
    
    def play_alert_sound(self):
        """Joue un son d'alerte"""
        if sys.platform == 'win32':
            winsound.Beep(1000, 200)  # Fréquence 1000Hz, durée 200ms
            winsound.Beep(1500, 200)  # Fréquence 1500Hz
        else:
            try:
                if sys.platform == 'darwin':  # macOS
                    os.system('afplay /System/Library/Sounds/Glass.aiff')
                else:  # Linux
                    os.system('paplay /usr/share/sounds/freedesktop/stereo/complete.oga 2>/dev/null || aplay /usr/share/sounds/alsa/Noise.wav 2>/dev/null')
            except Exception:
                pass  # Silencieusement ignorer les erreurs audio
    
    def show_alert_popup(self, strategy_name: str, current_price: float, target_price: float, is_inferior: bool):
        """Affiche un popup d'alerte"""
        from ..ui.alert_popup import AlertPopup
        popup = AlertPopup(strategy_name, current_price, target_price, is_inferior, self.window)
        popup.show()
