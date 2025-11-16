# pip install pyttsx3

import json
import logging
import os
import queue
import urllib.request
from time import sleep

import kthread
import pyttsx3
from simple_localization.localization import LocalizationManager

#rate = voiceEngine.getProperty('rate')
#volume = voiceEngine.getProperty('volume')
#voice = voiceEngine.getProperty('voice')
#voiceEngine.setProperty('rate', newVoiceRate)
#voiceEngine.setProperty('voice', voice.id)   id = 0, 1, ...

"""
File:Voice.py

Description:
  Class to enapsulate the Text to Speech package in python

To Use:
  See main() at bottom as example

Author: sumzer0@yahoo.com

"""


class _UATTSBridgeClient:

    def __init__(self, server_url, voice_name, log_unavailable, log_error):
        self.server_url = server_url
        self.voice_name = voice_name
        self._log_unavailable = log_unavailable
        self._log_error = log_error
        self._enabled = bool(server_url)

    def is_enabled(self):
        return self._enabled and bool(self.server_url)

    def disable(self):
        self._enabled = False

    def speak(self, text: str):
        if not self.is_enabled():
            return False
        payload = {"text": text}
        if self.voice_name:
            payload["voice"] = self.voice_name
        try:
            data = json.dumps(payload).encode('utf-8')
            request = urllib.request.Request(
                self.server_url,
                data=data,
                headers={'Content-Type': 'application/json'},
                method='POST'
            )
            with urllib.request.urlopen(request, timeout=3) as response:
                status_code = response.getcode()
                response_body = response.read()
            if status_code != 200:
                self._log_unavailable(f"HTTP {status_code}")
                self.disable()
                return False
            parsed = json.loads(response_body.decode('utf-8')) if response_body else {}
            if parsed.get('status') == 'ok':
                return True
            self._log_error(parsed.get('error', 'unknown'))
        except Exception as error:
            self._log_unavailable(error)
        self.disable()
        return False


