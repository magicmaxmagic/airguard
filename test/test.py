"""
Test simple du microphone (AirGuard)
→ Liste tous les périphériques d'entrée/sortie
→ Sélectionne le bon micro (MacBook Air Microphone)
→ Mesure le volume RMS sur quelques secondes
"""

import sounddevice as sd
import numpy as np
import time


def list_audio_devices():
    """Affiche la liste des périphériques disponibles"""
    print("🔍 Périphériques audio détectés :")
    devices = sd.query_devices()
    for i, d in enumerate(devices):
        print(f"{i:>2} | {d['name']:<30} (in:{d['max_input_channels']}, out:{d['max_output_channels']})")
    print()
    return devices


def select_mac_microphone():
    """Retourne l’index du MacBook Air Microphone, sinon le premier input dispo"""
    devices = sd.query_devices()
    mic_index = None

    # Priorité au micro interne
    for i, d in enumerate(devices):
        if "MacBook Air Microphone" in d["name"]:
            mic_index = i
            break

    # Sinon, premier device avec entrée audio
    if mic_index is None:
        for i, d in enumerate(devices):
            if d["max_input_channels"] > 0:
                mic_index = i
                break

    if mic_index is None:
        raise RuntimeError("Aucun périphérique d'entrée audio valide trouvé.")
    
    print(f"🎤 Micro sélectionné : {devices[mic_index]['name']} (index {mic_index})\n")
    return mic_index


def measure_volume(mic_index, duration=5):
    """Mesure le volume RMS pendant quelques secondes"""
    samplerate = 16000
    channels = 1
    frames = int(duration * samplerate)

    print(f"🎧 Enregistrement pendant {duration}s... Parle ou fais un bruit 📣")
    time.sleep(1)

    with sd.InputStream(device=mic_index, channels=channels, samplerate=samplerate) as stream:
        data, _ = stream.read(frames)

    volume = float(np.sqrt(np.mean(np.square(data))))
    print(f"\n📊 Niveau sonore moyen : {volume:.4f}")
    if volume < 0.02:
        print("🔇 Très faible signal — le micro ne capte rien ou est bloqué.")
    elif volume < 0.2:
        print("🙂 Niveau sonore normal (silence / faible bruit ambiant).")
    else:
        print("🔊 Son détecté (parle, musique ou bruit élevé).")


def main():
    list_audio_devices()
    mic_index = select_mac_microphone()
    measure_volume(mic_index)


if __name__ == "__main__":
    main()