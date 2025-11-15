# AGENTS.md  
**Extended Professional Specification for Code Agents / Codex**

## 1. Purpose of This Document
This document defines strict, professional-grade rules for all AI coding agents working on the **Elite Dangerous Autopilot Project**.  
It expands the original guidelines to ensure consistent behavior, safe refactoring, and full compliance with localization, UX, and architecture constraints.

Agents must follow these rules **exactly**, with no deviation.

---

# 2. Project Scope
The repository contains an automation framework for Elite Dangerous, including:

- **EDAPGui.py** — Tkinter GUI  
- **ED_AP.py** — core autopilot engine  
- **EDWayPoint.py**, **EDStationServicesInShip.py**, **Robigo.py** — navigation & automation logic  
- **LocalizationManager** — full UI/log/TTS localization system  
- **OCR modules** (Screen.py, MarketParser.py, CargoParser.py, NavRouteParser.py, StatusParser.py)  
- **Voice.py** — pyttsx3 text-to-speech and optional neural UA TTS  
- **locales/en.json, ru.json, uk.json** — translation files  

The system integrates UI, OCR, TTS, logs, and automation layers that must be unified under a single localization API.

---

# 3. Global Core Principles

### 3.1 Do Not Break Logic
All agents must preserve original project behavior:

- flight automation logic  
- keybind interaction  
- event timing  
- parsing rules  
- physics-related constraints  
- OCR behavior  

**Refactoring must NEVER change outcomes of automation.**

---

### 3.2 Do Not Remove or Rewrite Author Comments
- Existing comments are historically important.
- You may add new comments, but cannot modify or delete original ones.

---

### 3.3 External Dependencies Policy

#### 3.3.1 Baseline Allowed Dependencies
Agents must not introduce new arbitrary external dependencies. Only these packages are allowed by default:

- `tkinter`  
- `paddleocr`  
- `paddlepaddle`  
- `pyttsx3`  
- `keyboard`  
- `mss`  
- `opencv-python`  
- `numpy`  
- `PyAutoGUI`  
- `pynput`  
- `pydantic`  

#### 3.3.2 Explicit Exception: Ukrainian Neural TTS

A single **explicit exception** is allowed for high-quality Ukrainian TTS:

- `ukrainian-tts` — GitHub: `https://github.com/robinhad/ukrainian-tts`

Rules for using this dependency:

1. It may be used **only** inside the voice subsystem (`Voice.py` or a dedicated TTS adapter module used by `Voice.py`).  
2. It is part of **TASK 3 — Ukrainian Voice System** (see below).  
3. Integration must be strictly optional:
   - If `ukrainian_tts` cannot be imported, the system must fall back to **pyttsx3** without breaking.  
   - All fallback messages must be localized.  
4. Agents may:
   - Add it to documentation / README as an optional dependency.  
   - Add it to a requirements file if such file already exists (e.g. `requirements.txt`), clearly marked as optional.  
5. Agents must **never** use `!pip` calls or notebook-only patterns in project source code.

Example reference usage (for agents, not to be pasted literally):

