# Technical Documentation: EDAPGui – Elite Dangerous Autopilot

## 1. Project Overview

**EDAPGui** is an automation system for *Elite Dangerous* with a Tkinter-based GUI.  
It controls multiple autopilot assistance modes using computer vision, OCR, game journal parsing and simulated keyboard input.

### Core Objectives

- Automate long-distance FSD route navigation (with fuel management).
- Provide supercruise assistance and docking support.
- Execute waypoint-based trading routes.
- Automate Robigo passenger mission loops.
- Provide AFK combat/defensive assistance (interdiction, etc.).

### High-Level Architecture

- **GUI Layer (EDAPGui.py)**
  - Tkinter UI, layout, controls, menus, settings.
  - Logging panel, localization integration, hotkey configuration.

- **Autopilot Core (ED_AP.py)**
  - Central state machine for all assist modes.
  - Orchestrates OCR, input, journal, waypoints and safety logic.

- **Game Interface / Data Sources**
  - **Screen.py + OCR.py** – screen capture and text recognition.
  - **EDJournal.py + StatusParser.py** – journal & status.json parsing.
  - **EDKeys.py + directinput.py** – keyboard control.
  - **Overlay.py** – debug overlay.

- **Domain Modules**
  - **EDWayPoint.py** – route and trading execution.
  - **EDGalaxyMap.py / EDSystemMap.py / EDNavigationPanel.py** – map & panel automation.
  - **Robigo.py** – Robigo mission automation.
  - **EDShipControl.py / EDInterdictionEscape.py / EDafk_combat.py** – ship flight and combat assists.

