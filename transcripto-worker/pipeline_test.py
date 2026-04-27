import whisper
import subprocess

print("Loading model...")
model = whisper.load_model("base")
print("Model loaded!")

input_audio = "test.wav"
clean_audio = "clean.wav"

print("Normalizing audio...")
subprocess.run([
    "ffmpeg", "-y",
    "-i", input_audio,
    "-ar", "16000",
    "-ac", "1",
    clean_audio
])

print("Transcribing...")
result = model.transcribe(clean_audio)

print("\n=== TRANSCRIPTION ===")
print(result["text"])
