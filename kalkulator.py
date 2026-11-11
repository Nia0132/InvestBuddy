"""Fungsi hitung dan pembaca input angka InvestBot (tanpa Flask)."""
import re

SATUAN = {"rb": 1_000, "ribu": 1_000, "k": 1_000, "jt": 1_000_000, "juta": 1_000_000}


def rupiah(angka):  # rupiah: format angka jadi teks "Rp30.000.000"
    return "Rp" + f"{round(angka):,}".replace(",", ".")


def baca_rupiah(teks):  # baca_rupiah: "500rb" / "Rp500.000" -> 500000.0; gagal -> None
    s = teks.lower().replace("rp", "").replace(" ", "")
    m = re.fullmatch(r"(\d[\d.,]*)(rb|ribu|k|jt|juta)?", s)
    if not m:
        return None
    angka, satuan = m.groups()
    try:
        if satuan:
            return float(angka.replace(",", ".")) * SATUAN[satuan]
        return float(re.sub(r"[.,]", "", angka))
    except ValueError:
        return None


def baca_persen(teks):  # baca_persen: "8%" / "4,5" -> 8.0 / 4.5; gagal -> None
    m = re.search(r"\d+(?:[.,]\d+)?", teks)
    return float(m.group().replace(",", ".")) if m else None


def baca_durasi_tahun(teks):  # baca_durasi_tahun: "5 tahun" / "60 bulan" / "5" -> tahun (float)
    m = re.fullmatch(r"(\d+(?:[.,]\d+)?)\s*(tahun|thn|th|bulan|bln)?", teks.strip().lower())
    if not m:
        return None
    nilai = float(m.group(1).replace(",", "."))
    return nilai / 12 if m.group(2) in ("bulan", "bln") else nilai


def baca_usia(teks):  # baca_usia: "22" / "22 tahun" -> 22; gagal -> None
    m = re.fullmatch(r"(\d{1,3})\s*(tahun|thn|th)?", teks.strip().lower())
    return int(m.group(1)) if m else None


def cari_profil(total, profiles):  # cari_profil: total skor -> indeks profil risiko
    for i, p in enumerate(profiles):
        if p["min"] <= total <= p["max"]:
            return i
    return 0


def hitung_dca(nominal, tahun, return_pct):  # hitung_dca: modal total, nilai akhir, untung
    n = round(tahun * 12)
    r = return_pct / 100 / 12
    akhir = nominal * n if r == 0 else nominal * (((1 + r) ** n - 1) / r)
    modal = nominal * n
    return {"modal": modal, "akhir": akhir, "untung": akhir - modal}


def hitung_pensiun(pengeluaran, usia, usia_pensiun, inflasi_pct, return_pct):  # hitung_pensiun: target dana + setoran bulanan
    tahun = usia_pensiun - usia
    masa_depan = pengeluaran * (1 + inflasi_pct / 100) ** tahun
    target = masa_depan * 12 * 25  # aturan 4%
    n = tahun * 12
    r = return_pct / 100 / 12
    setoran = target / n if r == 0 else target * r / ((1 + r) ** n - 1)
    return {"tahun": tahun, "masa_depan": masa_depan, "target": target, "setoran": setoran}
