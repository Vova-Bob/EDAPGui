# EDJournal ship_state overview

## Initialization
- `EDJournal.__init__` builds `self.ship` with baseline fields for time, Odyssey flag, `status`, ship type/location targeting, combat flags (`fighter_destroyed`, `shieldsup`, `under_attack`, `interdicted`), docking outcomes, mission counters, body/route info, fuel metrics, scoop state, current star system/station metadata, cargo capacity/ship size, module capabilities (fuel scoop, docking computers, SCO FSD), and station services.
- After initial `ship_state()` read, `reset_items()` clears `under_attack` and `fighter_destroyed` to `False` so subsequent detections are edge-triggered.

## Status transitions from journal events
- `Fileheader` records Odyssey; `StartJump` sets `status` to `starting_<JumpType>` (hyperspace/supercruise) and resets destination drop type; hyperspace also stores `star_class`.
- `SupercruiseEntry` and `FSDJump` set `status` to `in_supercruise`.
- Docking flow: `DockingGranted` → `dockinggranted`; `DockingDenied` → `dockingdenied` with `no_dock_reason`; `DockingRequested` → `starting_docking`; `Music` with `DockingComputer` advances `starting_undocking` → `in_undocking` or `starting_docking` → `in_docking`; `Music` `NoTrack`/`Exploration` from `in_undocking` resets to `in_space`; `Docked` sets `in_station` and updates station/system metadata; `DockingCancelled` returns to `in_space`; `Undocked` marks `starting_undocking`.
- Supercruise transitions: `SupercruiseExit` sets `in_space` and records `body`; `SupercruiseDestinationDrop` stores destination drop `Type`.
- Location updates: `Location` refreshes system/station fields and, if docked, sets `in_station`; `FSDJump` updates current system and clears target when arrived; `NavRouteClear` clears target/jumps remaining; `CarrierJump` updates location/station details.

## Combat/hazard flag handling
- `ShieldState` toggles `shieldsup` True/False.
- `UnderAttack` sets `under_attack` True; cleared by `reset_items()` after initial load or when consumers reset.
- `FighterDestroyed` sets `fighter_destroyed` True; `reset_items()` clears initially, and `AFK_Combat.check_fighter_destroyed()` clears after reading.
- `Interdicted` sets `interdicted` True; `EDAutopilot.interdiction_check()` resets it to False after handling.

## Fuel and scoop tracking
- Fuel fields (`fuel_level`, `fuel_capacity`, `fuel_percent`) update when present in any event, with `FuelScoop` updating level and marking `is_scooping` True during initial post-start period while refueling below full.

## Downstream usage
- `ED_AP.py` reads `ship_state()['status']` extensively for navigation/state gating (e.g., ensuring space/SC before sequences, docking checks, jump monitoring). Interdiction handling uses `ship_state()['interdicted']` to detect/cancel interdicts and resets the flag when resolved.
- `EDafk_combat.py` monitors `ship_state()['shieldsup']` and `ship_state()['fighter_destroyed']`, clearing the fighter flag after consumption to trigger redeploy logic when fighters are lost.
- `Robigo.py` waits on `ship_state()['status']` to reach `in_space` before proceeding with loop actions.
