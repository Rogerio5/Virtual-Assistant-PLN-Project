import sounddevice as sd
from scipy.io.wavfile import write
import os
from faster_whisper import WhisperModel
from gtts import gTTS
from openai import OpenAI

# Configurações
fs = 44100  # taxa de amostragem (Hz)
duration = 5  # duração fixa de gravação em segundos

# Inicializa cliente OpenAI (usa chave do .env)
client = OpenAI()

# Pasta de saída
os.makedirs("audio_samples", exist_ok=True)

def gravar_audio(filename: str, phrase: str):
    print(f"\n🎙️ Gravando {filename}...")
    print(f"👉 Fale a frase: {phrase}")
    audio = sd.rec(int(duration * fs), samplerate=fs, channels=1)
    sd.wait()
    filepath = f"audio_samples/{filename}"
    write(filepath, fs, audio)
    print(f"✅ Arquivo salvo: {filepath}")
    return filepath

def transcrever_audio(filepath: str):
    print("\n🧠 Transcrevendo com Whisper...")
    model = WhisperModel("base", device="cpu")
    segments, info = model.transcribe(filepath)
    transcription = " ".join([seg.text for seg in segments])
    print(f"📝 Transcrição: {transcription}")
    return transcription

def conversar_com_chatgpt(texto: str):
    print("\n🤖 Enviando para ChatGPT...")
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": texto}]
    )
    # Garantir que nunca seja None
    resposta = response.choices[0].message.content or ""
    print(f"💬 Resposta do ChatGPT: {resposta}")
    return resposta

def responder_por_voz(texto: str, idioma: str = "pt"):
    if not texto:
        print("❌ Nenhum texto recebido para sintetizar.")
        return
    print("\n🔊 Convertendo resposta em voz...")
    tts = gTTS(text=texto, lang=idioma)
    tts.save("out.mp3")
    print("✅ Resposta falada salva em out.mp3")

if __name__ == "__main__":
    # Exemplo: gravar uma frase de teste
    frase = "Qual é a capital da França?"
    arquivo = gravar_audio("teste.wav", frase)
    texto = transcrever_audio(arquivo)
    resposta = conversar_com_chatgpt(texto)
    responder_por_voz(resposta)
