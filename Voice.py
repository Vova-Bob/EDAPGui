# pip install pyttsx3

import json
import logging
import os
import queue
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


class Voice:

    LANGUAGE_KEYWORDS = {
        'en': (
            'english', 'en-us', 'en-gb', 'eng', 'enus', 'en-gb', 'en_'
        ),
        'uk': (
            'ukrain', 'anatol', 'natalia', 'volodymyr', 'marianna', 'oleksa', 'dmytro',
            'uk-', 'uk_', 'ukrainian'
        ),
        'ru': ('russian', 'rus', 'ru-', 'ru_'),
        'de': ('german', 'deutsch', 'de-', 'de_'),
        'fr': ('french', 'franc', 'fr-', 'fr_'),
    }

    def __init__(self, log_func=None):
        self.q = queue.Queue(5)
        self.v_enabled = False
        self.v_quit = False
        self.t = kthread.KThread(target=self.voice_exec, name="Voice", daemon=True)
        self.t.start()
        self.v_id = 0
        self.log_func = log_func
        self._last_voice_warning = None
        self._last_language_warning = None
        self._fallback_localizer = None
        self.ui_language = 'en'
        self.voice_language = 'en'
        self._load_voice_settings()

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
        ui_language = 'en'
        if config:
            language = config.get('VoiceLanguage', language)
            ui_language = config.get('Language', ui_language)
        if language:
            self.voice_language = str(language).lower()
        if ui_language:
            self.ui_language = str(ui_language).lower()

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

    def set_voice_language(self, language):
        if language:
            normalized = str(language).lower()
            if normalized != self.voice_language:
                self.voice_language = normalized
                self._last_language_warning = None

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

    @staticmethod
    def _voice_languages(voice):
        langs = []
        for lang in getattr(voice, 'languages', []) or []:
            if isinstance(lang, bytes):
                try:
                    lang = lang.decode('utf-8')
                except Exception:
                    continue
            lang_str = str(lang).lower()
            lang_str = lang_str.replace('_', '-').replace('\x05', '')
            langs.append(lang_str)
        return langs

    @classmethod
    def matches_language_metadata(cls, languages, name, voice_id, language):
        target = str(language).lower().strip()
        if not target:
            return False
        for lang in languages or []:
            lang_normalized = str(lang).lower()
            if lang_normalized.startswith(target):
                return True
            if f"-{target}" in lang_normalized:
                return True
        if cls._match_language_keywords(voice_id, target):
            return True
        if cls._match_language_keywords(name, target):
            return True
        return False

    @classmethod
    def _match_language_keywords(cls, text, target):
        if not text:
            return False
        lowered = str(text).lower()
        keywords = cls.LANGUAGE_KEYWORDS.get(target, (target,))
        for keyword in keywords:
            if keyword and keyword in lowered:
                return True
        return False

    @classmethod
    def _matches_language(cls, voice, language):
        target = str(language).lower().strip()
        if not target:
            return False
        languages = cls._voice_languages(voice)
        for lang in languages:
            if lang.startswith(target):
                return True
            if f"-{target}" in lang:
                return True
        if cls._match_language_keywords(getattr(voice, 'id', ''), target):
            return True
        if cls._match_language_keywords(getattr(voice, 'name', ''), target):
            return True
        return False

    @staticmethod
    def _matches_ukrainian_name(name: str):
        if not name:
            return False
        lowered = name.lower()
        keywords = (
            'ukrain', 'anatol', 'natalia', 'volodymyr', 'marianna', 'oleksa', 'dmytro', 'uk-', 'ukrainian'
        )
        return any(keyword in lowered for keyword in keywords)

    def _find_voice_for_language(self, voices, language):
        if not voices:
            return None
        target = str(language).lower().strip()
        if not target:
            return None
        for idx, voice in enumerate(voices):
            if self._matches_language(voice, target):
                return idx
        if target == 'uk':
            for idx, voice in enumerate(voices):
                if self._matches_ukrainian_name(getattr(voice, 'name', '')):
                    return idx
        return None

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

    def _select_voice_id(self, voices, previous_id=None):
        normalized_id = self._normalize_voice_id(self.v_id, voices)
        if not voices:
            return normalized_id
        has_language_metadata = any(self._voice_languages(voice) for voice in voices)
        enable_language_search = has_language_metadata or self.voice_language == 'uk'
        language_match = None
        if enable_language_search:
            language_match = self._find_voice_for_language(voices, self.voice_language)
        if language_match is not None:
            if language_match != normalized_id and language_match != previous_id:
                self._emit_log(
                    'log.voice.language_override',
                    language=self.voice_language,
                    name=voices[language_match].name,
                    index=language_match
                )
            normalized_id = language_match
            self._last_language_warning = None
        elif self.voice_language and enable_language_search:
            warning_key = (self.voice_language, normalized_id)
            if self._last_language_warning != warning_key:
                self._last_language_warning = warning_key
                self._emit_log(
                    'log.voice.language_no_match',
                    level='warning',
                    language=self.voice_language,
                    voice_id=normalized_id
                )
        return normalized_id

    def _apply_voice(self, engine, voices, voice_id):
        if not voices:
            return
        try:
            engine.setProperty('voice', voices[voice_id].id)
        except Exception as error:
            self._log_tts_warning(error)

    def _log_available_voices(self, voices):
        if not voices:
            self._emit_log('log.voice.no_voices_installed', level='warning')
            return
        self._emit_log('log.voice.list_available_header')
        for idx, voice in enumerate(voices):
            languages = self._voice_languages(voice)
            language_hint = languages[0] if languages else ''
            suffix = f" [{language_hint}]" if language_hint else ''
            self._emit_log(
                'log.voice.list_available_entry',
                index=idx,
                name=voice.name,
                id=voice.id,
                language=suffix
            )

    def get_voice_options(self):
        engine = pyttsx3.init()
        voices = engine.getProperty('voices') or []
        options = []
        for idx, voice in enumerate(voices):
            languages = self._voice_languages(voice)
            options.append({
                'index': idx,
                'name': voice.name,
                'id': voice.id,
                'languages': languages,
            })
        return options

    def list_voices(self):
        engine = pyttsx3.init()
        voices = engine.getProperty('voices') or []
        self._log_available_voices(voices)

    def voice_exec(self):
        engine = pyttsx3.init()
        voices = engine.getProperty('voices') or []
        self._log_available_voices(voices)
        v_id_current = self._select_voice_id(voices)
        self._apply_voice(engine, voices, v_id_current)
        engine.setProperty('rate', 160)
        current_language = self.voice_language
        while not self.v_quit:
            desired_id = self._select_voice_id(voices, previous_id=v_id_current)
            if desired_id != v_id_current or self.voice_language != current_language:
                current_language = self.voice_language
                if desired_id != v_id_current:
                    v_id_current = desired_id
                    self._apply_voice(engine, voices, v_id_current)

            try:
                words = self.q.get(timeout=1)
            except queue.Empty:
                continue
            self.q.task_done()
            if words is None:
                continue
            try:
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
