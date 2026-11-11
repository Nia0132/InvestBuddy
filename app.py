"""InvestBot: aplikasi web chatbot edukasi investasi (Flask).
Jalankan: python app.py lalu buka http://127.0.0.1:5000
"""
import os
from pathlib import Path

from flask import Flask, jsonify, render_template, request, session

from dialog import proses, state_baru
from engine import ChatbotEngine, load_knowledge

BASE_DIR = Path(__file__).resolve().parent


def create_app(config=None):  # create_app: pabrik aplikasi Flask (memudahkan pengujian)
    app = Flask(__name__)
    app.config.update(
        SECRET_KEY=os.environ.get("SECRET_KEY", "ganti-dengan-kunci-rahasia"),
        THRESHOLD=float(os.environ.get("THRESHOLD", "0.45")),
        MAX_LEN=500,
    )
    if config:
        app.config.update(config)

    kb = load_knowledge(BASE_DIR / "knowledge.json")
    engine = ChatbotEngine(kb, app.config["THRESHOLD"])

    @app.get("/")
    def index():  # index: halaman chat; state percakapan direset
        session["state"] = state_baru()
        return render_template("chat.html", kb=kb, greeting=engine.jawab("greeting"))

    @app.post("/api/chat")
    def api_chat():  # api_chat: terima {"message"}, balas {"reply","intent","score"}
        data = request.get_json(silent=True) or {}
        message = str(data.get("message", "")).strip()
        if not message:
            return jsonify({"error": "Pesan tidak boleh kosong"}), 400
        if len(message) > app.config["MAX_LEN"]:
            return jsonify({"error": f"Pesan maksimal {app.config['MAX_LEN']} karakter"}), 400
        state = session.get("state") or state_baru()
        reply, intent, score = proses(message, state, engine, kb)
        session["state"] = state  # simpan ulang agar Flask menulis cookie
        return jsonify({"reply": reply, "intent": intent, "score": score})

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)  # debug hanya di komputer sendiri
