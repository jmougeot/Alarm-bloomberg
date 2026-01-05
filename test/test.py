from PySide6.QtWidgets import QApplication, QLabel
import sys

app = QApplication(sys.argv)
label = QLabel("Qt OK PySide6")
label.show()
sys.exit(app.exec())
