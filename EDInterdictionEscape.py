from __future__ import annotations

from time import sleep, time
from typing import Callable, Optional

from EDlogger import logger
from StatusParser import (
    FlagsBeingInterdicted,
    FlagsFsdCooldown,
    FlagsFsdMassLocked,
    FlagsSupercruise,
    Flags2FsdHyperdriveCharging,
)


class EDInterdictionEscape:
    def __init__(
        self,
        journal,
        status,
        keys,
        *,
        nav_route=None,
        scr_reg=None,
        log_func: Optional[Callable[..., str]] = None,
        speak_func: Optional[Callable[..., str]] = None,
        enabled: bool = False,
    ) -> None:
        self.journal = journal
        self.status = status
        self.keys = keys
        self.nav_route = nav_route
        self.scr_reg = scr_reg
        self.log_func = log_func
        self.speak_func = speak_func
        self.enabled = enabled
        self.escape_active = False
        self.previous_mode: Optional[str] = None

    def _log(self, key: str, *, level: str = 'info', **kwargs):
        if self.log_func:
            try:
                self.log_func(key, level=level, **kwargs)
                return
            except Exception:
                logger.debug('Interdiction escape log failed', exc_info=True)
        log_method = getattr(logger, level.lower(), logger.info)
        log_method(key)

    def check_and_arm(
        self,
        *,
        sc_assist_enabled: bool,
        fsd_assist_enabled: bool,
        waypoint_assist_enabled: bool,
        active_mode: Optional[str] = None,
    ) -> bool:
        if not self.enabled:
            return False
        if self.escape_active:
            return False
        if not (sc_assist_enabled or fsd_assist_enabled or waypoint_assist_enabled):
            return False

        ship_status = self.journal.ship_state().get('status')
        if ship_status != 'in_supercruise':
            return False
        if not self.status.get_flag(FlagsBeingInterdicted):
            return False

        if active_mode:
            self.previous_mode = active_mode
        elif sc_assist_enabled:
            self.previous_mode = 'sc_assist'
        elif fsd_assist_enabled:
            self.previous_mode = 'fsd_assist'
        elif waypoint_assist_enabled:
            self.previous_mode = 'waypoint_assist'
        else:
            self.previous_mode = None

        self.escape_active = True
        return True

    def _apply_engine_power(self):
        self.keys.send('IncreaseEnginesPower', repeat=4)

    def _boost_until(self, condition: Callable[[], bool], timeout: float) -> bool:
        start = time()
        while not condition():
            if time() - start > timeout:
                return False
            self.keys.send('SetSpeed100')
            self.keys.send('UseBoostJuice')
            sleep(1)
        return True

    def _target_next_route_system(self):
        try:
            if self.nav_route and self.nav_route.get_last_system():
                self.keys.send('TargetNextRouteSystem')
        except Exception:
            logger.debug('Interdiction escape target selection failed', exc_info=True)

    def _fallback_supercruise(self) -> bool:
        self.keys.send('SetSpeed100')
        self.keys.send('Supercruise')
        if self.status.wait_for_flag_on(FlagsSupercruise, timeout=45):
            self.journal.ship_state()['interdicted'] = False
            return True
        return False

    def run_escape_sequence(self) -> bool:
        if not self.escape_active:
            return False

        try:
            if self.speak_func:
                self.speak_func('voice.warning.interdiction')
            self._log('log.warning.interdiction', level='warning')

            submit_start = time()
            while self.status.get_flag(FlagsSupercruise) or self.status.get_flag2(Flags2FsdHyperdriveCharging):
                if time() - submit_start > 30:
                    return False
                self.keys.send('SetSpeedZero')
                sleep(0.5)

            self._apply_engine_power()
            self.keys.send('SetSpeed100')
            self.keys.send('UseBoostJuice')

            self.status.wait_for_flag_on(FlagsFsdCooldown, timeout=15)
            cooldown_cleared = self._boost_until(
                lambda: not self.status.get_flag(FlagsFsdCooldown),
                timeout=45,
            )
            if not cooldown_cleared:
                self._log('log.warning.interdiction_escape_cooldown_failed', level='warning')
                if self._fallback_supercruise():
                    return True
                return False

            masslock_cleared = self._boost_until(
                lambda: not self.status.get_flag(FlagsFsdMassLocked),
                timeout=60,
            )
            if not masslock_cleared:
                self._log('log.warning.masslock_escape_failed', level='warning')
                if self._fallback_supercruise():
                    return True
                return False

            self._target_next_route_system()

            if not self.status.get_flag(FlagsSupercruise):
                self.keys.send('SetSpeed100')
                self.keys.send('Supercruise')
                if self.status.wait_for_flag_on(FlagsSupercruise, timeout=45):
                    self.keys.send('SetSpeed50')
                    self.journal.ship_state()['interdicted'] = False
                    return True
                return False

            self.keys.send('SetSpeed50')
            self.journal.ship_state()['interdicted'] = False
            return True
        finally:
            self.escape_active = False
            self.previous_mode = None