class Voice:

    def __init__(self, log_func=None):
        self.q = queue.Queue(5)
        self.v_enabled = False
        self.v_quit = False
        self.t = kthread.KThread(target=self.voice_exec, name="Voice", daemon=True)
        self.t.start()
        self.v_id = 0
        self.log_func = log_func
        self._last_voice_warning = None
        self._fallback_localizer = None
        self.ui_language = 'en'
        self.voice_language = 'en'
        self.ua_voice_name = 'Dmytro'
        self.ua_neural_enabled = False
        self.ua_tts_bridge_url = 'http://127.0.0.1:8765/speak'
        self._ua_bridge_client = None
        self._ua_bridge_failed = False
        self._load_voice_settings()
        self._initialize_ua_bridge()

    def _read_config(self):
        config_path = os.path.join(os.path.dirname(__file__), 'configs', 'AP.json')
        try:
            with open(config_path, 'r', encoding='utf-8') as config_file:
                return json.load(config_file)
        except Exception:
            return None

    def _load_voice_settings(self):
        config = self._read_config()
        language = 'en'
        neural_enabled = False
        ui_language = 'en'
        bridge_url = self.ua_tts_bridge_url
        if config:
            language = config.get('VoiceLanguage', language)
            ui_language = config.get('Language', ui_language)
            self.ua_voice_name = config.get('UAVoice', self.ua_voice_name)
            neural_enabled = bool(config.get('UkrainianNeuralTTS', False))
            bridge_url = config.get('UATTSBridgeURL', bridge_url)
        if language:
            self.voice_language = str(language).lower()
        if ui_language:
            self.ui_language = str(ui_language).lower()
        if bridge_url:
            self.ua_tts_bridge_url = str(bridge_url)
        ua_requested = neural_enabled and self.voice_language.startswith('uk')
        self.ua_neural_enabled = ua_requested
        self._ua_bridge_failed = False

    def say(self, vSay):
        if self.v_enabled:
            # A better way to correct mis-pronunciation?
            vSay = vSay.replace(' Mk V ', ' mark five ')
            vSay = vSay.replace(' Mk ', ' mark ')
            vSay = vSay.replace(' Krait ', ' crate ')
            self.q.put(vSay)

    def set_off(self):
        self.v_enabled = False

    def set_on(self):
        self.v_enabled = True
        
    def set_voice_id(self, id):
        self.v_id = id

    def quit(self):
        self.v_quit = True
        
    def _get_localizer(self):
        if self._fallback_localizer is not None:
            return self._fallback_localizer
        locales_dir = os.path.join(os.path.dirname(__file__), 'locales')
        try:
            self._fallback_localizer = LocalizationManager(locales_dir, self.ui_language)
        except Exception:
            try:
                self._fallback_localizer = LocalizationManager(locales_dir, 'en')
            except Exception:
                self._fallback_localizer = None
        return self._fallback_localizer

    def _format_localized(self, key, **kwargs):
        localizer = self._get_localizer()
        try:
            template = localizer[key] if localizer else key
            return template.format(**kwargs)
        except Exception:
            return f"{key}: {kwargs}" if kwargs else key

    def _emit_log(self, key, level='info', **kwargs):
        if callable(self.log_func):
            self.log_func(key, level=level, **kwargs)
            return
        message = self._format_localized(key, **kwargs)
        logger = logging.getLogger(__name__)
        level_method = getattr(logger, level, logger.info)
        level_method(message)

    def _log_voice_error(self, voice_id, total, fallback=0):
        warning_key = (voice_id, total)
        if self._last_voice_warning == warning_key:
            return
        self._last_voice_warning = warning_key
        self._emit_log('log.voice.id_out_of_range', level='warning',
                       voice_id=voice_id, total=total, fallback=fallback)

    def _log_tts_warning(self, error):
        self._emit_log('log.voice.tts_error', level='warning', error=str(error))

    def _log_ua_tts_bridge_unavailable(self, error):
        self._emit_log('log.voice.ua_tts_bridge_unavailable', level='warning', error=str(error))

    def _log_ua_tts_bridge_error(self, error):
        self._emit_log('log.voice.ua_tts_bridge_error', level='warning', error=str(error))

    def _initialize_ua_bridge(self):
        if not self.ua_neural_enabled or self._ua_bridge_failed:
            return
        if not self.voice_language.startswith('uk'):
            return
        if not self.ua_tts_bridge_url:
            return
        self._ua_bridge_client = _UATTSBridgeClient(
            self.ua_tts_bridge_url,
            self.ua_voice_name,
            self._log_ua_tts_bridge_unavailable,
            self._log_ua_tts_bridge_error
        )

    def _disable_ua_bridge_after_failure(self):
        self.ua_neural_enabled = False
        self._ua_bridge_failed = True
        if self._ua_bridge_client:
            self._ua_bridge_client.disable()

    def _normalize_voice_id(self, requested_id, voices):
        fallback = 0
        total = len(voices)
        if total == 0:
            return fallback
        try:
            requested_id = int(requested_id)
        except (TypeError, ValueError):
            self._log_voice_error(requested_id, total, fallback)
            return fallback
        if requested_id < 0 or requested_id >= total:
            self._log_voice_error(requested_id, total, fallback)
            return fallback
        self._last_voice_warning = None
        return requested_id

    def _apply_voice(self, engine, voices, voice_id):
        if not voices:
            return
        try:
            engine.setProperty('voice', voices[voice_id].id)
        except Exception as error:
            self._log_tts_warning(error)

    def list_voices(self):
        engine = pyttsx3.init()
        voices = engine.getProperty('voices')
        if not voices:
            self._emit_log('log.voice.no_voices_installed', level='warning')
            return
        self._emit_log('log.voice.list_available_header')
        for idx, voice in enumerate(voices):
            self._emit_log(
                'log.voice.list_available_entry',
                index=idx,
                name=voice.name,
                id=voice.id
            )

    def voice_exec(self):
        engine = pyttsx3.init()
        voices = engine.getProperty('voices')
        v_id_current = self._normalize_voice_id(self.v_id, voices)
        self._apply_voice(engine, voices, v_id_current)
        engine.setProperty('rate', 160)
        while not self.v_quit:
            # check if the voice ID changed
            if self.v_id != v_id_current:
                new_id = self._normalize_voice_id(self.v_id, voices)
                if new_id != v_id_current:
                    v_id_current = new_id
                    self._apply_voice(engine, voices, v_id_current)

            try:
                words = self.q.get(timeout=1)
            except queue.Empty:
                continue
            self.q.task_done()
            if words is None:
                continue
            try:
                bridge_ready = (
                    self.ua_neural_enabled
                    and not self._ua_bridge_failed
                    and self._ua_bridge_client is not None
                    and self._ua_bridge_client.is_enabled()
                )
                if bridge_ready and self.voice_language.startswith('uk'):
                    if self._ua_bridge_client.speak(words):
                        continue
                    self._disable_ua_bridge_after_failure()
                engine.say(words)
                engine.runAndWait()
            except Exception as error:
                self._log_tts_warning(error)


def main():
    v = Voice()
    v.set_on()
    sleep(2)
    v.say(v._format_localized('voice.demo.sample_phrase'))
    sleep(2)
    v.say(v._format_localized('voice.demo.sample_phrase'))
    sleep(2)
    v.quit()


if __name__ == "__main__":
    main()
