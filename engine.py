import numpy as np
import os
import re
import sounddevice as sd
import queue
import threading
import time
from pywhispercpp.model import Model
from config_loader import config
from logger import SpeechLogger

class SpeechEngine:
    def __init__(self, callback=None, partial_callback=None):
        model_rel_path = config.get("stt.model_path", "models/ggml-base.en.bin")
        self.model_path = os.path.join(config.base_path, model_rel_path)
        self.language = config.get("stt.language", "en")
        self.sample_rate = config.get("stt.sample_rate", 16000)
        self.pause_amount = config.get("stt.pause_amount", 700) / 1000.0
        self.vad_threshold = config.get("stt.vad_threshold", 0.01)
        self.beam_size = config.get("stt.beam_size", 5)
        self.streaming_interval = config.get("stt.streaming_interval", 100) / 1000.0
        self.clear_on_pause = config.get("stt.clear_on_pause", False)
        self.show_live_words = config.get("display.show_live_words", True)
        
        self.lock = threading.Lock()
        self.processing = False
        
        self.callback = callback
        self.partial_callback = partial_callback
        self.logger = SpeechLogger(
            history_file=config.get("output.history_file", "speech_history.txt"),
            latest_file=config.get("output.latest_file", "latest_speech.txt")
        )
        
        self.audio_queue = queue.Queue()
        self.running = False
        self.model = None
        self.paused = False
        
        # Audio buffer for processing
        self.audio_buffer = []
        self.is_speaking = False
        self.last_audio_time = time.time()
        self.last_partial_time = time.time()

    def load_model(self):
        print(f"Loading Whisper model from {self.model_path}...")
        # Disable internal printing to avoid terminal clutter and "over 100%" progress issues
        self.model = Model(self.model_path, n_threads=4, print_progress=False, print_realtime=False)
        print("Model loaded.")

    def _audio_callback(self, indata, frames, time_info, status):
        if status:
            print(f"Audio status: {status}")
        self.audio_queue.put(indata.copy())

    def run(self):
        if not self.model:
            self.load_model()
            
        self.running = True
        self.is_speaking = False
        self.last_partial_time = time.time()
        
        # Start audio stream
        with sd.InputStream(samplerate=self.sample_rate, channels=1, 
                          callback=self._audio_callback, blocksize=int(self.sample_rate * 0.1)):
            print("Microphone active. Listening...")
            
            while self.running:
                try:
                    # Get audio data from queue
                    data = self.audio_queue.get(timeout=1.0)
                    self.audio_buffer.append(data)
                    
                    # Detect voice activity (simple energy based)
                    energy = np.linalg.norm(data) / np.sqrt(len(data))
                    # print(f"DEBUG: Energy={energy:.4f} (Threshold={self.vad_threshold})")
                    
                    if energy > self.vad_threshold: 
                        if not self.is_speaking:
                            # Instant feedback: clear previous line when new speech starts
                            if self.partial_callback:
                                self.partial_callback("")
                        self.is_speaking = True
                        self.last_audio_time = time.time()
                    else:
                        if self.is_speaking and (time.time() - self.last_audio_time > self.pause_amount):
                            # Silence detected after speech, process final buffer
                            if not self.paused:
                                self.process_buffer(is_partial=False)
                                # Clear UI if requested
                                if self.clear_on_pause and self.partial_callback:
                                    self.partial_callback("")
                            else:
                                self.audio_buffer = [] # Clear buffer if paused
                            self.is_speaking = False
                    
                    # Live feedback: transcribe while speaking
                    if self.is_speaking and not self.paused and self.partial_callback and self.show_live_words:
                        if time.time() - self.last_partial_time > self.streaming_interval:
                            self.process_buffer(is_partial=True)
                            self.last_partial_time = time.time()
                            
                except queue.Empty:
                    continue
                except Exception as e:
                    print(f"Engine error: {e}")
                    break

    def process_buffer(self, is_partial=False):
        with self.lock:
            if not self.audio_buffer:
                return
            if self.processing:
                return
            self.processing = True
            
        try:
            # Concatenate buffered audio
            audio_to_process = np.concatenate(self.audio_buffer).flatten()
            
            if len(audio_to_process) < self.sample_rate * 0.05: # Further reduced for real-time word-by-word
                self.processing = False
                return

            if not is_partial:
                self.audio_buffer = [] # Clear buffer only on final
            
            # Normalization
            max_val = np.abs(audio_to_process).max()
            if max_val > 0:
                audio_to_process = audio_to_process / max_val * 0.9
            
            # Core STT processing
            if is_partial:
                # Basic greedy for speed in live feedback
                segments = self.model.transcribe(audio_to_process, 
                                               language=self.language, 
                                               single_segment=True,
                                               temperature=0.0)
            else:
                # High accuracy for final result
                segments = self.model.transcribe(audio_to_process, 
                                               language=self.language, 
                                               single_segment=True,
                                               temperature=0.0,
                                               greedy={"best_of": 5})
            
            text = "".join([s.text for s in segments]).strip()
            # if text:
            #     print(f"DEBUG: Raw Transcription='{text}'") 
            
            # Filter out common Whisper hallucinations on silence (dots, dashes, etc.)
            # only clear if there are NO alphanumeric characters
            if text and (re.match(r'^[ ._\-…]+$', text) or not any(c.isalnum() for c in text)):
                text = ""
            
            if text:
                if is_partial:
                    if self.partial_callback:
                        self.partial_callback(text)
                else:
                    print(f"Final Recognized: {text}")
                    self.logger.log_speech(text)
                    if self.callback:
                        self.callback(text)
        except Exception as e:
            print(f"Transcription error: {e}")
        finally:
            self.processing = False

    def stop(self):
        self.running = False
        # Process remaining buffer if it contains enough audio
        if self.audio_buffer:
            print("Cleaning up engine. Processing final buffer...")
            self.process_buffer()

    def toggle_pause(self):
        self.paused = not self.paused
        state = "PAUSED" if self.paused else "RESUMED"
        print(f"Engine {state}")
        return self.paused

if __name__ == "__main__":
    # Test engine standalone
    def on_text(text):
        print(f"UI Callback: {text}")
        
    engine = SpeechEngine(callback=on_text)
    try:
        engine.run()
    except KeyboardInterrupt:
        engine.stop()
