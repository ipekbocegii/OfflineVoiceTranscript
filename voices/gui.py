import threading
import tkinter as tk
from tkinter import filedialog, messagebox
import os

from transcriber import ses_dosyasini_texte_cevir


class TranscriberGUI:
    def __init__(self, master: tk.Tk) -> None:
        self.master = master
        master.title("Ses -> Metin Dönüştürücü (Whisper)")
        master.geometry("520x240")

        self.audio_path_var = tk.StringVar()
        self.chunk_seconds_var = tk.StringVar(value="60")
        self.model_name_var = tk.StringVar(value="small")

        self._build_widgets()

    def _build_widgets(self) -> None:
        padding_y = 6

        # Dosya seçimi
        row1 = tk.Frame(self.master)
        row1.pack(fill=tk.X, padx=10, pady=padding_y)
        tk.Label(row1, text="Ses Dosyası (.m4a)").pack(side=tk.LEFT)
        entry = tk.Entry(row1, textvariable=self.audio_path_var)
        entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=8)
        tk.Button(row1, text="Gözat", command=self._browse_file).pack(side=tk.LEFT)

        # Parça süresi
        row2 = tk.Frame(self.master)
        row2.pack(fill=tk.X, padx=10, pady=padding_y)
        tk.Label(row2, text="Parça Süresi (sn)").pack(side=tk.LEFT)
        tk.Entry(row2, width=10, textvariable=self.chunk_seconds_var).pack(side=tk.LEFT, padx=8)

        # Model adı
        row3 = tk.Frame(self.master)
        row3.pack(fill=tk.X, padx=10, pady=padding_y)
        tk.Label(row3, text="Model Adı").pack(side=tk.LEFT)
        tk.OptionMenu(row3, self.model_name_var, "tiny", "base", "small", "medium", "large").pack(side=tk.LEFT, padx=8)

        # Çalıştır düğmesi ve durum
        row4 = tk.Frame(self.master)
        row4.pack(fill=tk.X, padx=10, pady=padding_y)
        self.start_button = tk.Button(row4, text="Dönüştür", command=self._start_transcription)
        self.start_button.pack(side=tk.LEFT)
        self.status_label = tk.Label(row4, text="Hazır")
        self.status_label.pack(side=tk.LEFT, padx=12)

        # Çıktı bilgisi
        row5 = tk.Frame(self.master)
        row5.pack(fill=tk.X, padx=10, pady=padding_y)
        self.output_hint = tk.Label(row5, text="Çıktı: aynı klasörde .txt olarak oluşturulacak")
        self.output_hint.pack(side=tk.LEFT)

    def _browse_file(self) -> None:
        file_path = filedialog.askopenfilename(
            title="Ses dosyası seç",
            filetypes=[("M4A files", "*.m4a"), ("All files", "*.*")]
        )
        if file_path:
            self.audio_path_var.set(file_path)

    def _start_transcription(self) -> None:
        audio_path = self.audio_path_var.get().strip()
        if not audio_path:
            messagebox.showwarning("Eksik bilgi", "Lütfen bir ses dosyası seçin.")
            return
        if not os.path.exists(audio_path):
            messagebox.showerror("Dosya yok", f"Dosya bulunamadı:\n{audio_path}")
            return

        try:
            chunk_seconds = int(self.chunk_seconds_var.get().strip())
            if chunk_seconds <= 0:
                raise ValueError
        except ValueError:
            messagebox.showwarning("Geçersiz değer", "Parça süresi pozitif bir tam sayı olmalı.")
            return

        model_name = self.model_name_var.get().strip() or "small"

        # UI'yi kilitlemeyelim: iş parçacığında çalıştır
        self._set_running(True)
        thread = threading.Thread(
            target=self._run_transcription,
            args=(audio_path, chunk_seconds, model_name),
            daemon=True,
        )
        thread.start()

    def _run_transcription(self, audio_path: str, chunk_seconds: int, model_name: str) -> None:
        try:
            self._set_status("İşlem başladı… (model yükleniyor)")
            ses_dosyasini_texte_cevir(
                dosya_adi=audio_path,
                cikti_dosya=None,
                parca_suresi=chunk_seconds,
                model_adi=model_name,
            )

            base = os.path.splitext(os.path.basename(audio_path))[0]
            out_dir = os.path.dirname(audio_path)
            out_path = os.path.join(out_dir, f"{base}.txt")
            self._show_info("Tamamlandı", f"Metin oluşturuldu:\n{out_path}")
        except Exception as exc:
            self._show_error("Hata", str(exc))
        finally:
            self._set_running(False)
            self._set_status("Hazır")

    def _set_running(self, running: bool) -> None:
        def update_widgets() -> None:
            self.start_button.config(state=(tk.DISABLED if running else tk.NORMAL))
        self.master.after(0, update_widgets)

    def _set_status(self, text: str) -> None:
        def update_status() -> None:
            self.status_label.config(text=text)
        self.master.after(0, update_status)

    def _show_info(self, title: str, text: str) -> None:
        self.master.after(0, lambda: messagebox.showinfo(title, text))

    def _show_error(self, title: str, text: str) -> None:
        self.master.after(0, lambda: messagebox.showerror(title, text))


def main() -> None:
    root = tk.Tk()
    app = TranscriberGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()


