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
- **OCR modules** (Screen.py, MarketParser, CargoParser, NavRouteParser, StatusParser)  
- **Voice.py** — pyttsx3 text-to-speech  
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

### 3.3 No New External Dependencies
Allowed packages only:

tkinter, paddleocr, paddlepaddle, pyttsx3, keyboard, mss, opencv-python, numpy, PyAutoGUI, pynput, pydantic

No new pip modules may be introduced under any circumstances.

---

### 3.4 DRY + KISS Across All Contributions
- Avoid repetition of UI/log/TTS strings  
- Replace duplicated logic with helper functions  
- Prefer small composable functions  
- Avoid complex abstractions, inheritance, or dynamic magic  
- Keep code readable and predictable  

---

# 4. Task System (Mandatory Workflow)

Agents may only work within **one task at a time**.  
Switching tasks requires explicit user approval.

---

## **TASK 1 — Full GUI Localization (Tkinter Layer)**
**Goal:** Achieve 100% localized UI, error dialogs, button labels, tooltips, and window titles.

Required actions:
- Extract all UI text from EDAPGui.py into JSON locale files  
- Integrate LocalizationManager everywhere in the GUI  
- Implement EN/UA/RU language switch  
- Patch layout for long strings  
- Remove hardcoded English fallback behavior  
- Validate every _t() key exists in all locale files  

Non-goals:
- No UI redesign  
- No functional changes  

---

## **TASK 2 — Full OCR Localization & Russian OCR Support**
Required actions:
- Move OCR trigger phrases into locale files  
- Ensure OCRLanguage flows correctly into PaddleOCR  
- Rebuild OCR dictionaries for UA/RU accuracy  
- Replace English fallback parsing text  
- Synchronize all OCR-related JSON keys  

Non-goals:
- No adding alternative OCR engines  
- No changing OCR scanning timings  

---

## **TASK 3 — Ukrainian Voice System**
Required actions:
- Add complete Ukrainian TTS dictionary  
- Move all voice templates into locale JSON  
- Add VoiceLanguage + VoiceID selection  
- Localize pronunciation rules  
- Store TTS fallback messages in locales  

Non-goals:
- No replacing pyttsx3 backend  
- No new audio dependencies  

---

## **TASK 4 — Final Cleanup & Architecture Consistency**
Required actions:
- Remove unused imports  
- Add new explanatory comments (author comments unchanged)  
- Validate locale structure  
- Ensure no English text bypasses LocalizationManager  
- Generate final technical summary  

Non-goals:
- No file restructuring  
- No rewriting features  

---

# 5. Localization Compliance Rules (Mandatory)

### 5.1 All messages must use locale keys
This includes:
- GUI buttons  
- status labels  
- messagebox dialogs  
- logs  
- warnings  
- debug info  
- TTS messages  
- fallback strings  
- OCR triggers  
- exception messages  

**Hardcoded English text is strictly prohibited.**

---

### 5.2 Structured Key Naming
Agents must always create keys in this strict format:

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

ocr.trigger.supercruise_exit
ocr.trigger.disengage
ocr.trigger.interdiction

yaml
Копіювати код

Keys must be:
- hierarchical  
- consistent  
- concise  
- stable  

---

### 5.3 Parameterized Strings
Use placeholders for all dynamic strings:

"log.waypoint.file_invalid": "Waypoint file {filename} is invalid."
"log.trade.debug_plan_buy": "Attempting to buy {qty} of {item}."
"log.screen.window_not_found": "Window '{window}' could not be detected."

yaml
Копіювати код

---

### 5.4 TTS / log_ui / speak_ui Unification  
All modules must use:
- `log_ui(key, **params)`
- `speak_ui(key, **params)`
- `_t(key, **params)`  
- `_log()` wrappers where present  

Never use:
- `print()`  
- `logger.debug("text")`  
- raw English strings  

---

# 6. Diagnostics, Debugging & Fallback Behavior

### 6.1 Debug logs must be localized too
All debug-level messages must go through localization.

Forbidden:
logger.debug("Attempting to buy 5 tons of Water...")

makefile
Копіювати код

Correct:
log_ui("log.trade.debug_plan_buy", qty=5, item="Water")

yaml
Копіювати код

---

### 6.2 Voice fallback messages
Absolutely all fallback text in Voice.py must be in JSON:
- missing voice  
- error initializing engine  
- pronunciation replacements  
- demo phrases  

---

### 6.3 Parser fallback error messages
All parsers (MarketParser, CargoParser, NavRouteParser, StatusParser) must move fallback text into locale files.

Forbidden:
"Status file attempt:"
"Failed to read NavRoute file"

makefile
Копіювати код

Correct:
log_func("log.status.retry_attempt", attempt=n)

yaml
Копіювати код

---

# 7. System Modules Requiring Strict Localization (Full Compliance)

| Module | Required fixes | Priority |
|-------|----------------|----------|
| ED_AP.py | TTS world types, debug logs, autopilot status messages | 🔴 High |
| EDWayPoint.py | JSON validation messages, fallback warnings | 🔴 High |
| EDStationServicesInShip.py | trading debug & diagnostic logs | 🔴 High |
| Parsers (Market, Cargo, NavRoute, Status) | I/O errors, retry text, fallback templates | 🟠 Medium |
| Screen.py | window detection/focus errors | 🟠 Medium |
| Voice.py | fallback text, pronunciation rules | 🟠 Medium |
| Robigo.py | scenario text, status prints | 🟡 Low |

Agents must resolve high-priority modules **first**.

---

# 8. TTS / OCR / GUI Interaction Rules

### 8.1 TTS always receives translated strings
No English parameters may be passed into TTS:
- planet types  
- body names  
- warnings  
- autopilot states  

Instead of raw text (“Earth”, “Water”), agents must pass localization keys:
world.earth
world.water
world.ammonia

yaml
Копіювати код

---

### 8.2 No English output allowed in GUI log panel
The GUI log panel receives text exclusively via `log_ui`.

---

### 8.3 No direct print() allowed anywhere
Every output must go through:
- `_log()`
- `log_ui()`
- `speak_ui()`
- `_t()`

---

# 9. File Modification Priority (Strict Order)
Agents must modify files in this sequence unless instructed otherwise:

1. **EDAPGui.py** — UI extraction + localization  
2. **LocalizationManager.py** — fix keys, unify interfaces  
3. **locales/*.json** — maintain key coverage  
4. **ED_AP.py** — TTS/parameters cleanup  
5. **Voice.py** — replace fallback text  
6. **configs/AP.json** — ensure config linkage  
7. **README.md** — document new keys/features  

---

# 10. Output Requirements for All Agent Work
Agents must always produce:

- Clear and minimal explanations  
- Focused context: only related code  
- Strict diffs in fenced ```diff blocks  
- Full functions if modified  
- Professional formatting  
- No unnecessary words  

---

# 11. Safety & Logic Integrity Rules

The following must NEVER be modified:
- autopilot flight sequences  
- keybinding execution timing  
- OCR capture timing  
- game physics assumptions  
- algorithmic decision making  
- navigation math  

Agents may adjust:
- UI layout  
- string keys  
- debug/log behavior  
- TTS output  
- comments  
- helper functions  

But cannot interfere with core automation.

---

# 12. When Agents Are Unsure
Agents must:
1. Ask for clarification  
2. Request the specific file  
3. Avoid guessing behavior  
4. Never generate incomplete assumptions  

---

# 13. End of Extended AGENTS.md
