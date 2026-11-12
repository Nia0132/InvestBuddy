CARA MENJALANKAN INVESTBOT
==========================

Prasyarat
- Python 3.10 atau lebih baru.
- Cek versi: python --version  (macOS/Linux: python3 --version)
- Di macOS/Linux, ganti "python" dengan "python3" bila perlu.


LANGKAH 1. Buka folder proyek
-----------------------------
1. Ekstrak investbuddy.zip.
2. Buka folder "investbuddy" di VS Code (File > Open Folder).
3. Buka terminal: Ctrl + `
4. Pastikan terminal berada di folder investbuddy
   (di sini ada app.py, dialog.py, engine.py).


LANGKAH 2. Buat virtual environment (sekali saja)
-------------------------------------------------
   python -m venv venv


LANGKAH 3. Aktifkan virtual environment
---------------------------------------
Windows PowerShell : venv\Scripts\Activate.ps1
Windows CMD        : venv\Scripts\activate
macOS / Linux      : source venv/bin/activate

Berhasil bila awal baris terminal berubah jadi (venv).
Aktifkan lagi setiap membuka terminal baru.

Bila PowerShell menolak skrip, jalankan sekali:
   Set-ExecutionPolicy -Scope CurrentUser RemoteSigned


LANGKAH 4. Pasang requirements (sekali saja)
--------------------------------------------
   pip install -r requirements.txt

Cek: flask --version  (harus Flask 3.x)


LANGKAH 5. Jalankan pengujian
-----------------------------
Folder tests/ berisi uji otomatis. Jalankan sebelum memakai bot:

   pytest -q          ringkas
   pytest -v          rinci 

Hasil yang diharapkan: "46 passed".

Opsi lain:
   pytest tests/test_investbuddy.py     hanya file uji ini
   pytest -k dca -v                     hanya uji yang namanya memuat "dca"

Bila ada uji gagal: baca nama uji dan baris galatnya, perbaiki kode,
lalu jalankan pytest lagi sampai semua lolos.


LANGKAH 6. Jalankan aplikasi
----------------------------
   python app.py

Terminal menampilkan: Running on http://127.0.0.1:5000


LANGKAH 7. Buka di peramban
---------------------------
   http://127.0.0.1:5000

Coba:
- Klik tombol saran, atau ketik "halo".
- Ketik 1 untuk tes profil risiko (jawab A-D).
- Ketik 2 untuk hitung DCA.
- Ketik 3 untuk hitung dana pensiun.
- Ketik 4 untuk daftar FAQ.
- Ketik "batal" untuk keluar dari alur.


LANGKAH 8. Hentikan aplikasi
----------------------------
- Tekan Ctrl + C di terminal.
- Nonaktifkan venv: deactivate


URUTAN SINGKAT (setelah pertama kali)
-------------------------------------
   venv\Scripts\activate        (atau source venv/bin/activate)
   pytest -q
   python app.py


MENGATASI MASALAH
-----------------
'python' is not recognized
   Pakai: py -m venv venv   atau pasang ulang Python (centang "Add to PATH").

No module named 'flask'
   venv belum aktif. Aktifkan, lalu: pip install -r requirements.txt

No module named 'dialog' / 'engine' / 'app'
   Terminal bukan di folder investbuddy. Gunakan cd ke folder itu.

Address already in use
   Server lama masih jalan. Tutup, atau: flask --app app run --port 5001

Perubahan CSS/JS tidak tampak
   Muat ulang tanpa cache: Ctrl + Shift + R

Bot salah menjawab setelah mengubah knowledge.json
   Periksa format JSON: python -m json.tool knowledge.json
   Lalu jalankan pytest -q lagi.


PENGATURAN OPSIONAL (variabel lingkungan)
-----------------------------------------
SECRET_KEY  kunci cookie sesi. Ganti di server sungguhan.
THRESHOLD   ambang intent (bawaan 0.45).

Linux/macOS : export THRESHOLD=0.4
PowerShell  : $env:THRESHOLD="0.4"
Lalu        : python app.py
