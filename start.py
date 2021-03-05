from PyQt5.QtWidgets import QApplication
import sys
from views import StartWindow

app = QApplication(sys.argv)
start_window = StartWindow()
start_window.setWindowTitle("Main Window")
start_window.show()
# app.aboutToQuit.connect(app.deleteLater)
app.exit(app.exec_())