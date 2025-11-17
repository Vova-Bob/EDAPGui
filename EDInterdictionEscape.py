from __future__ import annotations

import time
from typing import Callable, Optional

from EDAP_data import Flags2FsdHyperdriveCharging, FlagsBeingInterdicted, FlagsFsdCooldown, FlagsFsdJump, FlagsIsInDanger
from EDlogger import logger
from Screen import set_focus_elite_window


class EDInterdictionEscape:
    def __init__(self, jn, keys, status, nav_route, navigator, screen_regions, logger_obj, voice=None):
        self.jn = jn
        self.keys = keys
        self.status = status
        self.nav_route = nav_route
        self.navigator = navigator
        self.screen_regions = screen_regions
        self.logger = logger_obj
        self.voice = voice

        self.previous_mode: Optional[str] = None
        self.escape_active = False

    def check_and_arm(self, sc_assist_enabled: bool, waypoint_assist_enabled: bool, afk_combat_enabled: bool) -> bool:
        if self.escape_active:
            return False

        if afk_combat_enabled:
            return False

        ship_state = self.jn.ship_state()
        in_supercruise = ship_state.get('status') == 'in_supercruise'
        interdicted_flags = (
            ship_state.get('interdicted')
            or self.status.get_flag(FlagsBeingInterdicted)
            or self.status.get_flag(FlagsIsInDanger)
        )

        if not in_supercruise or not interdicted_flags:
            return False

        if not (sc_assist_enabled or waypoint_assist_enabled):
            return False

        if sc_assist_enabled:
            self.previous_mode = 'sc_assist'
        elif waypoint_assist_enabled:
            self.previous_mode = 'waypoint'
        else:
            self.previous_mode = None

        self.escape_active = True
        if self.voice:
            self.voice.say('WARNING: INTERDICTION')
        self.logger.warning('WARNING: INTERDICTION')
        return True

    def is_active(self) -> bool:
        return self.escape_active

    def run_escape_loop(self, callback: Optional[Callable[[str], None]] = None):
        if not self.escape_active:
            return None

        set_focus_elite_window()

        ship_state = self.jn.ship_state()
        while ship_state.get('status') == 'in_supercruise':
            self.keys.send('SetSpeedZero')  # submission
            self._max_engine_power()
            time.sleep(0.2)
            ship_state = self.jn.ship_state()

        self.keys.send('SetSpeed100')
        self._max_engine_power()
        self.keys.send('UseBoostJuice')

        while self.status.get_flag(FlagsFsdCooldown):
            self.keys.send('UseBoostJuice')
            self._max_engine_power()
            time.sleep(0.5)

        self._target_next_route_system()

        self._align_to_target()

        self.keys.send('SetSpeed100')
        self._max_engine_power()
        self.keys.send('HyperSuperCombination')

        while (not self.status.get_flag2(Flags2FsdHyperdriveCharging)
               and not self.status.get_flag(FlagsFsdJump)):
            self.keys.send('UseBoostJuice')
            self._max_engine_power()
            time.sleep(0.5)

        self.jn.ship_state()['interdicted'] = False
        self.escape_active = False
        if callback:
            self.resume_previous_mode(callback)
        return self.previous_mode

    def resume_previous_mode(self, callback: Callable[[str], None]):
        if self.previous_mode:
            callback(self.previous_mode)

        self.previous_mode = None
        self.escape_active = False
        self.jn.ship_state()['interdicted'] = False

    def _align_to_target(self):
        try:
            if hasattr(self.navigator, 'nav_align'):
                self.navigator.nav_align(self.screen_regions)
        except Exception:
            self.logger.debug('Unable to align during interdiction escape', exc_info=True)

    def _target_next_route_system(self):
        try:
            route_data = self.nav_route.get_nav_route_data()
        except Exception:
            self.logger.debug('Unable to read nav route for interdiction escape', exc_info=True)
            return

        if route_data and route_data.get('event') != 'NavRouteClear' and route_data.get('Route'):
            self.keys.send('TargetNextRouteSystem')

    def _max_engine_power(self):
        self.keys.send('IncreaseEnginesPower', repeat=4)
