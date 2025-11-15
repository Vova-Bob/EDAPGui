# pip install pyttsx3

from threading import Thread
import kthread
import queue
import pyttsx3
from time import sleep

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

    def __init__(self, log_func=None):
        self.q = queue.Queue(5)
        self.v_enabled = False
        self.v_quit = False
        self.t = kthread.KThread(target=self.voice_exec, name="Voice", daemon=True)
        self.t.start()
        self.v_id = 0
        self.log_func = log_func

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
        
    def _log_voice_error(self, voice_id, total, fallback=0):
        if callable(self.log_func):
            self.log_func('log.voice.id_out_of_range', level='warning',
                          voice_id=voice_id, total=total, fallback=fallback)
        else:
            print(f"Voice ID {voice_id} out of range (only {total} voices). Using {fallback}.")

    def _log_tts_warning(self, error):
        if callable(self.log_func):
            self.log_func('log.voice.tts_error', level='warning', error=str(error))
        else:
            print(f"TTS warning: {error}")

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
        for idx, voice in enumerate(voices):
            print(f"{idx}: {voice.name} ({voice.id})")
        if not voices:
            print("No voices installed.")

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
                engine.say(words)
                engine.runAndWait()
            except Exception as error:
                self._log_tts_warning(error)


def main():
    v = Voice()
    v.set_on()
    sleep(2)
    v.say("Hey dude")
    sleep(2)
    v.say("whats up")
    sleep(2)
    v.quit()


if __name__ == "__main__":
    main()
