import os


try:
    from local_config import FFMPEG_BIN_PATH as ffmpeg_bin

    if not os.path.isdir(ffmpeg_bin):
        print(f"UYARI: local_config'teki yol geçersiz. Genel PATH kullanılıyor.")
    else:
        # Yol geçerliyse, PATH'e ekle
        os.environ["PATH"] = ffmpeg_bin + os.pathsep + os.environ.get("PATH", "")
except ImportError:
    print("UYARI: local_config.py bulunamadı. FFmpeg'in sistem PATH'inizde yüklü olduğundan emin olun.")




from pydub import AudioSegment
import whisper

def ses_dosyasini_texte_cevir(
    dosya_adi,
    cikti_dosya=None,
    parca_suresi=60,
    model_adi="small",
    on_progress=None,
    on_status=None,
):
    # (Artık PATH içindeki ffmpeg/ffprobe kullanılacağından özel atama zorunlu değil)
    # Giriş dosyası yolu: Önce verilen yolu dene; yoksa bu dosyanın klasörüne göre çöz
    if not os.path.isabs(dosya_adi) and not os.path.exists(dosya_adi):
        script_dir = os.path.dirname(__file__)
        candidate = os.path.join(script_dir, dosya_adi)
        if os.path.exists(candidate):
            dosya_adi = candidate

    if not os.path.exists(dosya_adi):
        raise FileNotFoundError(f"Audio file not found at: {dosya_adi}")

    # Eğer çıktı dosyası belirtilmemişse, giriş ses dosyasının adıyla aynı tabanda .txt üret
    if cikti_dosya is None:
        giris_klasoru = os.path.dirname(dosya_adi)
        giris_tabani = os.path.splitext(os.path.basename(dosya_adi))[0]
        cikti_dosya = os.path.join(giris_klasoru, f"{giris_tabani}.txt") if giris_klasoru else f"{giris_tabani}.txt"

    if on_status:
        try:
            on_status("Ses dosyası yükleniyor…")
        except Exception:
            pass
    else:
        print("Ses dosyası yükleniyor...")
    try:
        # m4a için format belirtmek daha güvenli olabilir
        audio = AudioSegment.from_file(dosya_adi, format="m4a")
    except Exception as e:
        raise Exception(f"Failed to load audio file: {str(e)}")

    parca_uzunlugu_ms = parca_suresi * 1000
    toplam_parca = (len(audio) + parca_uzunlugu_ms - 1) // parca_uzunlugu_ms
    if on_status:
        try:
            on_status(f"Toplam {toplam_parca} parça bulundu.")
        except Exception:
            pass
    else:
        print(f"Toplam {toplam_parca} parça bulundu.")

    if on_status:
        try:
            on_status(f"Whisper '{model_adi}' modeli yükleniyor…")
        except Exception:
            pass
    else:
        print(f"Whisper '{model_adi}' modeli yükleniyor...")
    model = whisper.load_model(model_adi)

    full_text = ""
    for idx, start in enumerate(range(0, len(audio), parca_uzunlugu_ms), start=1):
        parca = audio[start:start + parca_uzunlugu_ms]
        parca_dosya = f"temp_chunk_{idx}.wav"
        parca.export(parca_dosya, format="wav")
        if on_status:
            try:
                on_status(f"Parça {idx} / {toplam_parca} işleniyor…")
            except Exception:
                pass
        else:
            print(f"Parça {idx} işleniyor...")
        if on_progress:
            try:
                on_progress(toplam_parca, idx - 1)
            except Exception:
                pass
        try:
            result = model.transcribe(parca_dosya, language="tr")
            full_text += result.get("text", "").strip() + " "
        except Exception as e:
            if on_status:
                try:
                    on_status(f"Parça {idx} işlenirken hata: {e}")
                except Exception:
                    pass
            else:
                print(f"Parça {idx} işlenirken hata: {e}")
        finally:
            if os.path.exists(parca_dosya):
                os.remove(parca_dosya)
        if on_progress:
            try:
                on_progress(toplam_parca, idx)
            except Exception:
                pass

    with open(cikti_dosya, "w", encoding="utf-8") as f:
        f.write(full_text)
    if on_status:
        try:
            on_status(f"Metin '{cikti_dosya}' dosyasına kaydedildi.")
        except Exception:
            pass
    else:
        print(f"Metin '{cikti_dosya}' dosyasına kaydedildi.")

if __name__ == "__main__":
    try:
        ses_dosyasini_texte_cevir("kocamuk.m4a", parca_suresi=60, model_adi="small")
    except Exception as e:
        print(f"Hata oluştu: {e}")
