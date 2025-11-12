"""
AirGuard - Noise Detector (version 1.2 - Architecture orientée objet)
Détection de bruit locale, auto-calibration, hystérésis et envoi d’alertes HTTP
"""

import os
import sys
import time
import requests
import numpy as np
from datetime import datetime
from dataclasses import dataclass
from dotenv import load_dotenv
import sounddevice as sd
import logging
import json


# ==========================
# == CONFIGURATION GLOBALE ==
# ==========================

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("AirGuard")


@dataclass
class Config:
    api_url: str
    debounce: float
    device_id: str
    calibration_duration: int
    recalibration_interval: int
    smoothing_alpha: float

    @staticmethod
    def load():
        load_dotenv()

        defaults = {
            "api_url": os.getenv("AIRGUARD_API_URL", "http://127.0.0.1:8000/events/"),
            "debounce": float(os.getenv("DEBOUNCE", "10")),
            "device_id": os.getenv("DEVICE_ID", "PC-LOCAL"),
            "calibration_duration": 5,
            "recalibration_interval": 300,  # 5 minutes
            "smoothing_alpha": 0.3,
        }

        # surcharge via config.json
        if os.path.exists("config.json"):
            try:
                with open("config.json", "r") as f:
                    cfg_file = json.load(f)
                defaults.update(cfg_file)
                logger.info("⚙️ Configuration chargée depuis config.json")
            except Exception as e:
                logger.warning(f"Impossible de lire config.json : {e}")

        return Config(**defaults)


@dataclass
class Thresholds:
    th_on: float
    th_off: float


# ==========================
# == MODULE AUDIO ==
# ==========================

class AudioHandler:
    """Gère la lecture audio continue via sounddevice."""

    def __init__(self, samplerate=16000, channels=1):
        self.samplerate = samplerate
        self.channels = channels
        self.mic_index = self._get_microphone_index()
        self.stream = self._init_stream()
        self.silent_count = 0

    def _get_microphone_index(self):
        """Sélectionne le micro interne par défaut (priorité MacBook Air Microphone)."""
        devices = sd.query_devices()
        mic_index = None

        for i, d in enumerate(devices):
            if "MacBook Air Microphone" in d["name"] and d["max_input_channels"] > 0:
                mic_index = i
                break

        if mic_index is None:
            for i, d in enumerate(devices):
                if d["max_input_channels"] > 0:
                    mic_index = i
                    break

        if mic_index is None:
            raise RuntimeError("Aucun périphérique d’entrée audio valide trouvé.")

        info = devices[mic_index]
        logger.info(f"🎤 Micro utilisé : {info['name']} (index {mic_index}, in:{info['max_input_channels']})")
        return mic_index

    def _init_stream(self):
        """Initialise un flux audio persistant."""
        try:
            stream = sd.InputStream(
                device=self.mic_index,
                channels=self.channels,
                samplerate=self.samplerate,
                blocksize=1024,
                latency="low",
                dtype="float32"
            )
            stream.start()
            time.sleep(0.2)
            _ = stream.read(512)  # purge du buffer initial
            return stream
        except Exception as e:
            raise RuntimeError(f"Impossible d'initialiser le flux audio : {e}")

    def read_rms(self, duration=1.0):
        """Retourne le RMS sur un intervalle donné."""
        frames = int(duration * self.samplerate)
        try:
            data, _ = self.stream.read(frames)
        except sd.PortAudioError:
            logger.warning("Overflow audio détecté → flux relancé.")
            self.stream.stop()
            self.stream.start()
            return 0.0

        rms = float(np.sqrt(np.mean(np.square(data))))
        if rms < 1e-10:
            self.silent_count += 1
            if self.silent_count > 5:
                logger.error("⚠️  Micro inactif depuis 5 cycles.")
        else:
            self.silent_count = 0
        return rms


# ==========================
# == MODULE DÉTECTION ==
# ==========================

