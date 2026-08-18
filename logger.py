import os
import datetime

class SpeechLogger:
    def __init__(self, history_file="speech_history.txt", latest_file="latest_speech.txt"):
        self.history_file = history_file
        self.latest_file = latest_file
        
        # Ensure files exist or clear them at start if needed
        # For history, we append. For latest, we overwrite.
        
    def log_speech(self, text):
        if not text.strip():
            return
            
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
        # 1. Full Timeline Storage (Append)
        with open(self.history_file, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {text}\n")
            
    def log_terminal(self, text):
        # 2. Terminal Display File (Overwrite)
        # This file exactly reflects what is shown in the terminal (live output)
        with open(self.latest_file, "w", encoding="utf-8") as f:
            f.write(text)

    def clear_terminal(self):
        with open(self.latest_file, "w", encoding="utf-8") as f:
            f.write("")
