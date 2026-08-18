from PySide6.QtWidgets import QLabel, QGraphicsDropShadowEffect, QFrame, QVBoxLayout, QWidget, QHBoxLayout, QPushButton
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QFont, QColor

class GlowingLabel(QLabel):
    def __init__(self, text="", font_size=18, color="#00ffea", glow_strength=15, typing_speed=0, cursor_blink_ms=500, alignment=Qt.AlignCenter, parent=None):
        super().__init__(text, parent)
        
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.typing_speed = typing_speed
        self.full_text = ""
        self.current_text = ""
        self.show_cursor = True
        self.cursor_state = True
        
        # Setup Font
        font = QFont("Consolas", font_size)
        font.setStyleStrategy(QFont.PreferAntialias)
        self.setFont(font)
        
        # Setup Color
        self.setStyleSheet(f"color: {color};")
        
        # Setup Glow Effect
        self.glow = QGraphicsDropShadowEffect(self)
        self.glow.setBlurRadius(glow_strength)
        self.glow.setColor(QColor(color))
        self.glow.setOffset(0, 0)
        self.setGraphicsEffect(self.glow)
        
        self.setAlignment(alignment)
        
        # Typing Timer
        self.typing_timer = QTimer(self)
        self.typing_timer.timeout.connect(self._type_next_char)
        
        # Cursor Timer
        self.cursor_timer = QTimer(self)
        self.cursor_timer.timeout.connect(self._toggle_cursor)
        self.cursor_timer.start(cursor_blink_ms)

    def setText(self, text):
        if not text:
            self.full_text = ""
            self.current_text = ""
            self.typing_timer.stop()
            self._update_display()
            return

        if self.typing_speed > 0:
            # OPTIMIZATION: If the new text is significantly longer than current, catch up faster
            # to avoid lagging behind live audio
            if len(text) - len(self.current_text) > 10:
                self.current_text = text[:-5] if len(text) > 5 else "" # Jump ahead but keep a bit of typing feel
            
            if self.full_text and text.startswith(self.full_text):
                self.full_text = text
                if not self.typing_timer.isActive():
                    self.typing_timer.start(self.typing_speed)
            else:
                self.full_text = text
                # If the text is a complete replacement (not a continuation), 
                # jump to it immediately for live feel
                self.current_text = text 
                self._update_display()
                if self.typing_speed > 0:
                    self.typing_timer.start(self.typing_speed)
        else:
            self.full_text = text
            self.current_text = text
            self._update_display()

    def _type_next_char(self):
        if len(self.current_text) < len(self.full_text):
            self.current_text += self.full_text[len(self.current_text)]
            self._update_display()
        else:
            self.typing_timer.stop()

    def _toggle_cursor(self):
        self.cursor_state = not self.cursor_state
        self._update_display()

    def _update_display(self):
        cursor_char = "_" if self.cursor_state else " "
        super().setText(self.current_text + cursor_char)

