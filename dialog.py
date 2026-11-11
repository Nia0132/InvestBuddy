"""Alur dialog InvestBot: menu, profil risiko, kalkulator DCA, kalkulator pensiun."""
import re

import kalkulator as kal

HURUF = "ABCD"
MENU = {"1": "start_risk_profile", "2": "start_dca", "3": "start_pension", "4": "faq_menu"}
YA = {"ya", "iya", "y", "yes", "ok", "oke", "boleh", "lanjut", "mau"}
TIDAK = {"tidak", "nggak", "gak", "ga", "enggak", "no", "n", "nanti"}
BATAL = {"batal", "menu", "keluar", "stop"}
RETURN_DEFAULT, INFLASI_DEFAULT = 8.0, 4.0
DISCLAIMER = "Ini asumsi, bukan jaminan."

# Urutan input tiap kalkulator
LANGKAH = {
    "dca": ["nominal", "durasi", "return"],
    "pension": ["usia", "pensiun", "pengeluaran", "inflasi", "return"],
}
PROMPT = {
    "nominal": "Nominal investasi per bulan? (mis. 500000 atau 500rb)",
    "durasi": "Durasi berapa lama? (mis. 5 tahun)",
    "usia": "Usia kamu sekarang?",
    "pensiun": "Mau pensiun usia berapa?",
    "pengeluaran": "Pengeluaran bulanan sekarang? (mis. 3000000)",
}
INTENT_LANGKAH = {
    "nominal": "input_nominal", "durasi": "input_duration", "return": "input_return",
    "usia": "input_age_now", "pensiun": "input_age_retire",
    "pengeluaran": "input_expense", "inflasi": "input_inflation",
}


def prompt(nama, state):  # prompt: teks permintaan input; 'return' dan 'inflasi' menyebut nilai default
    if nama == "return":
        if state["profil"]:
            default = f"{state['profil']['return']:g}% (dari profil {state['profil']['nama']})"
        else:
            default = f"{RETURN_DEFAULT:g}% (belum ada profil risiko)"
        return f"Asumsi return per tahun, 0–90%? (mis. 8%)\nKetik 'default' untuk pakai {default}."
    if nama == "inflasi":
        return f"Asumsi inflasi per tahun, 0–15%? (mis. 4%)\nKetik 'default' untuk pakai {INFLASI_DEFAULT:g}%."
    return PROMPT[nama]


def state_baru():  # state_baru: buat state percakapan kosong (disimpan di sesi)
    return {"mode": None, "step": 0, "data": {}, "profil": None, "dca_terakhir": None}


def reset_alur(state):  # reset_alur: keluar dari alur aktif; profil tetap tersimpan
    state.update(mode=None, step=0, data={})


# ---------------------------------------------------------------- profil risiko
def tanya(kb, i):  # tanya: susun teks pertanyaan kuesioner ke-i beserta opsi A-D
    q = kb["questions"][i]
    opsi = "\n".join(f"{HURUF[j]}) {o}" for j, o in enumerate(q["options"]))
    return f"Q{i + 1}. {q['text']}\n{opsi}"


def mulai_risiko(state, kb=None):  # mulai_risiko: reset skor, mulai kuesioner dari Q1
    state.update(mode="risk", step=0, data={"skor": []})
    return "Tes profil risiko: 6 pertanyaan. Jawab dengan huruf A–D.\n\n" + tanya(kb, 0)


def lanjut_risiko(teks, state, kb):  # lanjut_risiko: simpan jawaban A-D, lanjut Q berikut atau hasil
    pilih = teks.strip(" .)").upper()
    i = state["step"]
    if len(pilih) != 1 or pilih not in HURUF:
        return "Pilih A, B, C, atau D.\n" + tanya(kb, i), f"answer_q{i + 1}"
    state["data"]["skor"].append(4 - HURUF.index(pilih))  # A = skor 4 ... D = skor 1
    state["step"] += 1
    if state["step"] < len(kb["questions"]):
        return tanya(kb, state["step"]), f"answer_q{i + 1}"
    return hasil_risiko(state, kb), "show_risk_result"


