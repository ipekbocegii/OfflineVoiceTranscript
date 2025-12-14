import os
import re
from collections import Counter, defaultdict
from typing import List, Tuple, Optional

class MeetingSummarizer:
    """
    Transkript dosyasından toplantı maddelerini çıkarır ve özet dosyası yazar.
    Offline çalışır, dış bağımlılık gerektirmez.
    """

    DEFAULT_STOPWORDS = {
        "ve","bir","bu","o","da","de","ile","mi","mu","mü","ama","fakat","ancak",
        "için","gibi","var","yok","çok","az","ben","sen","biz","siz","onlar",
        "olarak","kadar","sonra","önce","şu","her","tüm","eğer","ki","daha","ise",
        "veya","ya","ne","nasıl","hangi","nerede","neden","olarak","ilebirlikte"
    }

    def __init__(self,
                 stopwords: Optional[List[str]] = None,
                 min_word_length: int = 2,
                 sentence_window: int = 3):
        self.stopwords = set(stopwords) if stopwords else set(self.DEFAULT_STOPWORDS)
        self.min_word_length = min_word_length
        self.sentence_window = sentence_window
        self.text = ""
        self.sentences: List[str] = []
        self.words: List[str] = []
        self.freqs: Counter = Counter()

    def load_from_file(self, path: str, encoding: str = "utf-8"):
        if not os.path.exists(path):
            raise FileNotFoundError(f"Dosya bulunamadı: {path}")
        with open(path, "r", encoding=encoding) as f:
            self.text = f.read().strip()
        if not self.text:
            raise ValueError("Yüklenen metin boş.")
        self._prepare()

    def _prepare(self):
        text = self.text
        # Normalize: birleştirilmiş boşluklar, satır başlarını cümle ayırıcı say
        text = re.sub(r"\s+", " ", text).strip()
        self.sentences = self._split_sentences(text)
        self.words = self._tokenize_words(text)
        self.freqs = Counter(w for w in self.words if w not in self.stopwords)

    def _tokenize_words(self, text: str) -> List[str]:
        words = re.findall(r"\w+", text.lower(), flags=re.UNICODE)
        return [w for w in words if len(w) >= self.min_word_length]

    def _split_sentences(self, text: str) -> List[str]:
        # Satır sonları, nokta, ünlem, soru işareti ile böl
        parts = re.split(r'(?<=[.!?])\s+|\n+', text)
        parts = [p.strip() for p in parts if p.strip()]
        return parts

    def _score_sentences(self) -> List[Tuple[int, float]]:
        """
        Her cümlenin puanını döner: (index, score)
        Score hesaplama: cümledeki önemli kelime frekanslarının toplamı
        ve cümlenin başlangıç pozisyonuna küçük bir ağırlık verilir (başta geçenler önemli kabul edilir).
        Ayrıca komşu cümlelerin kelime frekanslarını toplamak için sentence_window kullanılır.
        """
        n = len(self.sentences)
        scores = [0.0] * n
        for i, s in enumerate(self.sentences):
            words = re.findall(r"\w+", s.lower(), flags=re.UNICODE)
            words = [w for w in words if len(w) >= self.min_word_length]
            # pencere: i - k .. i + k
            window_start = max(0, i - self.sentence_window)
            window_end = min(n, i + self.sentence_window + 1)
            # pencere içindeki frekans toplamı
            window_score = 0.0
            for j in range(window_start, window_end):
                wlist = re.findall(r"\w+", self.sentences[j].lower(), flags=re.UNICODE)
                for w in wlist:
                    if len(w) >= self.min_word_length and w not in self.stopwords:
                        window_score += self.freqs.get(w, 0)
            # pozisyon ağırlığı (erken cümlelere hafif tercih)
            pos_weight = 1.0 + max(0, (1.0 - (i / max(1, n))) )
            scores[i] = window_score * pos_weight
        return list(enumerate(scores))

    def _extract_key_phrases(self, top_k: int = 10) -> List[Tuple[str, int]]:
        """
        Basit anahtar ifade çıkarımı: stopword dışı ardışık kelime gruplarını (1-3 uzunluk) sayar.
        Sık geçenleri döner.
        """
        text = self.text.lower()
        toks = re.findall(r"\w+", text, flags=re.UNICODE)
        toks = [t for t in toks if len(t) >= self.min_word_length]
        phrases = Counter()
        # unigram, bigram, trigram
        for i in range(len(toks)):
            # unigram
            if toks[i] not in self.stopwords:
                phrases[toks[i]] += 1
            # bigram
            if i + 1 < len(toks):
                b = toks[i] + " " + toks[i+1]
                if not any(w in self.stopwords for w in b.split()):
                    phrases[b] += 1
            # trigram
            if i + 2 < len(toks):
                t = toks[i] + " " + toks[i+1] + " " + toks[i+2]
                if not any(w in self.stopwords for w in t.split()):
                    phrases[t] += 1
        return phrases.most_common(top_k)

    def summarize(self, num_bullets: int = 8, top_k_phrases: int = 10) -> dict:
        """
        Özet üretir ve sözlük döner:
        {
            "bullets": [ "Madde 1", "Madde 2", ... ],
            "key_phrases": [ (phrase, count), ... ],
            "short_summary": "Tek paragraflık özet"
        }
        """
        if not self.text:
            raise ValueError("Önce metin yükleyin (load_from_file).")

        scored = self._score_sentences()
        # en yüksek puanlı cümleleri seç
        scored_sorted = sorted(scored, key=lambda x: x[1], reverse=True)
        selected_indices = [idx for idx, score in scored_sorted[:num_bullets]]
        selected_indices.sort()

        # bullets: seçilen cümleleri kısaltarak madde haline getir
        bullets = []
        for idx in selected_indices:
            s = self.sentences[idx]
            # cümleyi 20-30 kelimeye kırp (gerekirse)
            words = s.split()
            if len(words) > 30:
                s_short = " ".join(words[:30]) + "..."
            else:
                s_short = s
            # küçük düzenleme: uzun cümlelerde bağlantı edatlarından sonra kesme
            s_short = s_short.strip()
            bullets.append(s_short)

        key_phrases = self._extract_key_phrases(top_k=top_k_phrases)

        # kısa özet: en yüksek 2 cümleyi birleştir
        summary_sentences = [self.sentences[idx] for idx, _ in scored_sorted[:2]]
        short_summary = " ".join(summary_sentences).strip()

        return {
            "bullets": bullets,
            "key_phrases": key_phrases,
            "short_summary": short_summary
        }

    def save_summary(self, summary: dict, output_path: str, encoding: str = "utf-8"):
        lines = []
        lines.append("TOPLANTI ÖZETİ")
        lines.append("=" * 40)
        lines.append("")
        lines.append("KISA ÖZET:")
        lines.append(summary.get("short_summary", ""))
        lines.append("")
        lines.append("ÖNE ÇIKAN MADDELER:")
        for i, b in enumerate(summary.get("bullets", []), start=1):
            lines.append(f"{i}. {b}")
        lines.append("")
        lines.append("ANAHTAR KELİMELER / İFADELER:")
        for phrase, cnt in summary.get("key_phrases", []):
            lines.append(f"- {phrase} ({cnt})")
        lines.append("=" * 40)

        with open(output_path, "w", encoding=encoding) as f:
            f.write("\n".join(lines))
        return output_path

# Örnek kullanım
if __name__ == "__main__":
    summarizer = MeetingSummarizer()
    summarizer.load_from_file("donusturulmus_metin.txt")
    summary = summarizer.summarize(num_bullets=8, top_k_phrases=15)
    out = summarizer.save_summary(summary, "toplanti_ozeti.txt")
    print(f"Özet kaydedildi: {out}")
