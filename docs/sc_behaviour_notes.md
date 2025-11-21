# Supercruise assist behaviour and threat handling

## SC Assist entry and alignment
- `EDAutopilot.sc_assist` starts by forcing cockpit view, ensuring a compass target exists, and undocking/takeoff if docked or landed. It then enters supercruise when the journal status is not `in_supercruise`, sets throttle to 50%, performs `nav_align`, and clears the `interdicted` journal flag before the main loop.【F:ED_AP.py†L2511-L2540】
- The main loop runs only while `ship_state()['status']` reports supercruise or glide. In supercruise it repeatedly calls `sc_target_align` to keep the nose on target; a `Lost` return triggers a 10-second coast plus `nav_align`, `Found` continues, and `Disengage` breaks for drop handling.【F:ED_AP.py†L2541-L2590】【F:ED_AP.py†L1875-L1955】
- `sc_target_align` searches for compass offsets, repositions if the target is occluded, and logs warnings when the target is missing (`SC_TARGET_NOT_FOUND` or `SC_TARGET_LOST`). It also triggers hyper/super combination on an active disengage prompt, returning `Disengage` when the drop prompt is live.【F:ED_AP.py†L1875-L1955】

## Target occlusion / disappearance
- If no compass target is present at start, SC Assist aborts immediately with a compass warning.【F:ED_AP.py†L2518-L2522】
- During alignment, failure to locate a target or the target slipping behind yields `SC_TARGET_NOT_FOUND`/`SC_TARGET_LOST` logs from `sc_target_align`; the caller reacts by coasting forward and re-aligning before retrying.【F:ED_AP.py†L1875-L1955】【F:ED_AP.py†L2541-L2554】
- When `is_destination_occluded` reports a hidden target, `occluded_reposition` pitches away and re-aligns while logging `NAV_TARGET_OCCLUDED` and re-announcing ALIGN status.【F:ED_AP.py†L1934-L1938】【F:ED_AP.py†L1951-L1955】

## Supercruise drop handling
- A live disengage prompt detected in the loop or inside `sc_target_align` sends the `HyperSuperCombination`, stops SCO monitoring, and exits the loop to perform post-drop alignment and docking if enabled.【F:ED_AP.py†L1939-L1945】【F:ED_AP.py†L2579-L2590】【F:ED_AP.py†L2594-L2625】
- If the ship leaves supercruise unexpectedly (no glide flag), SC Assist marks `align_failed`, speaks the exiting-supercruise voice line, sets speed to zero, logs `SC_TERMINATED`, and skips docking logic.【F:ED_AP.py†L2561-L2629】
- Normal drops call `_post_sc_drop_alignment` to re-align and boost once, then proceed to docking unless docking is skipped for lack of a computer or because the destination type is a USS or similar restricted target; otherwise throttle zero is issued before logging completion.【F:ED_AP.py†L2594-L2625】【F:ED_AP.py†L2632-L2650】

## Supercruise exits away from target
- Leaving supercruise without glide sets `align_failed`; after the loop SC Assist announces exit, zeros speed, and logs termination instead of docking, signaling a non-target drop such as hitting a star/planet or other early exit.【F:ED_AP.py†L2561-L2629】
- If a target is missing at the very start, SC Assist ends immediately, leaving mode deactivated by the engine loop once `sc_assist_enabled` is cleared after the call returns.【F:ED_AP.py†L2518-L2522】【F:ED_AP.py†L2587-L2631】

## Interdiction and danger handling
- `interdiction_check` watches `FlagsBeingInterdicted`; on detection it submits by throttling zero in SC or hyperspace charge, then sets 100% speed, waits for FSD cooldown, repeatedly boosts, and commands Supercruise until an FSD jump flag appears, finally clearing `ship_state()['interdicted']`. The method is invoked inside SC Assist’s loop and during refuel waits so both travel and scooping try to escape immediately.【F:ED_AP.py†L1144-L1185】【F:ED_AP.py†L2572-L2578】【F:ED_AP.py†L2170-L2198】
- SC Assist responds to an interdiction return by re-aligning at 50% throttle to resume the run; refuel logic instead pauses at zero throttle until scooping resumes.【F:ED_AP.py†L2572-L2578】【F:ED_AP.py†L2144-L2198】
- FSD Assist itself does not poll interdiction inside its main jump loop; threat reactions are centralized in `interdiction_check` calls from SC Assist and refueling rather than a dedicated escape controller.【F:ED_AP.py†L1700-L1720】【F:ED_AP.py†L1144-L1185】

## Autonomous escape modules
- No standalone “escape” module exists; `interdiction_check` is embedded within `EDAutopilot` and reused opportunistically by SC Assist and refuel routines. There is no separate class orchestrating evasive maneuvers independent of the current mode.【F:ED_AP.py†L1144-L1185】【F:ED_AP.py†L2572-L2578】【F:ED_AP.py†L2144-L2198】