def hasil_risiko(state, kb):  # hasil_risiko: hitung profil + aturan override, tawarkan DCA
    skor = state["data"]["skor"]
    total = sum(skor)
    profiles = kb["profiles"]
    idx = kal.cari_profil(total, profiles)
    catatan = []
    if skor[1] == 1 and profiles[idx]["nama"] == "Agresif":  # horizon pendek: turun satu level
        idx -= 1
        catatan.append("Profil diturunkan satu level (horizon pendek).")
    if skor[4] == 1:
        catatan.append("⚠ Siapkan dana darurat dulu.")
    if skor[1] == 1:
        catatan.append("⚠ Horizon pendek. Hindari instrumen berisiko.")
    p = profiles[idx]
    state.update(mode="offer_dca", step=0, data={})
    state["profil"] = {"nama": p["nama"], "return": p["return"], "skor": total}
    baris = [f"Skor {total} → {p['nama']}.", f"Instrumen umum: {p['instrumen']}.",
             f"Asumsi return: {p['return']}% per tahun."] + catatan
    baris.append(f"Mau hitung DCA pakai return {p['return']}%? (ya/tidak)")
    return "\n".join(baris)


# ------------------------------------------------------------------ kalkulator
def mulai_dca(state, kb=None, preset=False):  # mulai_dca: mulai input DCA; preset = pakai return profil
    data = {"return": state["profil"]["return"]} if preset and state["profil"] else {}
    state.update(mode="dca", step=0, data=data)
    info = f"Return pakai {data['return']}% dari profilmu.\n" if data else ""
    return f"Hitung DCA.\n{info}{PROMPT['nominal']}"


def mulai_pensiun(state, kb=None):  # mulai_pensiun: mulai input dana pensiun (5 input)
    state.update(mode="pension", step=0, data={})
    return f"Hitung dana pensiun. Ada 5 input.\n{PROMPT['usia']}"


MULAI = {  # peta intent -> fungsi pemulai alur
    "start_risk_profile": mulai_risiko, "retake_profile": mulai_risiko,
    "start_dca": mulai_dca, "start_pension": mulai_pensiun,
}


def baca_nominal(teks, state):  # baca_nominal: validasi nominal bulanan (min Rp10.000)
    nilai = kal.baca_rupiah(teks)
    if nilai is None:
        return None, "Masukkan angka, mis. 500000 atau 500rb."
    if nilai < 10_000:
        return None, "Minimal Rp10.000."
    return nilai, None


def baca_durasi(teks, state):  # baca_durasi: validasi durasi 1-50 tahun
    tahun = kal.baca_durasi_tahun(teks)
    if tahun is None or not 1 <= tahun <= 50:
        return None, "Durasi 1–50 tahun, mis. 5 tahun."
    return tahun, None


def baca_return(teks, state):  # baca_return: validasi return 0-90%; 'default' = profil atau 8%
    if "default" in teks:
        return (state["profil"]["return"] if state["profil"] else RETURN_DEFAULT), None
    nilai = kal.baca_persen(teks)
    if nilai is None or not 0 <= nilai <= 90:
        return None, "Return harus 0–90%."
    return nilai, None


def baca_usia(teks, state):  # baca_usia: validasi usia sekarang 17-70
    nilai = kal.baca_usia(teks)
    if nilai is None or not 17 <= nilai <= 70:
        return None, "Usia 17–70."
    return nilai, None


def baca_pensiun(teks, state):  # baca_pensiun: usia pensiun harus > usia sekarang, maks 70
    nilai = kal.baca_usia(teks)
    if nilai is None or not state["data"]["usia"] < nilai <= 70:
        return None, f"Usia pensiun harus di atas {state['data']['usia']} dan maksimal 70."
    return nilai, None


def baca_pengeluaran(teks, state):  # baca_pengeluaran: pengeluaran bulanan harus > 0
    nilai = kal.baca_rupiah(teks)
    if nilai is None or nilai <= 0:
        return None, "Masukkan angka lebih dari 0, mis. 3000000."
    return nilai, None


def baca_inflasi(teks, state):  # baca_inflasi: validasi inflasi 0-15%; 'default' = 4%
    if "default" in teks:
        return INFLASI_DEFAULT, None
    nilai = kal.baca_persen(teks)
    if nilai is None or not 0 <= nilai <= 15:
        return None, "Inflasi harus 0–15%."
    return nilai, None


BACA = {"nominal": baca_nominal, "durasi": baca_durasi, "return": baca_return, "usia": baca_usia,
        "pensiun": baca_pensiun, "pengeluaran": baca_pengeluaran, "inflasi": baca_inflasi}


