import json
import logging
import os
import tempfile
from http.server import BaseHTTPRequestHandler, HTTPServer

import winsound
from ukrainian_tts.tts import Stress, TTS, Voices

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8765


class UATTSRequestHandler(BaseHTTPRequestHandler):
    tts_engine = None
    default_voice = None
    stress_mode = None

    def _send_json(self, status_code, payload):
        response = json.dumps(payload).encode('utf-8')
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(response)))
        self.end_headers()
        self.wfile.write(response)

    def _resolve_voice(self, voice_name):
        if not voice_name:
            return self.default_voice
        normalized = str(voice_name).strip()
        candidate = getattr(Voices, normalized, None)
        if candidate is None:
            candidate = getattr(Voices, normalized.capitalize(), None)
        if candidate is None:
            return self.default_voice
        return candidate

    def do_POST(self):
        if self.path != "/speak":
            self.send_error(404)
            return
        content_length = int(self.headers.get('Content-Length', 0))
        raw_body = self.rfile.read(content_length) if content_length > 0 else b''
        try:
            payload = json.loads(raw_body.decode('utf-8')) if raw_body else {}
        except Exception as error:
            logging.exception("Failed to parse request: %s", error)
            self._send_json(400, {"status": "error", "error": "invalid json"})
            return
        text = str(payload.get('text', '')).strip()
        voice_name = payload.get('voice')
        if not text:
            self._send_json(400, {"status": "error", "error": "empty text"})
            return
        tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
        try:
            with tmp_file as handle:
                voice_choice = self._resolve_voice(voice_name)
                stress_mode = self.stress_mode
                voice_value = voice_choice.value if hasattr(voice_choice, 'value') else voice_choice
                stress_value = stress_mode.value if hasattr(stress_mode, 'value') else stress_mode
                self.tts_engine.tts(text, voice_value, stress_value, handle)
            winsound.PlaySound(tmp_file.name, winsound.SND_FILENAME | winsound.SND_ASYNC)
            self._send_json(200, {"status": "ok"})
        except Exception as error:
            logging.exception("Ukrainian TTS synthesis failed: %s", error)
            self._send_json(500, {"status": "error", "error": str(error)})
        finally:
            try:
                os.remove(tmp_file.name)
            except OSError:
                pass

    def log_message(self, format, *args):
        logging.info("%s - - %s", self.address_string(), format % args)


def create_server(host=DEFAULT_HOST, port=DEFAULT_PORT):
    logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s: %(message)s")
    tts_engine = TTS(device="cpu")
    UATTSRequestHandler.tts_engine = tts_engine
    UATTSRequestHandler.default_voice = getattr(Voices, 'Dmytro', list(Voices)[0])
    UATTSRequestHandler.stress_mode = getattr(Stress, 'Dictionary', list(Stress)[0])
    server = HTTPServer((host, port), UATTSRequestHandler)
    logging.info("Ukrainian TTS bridge listening on http://%s:%s/speak", host, port)
    return server


def main():
    server = create_server()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logging.info("Stopping Ukrainian TTS bridge")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
