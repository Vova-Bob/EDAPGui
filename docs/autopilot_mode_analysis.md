# Autopilot mode and interdiction instability analysis

## Mode state handling and unintended transitions
- Mode activation relies on multiple booleans (`fsd_assist_enabled`, `sc_assist_enabled`, `waypoint_assist_enabled`, `robigo_assist_enabled`, etc.) that are all initialized independently and can be true at the same time.
- The `engine_loop` executes the first enabled mode in a fixed priority order (FSD → SC → waypoint → Robigo → AFK → DSS → single waypoint), then clears its flag and fires a corresponding callback such as `fsd_stop` or `sc_stop`.
- Completing FSD with an in-system destination triggers `ap_ckb("sc_start")`, which can enable SC Assist even if another mode was also toggled; overlapping flags make the executed mode depend on that fixed priority rather than an explicit active-mode state machine.
- Because callbacks only flip booleans rather than a single authoritative state, GUI actions or keybind handlers can leave multiple assists enabled, allowing the loop to pivot from FSD into Robigo or SC without a deliberate user command when the next iteration evaluates the remaining true flags.

## Interdiction escape integration
- `interdiction_check` arms `EDInterdictionEscape` only when one of the main assists is active in supercruise; the helper records `previous_mode` and, after a handled escape, sets `_interdiction_resume_mode` but does not re-enable any assist flags.
- The escape sequence may retarget the “next route system” while clearing interdiction, changing the nav focus mid-run. When control returns, SC Assist resumes only if it was already running and sees `_interdiction_resume_mode == 'sc_assist'`; otherwise no autopilot mode is automatically rearmed.
- Because the escape resets the journal interdicted flag and clears `previous_mode`, subsequent iterations can exit supercruise without a valid target and never re-enter the intended assist, leaving the ship idle.

## SC Assist termination sensitivity
- SC Assist aborts immediately if the compass/destination is missing at start, with no retry window.
- In-flight alignment depends on repeated `sc_target_align` calls that try five quick OCR reads before declaring “target not found,” then treat any single failed read inside the loop as “target lost.”
- During or after interdiction, temporary loss of supercruise or delayed compass updates flip `align_failed`, ending SC Assist even if the ship soon re-enters SC.
- The interdiction recovery buffer is short and only retries a simple `nav_align`; persistent OCR noise or missing targets during that window end the mode with “target not found” or “supercruise dropped” logs.

## OCR/compass noise effects
- Destination presence and offset rely entirely on template/OCR matches without debouncing or averaging; every iteration of SC Assist re-queries `get_destination_offset` and reacts to single-frame misses.
- This tight coupling to noisy OCR leads to frequent re-alignments (“twitching”) and mode exits when the compass flickers or the target briefly disappears, especially after interdiction when HUD elements are settling.

## Summary diagnosis
- The combination of parallel mode flags, priority-based dispatch, and callback-driven flag toggling allows unintended mode switches when multiple assists are active.
- Interdiction escape is treated as a temporary detour rather than a structured substate; it may retarget the route and clears its own mode markers without restoring the original assist, so SC Assist/FSD may not resume automatically.
- SC Assist’s termination rules assume stable, continuous OCR; even brief compass loss during or after interdiction ends the mode, explaining reports of “Target not found” and autopilot idling despite successful escapes.

## Design-level recommendations (no code)
- Introduce a single active-mode state machine (with an explicit substate for interdiction recovery) instead of multiple independent booleans and priority dispatch.
- Preserve and restore both the intended mode and target across interdiction by explicitly re-arming the prior assist after escape, with a grace period before declaring failures.
- Add debounced, multi-sample confirmation for compass/target presence and lengthen the post-interdiction recovery window so transient OCR glitches do not end SC Assist.
