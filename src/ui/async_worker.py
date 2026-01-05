"""
Worker pour exécuter des tâches async dans un thread séparé
"""
import asyncio
from typing import Callable
from PySide6.QtCore import QThread, Signal


class AsyncWorker(QThread):
    """Thread worker pour exécuter des coroutines async"""
    
    finished = Signal(object)  # Résultat de la coroutine
    error = Signal(str)  # Message d'erreur
    
    def __init__(self, coroutine_func: Callable, *args, **kwargs):
        super().__init__()
        self.coroutine_func = coroutine_func
        self.args = args
        self.kwargs = kwargs
        self.setTerminationEnabled(True)
    
    def run(self):
        """Exécute la coroutine dans un nouveau event loop"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(
                self.coroutine_func(*self.args, **self.kwargs)
            )
            loop.close()
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))
    
    def __del__(self):
        """Nettoyage lors de la destruction"""
        self.wait()
