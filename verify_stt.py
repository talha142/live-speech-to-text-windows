import sys
import os
from engine import SpeechEngine
import numpy as np

def test_stt_load():
    print("Testing STT engine initialization...")
    try:
        engine = SpeechEngine()
        engine.load_model()
        print("SUCCESS: Engine and model loaded.")
        
        # Test transcription with silence
        print("Testing transcription with dummy audio...")
        dummy_audio = np.zeros(16000, dtype=np.float32)
        # Use a dummy segment for testing transcribe if it returns something
        segments = engine.model.transcribe(dummy_audio, single_segment=True)
        print(f"SUCCESS: Transcription call returned {len(list(segments))} segments.")
        
        return True
    except Exception as e:
        print(f"FAILURE: {e}")
        return False

if __name__ == "__main__":
    if test_stt_load():
        print("\nVerification passed!")
        sys.exit(0)
    else:
        print("\nVerification failed!")
        sys.exit(1)
