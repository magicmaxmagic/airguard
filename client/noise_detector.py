import pyaudio
import numpy as np
import requests
import time
import socket
from datetime import datetime

# Configuration
API_URL = "http://localhost:8000/events/"
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
THRESHOLD = 2000  # Noise threshold
DEVICE_ID = socket.gethostname()
LOCATION = "living_room"


def get_noise_level():
    """Capture audio and calculate noise level."""
    p = pyaudio.PyAudio()
    
    try:
        stream = p.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            input=True,
            frames_per_buffer=CHUNK
        )
        
        data = stream.read(CHUNK)
        stream.stop_stream()
        stream.close()
        
        # Convert to numpy array and calculate RMS
        audio_data = np.frombuffer(data, dtype=np.int16)
        rms = np.sqrt(np.mean(audio_data**2))
        
        return rms
    
    except Exception as e:
        print(f"Error capturing audio: {e}")
        return 0
    finally:
        p.terminate()


def send_event(noise_level):
    """Send noise event to backend API."""
    try:
        payload = {
            "noise_level": float(noise_level),
            "location": LOCATION,
            "device_id": DEVICE_ID
        }
        response = requests.post(API_URL, json=payload)
        if response.status_code == 200:
            print(f"Event sent successfully: {noise_level:.2f}")
        else:
            print(f"Failed to send event: {response.status_code}")
    except Exception as e:
        print(f"Error sending event: {e}")


def main():
    """Main loop to monitor noise levels."""
    print(f"Starting noise detector on {DEVICE_ID} at {LOCATION}")
    print(f"Threshold: {THRESHOLD}")
    print(f"Sending events to: {API_URL}")
    
    while True:
        try:
            noise_level = get_noise_level()
            print(f"Current noise level: {noise_level:.2f}", end="\r")
            
            if noise_level > THRESHOLD:
                print(f"\nAlert! High noise detected: {noise_level:.2f}")
                send_event(noise_level)
            
            time.sleep(1)
        
        except KeyboardInterrupt:
            print("\nStopping noise detector...")
            break
        except Exception as e:
            print(f"\nError in main loop: {e}")
            time.sleep(5)


if __name__ == "__main__":
    main()