class NoiseDetector:
    """Effectue la calibration, le suivi du bruit et l’envoi d’alertes."""

    def __init__(self, config: Config, audio: AudioHandler):
        self.config = config
        self.audio = audio
        self.thresholds = None
        self.armed = False
        self.last_alert = 0.0
        self.prev_level_db = -100.0
        self.last_calibration = 0.0

    @staticmethod
    def rms_to_db(rms: float) -> float:
        rms = max(rms, 1e-10)
        return 20 * np.log10(rms) + 94

    def smooth_level(self, new_level):
        alpha = self.config.smoothing_alpha
        self.prev_level_db = alpha * new_level + (1 - alpha) * self.prev_level_db
        return self.prev_level_db
    
    def calibrate(self, duration=None) -> Thresholds:
        """Calibre les seuils d’alerte à partir du bruit ambiant."""
        duration = duration or self.config.calibration_duration
        logger.info(f"🧭 Calibration du bruit ambiant pendant {duration}s...")
        samples = []
        start_time = time.time()
        while time.time() - start_time < duration:
            loop_start = time.time()
            rms = self.audio.read_rms(0.5)
            samples.append(rms)
            elapsed = time.time() - loop_start
            time.sleep(max(0, 0.5 - elapsed))
        self.last_calibration = time.time()
        mean_rms = np.mean(samples)
        mean_db = self.rms_to_db(mean_rms)
        th_off = mean_db + 3
        th_on = mean_db + 10
        logger.info(f"📊 Niveau ambiant : {mean_db:.1f} dB → Seuils : ON={th_on:.1f} / OFF={th_off:.1f}")
        self.thresholds = Thresholds(th_on=th_on, th_off=th_off)
        self.prev_level_db = mean_db
        return self.thresholds
    
    def auto_recalibrate(self):
        """Recalibre automatiquement si le délai est dépassé."""
        if time.time() - self.last_calibration > self.config.recalibration_interval:
            logger.info("🔁 Recalibration automatique en cours...")
            self.calibrate(self.config.calibration_duration)
        logger.info(f"🔧 Seuils mis à jour : ON={self.thresholds.th_on:.1f} / OFF={self.thresholds.th_off:.1f}")

    def should_alert(self, level_db: float) -> bool:
        """Retourne True si le niveau dépasse le seuil (hystérésis)."""
        if not self.armed and level_db > self.thresholds.th_on:
            self.armed = True
            return True
        elif self.armed and level_db < self.thresholds.th_off:
            self.armed = False
        return False

    def send_alert(self, level_db: float):
        """Envoie une alerte HTTP."""
        payload = {
            "device_id": self.config.device_id,
            "type": "noise",
            "value": float(level_db),
            "timestamp": datetime.utcnow().isoformat(),
        }
        try:
            r = requests.post(self.config.api_url, json=payload, timeout=3)
            logger.info(f"🚨 Alerte envoyée ({r.status_code}) - {level_db:.1f} dB")
        except Exception as e:
            logger.error(f"Erreur d’envoi : {e}")

    def run(self):
        """Boucle principale du détecteur."""
        self.calibrate()

        logger.info("🎧 AirGuard Noise Detector running...")
        logger.info(f"→ Backend : {self.config.api_url}")
        logger.info(f"→ Délai minimum entre alertes : {self.config.debounce}s")

        try:
            while True:
                cycle_start = time.time()
                self.auto_recalibrate()
                rms = self.audio.read_rms(1.0)
                level_db = self.rms_to_db(rms)
                level_db = self.smooth_level(level_db)
                logger.info(f"Niveau sonore : {level_db:.1f} dB")

                if level_db < -100:
                    logger.warning("Micro non détecté ou signal inexistant.")

                trigger = self.should_alert(level_db)
                now = time.time()

                if trigger and (now - self.last_alert > self.config.debounce):
                    self.last_alert = now
                    self.send_alert(level_db)

                elapsed = time.time() - cycle_start
                time.sleep(max(0, 1.0 - elapsed))

        except KeyboardInterrupt:
            logger.info("🛑 Arrêt manuel du détecteur.")
        except Exception as e:
            logger.error(f"❌ Erreur fatale : {e}")
            raise


# ==========================
# == LANCEMENT ==
# ==========================
if __name__ == "__main__":
    cfg = Config.load()

    # Mode calibration-only
    if "--calibrate-only" in sys.argv:
        audio = AudioHandler()
        detector = NoiseDetector(cfg, audio)
        detector.calibrate(cfg.calibration_duration)
        logger.info("✅ Calibration terminée. Fin du mode --calibrate-only.")
        sys.exit(0)

    try:
        audio = AudioHandler()
        detector = NoiseDetector(cfg, audio)
        detector.run()
    except Exception as e:
        logger.error(f"❌ Échec du démarrage : {e}")