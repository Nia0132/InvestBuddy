"""Mesin NLU InvestBot: praproses teks, skor kemiripan, klasifikasi intent."""
import json
import random
import re
from difflib import SequenceMatcher

# Kamus kata tidak baku -> baku ("" = kata dibuang)
NORMALISASI = {
    "gak": "tidak", "ga": "tidak", "nggak": "tidak", "enggak": "tidak",
    "gimana": "bagaimana", "gmn": "bagaimana", "brp": "berapa",
    "yg": "yang", "utk": "untuk", "sy": "saya", "aku": "saya", "gue": "saya", "gw": "saya",
    "kak": "", "min": "", "dong": "", "sih": "", "nih": "", "ya": "",
    "makasih": "terima kasih", "thanks": "terima kasih", "thx": "terima kasih",
    "hai": "halo", "hi": "halo", "hello": "halo",
    "reksadana": "reksa dana", "pensiunku": "pensiun",
}

# Kata henti: dibuang saat praproses
STOPWORDS = {"yang", "di", "ke", "dari", "dan", "atau", "itu", "ini", "untuk", "dengan",
             "apa", "saya", "mau", "ingin", "tolong", "per"}


def load_knowledge(path):  # load_knowledge: baca file knowledge.json jadi dict
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def preprocess(teks):  # preprocess: kalimat mentah -> daftar token baku tanpa kata henti
    teks = re.sub(r"[^a-z0-9\s]", " ", teks.lower())
    tokens = []
    for kata in teks.split():
        for k in NORMALISASI.get(kata, kata).split():
            if k and k not in STOPWORDS:
                tokens.append(k)
    return tokens


def similarity(a, b):  # similarity: skor 0..1 = 0,4 Jaccard + 0,3 kemiripan huruf + 0,3 cakupan
    if not a or not b:
        return 0.0
    sa, sb = set(a), set(b)
    jaccard = len(sa & sb) / len(sa | sb)
    fuzzy = SequenceMatcher(None, " ".join(a), " ".join(b)).ratio()
    cakupan = len(sa & sb) / len(sb)
    return round(0.4 * jaccard + 0.3 * fuzzy + 0.3 * cakupan, 4)


class ChatbotEngine:  # ChatbotEngine: mencocokkan pesan dengan intent dan memberi jawaban statis
    def __init__(self, kb, threshold=0.45):  # __init__: praproses semua pola sekali saja
        self.kb = kb
        self.threshold = threshold
        self._pola = [(i["tag"], preprocess(p)) for i in kb["intents"] for p in i["patterns"]]
        self._respons = {i["tag"]: i.get("responses", []) for i in kb["intents"]}

    def classify(self, pesan):  # classify: pilih intent terbaik; None bila skor < ambang
        tokens = preprocess(pesan)
        terbaik, skor_terbaik = None, 0.0
        for tag, pola_tokens in self._pola:
            skor = similarity(tokens, pola_tokens)
            if skor > skor_terbaik:
                terbaik, skor_terbaik = tag, skor
        if skor_terbaik < self.threshold:
            return None, skor_terbaik
        return terbaik, skor_terbaik

    def jawab(self, tag):  # jawab: ambil satu respons acak milik intent
        return random.choice(self._respons[tag])

    def fallback(self):  # fallback: jawaban saat pesan tidak dikenali
        return random.choice(self.kb["fallback"])
