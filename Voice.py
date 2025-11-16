# pip install pyttsx3

import json
import logging
import os
import queue
import shutil
import subprocess
import sys
import tempfile
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


class _UkrainianNeuralEngine:

    def __init__(self, voice_name, log_import_error, log_init_failed,
                 log_synthesis_failed, resolve_voice, resolve_stress,
                 voices_cls=None, stress_cls=None, tts_instance=None):
        self.tts = tts_instance
        self.voice = None
        self.stress_mode = None
        self.voice_name = voice_name
        self._log_import_error = log_import_error
        self._log_init_failed = log_init_failed
        self._log_synthesis_failed = log_synthesis_failed
        self._resolve_voice = resolve_voice
        self._resolve_stress = resolve_stress
        self._voices_cls = voices_cls
        self._stress_cls = stress_cls

    def ensure_initialized(self):
        if self.tts is None or self._voices_cls is None or self._stress_cls is None:
            self._log_init_failed(RuntimeError('ukrainian tts components unavailable'))
            return False
        if self.voice is not None and self.stress_mode is not None:
            return True
        try:
            self.voice = self._resolve_voice(self.voice_name, self._voices_cls)
            self.stress_mode = self._resolve_stress(self._stress_cls)
        except Exception as error:
            self._log_init_failed(error)
            self.voice = None
            self.stress_mode = None
            return False
        if self.voice is None or self.stress_mode is None:
            self._log_init_failed(RuntimeError('ukrainian tts components unavailable'))
            return False
        return True

    def speak(self, text: str, tmp_dir, playback_callback):
        if not self.ensure_initialized():
            return False
        tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav', dir=tmp_dir)
        tmp_path = tmp_file.name
        try:
            with tmp_file as handle:
                self.tts.tts(text, self.voice.value, self.stress_mode.value, handle)
            playback_callback(tmp_path)
            return True
        except Exception as error:
            self._log_synthesis_failed(error)
            return False
        finally:
            try:
                os.remove(tmp_path)
            except OSError:
                pass


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
        self._ua_neural_enabled = False
        self._ua_neural_failure_logged = False
        self._ua_neural_engine = None
        self._load_voice_settings()
        self._initialize_ua_engine()

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
        if config:
            language = config.get('VoiceLanguage', language)
            ui_language = config.get('Language', ui_language)
            self.ua_voice_name = config.get('UAVoice', self.ua_voice_name)
            neural_enabled = bool(config.get('UkrainianNeuralTTS', False))
        if language:
            self.voice_language = str(language).lower()
        if ui_language:
            self.ui_language = str(ui_language).lower()
        ua_requested = neural_enabled and self.voice_language.startswith('uk')
        self.ua_neural_enabled = ua_requested
        self._ua_neural_enabled = ua_requested

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

    def _log_ua_tts_import_error(self, error):
        self._emit_log('log.voice.ua_tts_import_error', level='warning', error=str(error))

    def _log_ua_tts_init_failed(self, error):
        self._emit_log('log.voice.ua_tts_init_failed', level='warning', error=str(error))

    def _log_ua_tts_synthesis_failed(self, error):
        self._emit_log('log.voice.ua_tts_synthesis_failed', level='warning', error=str(error))

    def _log_ua_tts_unknown_voice(self, voice_name):
        self._emit_log('log.voice.ua_tts_unknown_voice', level='warning', voice=voice_name)

    def _resolve_ua_neural_voice(self, config_voice_name, voices_cls):
        default_voice = getattr(voices_cls, 'Dmytro', None)
        voice_name = str(config_voice_name).strip() if config_voice_name else ''
        normalized_name = voice_name.lower()
        mapping = {
            'dmytro': getattr(voices_cls, 'Dmytro', default_voice),
            'natalia': getattr(voices_cls, 'Natalia', default_voice),
            'mykyta': getattr(voices_cls, 'Mykyta', default_voice),
            'oleksa': getattr(voices_cls, 'Oleksa', default_voice),
            'tetiana': getattr(voices_cls, 'Tetiana', default_voice),
        }
        resolved = mapping.get(normalized_name, default_voice)
        if resolved is None and hasattr(voices_cls, '__iter__'):
            try:
                resolved = list(voices_cls)[0]
            except Exception:
                resolved = None
        if resolved is None:
            return default_voice
        if normalized_name not in mapping and voice_name:
            self._log_ua_tts_unknown_voice(voice_name)
        return resolved

    def _resolve_ua_stress_mode(self, stress_cls):
        return getattr(stress_cls, 'Dictionary', None) or (list(stress_cls)[0] if hasattr(stress_cls, '__iter__') else None)

    def _should_use_ua_tts(self):
        return self._ua_neural_enabled and self.voice_language.startswith('uk') and not self._ua_neural_failure_logged

    def _initialize_ua_engine(self):
        if not self._should_use_ua_tts() or self._ua_neural_engine is not None:
            return
        try:
            from ukrainian_tts.tts import TTS, Voices, Stress
        except Exception as error:
            self._log_ua_tts_import_error(error)
            self._disable_ua_neural_after_failure()
            self._ua_neural_engine = None
            return
        try:
            ua_engine = _UkrainianNeuralEngine(
                self.ua_voice_name,
                self._log_ua_tts_import_error,
                self._log_ua_tts_init_failed,
                self._log_ua_tts_synthesis_failed,
                self._resolve_ua_neural_voice,
                self._resolve_ua_stress_mode,
                voices_cls=Voices,
                stress_cls=Stress,
                tts_instance=TTS(device="cpu"))
            if not ua_engine.ensure_initialized():
                self._disable_ua_neural_after_failure()
                self._ua_neural_engine = None
                return
            self._ua_neural_engine = ua_engine
        except Exception as error:
            self._log_ua_tts_init_failed(error)
            self._disable_ua_neural_after_failure()
            self._ua_neural_engine = None

    def _disable_ua_neural_after_failure(self):
        self.ua_neural_enabled = False
        self._ua_neural_enabled = False
        self._ua_neural_failure_logged = True
        self._ua_neural_engine = None

    def _play_audio_file(self, filepath):
        if sys.platform.startswith('win'):
            import winsound
            winsound.PlaySound(filepath, winsound.SND_FILENAME)
            return
        player = shutil.which('aplay') or shutil.which('paplay') or shutil.which('afplay')
        if player:
            subprocess.run([player, filepath], check=True)
            return
        message = self._format_localized('log.voice.ua_tts_playback_missing')
        self._emit_log('log.voice.ua_tts_playback_missing', level='warning')
        raise RuntimeError(message)

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
                if self._ua_neural_enabled and self._ua_neural_engine is not None:
                    try:
                        if self._ua_neural_engine.speak(words, None, self._play_audio_file):
                            continue
                    except Exception as error:
                        self._log_ua_tts_synthesis_failed(error)
                        self._disable_ua_neural_after_failure()
                    else:
                        self._disable_ua_neural_after_failure()
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