```python
from ukrainian_tts.tts import TTS, Voices, Stress

tts = TTS(device="cpu")
with open("test.wav", mode="wb") as f:
    _, accented = tts.tts(
        "Привіт, як у тебе справи?",
        Voices.Dmytro.value,
        Stress.Dictionary.value,
        f,
    )
Any other new dependency (not listed above) remains forbidden.

3.4 DRY + KISS Across All Contributions
Avoid repetition of UI/log/TTS strings.

Replace duplicated logic with helper functions.

Prefer small composable functions.

Avoid complex abstractions, inheritance, or dynamic magic.

Keep code readable and predictable.

4. Task System (Mandatory Workflow)
Agents may only work within one task at a time.
Switching tasks requires explicit user approval.

TASK 1 — Full GUI Localization (Tkinter Layer)
Goal: Achieve 100% localized UI, error dialogs, button labels, tooltips, and window titles.

Required actions:

Extract all UI text from EDAPGui.py into JSON locale files.

Integrate LocalizationManager everywhere in the GUI.

Implement EN/UA/RU language switch.

Patch layout for long strings.

Remove hardcoded English fallback behavior.

Validate every _t() key exists in all locale files.

Non-goals:

No UI redesign.

No functional changes.

TASK 2 — Full OCR Localization & Russian OCR Support
Required actions:

Move OCR trigger phrases into locale files.

Ensure OCRLanguage flows correctly into PaddleOCR.

Rebuild OCR dictionaries for UA/RU accuracy.

Replace English fallback parsing text.

Synchronize all OCR-related JSON keys.

Non-goals:

No adding alternative OCR engines.

No changing OCR scanning timings.

TASK 3 — Ukrainian Voice System
This task has two layers.

3.1 Baseline pyttsx3 Voice System
Required actions:

Add full uk.json coverage for all TTS messages.

Move all voice templates (phrases sent to TTS) into locale JSON.

Add VoiceLanguage and VoiceID selection logic.

Auto-select appropriate pyttsx3 voice for each language.

Ensure all voice-related errors, warnings and test phrases are localized.

Non-goals:

No replacement of pyttsx3 backend.

No new audio engines other than the explicit exception below.

3.2 Optional Neural Ukrainian TTS (ukrainian-tts)
Goal: Provide a high-quality neural Ukrainian TTS while keeping pyttsx3 as a safe fallback.

Library:

ukrainian-tts (GitHub: https://github.com/robinhad/ukrainian-tts)

3.2.1 Integration Constraints
Do not break existing Voice API.

The public interface (e.g. Voice.say(text_key, **params)) must stay the same.

Callers must not know which engine (pyttsx3 / ukrainian-tts) is used.

Engine Selection & Config

Add a configuration flag in existing config structures (e.g. configs/AP.json), such as:

"UkrainianNeuralTTS": true/false

Use this flag only when VoiceLanguage is Ukrainian.

If the flag is off or import fails, always fall back to pyttsx3.

Lazy Initialization

The ukrainian-tts engine must be initialized lazily to avoid slow startup:

create a small internal adapter (e.g. _UkrainianNeuralEngine),

instantiate TTS only on first Ukrainian utterance when the feature is enabled.

Error Handling (Localized)

If initialization fails (import error, missing models, CUDA issues, etc.), log a localized error via log_ui() and continue with pyttsx3.

All error messages must use keys such as:

log.voice.ua_tts_import_error

log.voice.ua_tts_init_failed

log.voice.ua_tts_synthesis_failed

Audio Handling

Respect current audio pipeline: if the project expects in-memory playback, write to a temporary WAV file or buffer in a way that does not break existing playback.

Ensure paths are OS-safe and cleaned up where needed.

Voices & Stress Controls

Map voice selection in config (e.g. "UAVoice": "Dmytro") to Voices.* from ukrainian-tts in one central place.

Stress mode (Stress.Dictionary, etc.) must be chosen in one function and must not be duplicated.

Licensing & Attribution

The library is MIT-licensed. The code must not embed large parts of the library itself.

A short note may be added in README to credit ukrainian-tts and its author.

3.2.2 Non-goals
Do not modify ukrainian-tts library code.

Do not add any additional TTS libraries.

Do not hardcode paths to models; rely on how ukrainian-tts manages its own assets.

TASK 4 — Final Cleanup & Architecture Consistency
Required actions:

Remove unused imports.

Add new explanatory comments (author comments unchanged).

Validate locale structure.

Ensure no English text bypasses LocalizationManager.

Generate a final technical summary of localization/TTS/OCR state.

Non-goals:

No large-scale file restructuring.

No rewriting features.

5. Localization Compliance Rules (Mandatory)
5.1 All Messages Must Use Locale Keys
This includes:

GUI buttons

status labels

messagebox dialogs

logs

warnings

debug info

TTS messages

fallback strings

OCR triggers

exception messages

Hardcoded English text is strictly prohibited.

5.2 Structured Key Naming
Agents must always create keys in this strict format:

text
Копіювати код
ui.window.title
ui.button.start
ui.button.stop
ui.menu.language
ui.message.error

log.autopilot.has_destination_debug
log.trade.debug_plan_buy
log.cargo.retry_attempt
log.status.read_error
log.screen.window_not_found

voice.pronunciation.krait
voice.demo.hello
voice.warning.tts_missing
voice.ua.neural_enabled
voice.ua.neural_fallback_to_pyttsx3

ocr.trigger.supercruise_exit
ocr.trigger.disengage
ocr.trigger.interdiction
Keys must be:

hierarchical

consistent

concise

stable

5.3 Parameterized Strings
Use placeholders for all dynamic strings, for example:

json
Копіювати код
"log.waypoint.file_invalid": "Waypoint file {filename} is invalid.",
"log.trade.debug_plan_buy": "Attempting to buy {qty} of {item}.",
"log.screen.window_not_found": "Window '{window}' could not be detected.",
"log.voice.ua_tts_import_error": "Failed to load Ukrainian neural TTS library.",
"log.voice.ua_tts_synthesis_failed": "Ukrainian neural TTS synthesis failed; falling back to standard voice."
5.4 TTS / log_ui / speak_ui Unification
All modules must use:

log_ui(key, **params)

speak_ui(key, **params)

_t(key, **params)

_log() wrappers where present

Never use:

print()

logger.debug("raw English text")

direct English strings

6. Diagnostics, Debugging & Fallback Behavior
6.1 Debug Logs Must Be Localized Too
All debug-level messages must go through localization.

Forbidden:

python
Копіювати код
logger.debug("Attempting to buy 5 tons of Water...")
Correct:

python
Копіювати код
log_ui("log.trade.debug_plan_buy", qty=5, item="Water")
6.2 Voice Fallback Messages
Absolutely all fallback text in Voice.py must be in JSON:

missing voice

error initializing engine

pronunciation replacements

demo phrases

neural TTS import/init/synthesis errors

6.3 Parser Fallback Error Messages
All parsers (MarketParser, CargoParser, NavRouteParser, StatusParser) must move fallback text into locale files.

Forbidden:

python
Копіювати код
print("Status file attempt:", attempt)
logger.warning("Failed to read NavRoute file")
Correct:

python
Копіювати код
log_func("log.status.retry_attempt", attempt=attempt)
log_func("log.navroute.read_error", filename=filename)
7. System Modules Requiring Strict Localization (Full Compliance)
Module	Required fixes	Priority
ED_AP.py	TTS world types, debug logs, autopilot status messages	🔴 High
EDWayPoint.py	JSON validation messages, fallback warnings	🔴 High
EDStationServicesInShip.py	trading debug & diagnostic logs	🔴 High
Parsers (Market, Cargo, NavRoute, Status)	I/O errors, retry text, fallback templates	🟠 Medium
Screen.py	window detection/focus errors	🟠 Medium
Voice.py	fallback text, pronunciation rules, UA neural TTS	🟠 Medium
Robigo.py	scenario text, status prints	🟡 Low

Agents must resolve high-priority modules first.

8. TTS / OCR / GUI Interaction Rules
8.1 TTS Always Receives Translated Strings
No English parameters may be passed into TTS:

planet types

body names

warnings

autopilot states

Instead of raw text ("Earth", "Water"), agents must pass localization keys:

text
Копіювати код
world.earth
world.water
world.ammonia
8.2 No English Output in GUI Log Panel
The GUI log panel receives text exclusively via log_ui.

8.3 No Direct print() Allowed Anywhere
Every output must go through:

_log()

log_ui()

speak_ui()

_t()

9. File Modification Priority (Strict Order)
Agents must modify files in this sequence unless instructed otherwise:

EDAPGui.py — UI extraction + localization

LocalizationManager.py — fix keys, unify interfaces

locales/*.json — maintain key coverage

ED_AP.py — TTS/parameters cleanup

Voice.py — fallback text + Ukrainian neural TTS wrapper

configs/AP.json — ensure config linkage

README.md — document new keys/features and optional ukrainian-tts support

10. Output Requirements for All Agent Work
Agents must always:

Be clear and minimal in explanations.

Focus on the relevant code and context only.

Use professional formatting.

Avoid unnecessary verbosity.

10.1 Environments With Direct Repository Write Access
If your runtime environment provides tools to edit files directly (for example, apply_edit, write_file, or similar):

You MUST apply safe, small, task-aligned changes directly to the project files.

You should treat diffs as a reporting tool, not as your primary output.

After editing, respond with:

a short summary of what changed,

the list of edited files and functions,

optionally a small, focused diff snippet for human review.

10.2 Environments Without Direct Write Access
If your environment is effectively read-only and cannot modify files:

Produce strict unified diffs in fenced ```diff code blocks.

Include full functions if they were modified.

Keep the diff minimal and tightly scoped to the described task.

This document regulates what may be changed; whether you apply edits directly or output diffs depends on the capabilities of your environment.

11. Safety & Logic Integrity Rules
The following must NEVER be modified:

autopilot flight sequences

keybinding execution timing

OCR capture timing

game physics assumptions

algorithmic decision making

navigation math

Agents may adjust:

UI layout

string keys

debug/log behavior

TTS output (including adding optional Ukrainian neural TTS)

comments

helper functions

But cannot interfere with core automation.

12. When Agents Are Unsure
Agents must:

Ask for clarification.

Request the specific file.

Avoid guessing core behavior.

Never generate incomplete or speculative changes to core logic.

13. Repository Write Access Clarification
If you are a tool-enabled agent (e.g. Codex or similar) with full read/write access to this repository:

You are explicitly allowed to modify project files in-place, as long as you fully respect all rules in this AGENTS.md.

You should prefer applying changes directly over merely suggesting them, unless the higher-level system explicitly restricts you to suggestions.

All edits must remain small, localized, and aligned with the currently active TASK (1–4).

14. End of Extended AGENTS.md