class RetroTerminalWidget(QFrame):
    minimize_requested = Signal()
    maximize_requested = Signal()
    close_requested = Signal()

    def __init__(self, config_data, parent=None):
        super().__init__(parent)
        self.config = config_data
        self.mode = self.config.get("output.mode", "live")
        
        self.setup_ui()
        
    def setup_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 5, 10, 15)
        self.layout.setSpacing(5)
        
        # Header for window controls
        self.header_layout = QHBoxLayout()
        self.header_layout.setSpacing(2)
        self.header_layout.addStretch()
        
        btn_style = """
            QPushButton {
                background-color: transparent;
                color: %color%;
                border: none;
                font-family: 'Consolas';
                font-size: 16px;
                padding: 2px 5px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.1);
                border-radius: 3px;
            }
        """.replace("%color%", self.config.get("display.text_color", "#00ffea"))

        self.btn_min = QPushButton("—")
        self.btn_min.setToolTip("Minimize")
        self.btn_min.setStyleSheet(btn_style)
        self.btn_min.clicked.connect(self.minimize_requested.emit)

        self.btn_max = QPushButton("□")
        self.btn_max.setToolTip("Maximize/Restore")
        self.btn_max.setStyleSheet(btn_style)
        self.btn_max.clicked.connect(self.maximize_requested.emit)
        
        self.btn_close = QPushButton("×")
        self.btn_close.setToolTip("Close")
        self.btn_close.setStyleSheet(btn_style)
        self.btn_close.clicked.connect(self.close_requested.emit)
        
        self.header_layout.addWidget(self.btn_min)
        self.header_layout.addWidget(self.btn_max)
        self.header_layout.addWidget(self.btn_close)
        self.layout.addLayout(self.header_layout)

        from logger import SpeechLogger
        self.logger = SpeechLogger(
            history_file=self.config.get("output.history_file", "speech_history.txt"),
            latest_file=self.config.get("output.latest_file", "latest_speech.txt")
        )

        # We'll use a container for labels
        self.labels_container = QWidget()
        self.labels_layout = QVBoxLayout(self.labels_container)
        self.layout.addWidget(self.labels_container)
        
        font_size = self.config.get("display.font_size", 18)
        color = self.config.get("display.text_color", "#00ffea")
        glow = self.config.get("display.glow_strength", 15)
        typing_speed = self.config.get("display.typing_speed_ms", 30)
        
        cursor_blink = self.config.get("display.cursor_blink_ms", 500)
        
        # Alignment mapping
        align_str = self.config.get("display.text_alignment", "center").lower()
        if align_str == "left":
            self.text_alignment = Qt.AlignLeft | Qt.AlignVCenter
        elif align_str == "right":
            self.text_alignment = Qt.AlignRight | Qt.AlignVCenter
        else:
            self.text_alignment = Qt.AlignCenter
            
        # Position mapping
        pos_str = self.config.get("display.text_position", "bottom-center").lower()
        self._apply_positioning(pos_str, color)
        
        if self.mode == "live":
            self.main_label = GlowingLabel("", font_size, color, glow, typing_speed, cursor_blink, self.text_alignment)
            self.labels_layout.addWidget(self.main_label)
        else:
            self.timeline_labels = []
            for _ in range(5):
                lbl = GlowingLabel("", font_size - 2, color, glow - 5, typing_speed, cursor_blink, self.text_alignment)
                self.timeline_labels.append(lbl)
                self.labels_layout.addWidget(lbl)
                
    def _apply_positioning(self, position, border_color="#00ffea"):
        # Remove old stretches
        for i in reversed(range(self.layout.count())):
            item = self.layout.itemAt(i)
            if item.spacerItem():
                self.layout.removeItem(item)

        if "top" in position:
            # Container is at top, add stretch below
            self.labels_layout.setAlignment(Qt.AlignTop)
            self.layout.addStretch(1)
        elif "bottom" in position:
            # Container is at bottom, insert stretch above (at index 1, after header)
            self.labels_layout.setAlignment(Qt.AlignBottom)
            self.layout.insertStretch(1, 1)
        else: # center
            self.labels_layout.setAlignment(Qt.AlignCenter)
            self.layout.insertStretch(1, 1)
            self.layout.addStretch(1)

        # Horizontal alignment within the container is handled by the label itself
        # but we can also align the labels_layout
        if "left" in position:
            self.labels_layout.setAlignment(Qt.AlignLeft | (Qt.AlignTop if "top" in position else Qt.AlignBottom if "bottom" in position else Qt.AlignVCenter))
        elif "right" in position:
            self.labels_layout.setAlignment(Qt.AlignRight | (Qt.AlignTop if "top" in position else Qt.AlignBottom if "bottom" in position else Qt.AlignVCenter))
        else:
            self.labels_layout.setAlignment(Qt.AlignHCenter | (Qt.AlignTop if "top" in position else Qt.AlignBottom if "bottom" in position else Qt.AlignVCenter))
        
        # Terminal Background Style
        opacity = self.config.get("display.background_opacity", 0.8)
        bg_color_hex = self.config.get("display.background_color", "#000000")
        
        # Convert hex to rgba
        qcolor = QColor(bg_color_hex)
        bg_color = f"rgba({qcolor.red()}, {qcolor.green()}, {qcolor.blue()}, {int(opacity * 255)})"
        
        self.setStyleSheet(f"""
            RetroTerminalWidget {{
                background-color: {bg_color};
                border: 2px solid {border_color};
                border-radius: 10px;
            }}
        """)
        
    def update_text(self, text):
        import datetime
        show_ts = self.config.get("display.show_timestamp", True)
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        
        display_text = f"[{ts}] {text}" if show_ts else text

        if self.mode == "live":
            # 1. Live Output Overwrite: Always show only the latest segment
            self.main_label.setText(display_text)
            
            # 3. Terminal Display File: Mirror terminal state
            self.logger.log_terminal(display_text)
            
            display_time = self.config.get("display.display_time_ms", 5000)
            if display_time > 0:
                # Use a specific capture of display_text to avoid clearing if new text arrives
                QTimer.singleShot(display_time, lambda: self._clear_if_match(display_text))
        else:
            # Shift labels up
            for i in range(len(self.timeline_labels) - 1):
                self.timeline_labels[i].setText(self.timeline_labels[i+1].text())
            self.timeline_labels[-1].setText(display_text)
            self.logger.log_terminal(display_text) # For timeline, maybe mirror the last line?

    def update_live_text(self, text):
        if self.mode == "live":
            # For live feedback, we don't usually show timestamp until finalized
            # But we want it to look consistent.
            self.main_label.setText(text)
            
            # If we are clearing, we also clear the terminal log file
            if not text:
                self.logger.clear_terminal()

    def _clear_if_match(self, text_to_clear):
        if self.mode == "live" and self.main_label.text() == text_to_clear:
            self.main_label.setText("")
            self.logger.clear_terminal()
