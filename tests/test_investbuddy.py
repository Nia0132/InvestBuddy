"""Uji InvestBot: mesin, kalkulator, dan alur dialog lewat route Flask."""
import pytest

from app import create_app
from engine import ChatbotEngine, load_knowledge, preprocess, similarity
import kalkulator as kal

KB = load_knowledge("knowledge.json")


# ---------- uji unit ----------
def test_preprocess_normalisasi_dan_stopword():  # preprocess: huruf kecil, baku, tanpa stopword
    assert preprocess("Apa itu Reksadana?") == ["reksa", "dana"]


def test_similarity_sama_bernilai_satu():  # similarity: kalimat sama = 1.0
    assert similarity(["dca"], ["dca"]) == 1.0


@pytest.mark.parametrize("pesan, intent", [
    ("Halo", "greeting"), ("Menu", "menu"), ("Bisa apa?", "menu"),
    ("Kamu siapa?", "about_bot"), ("Ini nasihat resmi?", "disclaimer"),
    ("Makasih", "goodbye"), ("Bye", "goodbye"),
    ("Cek profil risiko", "start_risk_profile"), ("Aku tipe investor apa?", "start_risk_profile"),
    ("Apa itu konservatif?", "explain_profile"), ("Ulangi tes", "retake_profile"),
    ("Kenapa perlu profil risiko?", "why_risk_profile"),
    ("Hitung DCA", "start_dca"), ("Nabung Rp500rb/bulan jadi berapa?", "start_dca"),
    ("Apa itu DCA?", "explain_dca"),
    ("Hitung dana pensiun", "start_pension"), ("Berapa uang pensiunku?", "start_pension"),
    ("Kenapa dikali 25?", "explain_pension_rule"),
    ("Apa itu reksa dana?", "faq_reksadana"), ("Apa itu SBN ritel?", "faq_sbn"),
    ("Dana darurat berapa?", "faq_emergency_fund"), ("Modal minimal berapa?", "faq_min_invest"),
    ("Kenapa return tinggi berisiko?", "faq_risk_return"), ("Apa itu inflasi?", "faq_inflation"),
    ("Cek izin platform di mana?", "faq_ojk"),
])
def test_klasifikasi_intent(pesan, intent):  # classify: contoh pertanyaan -> intent benar
    assert ChatbotEngine(KB).classify(pesan)[0] == intent


def test_di_luar_tema_fallback():  # classify: pertanyaan luar tema -> None
    assert ChatbotEngine(KB).classify("harga bensin berapa")[0] is None


def test_baca_rupiah():  # baca_rupiah: variasi penulisan nominal
    assert kal.baca_rupiah("500rb") == 500_000
    assert kal.baca_rupiah("Rp500.000") == 500_000
    assert kal.baca_rupiah("1,5jt") == 1_500_000
    assert kal.baca_rupiah("abc") is None


def test_durasi_dan_persen():  # baca_durasi_tahun + baca_persen
    assert kal.baca_durasi_tahun("5 tahun") == 5
    assert kal.baca_durasi_tahun("60 bulan") == 5
    assert kal.baca_persen("4,5%") == 4.5


def test_hitung_dca_contoh_dokumen():  # hitung_dca: Rp500rb x 5 thn x 8% ≈ Rp36,7 juta
    h = kal.hitung_dca(500_000, 5, 8)
    assert h["modal"] == 30_000_000
    assert round(h["akhir"], -5) == 36_700_000


def test_hitung_dca_return_nol():  # hitung_dca: return 0% = modal saja
    assert kal.hitung_dca(100_000, 1, 0)["akhir"] == 1_200_000


def test_hitung_pensiun():  # hitung_pensiun: target = pengeluaran masa depan x 12 x 25
    h = kal.hitung_pensiun(3_000_000, 22, 55, 4, 8)
    assert h["tahun"] == 33
    assert round(h["target"]) == round(3_000_000 * 1.04 ** 33 * 12 * 25)
    assert h["setoran"] > 0


# ---------- uji integrasi ----------
@pytest.fixture
def chat():  # chat: kirim pesan lewat test client (cookie sesi ikut terbawa)
    client = create_app({"TESTING": True}).test_client()
    client.get("/")
    return lambda msg: client.post("/api/chat", json={"message": msg}).get_json()


def isi_profil(chat, jawaban):  # isi_profil: jalankan kuesioner 6 pertanyaan
    chat("1")
    hasil = None
    for j in jawaban:
        hasil = chat(j)
    return hasil


def test_halaman_utama():  # GET / berisi nama bot
    res = create_app({"TESTING": True}).test_client().get("/")
    assert res.status_code == 200 and "InvestBot" in res.get_data(as_text=True)


@pytest.mark.parametrize("payload", [{}, {"message": ""}, {"message": "a" * 501}])
def test_input_tidak_valid(payload):  # /api/chat: input buruk -> 400
    client = create_app({"TESTING": True}).test_client()
    assert client.post("/api/chat", json=payload).status_code == 400


def test_profil_agresif_lalu_dca(chat):  # alur: profil -> tawaran DCA -> hasil
    hasil = isi_profil(chat, ["A"] * 6)
    assert hasil["intent"] == "show_risk_result" and "Agresif" in hasil["reply"]
    assert "Nominal" in chat("ya")["reply"]
    chat("500rb")
    assert "Modal total: Rp30.000.000" in chat("5 tahun")["reply"]


def test_override_horizon_pendek(chat):  # Q2 = D (skor 1) + Agresif -> Moderat + peringatan
    hasil = isi_profil(chat, ["A", "D", "A", "A", "A", "A"])
    assert "Moderat" in hasil["reply"] and "Horizon pendek" in hasil["reply"]


def test_peringatan_dana_darurat(chat):  # Q5 = D (skor 1) -> peringatan dana darurat
    hasil = isi_profil(chat, ["B", "B", "B", "B", "D", "B"])
    assert "dana darurat dulu" in hasil["reply"]


def test_jawaban_kuesioner_salah(chat):  # jawaban bukan A-D -> ulang pertanyaan
    chat("1")
    assert "Pilih A, B, C, atau D" in chat("xyz")["reply"]


def test_dca_langsung_dan_ubah_return(chat):  # alur DCA + "coba return 6%"
    chat("2"); chat("500000"); chat("5 tahun")
    assert "Rp36.7" in chat("8%")["reply"]
    assert "return 6%" in chat("coba return 6%")["reply"]


def test_validasi_input_dca(chat):  # nominal bukan angka -> pesan galat
    chat("2")
    assert "Masukkan angka" in chat("abc")["reply"]
    assert "Minimal" in chat("5000")["reply"]


def test_alur_pensiun(chat):  # alur pensiun 5 input -> target dan setoran
    for msg in ["3", "22", "55", "3000000", "4%"]:
        chat(msg)
    hasil = chat("default")
    assert hasil["intent"] == "show_pension_result"
    assert "Target dana" in hasil["reply"] and "Setoran bulanan" in hasil["reply"]


def test_batal_keluar_alur(chat):  # 'batal' di tengah alur -> menu
    chat("2")
    assert "1)" in chat("batal")["reply"]


def test_fallback_intent_none(chat):  # pesan luar tema -> intent None
    assert chat("harga bensin berapa")["intent"] is None
