import json
import os
import sys
from http.server import BaseHTTPRequestHandler
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from lib.chatbot import FAQMatcher


matcher = FAQMatcher(ROOT / "data" / "faqs.json")


def _gemini_models() -> tuple[str, ...]:
    """Return the configured Gemini model followed by stable fallbacks."""
    configured_model = os.environ.get("GEMINI_MODEL", "").strip()
    return tuple(dict.fromkeys(filter(None, (
        configured_model,
        "gemini-3.5-flash-lite",
        "gemini-3.6-flash",
    ))))


def _gemini_http_error(exc: HTTPError, model: str) -> str:
    """Extract Google's safe error status/message for deployment diagnostics."""
    detail = ""
    try:
        body = exc.read().decode("utf-8", errors="replace")
        payload = json.loads(body)
        error = payload.get("error", {})
        message = str(error.get("message", "")).strip()
        status = str(error.get("status", "")).strip()
        detail = " ".join(part for part in (status, message) if part)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, AttributeError):
        detail = ""

    suffix = f": {detail[:500]}" if detail else ""
    return f"{model} returned HTTP {exc.code}{suffix}"


def answer_with_gemini(question: str, candidates: list[dict]) -> tuple[str | None, str | None]:
    """Use Gemini for general answers, grounded by FAQ context when available."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return None, "GEMINI_API_KEY is not configured."

    context = "\n\n".join(
        f"FAQ {index + 1}\nQuestion: {faq['question']}\nAnswer: {faq['answer']}"
        for index, faq in enumerate(candidates)
    ) or "No relevant SecureBank FAQ was provided."
    payload = {
        "systemInstruction": {
            "parts": [
                {
                    "text": (
                        "You are a helpful general assistant on the SecureBank website. "
                        "For a question about SecureBank, use the FAQ context as the source "
                        "of truth and do not invent bank policies, fees, limits, timelines, "
                        "or procedures. If a specific SecureBank detail is not in the context, "
                        "say you cannot confirm it and advise contacting SecureBank support. "
                        "For general, non-SecureBank questions, answer normally and concisely. "
                        "Do not provide personalized financial, legal, or medical advice."
                    )
                }
            ]
        },
        "contents": [{
            "role": "user",
            "parts": [{
                "text": f"Customer question: {question}\n\nFAQ context:\n{context}"
            }],
        }],
        "generationConfig": {
            "temperature": 0.2,
            "maxOutputTokens": 300,
        },
    }
    errors = []
    for model in _gemini_models():
        request = Request(
            f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "x-goog-api-key": api_key,
            },
            method="POST",
        )
        try:
            with urlopen(request, timeout=15) as response:
                result = json.loads(response.read().decode("utf-8"))
            parts = result["candidates"][0]["content"]["parts"]
            answer = "".join(str(part.get("text", "")) for part in parts).strip()
            if answer:
                return answer, None
            errors.append(f"{model} returned an empty response")
        except HTTPError as exc:
            errors.append(_gemini_http_error(exc, model))
        except (URLError, KeyError, IndexError, TimeoutError, json.JSONDecodeError) as exc:
            errors.append(f"{model} request failed: {exc}")

    error_summary = "Gemini models failed | " + " | ".join(errors)
    print(error_summary)
    return None, error_summary


class handler(BaseHTTPRequestHandler):
    def _send_json(self, payload, status=200):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")

        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_file(self, file_path: Path, content_type: str):
        body = file_path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Cache-Control", "public, max-age=300")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        request_path = urlparse(self.path).path
        static_files = {
            "/": ("index.html", "text/html; charset=utf-8"),
            "/index.html": ("index.html", "text/html; charset=utf-8"),
            "/styles.css": ("styles.css", "text/css; charset=utf-8"),
            "/script.js": ("script.js", "application/javascript; charset=utf-8"),
        }

        if request_path in static_files:
            filename, content_type = static_files[request_path]
            return self._send_file(ROOT / filename, content_type)

        if request_path == "/api/chat":
            return self._send_json({
                "ok": True,
                "service": "SecureBank FAQ Chatbot",
                "method": "FAQ retrieval + Gemini answers",
                "ai_enabled": bool(os.environ.get("GEMINI_API_KEY")),
                "configured_model": os.environ.get("GEMINI_MODEL") or "automatic",
            })

        return self._send_json({"error": "Not found."}, 404)

    def do_POST(self):
        try:
            if urlparse(self.path).path != "/api/chat":
                return self._send_json({"error": "Not found."}, 404)

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

            normalized_question = " ".join(question.lower().split()).rstrip("!.,?")
            if normalized_question in {
                "hi", "hello", "hey", "good morning", "good afternoon", "good evening"
            }:
                return self._send_json({
                    "answer": "Hello! How can I help you today?",
                    "matched": False,
                    "confidence": 1.0,
                    "matched_question": None,
                    "category": "conversation",
                    "source": "built-in",
                })

            all_candidates = matcher.top_matches(question, limit=5)
            # Weak lexical matches are not useful context for a general question.
            has_relevant_faq = bool(all_candidates and all_candidates[0]["score"] >= 0.14)
            candidates = all_candidates if has_relevant_faq else []
            ai_answer, ai_error = answer_with_gemini(question, candidates)

            if ai_answer:
                result = {
                    "answer": ai_answer,
                    "matched": has_relevant_faq,
                    "confidence": all_candidates[0]["score"] if has_relevant_faq else 0.0,
                    "matched_question": all_candidates[0]["question"] if has_relevant_faq else None,
                    "category": all_candidates[0].get("category") if has_relevant_faq else None,
                    "source": "grounded-knowledge" if has_relevant_faq else "general-ai",
                }
            else:
                # Keep FAQ matching available and return a safe diagnostic for logs.
                result = matcher.match(question)
                result["source"] = "faq-matching"
                result["ai_error"] = ai_error
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
