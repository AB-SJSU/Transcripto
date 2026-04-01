import whisper

print("Loading model...")
model = whisper.load_model("base")
print("Model loaded successfully!")

print("Device:", model.device)

