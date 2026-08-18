import sys
import threading
import keyboard
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout
from PySide6.QtCore import Qt, Signal, QObject
from PySide6.QtGui import QMouseEvent

from config_loader import config
from engine import SpeechEngine
from ui_components import RetroTerminalWidget

class Communicate(QObject):
    text_received = Signal(str)
    partial_text_received = Signal(str)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("Retro STT Terminal")
        self.setWindowTitle("Retro STT Terminal")
        
        flags = Qt.WindowStaysOnTopHint
        if not config.get("window.framed", False):
            flags |= Qt.FramelessWindowHint
            self.setAttribute(Qt.WA_TranslucentBackground)
        
        self.setWindowFlags(flags)
        
        # Size from config
        width = config.get("window.width", 600)
        height = config.get("window.height", 200)
        self.resize(width, height)
        
        # Central Widget
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        # Terminal Widget
        self.terminal = RetroTerminalWidget(config)
        self.layout.addWidget(self.terminal)
        
        # Interaction
        self._old_pos = None
        
        # STT Engine Setup
        self.comm = Communicate()
        self.comm.text_received.connect(self.terminal.update_text)
        self.comm.partial_text_received.connect(self.terminal.update_live_text)
        self.terminal.minimize_requested.connect(self.showMinimized)
        self.terminal.maximize_requested.connect(self.toggle_maximize)
        self.terminal.close_requested.connect(self.close)
        
        self.engine = SpeechEngine(callback=self.handle_stt, partial_callback=self.handle_partial_stt)
        self.engine_thread = threading.Thread(target=self.engine.run, daemon=True)
        self.engine_thread.start()
        
        # Setup Hotkey
        self.hotkey = config.get("window.hotkey", "f8")
        try:
            keyboard.add_hotkey(self.hotkey, self.toggle_engine)
            print(f"Global hotkey '{self.hotkey}' registered.")
        except Exception as e:
            print(f"Failed to register hotkey: {e}")

    def toggle_engine(self):
        is_paused = self.engine.toggle_pause()
        # Optionally update UI to show status
        status = "OFF" if is_paused else "ON"
        print(f"STT Listener: {status}")

    def toggle_maximize(self):
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()

    def handle_stt(self, text):
        self.comm.text_received.emit(text)

    def handle_partial_stt(self, text):
        self.comm.partial_text_received.emit(text)

    # Make window movable
    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self._old_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event: QMouseEvent):
        if self._old_pos is not None:
            delta = event.globalPosition().toPoint() - self._old_pos
            self.move(self.pos() + delta)
            self._old_pos = event.globalPosition().toPoint()

    def mouseReleaseEvent(self, event: QMouseEvent):
        self._old_pos = None

    def closeEvent(self, event):
        self.engine.stop()
        super().closeEvent(event)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
