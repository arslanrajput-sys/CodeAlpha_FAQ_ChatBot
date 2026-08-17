import json
import sys
from http.server import BaseHTTPRequestHandler
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from lib.chatbot import FAQMatcher


matcher = FAQMatcher(ROOT / "data" / "faqs.json")


class handler(BaseHTTPRequestHandler):
    def _send_json(self, payload, status=200):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")

        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        self._send_json({
            "ok": True,
            "service": "SecureBank FAQ Chatbot",
            "method": "NLTK preprocessing + TF-IDF + cosine similarity",
        })

    def do_POST(self):
        try:
            content_length = int(self.headers.get("Content-Length", "0"))
            if content_length <= 0:
                return self._send_json({"error": "Request body is required."}, 400)

            raw_body = self.rfile.read(content_length)
            data = json.loads(raw_body.decode("utf-8"))
            question = str(data.get("question", "")).strip()

            if not question:
                return self._send_json({"error": "Please enter a question."}, 400)

            if len(question) > 700:
                return self._send_json(
                    {"error": "Question is too long. Please keep it under 700 characters."},
                    400,
                )

            result = matcher.match(question)
            return self._send_json(result)

        except json.JSONDecodeError:
            return self._send_json({"error": "Invalid JSON request."}, 400)
        except Exception as exc:
            print(f"Chat API error: {exc}")
            return self._send_json(
                {"error": "The chatbot is temporarily unavailable. Please try again."},
                500,
            )

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Allow", "GET, POST, OPTIONS")
        self.end_headers()