- **Support**
  - **Voice.py** – TTS and voice prompts.
  - **configs/** (JSON) – app, resolution, ship settings.
  - **locales/** – localization.
  - **test/** – tests and debug scripts.
  - **EDlogger.py** – logging.

---

## 2. Main Modules and Responsibilities

### GUI & Entry

- **EDAPGui.py**
  - Main entry point & GUI.
  - Class `APGui` manages layout, tabs, buttons, checkboxes, status panel.
  - Handles callbacks from `EDAutopilot` and user actions (start/stop assists, load waypoint file, language selection).

- **start_ed_ap.bat / install_requirements.bat**
  - Convenience scripts to set up environment and run the app.

### Autopilot Core

- **ED_AP.py**
  - Class `EDAutopilot` – main autopilot engine.
  - Manages:
    - FSD assist, SC assist, Robigo assist, AFK combat, etc.
    - Global config (`AP.json`) and runtime flags.
    - `log_ui()` / `speak_ui()` for localized messages.
  - Uses:
    - `Screen`, `OCR`, `EDKeys`, `EDJournal`, `EDWayPoint`, `StatusParser`, `Overlay`, `Voice`.

### Navigation & Waypoints

- **EDWayPoint.py**
  - Loads and validates waypoint JSON files from `waypoints/`.
  - Tracks current waypoint, `Completed`, `Skip`, and `REPEAT` logic.
  - Trading automation: sell/buy commodities at stations.

- **EDNavigationPanel.py / EDGalaxyMap.py / EDSystemMap.py / EDStationServicesInShip.py**
  - Automate respective UI panels and maps (select system, station, cartographics, etc.).

- **EDShipControl.py**
  - Low-level ship maneuver control (pitch, roll, thrust) by sending key inputs.

### Data Processing & Recognition

- **OCR.py**
  - PaddleOCR + OpenCV-based text recognition.
  - Screen region-based OCR for HUD, menus, system names, disengage prompts, etc.
  - Normalization and similarity checking for noisy OCR results.

- **Screen.py / Screen_Regions.py / Image_Templates.py**
  - Screen capture (mss).
  - Coordinate and region definitions, resolution scaling.
  - Template matching for UI elements.

- **MarketParser.py / CargoParser.py / NavRouteParser.py**
  - Parse market, cargo and navigation route data.

- **StatusParser.py**
  - Reads and normalizes `Status.json`.
  - Provides boolean flags and structured data (docked, in supercruise, mass-locked, etc.).

- **EDJournal.py**
  - Monitor Elite Dangerous journal logs.
  - Extract events for route progress, missions, travel and combat.

### Input, Messaging & Voice

- **EDKeys.py / directinput.py**
  - Input simulation (DirectInput, keyboard events).
  - Bindings are read from Elite Dangerous keybindings XML.

- **EDMesg/** + `EDAP_EDMesg_*.py`
  - Messaging and IPC between components (client/provider).

- **Voice.py**
  - TTS with pyttsx3 and Windows voices.
  - Multi-language support (EN, UK, RU, etc.) for spoken messages.

### Utilities & Support

- **EDlogger.py** – central logging wrapper (file + console + GUI panel).
- **MousePt.py**, **WindowsKnownPaths.py** – helper utilities.
- **test/** – test scripts for OCR, map interactions, waypoint configs, etc.

---

## 3. Project Structure (Summary)

```text
EDAPGui/
├── EDAPGui.py                 # Main GUI + entry point
├── ED_AP.py                   # Autopilot core
├── Core & Automation
│   ├── EDWayPoint.py
│   ├── EDShipControl.py
│   ├── EDNavigationPanel.py
│   ├── EDGalaxyMap.py
│   ├── EDSystemMap.py
│   ├── EDStationServicesInShip.py
│   ├── EDafk_combat.py
│   └── EDInterdictionEscape.py
├── Data & Vision
│   ├── OCR.py
│   ├── Screen.py
│   ├── Screen_Regions.py
│   ├── Image_Templates.py
│   ├── MarketParser.py
│   ├── CargoParser.py
│   └── NavRouteParser.py
├── IO & Status
│   ├── EDKeys.py
│   ├── EDJournal.py
│   ├── StatusParser.py
│   ├── EDMesg/
│   └── Voice.py
├── configs/                   # AP.json, resolution.json, ship configs, etc.
├── locales/                   # *.json translations + OCR patterns
├── simple_localization/       # Localization engine
├── waypoints/                 # Waypoint route files
├── test/                      # Test scripts
├── docs/                      # Documentation
├── Overlay.py                 # Debug overlay
├── EDlogger.py                # Logging
├── requirements*.txt          # Python dependencies
└── start_ed_ap.bat, install_requirements.bat
4. Configuration and Data Files
configs/AP.json (Main Settings)
Contains core behavior tuning:

Assist logic

JumpTries, NavAlignTries, DockingRetries

Fuel thresholds (RefuelThreshold, FuelThreasholdAbortAP)

Timeouts (fuel scooping, autodock wait, etc.)

Hotkeys

HotKey_StartFSD, HotKey_StartSC, HotKey_StartRobigo, HotKey_StopAllAssists

Must not conflict with in-game bindings.

Overlay & Debug

OverlayTextEnable, OverlayGraphicEnable, coordinates, font, DebugOverlay.

Voice & Language

VoiceEnable, VoiceID, VoiceLanguage

Language – UI language (e.g. uk/en).

OCRLanguage – OCR input language (e.g. en, ru).

configs/resolution.json (Screen Scaling)
Maps resolution strings (e.g. "2560x1440") to scaling factors [scale_x, scale_y].

Used by Screen and Screen_Regions to adapt coordinates.

"Calibrated": [-1.0, -1.0] indicates user calibration.

Waypoint Files (waypoints/*.json)
JSON dictionary keyed by numeric string ("1", "2", ...).

Typical fields:

SystemName, StationName

Bookmark type/number (SystemBookmarkType, SystemBookmarkNumber, etc.)

SellCommodities / BuyCommodities ({ "Commodity": quantity })

Flags: Skip, Completed, UpdateCommodityCount, FleetCarrierTransfer

Special command:

SystemName: "REPEAT" – repeat route from the beginning.

Autopilot flow:

Load waypoint file (GUI or config).

Validate structure and required fields.

Process entries in order: navigation, docking, trading, mission steps.

Respect Skip and Completed flags.

Handle REPEAT looping.

GUI Config (gui_config.json)
Stores GUI-specific settings such as:

last_waypoint_file – last used waypoint JSON path.

Optional app_version or other GUI state.

Used to auto-load last route at application start.

Localization Files (locales/*.json)
en.json, uk.json, ru.json, de.json, fr.json – UI/log/voice strings.

OCR_en.json, OCR_ru.json – OCR pattern strings.

Must stay in sync for all functional keys (see Localization Rules).

5. Localization Rules
Architecture
Two layers:

UI/Log/Voice Localization

All user-visible texts, log messages, dialogs, menu entries.

Languages: at least Ukrainian (uk) and English (en), plus others.

Selected via GUI (Language menu).

OCR Language

Game text recognition language.

Currently: English + Russian patterns.

Selected separately in settings (OCR language radio buttons).

Rules
Full Key Coverage (Mandatory)

Every functional key must exist in all supported locale files.

No missing keys or empty strings in any locales/*.json.

When adding a new feature, update all locale files together.

Key Naming Convention

Use hierarchical dot-notation:

ui.* – GUI (labels, buttons, menus, tabs).

log.* – log messages/status lines.

voice.* – spoken messages/TTS.

error.* – error messages.

ocr.* – OCR-related patterns and triggers.

message.* – dialog text.

Examples:

ui.button.start_fsd

log.autopilot.fsd_start

error.waypoint.file_not_found

voice.warning.low_fuel

ocr.system_map.cartographics

Parameterized Strings

Use {placeholder} format:

json
Копіювати код
"log.waypoint.file_loaded": "Waypoint file {filename} loaded successfully"
OCR Pattern Keys

OCR locale files (OCR_en.json, OCR_ru.json) store literal in-game text or normalized patterns.

These values often should not be translated, but matched to actual HUD/menu strings.

Implementation
Localization is handled by simple_localization.localization.LocalizationManager.

Typical usage:

self._t("ui.button.start_fsd")

self.log_ui("log.autopilot.fsd_start")

self.speak_ui("voice.autopilot.fsd_on")

AI must always use existing keys where possible and add new keys consistently.

6. Coding Guidelines and Style
Language
Code (identifiers, comments, docstrings): English only.

User explanations from AI: Ukrainian.

Generated code blocks: English comments and names.

Principles
KISS – keep logic simple, readable, and explicit.

DRY – avoid duplication; extract helpers where appropriate.

Prefer composition over deep inheritance.

Avoid new heavy external dependencies unless absolutely necessary.

Naming and Structure
snake_case for functions and variables.

PascalCase for classes.

Modules: one clear responsibility.

Error Handling & Logging
Use try/except around IO, parsing, and external interactions.

Log failures with localized keys via log_ui() when possible.

Avoid print(); rely on logger and GUI log.

Example pattern:

python
Копіювати код
def load_waypoint_file(filepath: str) -> Optional[Dict[str, Any]]:
    """Load waypoint file and log localized messages on failure."""
    try:
        if not os.path.exists(filepath):
            self.log_ui("error.waypoint.file_not_found", filepath=filepath)
            return None

        with open(filepath, "r", encoding="utf-8") as file:
            data = json.load(file)
        self.log_ui("log.waypoint.file_loaded", filepath=filepath)
        return data

    except json.JSONDecodeError as exc:
        self.log_ui("error.waypoint.invalid_json", filepath=filepath, error=str(exc))
        return None
    except Exception as exc:
        self.log_ui("error.waypoint.load_failed", filepath=filepath, error=str(exc))
        return None
Type Hints
Use type hints in new or refactored code where helpful:

python
Копіювати код
from typing import Dict, List, Optional

def navigate_to_waypoint(waypoint: Dict[str, Any]) -> bool:
    ...
7. AI Interaction Rules
Language Rules
User ↔ AI dialog: Ukrainian.

Generated code: English (identifiers, comments, docstrings).

Any explanation of code in plain language: Ukrainian.

Localization Rules for AI
When AI:

Adds a new UI element or message → must add a localization key.

Adds a new key → must be added to all locale files (en, uk, ru, etc.).

Must not hardcode user-facing English strings in code; always use localization.

🚨 **STRICT RULE: NO HARDCODED STRINGS IN USER-FACING CODE** 🚨

**ABSOLUTELY FORBIDDEN:**
```python
# ❌ WRONG - Hardcoded strings
logger.info("Виклик stop_sc() - stack trace:")
logger.info("Натиснуто гарячу клавішу: 'combo'")
log_msg("Старт SC асистента")
```

**ALWAYS REQUIRED:**
```python
# ✅ CORRECT - Use localization
logger.info(self._t("debug.stop_sc_called"))
logger.info(self._t("debug.hotkey_pressed", combo=combo))
self.log_msg(self._t("log.sc.start"))
```

**Debug logging also requires localization keys.** All user-visible messages must use `_t()` or `log_ui()` methods.

**For internal debug logs**, use English with proper context:
```python
# ✅ Acceptable for internal technical debug logs
logger.debug("Function stop_sc() called from callback")
logger.info(f"Hotkey '{combo}' triggered -> {target.__name__} with args={args}")
```

Sensitive vs Safe Areas
AI must treat as sensitive (do not rewrite core behavior without explicit instruction):

ED_AP.py state machine and timing logic.

EDWayPoint.py core route execution.

OCR.py recognition pipeline.

EDJournal.py and StatusParser.py parsing logic.

Screen coordinate/scaling logic in Screen.py and Screen_Regions.py.

DirectInput handling (EDKeys.py, directinput.py).

Safe to extend (if done carefully):

GUI tabs, menus and controls in EDAPGui.py.

Additional voice lines in Voice.py (with localization).

New overlay visualization in Overlay.py.

New assist modules following existing patterns (separate file, clearly plugged into ED_AP.py).

8. Critical Areas and Safe Extension Points
Critical Areas (High-Risk)
Autopilot Core:

ED_AP.py, EDShipControl.py, EDInterdictionEscape.py, EDafk_combat.py

Recognition & Status:

OCR.py, Screen.py, Screen_Regions.py, StatusParser.py, EDJournal.py

Routing & Trading:

EDWayPoint.py, MarketParser.py, CargoParser.py

Config & Localization:

configs/AP.json, configs/resolution.json

locales/*.json (any mismatch can break UI or logs)

Changes to these must be minimal, localized, and backward compatible.

Safe Extension Points
New tabs/frames/controls in EDAPGui.py.

Additional voice notifications in Voice.py.

New overlay elements for debugging in Overlay.py.

New optional assist features in separate module files, registered in ED_AP.py with:

clear config flags;

localized messages;

separate enabling/disabling logic;

safety checks.

9. Known Limitations and Constraints
Platform: Windows-only (uses Win32, SAPI, DirectInput).

Game Settings:

Borderless windowed mode recommended.

HUD colors should remain near default.

FOV and layout changes can impact templates/OCR.

OCR Limitations:

Sensitive to brightness, star glare, and non-standard HUD.

Supports English & Russian game text only by default.

Performance:

Continuous OCR & screen capture is CPU intensive.

PaddleOCR and OpenCV require sufficient RAM.

Trading & Routes:

Depends on game’s market data and visits history.

No prediction of dynamic prices; relies on static definitions in waypoint files.

10. Run, Test and Tooling
Running the Application
bash
Копіювати код
# Preferred
start_ed_ap.bat

# Direct
python EDAPGui.py
Installing Dependencies
bash
Копіювати код
install_requirements.bat
# or
pip install -r requirements.txt
Tests
From project root:

bash
Копіювати код
python test_OCR.py          # OCR tests
python test_GalaxyMap.py    # Galaxy map interaction
python test_SystemMap.py    # System map interaction
python test_waypoint_config.py  # Waypoint config validation
python test/Test_Routines.py    # Combined tests (if present)
Logging & Debug
Default log file: autopilot.log in project root.

Log panel in GUI shows messages with filters.

Debug overlay and CV debugging can be enabled via config and GUI settings.

Environment Requirements
OS: Windows 10/11.

Python: 3.9–3.11 (3.11 recommended).

Main libs: Tkinter, PaddleOCR, PaddlePaddle, OpenCV, Pillow, numpy, pyttsx3, pywin32, keyboard/pynput, etc. (see requirements.txt).

Adequate hardware (≥8GB RAM, faster CPU recommended).

11. Rules for Future Code Generation
General Rules
Maintain backward compatibility with existing configs and waypoints.

Do not remove existing public methods without explicit reason.

Always integrate new features behind configuration flags (with reasonable defaults).

Expand tests where practical, especially for new modules.

When Adding a New Feature
Design

Place in a new module or extend an appropriate existing module.

Follow naming/style rules.

Configuration

Add new keys to AP.json with defaults.

Validate config gracefully (fallback to defaults, log warnings).

Localization

Add all new user-facing text as keys under ui.*, log.*, voice.*, error.*.

Update every language file consistently.

Integration

Wire into ED_AP.py in a minimal and explicit way (e.g. start_*, stop_* methods).

Add GUI control(s) in EDAPGui.py only if needed.

Safety

Protect critical state with checks (e.g. only run when in supercruise, only dock when at station).

Add logging for key decision points (using localized keys).

Testing

If possible, add or update test scripts in test/.

At minimum, ensure no unhandled exceptions during normal flows.

This document is the primary reference for AI assistants working on the EDAPGui project.
All automated modifications must respect these rules to keep the autopilot stable, safe, and fully localized.