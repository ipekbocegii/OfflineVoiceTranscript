from pydub import AudioSegment

# Ses dosyasının yolunu buraya yaz
dosya = "perfGor.m4a"

# Ses dosyasını yükle
audio = AudioSegment.from_file(dosya)

# Ses uzunluğunu hesapla
sure_saniye = len(audio) / 1000
print(f"Ses dosyası uzunluğu: {sure_saniye:.2f} saniye")
