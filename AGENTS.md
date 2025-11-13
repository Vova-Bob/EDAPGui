# AGENTS.md – Project Rules for Code Agents / Codex

## Overview
This repository contains the Elite Dangerous Autopilot GUI and automation tools:
- **Tkinter interface (EDAPGui.py)**
- **Autopilot core logic (ED_AP.py)**
- **Localization system (LocalizationManager)**
- **OCR using PaddleOCR**
- **Voice system using pyttsx3 (Voice.py)**
- **Config folder and JSON locales (locales/en.json, ru.json, uk.json)**

The goal of all agents is to improve the project **without breaking existing logic**, following controlled refactoring rules.

---

## Agent Behavior Rules

### 1. DO NOT modify or remove original author comments
These comments describe internal logic and must remain intact.  
Agents may add **new comments**, but never replace or delete old ones.

---

### 2. DO NOT introduce new external dependencies
Only the following libraries are allowed:
- tkinter
- paddleocr
- paddlepaddle
- pyttsx3
- keyboard
- mss
- opencv-python
- numpy
- PyAutoGUI
- pynput
- pydantic

No new pip packages may be added.

---

### 3. Maintain DRY + KISS principles
- No copy–paste logic
- Prefer helper functions
- Prefer clean structure
- Avoid deep inheritance or overengineering

---

### 4. Work only within one task at a time
There are exactly **four official tasks** in this project:

### **TASK 1 — Full UI Localization (Tkinter)**
- Extract ALL text from EDAPGui.py into JSON locale files.
- Integrate LocalizationManager into the GUI.
- Add language switcher: EN / UA / RU.
- Fix layout for longer translations.
- No breaking changes.

### **TASK 2 — Full Russian OCR Support**
- Move all OCR trigger text to locale files.
- Synchronize JSON keys between languages.
- Correctly pass OCRLanguage to PaddleOCR.
- Verify OCR behavior on Russian UI.

### **TASK 3 — Ukrainian Voice System**
- Add uk.json.
- Move voice messages to locale JSON.
- Add VoiceLanguage + VoiceID logic.
- Auto-select appropriate pyttsx3 voice.
- Keep original comments intact.

### **TASK 4 — Final Cleanup**
- Remove unused imports.
- Add new comments (do not touch original).
- Verify locale keys.
- Generate technical summary.

Agents must ask before switching to another task.

---

## Interaction Rules

### When reading code:
- Analyze structure.
- Identify hard-coded text.
- Detect repeated logic.
- Detect UI elements needing layout fixes.

### When modifying:
- Produce isolated diffs.
- Keep code readable.
- Never break compatibility.
- Never rewrite entire files unless asked to.

### When generating localization keys:
- Use consistent structured keys:
ui.window.title
ui.button.start
ui.button.stop
ui.tooltip.start
ui.message.error
voice.welcome
voice.route_assist_on
ocr.trigger.disengage


---

## Language Switching Support
Agents must maintain the ability to switch:
- **UI Language** (EN/UA)
- **Voice Language**
- **Game OCR Language**

Switch must be in menu:


Help → Language →
• English
• Українська


---

## Safety Requirements
- Never change autopilot logic.
- Never alter ED/AP flight algorithms.
- Never change bindings or keypress logic.
- Never alter time-critical OCR code.

---

## Files of Primary Importance
Priority order for modification:

1. `EDAPGui.py`
2. `LocalizationManager.py`
3. `locales/*.json`
4. `ED_AP.py`
5. `Voice.py`
6. `configs/AP.json`
7. `README.md`

---

## Output Format Requirements for Agents
All outputs must be:

- Minimal, clear, professional.
- With explanations when needed.
- With code blocks for every change.
- No unnecessary verbosity.

---

## When In Doubt
If an agent is unsure:
- Ask for clarification before acting.
- Request the specific file.
- Never guess architecture.

---

## End of AGENTS.md