def teks_dca(d):  # teks_dca: hitung DCA lalu susun teks hasil
    h = kal.hitung_dca(d["nominal"], d["durasi"], d["return"])
    return (f"Modal total: {kal.rupiah(h['modal'])}\n"
            f"Estimasi nilai akhir: {kal.rupiah(h['akhir'])}\n"
            f"Estimasi untung: {kal.rupiah(h['untung'])}\n"
            f"Asumsi: return {d['return']:g}%/tahun, {d['durasi']:g} tahun.\n"
            f"{DISCLAIMER} Coba ketik mis. 'coba return 6%'.")


def teks_pensiun(d):  # teks_pensiun: hitung dana pensiun lalu susun teks hasil
    h = kal.hitung_pensiun(d["pengeluaran"], d["usia"], d["pensiun"], d["inflasi"], d["return"])
    return (f"Pengeluaran saat pensiun: {kal.rupiah(h['masa_depan'])}/bulan\n"
            f"Target dana (×12×25): {kal.rupiah(h['target'])}\n"
            f"Setoran bulanan: {kal.rupiah(h['setoran'])}\n"
            f"Asumsi: inflasi {d['inflasi']:g}%, return {d['return']:g}%, {h['tahun']} tahun.\n"
            f"{DISCLAIMER}")


def lanjut_kalkulator(teks, state):  # lanjut_kalkulator: baca satu input, lanjut atau tampilkan hasil
    mode = state["mode"]
    langkah = LANGKAH[mode]
    nama = langkah[state["step"]]
    nilai, galat = BACA[nama](teks, state)
    if galat:
        return f"{galat}\n{prompt(nama, state)}\n(ketik 'batal' untuk keluar)", INTENT_LANGKAH[nama]
    state["data"][nama] = nilai
    state["step"] += 1
    while state["step"] < len(langkah) and langkah[state["step"]] in state["data"]:
        state["step"] += 1  # lewati input yang sudah terisi (return dari profil)
    if state["step"] < len(langkah):
        return prompt(langkah[state["step"]], state), INTENT_LANGKAH[nama]
    data = dict(state["data"])
    reset_alur(state)
    if mode == "dca":
        state["dca_terakhir"] = data
        return teks_dca(data), "show_dca_result"
    return teks_pensiun(data), "show_pension_result"


def ubah_return(teks, state):  # ubah_return: "coba return 6%" -> hitung ulang DCA terakhir
    m = re.search(r"(?:coba|ganti|ubah)\s+return\s+(\d+(?:[.,]\d+)?)", teks)
    if not m:
        return None
    if not state["dca_terakhir"]:
        return "Hitung DCA dulu. Ketik 2."
    nilai = float(m.group(1).replace(",", "."))
    if nilai > 90:
        return "Return harus 0–90%."
    state["dca_terakhir"] = {**state["dca_terakhir"], "return": nilai}
    return teks_dca(state["dca_terakhir"])


# ------------------------------------------------------------------ pintu utama
def proses(pesan, state, engine, kb):  # proses: satu pesan masuk -> (balasan, intent, skor)
    teks = pesan.strip().lower()
    mode = state["mode"]
    if mode and teks in BATAL:
        reset_alur(state)
        return engine.jawab("menu"), "menu", 1.0
    if mode == "offer_dca":
        if teks in YA:
            return mulai_dca(state, kb, preset=True), "start_dca", 1.0
        reset_alur(state)
        if teks in TIDAK:
            return "Oke. Ketik menu untuk pilihan lain.", "menu", 1.0
    elif mode == "risk":
        balasan, tag = lanjut_risiko(teks, state, kb)
        return balasan, tag, 1.0
    elif mode in LANGKAH:
        balasan, tag = lanjut_kalkulator(teks, state)
        return balasan, tag, 1.0

    ubah = ubah_return(teks, state)
    if ubah:
        return ubah, "change_assumption", 1.0
    if teks in MENU:
        tag, skor = MENU[teks], 1.0
    else:
        tag, skor = engine.classify(pesan)
    if tag is None:
        return engine.fallback(), None, skor
    if tag in MULAI:
        return MULAI[tag](state, kb), tag, skor
    return engine.jawab(tag), tag, skor