import queue
import sys
import os
import threading
# import kthread
from datetime import datetime
from time import sleep
# import cv2
import json
from pathlib import Path
import subprocess

import keyboard
import webbrowser
# import requests


# from PIL import Image, ImageGrab, ImageTk
import tkinter as tk
from tkinter import filedialog as fd
# from tkinter import messagebox
from tkinter import ttk
import sv_ttk
import pywinstyles
import sys  # Do not delete - prevents a 'super' error from tktoolip.
from tktooltip import ToolTip  # In requirements.txt as 'tkinter-tooltip'.

# from OCR import RegionCalibration
# from Voice import *
# from MousePt import MousePoint

# from Image_Templates import *
# from Screen import *
# from Screen_Regions import *
# from EDKeys import *
# from EDJournal import *
from ED_AP import *
from EDAPWaypointEditor import WaypointEditorTab

from EDlogger import logger
from simple_localization import LocalizationManager


"""
File:EDAPGui.py

Description:
User interface for controlling the ED Autopilot

Note:
Ideas taken from:  https://github.com/skai2/EDAutopilot

 HotKeys:
    Home - Start FSD Assist
    INS  - Start SC Assist
    PG UP - Start Robigo Assist
    End - Terminate any ongoing assist (FSD, SC, AFK)

Author: sumzer0@yahoo.com
"""


# ---------------------------------------------------------------------------
# must be updated with a new release so that the update check works properly!
# contains the names of the release.
EDAP_VERSION = "V1.8.0"
# depending on how release versions are best marked you could also change it to the release tag, see function check_update.
# ---------------------------------------------------------------------------

FORM_TYPE_CHECKBOX = 0
FORM_TYPE_SPINBOX = 1
FORM_TYPE_ENTRY = 2


def str_to_float(input_str: str) -> float:
    try:
        return float(input_str)
    except ValueError:
        return 0.0  # Assign a default value on error


class APGui:

    def __init__(self, root):
        self.statusbar = None
        self.root = root

        # Initialize critical attributes BEFORE creating EDAutopilot
        # These are needed by callback() which is called during EDAutopilot initialization
        self.gui_loaded = False
        self.log_buffer = queue.Queue()

        # Initialize localization manager with language from config
        # Load config first to get language setting
        self.load_ocr_calibration_data()
        self.ed_ap = EDAutopilot(cb=self.callback)

        # Get language from config, default to 'en' if not set
        language = self.ed_ap.config.get('Language', 'en')
        self.locale = LocalizationManager("locales", language)
        root.title(self.locale["gui.main.title"] + " " + self.locale["gui.version"])
        # root.overrideredirect(True)
        # root.geometry("400x550")
        # root.configure(bg="blue")
        root.protocol("WM_DELETE_WINDOW", self.close_window)
        root.resizable(False, False)

        self.tooltips = {
            'FSD Route Assist': self.locale["tooltips.fsd_route_assist"],
            'Supercruise Assist': self.locale["tooltips.supercruise_assist"],
            'Waypoint Assist': self.locale["tooltips.waypoint_assist"],
            'Robigo Assist': self.locale["tooltips.robigo_assist"],
            'DSS Assist': self.locale["tooltips.dss_assist"],
            'Single Waypoint Assist': self.locale["tooltips.single_waypoint_assist"],
            'ELW Scanner': self.locale["tooltips.elw_scanner"],
            'AFK Combat Assist': self.locale["tooltips.afk_combat_assist"],
            self.locale['gui.ship.roll_rate']: self.locale["tooltips.roll_rate"],
            self.locale['gui.ship.pitch_rate']: self.locale["tooltips.pitch_rate"],
            self.locale['gui.ship.yaw_rate']: self.locale["tooltips.yaw_rate"],
            self.locale['gui.ship.roll_factor']: self.locale["tooltips.roll_factor"],
            self.locale['gui.ship.pitch_factor']: self.locale["tooltips.pitch_factor"],
            self.locale['gui.ship.yaw_factor']: self.locale["tooltips.yaw_factor"],
            self.locale['gui.ship.sun_pitch_up_time']: self.locale["tooltips.sun_pitch_up_time"],
            self.locale['gui.autopilot.sun_bright_threshold']: self.locale["tooltips.sun_bright_threshold"],
            self.locale['gui.autopilot.nav_align_tries']: self.locale["tooltips.nav_align_tries"],
            self.locale['gui.autopilot.jump_tries']: self.locale["tooltips.jump_tries"],
            self.locale['gui.autopilot.docking_retries']: self.locale["tooltips.docking_retries"],
            self.locale['gui.autopilot.wait_for_autodock']: self.locale["tooltips.wait_for_autodock"],
            self.locale['gui.buttons.start_fsd']: self.locale["tooltips.start_fsd"],
            self.locale['gui.buttons.start_sc']: self.locale["tooltips.start_sc"],
            self.locale['gui.buttons.start_robigo']: self.locale["tooltips.start_robigo"],
            self.locale['gui.buttons.stop_all']: self.locale["tooltips.stop_all"],
            self.locale['gui.refuel.refuel_threshold']: self.locale["tooltips.refuel_threshold"],
            self.locale['gui.refuel.scoop_timeout']: self.locale["tooltips.scoop_timeout"],
            self.locale['gui.refuel.fuel_threshold_abort']: self.locale["tooltips.fuel_threshold_abort"],
            self.locale['gui.overlay.x_offset']: self.locale["tooltips.x_offset"],
            self.locale['gui.overlay.y_offset']: self.locale["tooltips.y_offset"],
            self.locale['gui.overlay.font_size']: self.locale["tooltips.font_size"],
            'Calibrate': self.locale["tooltips.calibrate"],
            'Waypoint List Button': self.locale["tooltips.waypoint_list_button"],
            'Cap Mouse XY': self.locale["tooltips.cap_mouse_xy"],
            'Reset Waypoint List': self.locale["tooltips.reset_waypoint_list"],
            'Debug Overlay': self.locale["tooltips.debug_overlay"],
            'Debug OCR': self.locale["tooltips.debug_ocr"],
            'Debug Images': self.locale["tooltips.debug_images"],
            'Debug Mode': self.locale["tooltips.mode"],
            self.locale['gui.keys.modifier_key_delay']: self.locale["tooltips.modifier_key_delay"],
            self.locale['gui.keys.default_hold_time']: self.locale["tooltips.default_hold_time"],
            self.locale['gui.keys.repeat_key_delay']: self.locale["tooltips.repeat_key_delay"]
        }

        self.callback('log', f'Starting ED Autopilot {EDAP_VERSION}.')

        self.ocr_calibration_data = {}

        self.mouse = MousePoint()

        self.checkboxvar = {}
        self.radiobuttonvar = {}
        self.entries = {}
        self.lab_ck = {}
        self.single_waypoint_system = tk.StringVar()
        self.single_waypoint_station = tk.StringVar()
        self._global_shopping_list_tab = None
        self.waypoint_editor_tab = None

        self.FSD_A_running = False
        self.SC_A_running = False
        self.WP_A_running = False
        self.RO_A_running = False
        self.DSS_A_running = False
        self.SWP_A_running = False

        self.cv_view = False

        self.msgList = self.gui_gen(root)

        self.checkboxvar['Enable Randomness'].set(self.ed_ap.config['EnableRandomness'])
        self.checkboxvar['Activate Elite for each key'].set(self.ed_ap.config['ActivateEliteEachKey'])
        self.checkboxvar['Automatic logout'].set(self.ed_ap.config['AutomaticLogout'])
        self.checkboxvar['Enable Overlay'].set(self.ed_ap.config['OverlayTextEnable'])
        self.checkboxvar['Enable Voice'].set(self.ed_ap.config['VoiceEnable'])
        self.checkboxvar['Enable Hotkeys'].set(self.ed_ap.config['HotkeysEnable'])
        self.checkboxvar['Debug Overlay'].set(self.ed_ap.config['DebugOverlay'])
        self.checkboxvar['Debug OCR'].set(self.ed_ap.config['DebugOCR'])
        self.checkboxvar['Debug Images'].set(self.ed_ap.config['DebugImages'])
        self.checkboxvar['AFKCombat AttackAtWill'].set(self.ed_ap.config['AFKCombat_AttackAtWill'])

        self.radiobuttonvar['dss_button'].set(self.ed_ap.config['DSSButton'])

        self.entries['ship'][self.locale['gui.ship.pitch_rate']].delete(0, tk.END)
        self.entries['ship'][self.locale['gui.ship.roll_rate']].delete(0, tk.END)
        self.entries['ship'][self.locale['gui.ship.yaw_rate']].delete(0, tk.END)
        self.entries['ship'][self.locale['gui.ship.sun_pitch_up_time']].delete(0, tk.END)
        self.entries['ship'][self.locale['gui.ship.pitch_factor']].delete(0, tk.END)
        self.entries['ship'][self.locale['gui.ship.roll_factor']].delete(0, tk.END)
        self.entries['ship'][self.locale['gui.ship.yaw_factor']].delete(0, tk.END)

        self.entries['autopilot'][self.locale['gui.autopilot.sun_bright_threshold']].delete(0, tk.END)
        self.entries['autopilot'][self.locale['gui.autopilot.nav_align_tries']].delete(0, tk.END)
        self.entries['autopilot'][self.locale['gui.autopilot.jump_tries']].delete(0, tk.END)
        self.entries['autopilot'][self.locale['gui.autopilot.docking_retries']].delete(0, tk.END)
        self.entries['autopilot'][self.locale['gui.autopilot.wait_for_autodock']].delete(0, tk.END)

        self.entries['refuel'][self.locale['gui.refuel.refuel_threshold']].delete(0, tk.END)
        self.entries['refuel'][self.locale['gui.refuel.scoop_timeout']].delete(0, tk.END)
        self.entries['refuel'][self.locale['gui.refuel.fuel_threshold_abort']].delete(0, tk.END)

        self.entries['overlay'][self.locale['gui.overlay.x_offset']].delete(0, tk.END)
        self.entries['overlay'][self.locale['gui.overlay.y_offset']].delete(0, tk.END)
        self.entries['overlay'][self.locale['gui.overlay.font_size']].delete(0, tk.END)

        self.entries['buttons'][self.locale['gui.buttons.start_fsd']].delete(0, tk.END)
        self.entries['buttons'][self.locale['gui.buttons.start_sc']].delete(0, tk.END)
        self.entries['buttons'][self.locale['gui.buttons.start_robigo']].delete(0, tk.END)
        self.entries['buttons'][self.locale['gui.buttons.stop_all']].delete(0, tk.END)

        self.entries['keys'][self.locale['gui.keys.modifier_key_delay']].delete(0, tk.END)
        self.entries['keys'][self.locale['gui.keys.default_hold_time']].delete(0, tk.END)
        self.entries['keys'][self.locale['gui.keys.repeat_key_delay']].delete(0, tk.END)

        self.entries['ship'][self.locale['gui.ship.pitch_rate']].insert(0, float(self.ed_ap.pitchrate))
        self.entries['ship'][self.locale['gui.ship.roll_rate']].insert(0, float(self.ed_ap.rollrate))
        self.entries['ship'][self.locale['gui.ship.yaw_rate']].insert(0, float(self.ed_ap.yawrate))
        self.entries['ship'][self.locale['gui.ship.sun_pitch_up_time']].insert(0, float(self.ed_ap.sunpitchuptime))
        self.entries['ship'][self.locale['gui.ship.pitch_factor']].insert(0, float(self.ed_ap.pitchfactor))
        self.entries['ship'][self.locale['gui.ship.roll_factor']].insert(0, float(self.ed_ap.rollfactor))
        self.entries['ship'][self.locale['gui.ship.yaw_factor']].insert(0, float(self.ed_ap.yawfactor))

        self.entries['autopilot'][self.locale['gui.autopilot.sun_bright_threshold']].insert(0, int(self.ed_ap.config['SunBrightThreshold']))
        self.entries['autopilot'][self.locale['gui.autopilot.nav_align_tries']].insert(0, int(self.ed_ap.config['NavAlignTries']))
        self.entries['autopilot'][self.locale['gui.autopilot.jump_tries']].insert(0, int(self.ed_ap.config['JumpTries']))
        self.entries['autopilot'][self.locale['gui.autopilot.docking_retries']].insert(0, int(self.ed_ap.config['DockingRetries']))
        self.entries['autopilot'][self.locale['gui.autopilot.wait_for_autodock']].insert(0, int(self.ed_ap.config['WaitForAutoDockTimer']))
        self.entries['refuel'][self.locale['gui.refuel.refuel_threshold']].insert(0, int(self.ed_ap.config['RefuelThreshold']))
        self.entries['refuel'][self.locale['gui.refuel.scoop_timeout']].insert(0, int(self.ed_ap.config['FuelScoopTimeOut']))
        self.entries['refuel'][self.locale['gui.refuel.fuel_threshold_abort']].insert(0, int(self.ed_ap.config['FuelThreasholdAbortAP']))
        self.entries['overlay'][self.locale['gui.overlay.x_offset']].insert(0, int(self.ed_ap.config['OverlayTextXOffset']))
        self.entries['overlay'][self.locale['gui.overlay.y_offset']].insert(0, int(self.ed_ap.config['OverlayTextYOffset']))
        self.entries['overlay'][self.locale['gui.overlay.font_size']].insert(0, int(self.ed_ap.config['OverlayTextFontSize']))

        self.entries['buttons'][self.locale['gui.buttons.start_fsd']].insert(0, str(self.ed_ap.config['HotKey_StartFSD']))
        self.entries['buttons'][self.locale['gui.buttons.start_sc']].insert(0, str(self.ed_ap.config['HotKey_StartSC']))
        self.entries['buttons'][self.locale['gui.buttons.start_robigo']].insert(0, str(self.ed_ap.config['HotKey_StartRobigo']))
        self.entries['buttons'][self.locale['gui.buttons.stop_all']].insert(0, str(self.ed_ap.config['HotKey_StopAllAssists']))

        self.entries['keys'][self.locale['gui.keys.modifier_key_delay']].insert(0, float(self.ed_ap.config['Key_ModDelay']))
        self.entries['keys'][self.locale['gui.keys.default_hold_time']].insert(0, float(self.ed_ap.config['Key_DefHoldTime']))
        self.entries['keys'][self.locale['gui.keys.repeat_key_delay']].insert(0, float(self.ed_ap.config['Key_RepeatDelay']))

        if self.ed_ap.config['LogDEBUG']:
            self.radiobuttonvar['debug_mode'].set("Debug")
        elif self.ed_ap.config['LogINFO']:
            self.radiobuttonvar['debug_mode'].set("Info")
        else:
            self.radiobuttonvar['debug_mode'].set("Error")

        # global trap for these keys, the 'end' key will stop any current AP action
        # the 'home' key will start the FSD Assist.  May want another to start SC Assist
        if self.ed_ap.config['HotkeysEnable']:
            keyboard.add_hotkey(self.ed_ap.config['HotKey_StopAllAssists'], self.stop_all_assists)
            keyboard.add_hotkey(self.ed_ap.config['HotKey_StartFSD'], self.callback, args=('fsd_start', None))
            keyboard.add_hotkey(self.ed_ap.config['HotKey_StartSC'],  self.callback, args=('sc_start',  None))
            keyboard.add_hotkey(self.ed_ap.config['HotKey_StartRobigo'],  self.callback, args=('robigo_start',  None))

        # check for updates
        self.check_updates()

        sleep(0.25)  # Added because the custom tkinter takes longer to load? Without, you occasionally get errors
        # that the main thread is not in main loop.
        self.ed_ap.gui_loaded = True
        self.gui_loaded = True
        # Send a log entry which will flush out the buffer.
        self.callback('log', 'ED Autopilot loaded successfully.')

    # callback from the EDAP, to configure GUI items
    def callback(self, msg, body=None):
        if msg == 'log':
            self.log_msg(body)
        elif msg == 'log+vce':
            self.log_msg(body)
            self.ed_ap.vce.say(body)
        elif msg == 'statusline':
            self.update_statusline(body)
        elif msg == 'fsd_stop':
            logger.debug("Detected 'fsd_stop' callback msg")
            self.checkboxvar['FSD Route Assist'].set(0)
            self.check_cb('FSD Route Assist')
        elif msg == 'fsd_start':
            self.checkboxvar['FSD Route Assist'].set(1)
            self.check_cb('FSD Route Assist')
        elif msg == 'sc_stop':
            logger.debug("Detected 'sc_stop' callback msg")
            self.checkboxvar['Supercruise Assist'].set(0)
            self.check_cb('Supercruise Assist')
        elif msg == 'sc_start':
            self.checkboxvar['Supercruise Assist'].set(1)
            self.check_cb('Supercruise Assist')
        elif msg == 'waypoint_stop':
            logger.debug("Detected 'waypoint_stop' callback msg")
            self.checkboxvar['Waypoint Assist'].set(0)
            self.check_cb('Waypoint Assist')
        elif msg == 'waypoint_start':
            self.checkboxvar['Waypoint Assist'].set(1)
            self.check_cb('Waypoint Assist')
        elif msg == 'robigo_stop':
            logger.debug("Detected 'robigo_stop' callback msg")
            self.checkboxvar['Robigo Assist'].set(0)
            self.check_cb('Robigo Assist')
        elif msg == 'robigo_start':
            self.checkboxvar['Robigo Assist'].set(1)
            self.check_cb('Robigo Assist')
        elif msg == 'afk_stop':
            logger.debug("Detected 'afk_stop' callback msg")
            self.checkboxvar['AFK Combat Assist'].set(0)
            self.check_cb('AFK Combat Assist')
        elif msg == 'dss_start':
            logger.debug("Detected 'dss_start' callback msg")
            self.checkboxvar['DSS Assist'].set(1)
            self.check_cb('DSS Assist')
        elif msg == 'dss_stop':
            logger.debug("Detected 'dss_stop' callback msg")
            self.checkboxvar['DSS Assist'].set(0)
            self.check_cb('DSS Assist')
        elif msg == 'single_waypoint_stop':
            logger.debug("Detected 'single_waypoint_stop' callback msg")
            self.checkboxvar['Single Waypoint Assist'].set(0)
            self.check_cb('Single Waypoint Assist')

        elif msg == 'stop_all_assists':
            logger.debug("Detected 'stop_all_assists' callback msg")

            self.checkboxvar['FSD Route Assist'].set(0)
            self.check_cb('FSD Route Assist')

            self.checkboxvar['Supercruise Assist'].set(0)
            self.check_cb('Supercruise Assist')

            self.checkboxvar['Waypoint Assist'].set(0)
            self.check_cb('Waypoint Assist')

            self.checkboxvar['Robigo Assist'].set(0)
            self.check_cb('Robigo Assist')

            self.checkboxvar['AFK Combat Assist'].set(0)
            self.check_cb('AFK Combat Assist')

            self.checkboxvar['DSS Assist'].set(0)
            self.check_cb('DSS Assist')

            self.checkboxvar['Single Waypoint Assist'].set(0)
            self.check_cb('Single Waypoint Assist')

        elif msg == 'jumpcount':
            self.update_jumpcount(body)
        elif msg == 'update_ship_cfg':
            self.update_ship_cfg()

    def update_ship_cfg(self):
        # load up the display with what we read from ED_AP for the current ship
        self.entries['ship'][self.locale['gui.ship.pitch_rate']].delete(0, tk.END)
        self.entries['ship'][self.locale['gui.ship.roll_rate']].delete(0, tk.END)
        self.entries['ship'][self.locale['gui.ship.yaw_rate']].delete(0, tk.END)
        self.entries['ship'][self.locale['gui.ship.sun_pitch_up_time']].delete(0, tk.END)
        self.entries['ship'][self.locale['gui.ship.pitch_factor']].delete(0, tk.END)
        self.entries['ship'][self.locale['gui.ship.roll_factor']].delete(0, tk.END)
        self.entries['ship'][self.locale['gui.ship.yaw_factor']].delete(0, tk.END)

        self.entries['ship'][self.locale['gui.ship.pitch_rate']].insert(0, self.ed_ap.pitchrate)
        self.entries['ship'][self.locale['gui.ship.roll_rate']].insert(0, self.ed_ap.rollrate)
        self.entries['ship'][self.locale['gui.ship.yaw_rate']].insert(0, self.ed_ap.yawrate)
        self.entries['ship'][self.locale['gui.ship.sun_pitch_up_time']].insert(0, self.ed_ap.sunpitchuptime)
        self.entries['ship'][self.locale['gui.ship.pitch_factor']].insert(0, self.ed_ap.pitchfactor)
        self.entries['ship'][self.locale['gui.ship.roll_factor']].insert(0, self.ed_ap.rollfactor)
        self.entries['ship'][self.locale['gui.ship.yaw_factor']].insert(0, self.ed_ap.yawfactor)

    def calibrate_callback(self):
        self.ed_ap.calibrate_target()

    def calibrate_compass_callback(self):
        self.ed_ap.calibrate_compass()

    def quit(self):
        logger.debug("Entered: quit")
        self.close_window()

    def close_window(self):
        logger.debug("Entered: close_window")
        self.stop_fsd()
        self.stop_sc()
        self.ed_ap.quit()
        sleep(0.1)
        self.root.destroy()

    def reload_localization(self):
        """Reload localization and update all GUI elements with localized text."""
        # Reload localization data
        self.locale.reload()

        # Update window title
        self.root.title(self.locale["gui.main.title"] + " " + self.locale["gui.version"])

        # Update status bar text
        self.statusbar.configure(text=self.locale["gui.status"] + ": " + self.locale["gui.status"])

        # Update tooltips with localized text
        self.tooltips = {
            'FSD Route Assist': self.locale["tooltips.fsd_route_assist"],
            'Supercruise Assist': self.locale["tooltips.supercruise_assist"],
            'Waypoint Assist': self.locale["tooltips.waypoint_assist"],
            'Robigo Assist': self.locale["tooltips.robigo_assist"],
            'DSS Assist': self.locale["tooltips.dss_assist"],
            'Single Waypoint Assist': self.locale["tooltips.single_waypoint_assist"],
            'ELW Scanner': self.locale["tooltips.elw_scanner"],
            'AFK Combat Assist': self.locale["tooltips.afk_combat_assist"],
            self.locale['gui.ship.roll_rate']: self.locale["tooltips.roll_rate"],
            self.locale['gui.ship.pitch_rate']: self.locale["tooltips.pitch_rate"],
            self.locale['gui.ship.yaw_rate']: self.locale["tooltips.yaw_rate"],
            self.locale['gui.ship.roll_factor']: self.locale["tooltips.roll_factor"],
            self.locale['gui.ship.pitch_factor']: self.locale["tooltips.pitch_factor"],
            self.locale['gui.ship.yaw_factor']: self.locale["tooltips.yaw_factor"],
            self.locale['gui.ship.sun_pitch_up_time']: self.locale["tooltips.sun_pitch_up_time"],
            'Sun Bright Threshold': self.locale["tooltips.sun_bright_threshold"],
            'Nav Align Tries': self.locale["tooltips.nav_align_tries"],
            'Jump Tries': self.locale["tooltips.jump_tries"],
            'Docking Retries': self.locale["tooltips.docking_retries"],
            'Wait For Autodock': self.locale["tooltips.wait_for_autodock"],
            'Start FSD': self.locale["tooltips.start_fsd"],
            'Start SC': self.locale["tooltips.start_sc"],
            'Start Robigo': self.locale["tooltips.start_robigo"],
            'Stop All': self.locale["tooltips.stop_all"],
            'Refuel Threshold': self.locale["tooltips.refuel_threshold"],
            'Scoop Timeout': self.locale["tooltips.scoop_timeout"],
            'Fuel Threshold Abort': self.locale["tooltips.fuel_threshold_abort"],
            'X Offset': self.locale["tooltips.x_offset"],
            'Y Offset': self.locale["tooltips.y_offset"],
            'Font Size': self.locale["tooltips.font_size"],
            'Calibrate': self.locale["tooltips.calibrate"],
            'Waypoint List Button': self.locale["tooltips.waypoint_list_button"],
            'Cap Mouse XY': self.locale["tooltips.cap_mouse_xy"],
            'Reset Waypoint List': self.locale["tooltips.reset_waypoint_list"],
            'Debug Overlay': self.locale["tooltips.debug_overlay"],
            'Debug OCR': self.locale["tooltips.debug_ocr"],
            'Debug Images': self.locale["tooltips.debug_images"],
            'Debug Mode': self.locale["tooltips.mode"],
            'Modifier Key Delay': self.locale["tooltips.modifier_key_delay"],
            'Default Hold Time': self.locale["tooltips.default_hold_time"],
            'Repeat Key Delay': self.locale["tooltips.repeat_key_delay"]
        }

        # Update all GUI labels and buttons with localized text
        # This would require iterating through all GUI elements and updating their text
        # For now, we'll update key elements that are already using hardcoded strings
        # The full integration would require a more comprehensive refactoring of GUI generation code
        # For this task, we're adding the infrastructure for localization support

        # Log reload
        self.log_msg(self.locale["messages.update_available"])

    def on_language_change(self, event):
        """Handle language change event from dropdown.

        Args:
            event: The event object from the combobox selection.
        """
        try:
            # Get selected language from combobox
            new_language = self.language_var.get()

            # Validate language code (should be 2-3 characters)
            if len(new_language) != 2 or new_language not in self.locale.get_available_languages():
                self.log_msg(f"Invalid language code: {new_language}")
                return

            # Update configuration
            self.ed_ap.config['Language'] = new_language

            # Save configuration
            self.ed_ap.update_config()

            # Reload localization with new language
            self.locale.set_language(new_language)

            # Update GUI with new language
            self.update_language(new_language)

            self.log_msg(self.locale["messages.language_changed"])
        except Exception as e:
            logger.error(f"Error changing language: {e}")
            self.log_msg(f"Error changing language: {e}")

    def update_language(self, new_language: str):
        """Update all GUI elements with new language.

        Args:
            new_language: The new language code to apply.
        """
        # Update window title
        self.root.title(self.locale["gui.main.title"] + " " + self.locale["gui.version"])

        # Update tooltips with localized text
        self.tooltips = {
            'FSD Route Assist': self.locale["tooltips.fsd_route_assist"],
            'Supercruise Assist': self.locale["tooltips.supercruise_assist"],
            'Waypoint Assist': self.locale["tooltips.waypoint_assist"],
            'Robigo Assist': self.locale["tooltips.robigo_assist"],
            'DSS Assist': self.locale["tooltips.dss_assist"],
            'Single Waypoint Assist': self.locale["tooltips.single_waypoint_assist"],
            'ELW Scanner': self.locale["tooltips.elw_scanner"],
            'AFK Combat Assist': self.locale["tooltips.afk_combat_assist"],
            self.locale['gui.ship.roll_rate']: self.locale["tooltips.roll_rate"],
            self.locale['gui.ship.pitch_rate']: self.locale["tooltips.pitch_rate"],
            self.locale['gui.ship.yaw_rate']: self.locale["tooltips.yaw_rate"],
            self.locale['gui.ship.roll_factor']: self.locale["tooltips.roll_factor"],
            self.locale['gui.ship.pitch_factor']: self.locale["tooltips.pitch_factor"],
            self.locale['gui.ship.yaw_factor']: self.locale["tooltips.yaw_factor"],
            self.locale['gui.ship.sun_pitch_up_time']: self.locale["tooltips.sun_pitch_up_time"],
            'Sun Bright Threshold': self.locale["tooltips.sun_bright_threshold"],
            'Nav Align Tries': self.locale["tooltips.nav_align_tries"],
            'Jump Tries': self.locale["tooltips.jump_tries"],
            'Docking Retries': self.locale["tooltips.docking_retries"],
            'Wait For Autodock': self.locale["tooltips.wait_for_autodock"],
            'Start FSD': self.locale["tooltips.start_fsd"],
            'Start SC': self.locale["tooltips.start_sc"],
            'Start Robigo': self.locale["tooltips.start_robigo"],
            'Stop All': self.locale["tooltips.stop_all"],
            'Refuel Threshold': self.locale["tooltips.refuel_threshold"],
            'Scoop Timeout': self.locale["tooltips.scoop_timeout"],
            'Fuel Threshold Abort': self.locale["tooltips.fuel_threshold_abort"],
            'X Offset': self.locale["tooltips.x_offset"],
            'Y Offset': self.locale["tooltips.y_offset"],
            'Font Size': self.locale["tooltips.font_size"],
            'Calibrate': self.locale["tooltips.calibrate"],
            'Waypoint List Button': self.locale["tooltips.waypoint_list_button"],
            'Cap Mouse XY': self.locale["tooltips.cap_mouse_xy"],
            'Reset Waypoint List': self.locale["tooltips.reset_waypoint_list"],
            'Debug Overlay': self.locale["tooltips.debug_overlay"],
            'Debug OCR': self.locale["tooltips.debug_ocr"],
            'Debug Images': self.locale["tooltips.debug_images"],
            'Debug Mode': self.locale["tooltips.mode"],
            'Modifier Key Delay': self.locale["tooltips.modifier_key_delay"],
            'Default Hold Time': self.locale["tooltips.default_hold_time"],
            'Repeat Key Delay': self.locale["tooltips.repeat_key_delay"]
        }

        # Update status line
        self.update_statusline(self.locale["messages.status_idle"])

        # Update language combobox to show current selection
        self.language_var.set(new_language)

        # Note: Full GUI text update would require iterating through all GUI elements
        # and updating their text. For now, we update key elements that are
        # already using localized strings through self.locale dictionary.

    # this routine is to stop any current autopilot activity
    def stop_all_assists(self):
        logger.debug("Entered: stop_all_assists")
        self.callback('stop_all_assists')

    def start_fsd(self):
        logger.debug("Entered: start_fsd")
        self.ed_ap.set_fsd_assist(True)
        self.FSD_A_running = True
        self.log_msg(self.locale["messages.fsd_route_assist_start"])
        self.ed_ap.vce.say(self.locale["messages.fsd_route_assist_on"])

    def stop_fsd(self):
        logger.debug("Entered: stop_fsd")
        self.ed_ap.set_fsd_assist(False)
        self.FSD_A_running = False
        self.log_msg(self.locale["messages.fsd_route_assist_stop"])
        self.ed_ap.vce.say(self.locale["messages.fsd_route_assist_off"])
        self.update_statusline(self.locale["messages.status_idle"])

    def start_sc(self):
        logger.debug("Entered: start_sc")
        self.ed_ap.set_sc_assist(True)
        self.SC_A_running = True
        self.log_msg(self.locale["messages.sc_assist_start"])
        self.ed_ap.vce.say(self.locale["messages.supercruise_assist_on"])

    def stop_sc(self):
        logger.debug("Entered: stop_sc")
        self.ed_ap.set_sc_assist(False)
        self.SC_A_running = False
        self.log_msg(self.locale["messages.sc_assist_stop"])
        self.ed_ap.vce.say(self.locale["messages.supercruise_assist_off"])
        self.update_statusline(self.locale["messages.status_idle"])

    def start_waypoint(self):
        logger.debug("Entered: start_waypoint")
        self.ed_ap.set_waypoint_assist(True)
        self.WP_A_running = True
        self.log_msg(self.locale["messages.waypoint_assist_start"])
        self.ed_ap.vce.say(self.locale["messages.waypoint_assist_on"])

    def stop_waypoint(self):
        logger.debug("Entered: stop_waypoint")
        self.ed_ap.set_waypoint_assist(False)
        self.WP_A_running = False
        self.log_msg(self.locale["messages.waypoint_assist_start"])
        self.ed_ap.vce.say(self.locale["messages.waypoint_assist_on"])
        self.update_statusline("Idle")

    def start_robigo(self):
        logger.debug("Entered: start_robigo")
        self.ed_ap.set_robigo_assist(True)
        self.RO_A_running = True
        self.log_msg(self.locale["messages.robigo_assist_start"])
        self.ed_ap.vce.say(self.locale["messages.robigo_assist_on"])

    def stop_robigo(self):
        logger.debug("Entered: stop_robigo")
        self.ed_ap.set_robigo_assist(False)
        self.RO_A_running = False
        self.log_msg(self.locale["messages.robigo_assist_stop"])
        self.ed_ap.vce.say(self.locale["messages.robigo_assist_off"])
        self.update_statusline(self.locale["messages.status_idle"])

    def start_dss(self):
        logger.debug("Entered: start_dss")
        self.ed_ap.set_dss_assist(True)
        self.DSS_A_running = True
        self.log_msg(self.locale["messages.dss_assist_start"])
        self.ed_ap.vce.say(self.locale["messages.dss_assist_on"])

    def stop_dss(self):
        logger.debug("Entered: stop_dss")
        self.ed_ap.set_dss_assist(False)
        self.DSS_A_running = False
        self.log_msg(self.locale["messages.dss_assist_stop"])
        self.ed_ap.vce.say(self.locale["messages.dss_assist_off"])
        self.update_statusline(self.locale["messages.status_idle"])

    def start_single_waypoint_assist(self):
        """ The debug command to go to a system or station or both."""
        logger.debug("Entered: start_single_waypoint_assist")
        system = self.single_waypoint_system.get()
        station = self.single_waypoint_station.get()

        if system != "" or station != "":
            self.ed_ap.set_single_waypoint_assist(system, station, True)
            self.SWP_A_running = True
            self.log_msg(self.locale["messages.single_waypoint_assist_start"])
            self.ed_ap.vce.say(self.locale["messages.single_waypoint_assist_on"])

    def stop_single_waypoint_assist(self):
        """ The debug command to go to a system or station or both."""
        logger.debug("Entered: stop_single_waypoint_assist")
        self.ed_ap.set_single_waypoint_assist("", "", False)
        self.SWP_A_running = False
        self.log_msg(self.locale["messages.single_waypoint_assist_stop"])
        self.ed_ap.vce.say(self.locale["messages.single_waypoint_assist_off"])
        self.update_statusline(self.locale["messages.status_idle"])

    def about(self):
        webbrowser.open_new("https://github.com/SumZer0-git/EDAPGui")

    def check_for_updates(self, repo_path):
        try:
            # Fetch the latest changes from the remote repository
            subprocess.run(["git", "fetch"], cwd=repo_path, check=True, capture_output=True)

            # Get the current commit hash of the local repository
            local_hash = subprocess.run(["git", "rev-parse", "HEAD"], cwd=repo_path, capture_output=True, text=True,
                                        check=True).stdout.strip()

            # Get the commit hash of the remote repository
            remote_hash = subprocess.run(["git", "rev-parse", "origin/HEAD"], cwd=repo_path, capture_output=True,
                                         text=True, check=True).stdout.strip()

            # Compare commit hashes
            if local_hash != remote_hash:
                print(self.locale["messages.repository_updated"])
                return True
            else:
                print(self.locale["messages.repository_up_to_date"])
                return False

        except subprocess.CalledProcessError as e:
            print(self.locale["messages.error_checking_updates"].format(e=e))
            return False
        except FileNotFoundError:
            print(self.locale["messages.git_not_found"])
            return False

    def check_updates(self):
        # response = requests.get("https://api.github.com/repos/SumZer0-git/EDAPGui/releases/latest")
        # if EDAP_VERSION != response.json()["name"]:
        #     mb = messagebox.askokcancel("Update Check", "A new release version is available. Download now?")
        #     if mb == True:
        #         webbrowser.open_new("https://github.com/SumZer0-git/EDAPGui/releases/latest")

        # Example usage:
        # repo_path = "/path/to/your/local/repo"
        repo_path = "./"
        updates_available = self.check_for_updates(repo_path)

        if updates_available:
            # Optionally, provide further instructions or automate the cloning process
            self.log_msg("=====================================================")
            self.log_msg("========== An update to EDAP is available ===========")
            self.log_msg("==== Click 'Check for Updates' on the Debug tab, ====")
            self.log_msg("====== or go directly to the EDAP Github page =======")
            self.log_msg("=====================================================")

            # print("You can use the following command to clone the repository again:")
            # print("git clone <repository_url> <new_directory_name>")
        else:
            self.log_msg(self.locale["messages.you_have_latest_version"])

    def open_changelog(self):
        webbrowser.open_new("https://github.com/SumZer0-git/EDAPGui/blob/main/ChangeLog.md")

    def open_discord(self):
        webbrowser.open_new("https://discord.gg/HCgkfSc")

    def open_logfile(self):
        os.startfile('autopilot.log')

    def log_msg(self, msg):
        message = datetime.now().strftime("%H:%M:%S: ") + msg

        try:
            if not self.gui_loaded:
                # Store message in queue
                self.log_buffer.put(message)
                logger.info(msg)
            else:
                # Add queued messages to the list
                while not self.log_buffer.empty():
                    self.msgList.insert(tk.END, self.log_buffer.get())

                self.msgList.insert(tk.END, message)
                self.msgList.yview(tk.END)
                logger.info(msg)
        except:
            # Store message in queue
            self.log_buffer.put(message)
            logger.info(msg)

    def set_statusbar(self, txt):
        self.statusbar.configure(text=txt)

    def update_jumpcount(self, txt):
        self.jumpcount.configure(text=txt)

    def update_statusline(self, txt):
        self.status.configure(text=self.locale["gui.status.label"] + ": " + txt)
        self.log_msg(f"Status update: {txt}")

    def ship_tst_pitch(self):
        # self.ed_ap.ship_tst_pitch(360)
        # self.ed_ap.ship_tst_pitch_new(360)
        self.ed_ap.ship_tst_pitch_enabled = True

    def ship_tst_roll(self):
        # self.ed_ap.ship_tst_roll(360)
        # self.ed_ap.ship_tst_roll_new(360)
        self.ed_ap.ship_tst_roll_enabled = True

    def ship_tst_yaw(self):
        # self.ed_ap.ship_tst_yaw(360)
        # self.ed_ap.ship_tst_yaw_new(360)
        self.ed_ap.ship_tst_yaw_enabled = True

    def ship_tst_pitch_30(self):
        self.ed_ap.ship_tst_pitch(30)

    def ship_tst_roll_30(self):
        self.ed_ap.ship_tst_roll(30)

    def ship_tst_yaw_30(self):
        self.ed_ap.ship_tst_yaw(30)

    def ship_tst_pitch_45(self):
        self.ed_ap.ship_tst_pitch(45)

    def ship_tst_roll_45(self):
        self.ed_ap.ship_tst_roll(45)

    def ship_tst_yaw_45(self):
        self.ed_ap.ship_tst_yaw(45)

    def ship_tst_pitch_90(self):
        self.ed_ap.ship_tst_pitch(90)

    def ship_tst_roll_90(self):
        self.ed_ap.ship_tst_roll(90)

    def ship_tst_yaw_90(self):
        self.ed_ap.ship_tst_yaw(90)

    def open_wp_file(self):
        filetypes = (
            ('json files', '*.json'),
            ('All files', '*.*')
        )
        filename = fd.askopenfilename(title=self.locale["file.waypoint_file"], initialdir='./waypoints/', filetypes=filetypes)
        if filename != "":
            res = self.ed_ap.waypoint.load_waypoint_file(filename)
            if res:
                self.wp_filelabel.set(self.locale["file.loaded_filename"] + Path(filename).name)
            else:
                self.wp_filelabel.set(self.locale["file.no_list_loaded"])

    def reset_wp_file(self):
        if not self.WP_A_running:
            mb = messagebox.askokcancel(self.locale["file.waypoint_list_reset"], self.locale["file.waypoint_list_reset_description"])
            if mb:
                self.ed_ap.waypoint.mark_all_waypoints_not_complete()
        else:
            mb = messagebox.showerror(self.locale["file.waypoint_list_error"], self.locale["file.waypoint_list_error_description"])

    def save_settings(self):
        self.entry_update(None)
        self.ed_ap.update_config()
        self.ed_ap.update_ship_configs()
        self.save_ocr_calibration_data()
        self.log_msg(self.locale["messages.saved_all_settings"])

    # new data was added to a field, re-read them all for simple logic
    def entry_update(self, event):
        try:
            self.ed_ap.pitchrate = float(self.entries['ship'][self.locale['gui.ship.pitch_rate']].get())
            self.ed_ap.rollrate = float(self.entries['ship'][self.locale['gui.ship.roll_rate']].get())
            self.ed_ap.yawrate = float(self.entries['ship'][self.locale['gui.ship.yaw_rate']].get())
            self.ed_ap.sunpitchuptime = float(self.entries['ship'][self.locale['gui.ship.sun_pitch_up_time']].get())
            self.ed_ap.pitchfactor = float(self.entries['ship'][self.locale['gui.ship.pitch_factor']].get())
            self.ed_ap.rollfactor = float(self.entries['ship'][self.locale['gui.ship.roll_factor']].get())
            self.ed_ap.yawfactor = float(self.entries['ship'][self.locale['gui.ship.yaw_factor']].get())

            self.ed_ap.config['SunBrightThreshold'] = int(self.entries['autopilot'][self.locale['gui.autopilot.sun_bright_threshold']].get())
            self.ed_ap.config['NavAlignTries'] = int(self.entries['autopilot'][self.locale['gui.autopilot.nav_align_tries']].get())
            self.ed_ap.config['JumpTries'] = int(self.entries['autopilot'][self.locale['gui.autopilot.jump_tries']].get())
            self.ed_ap.config['DockingRetries'] = int(self.entries['autopilot'][self.locale['gui.autopilot.docking_retries']].get())
            self.ed_ap.config['WaitForAutoDockTimer'] = int(self.entries['autopilot'][self.locale['gui.autopilot.wait_for_autodock']].get())
            self.ed_ap.config['RefuelThreshold'] = int(self.entries['refuel'][self.locale['gui.refuel.refuel_threshold']].get())
            self.ed_ap.config['FuelScoopTimeOut'] = int(self.entries['refuel'][self.locale['gui.refuel.scoop_timeout']].get())
            self.ed_ap.config['FuelThreasholdAbortAP'] = int(self.entries['refuel'][self.locale['gui.refuel.fuel_threshold_abort']].get())
            self.ed_ap.config['OverlayTextXOffset'] = int(self.entries['overlay'][self.locale['gui.overlay.x_offset']].get())
            self.ed_ap.config['OverlayTextYOffset'] = int(self.entries['overlay'][self.locale['gui.overlay.y_offset']].get())
            self.ed_ap.config['OverlayTextFontSize'] = int(self.entries['overlay'][self.locale['gui.overlay.font_size']].get())
            self.ed_ap.config['HotKey_StartFSD'] = str(self.entries['buttons'][self.locale['gui.buttons.start_fsd']].get())
            self.ed_ap.config['HotKey_StartSC'] = str(self.entries['buttons'][self.locale['gui.buttons.start_sc']].get())
            self.ed_ap.config['HotKey_StartRobigo'] = str(self.entries['buttons'][self.locale['gui.buttons.start_robigo']].get())
            self.ed_ap.config['HotKey_StopAllAssists'] = str(self.entries['buttons'][self.locale['gui.buttons.stop_all']].get())
            self.ed_ap.config['VoiceEnable'] = self.checkboxvar['Enable Voice'].get()
            self.ed_ap.config['DebugOverlay'] = self.checkboxvar['Debug Overlay'].get()
            self.ed_ap.config['AFKCombat_AttackAtWill'] = self.checkboxvar['AFKCombat AttackAtWill'].get()
            self.ed_ap.config['HotkeysEnable'] = self.checkboxvar['Enable Hotkeys'].get()
            self.ed_ap.config['DebugOCR'] = self.checkboxvar['Debug OCR'].get()
            self.ed_ap.config['DebugImages'] = self.checkboxvar['Debug Images'].get()
            self.ed_ap.config['Key_ModDelay'] = float(self.entries['keys'][self.locale['gui.keys.modifier_key_delay']].get())
            self.ed_ap.config['Key_DefHoldTime'] = float(self.entries['keys'][self.locale['gui.keys.default_hold_time']].get())
            self.ed_ap.config['Key_RepeatDelay'] = float(self.entries['keys'][self.locale['gui.keys.repeat_key_delay']].get())

            # Process config[] settings to update classes as necessary
            self.ed_ap.process_config_settings()
        except:
            messagebox.showinfo("Exception", self.locale["messages.invalid_float"])

    # ckbox.state:(ACTIVE | DISABLED)

    # ('FSD Route Assist', 'Supercruise Assist', 'Enable Voice', 'Enable CV View')
    def check_cb(self, field):
        # print("got event:",  checkboxvar['FSD Route Assist'].get(), " ", str(FSD_A_running))
        if field == 'FSD Route Assist':
            if self.checkboxvar['FSD Route Assist'].get() == 1 and self.FSD_A_running == False:
                self.lab_ck['AFK Combat Assist'].config(state='disabled')
                self.lab_ck['Supercruise Assist'].config(state='disabled')
                self.lab_ck['Waypoint Assist'].config(state='disabled')
                self.lab_ck['Robigo Assist'].config(state='disabled')
                self.lab_ck['DSS Assist'].config(state='disabled')
                self.start_fsd()

            elif self.checkboxvar['FSD Route Assist'].get() == 0 and self.FSD_A_running == True:
                self.stop_fsd()
                self.lab_ck['Supercruise Assist'].config(state='active')
                self.lab_ck['AFK Combat Assist'].config(state='active')
                self.lab_ck['Waypoint Assist'].config(state='active')
                self.lab_ck['Robigo Assist'].config(state='active')
                self.lab_ck['DSS Assist'].config(state='active')

        if field == 'Supercruise Assist':
            if self.checkboxvar['Supercruise Assist'].get() == 1 and self.SC_A_running == False:
                self.lab_ck['FSD Route Assist'].config(state='disabled')
                self.lab_ck['AFK Combat Assist'].config(state='disabled')
                self.lab_ck['Waypoint Assist'].config(state='disabled')
                self.lab_ck['Robigo Assist'].config(state='disabled')
                self.lab_ck['DSS Assist'].config(state='disabled')
                self.start_sc()

            elif self.checkboxvar['Supercruise Assist'].get() == 0 and self.SC_A_running == True:
                self.stop_sc()
                self.lab_ck['FSD Route Assist'].config(state='active')
                self.lab_ck['AFK Combat Assist'].config(state='active')
                self.lab_ck['Waypoint Assist'].config(state='active')
                self.lab_ck['Robigo Assist'].config(state='active')
                self.lab_ck['DSS Assist'].config(state='active')

        if field == 'Waypoint Assist':
            if self.checkboxvar['Waypoint Assist'].get() == 1 and self.WP_A_running == False:
                self.lab_ck['FSD Route Assist'].config(state='disabled')
                self.lab_ck['Supercruise Assist'].config(state='disabled')
                self.lab_ck['AFK Combat Assist'].config(state='disabled')
                self.lab_ck['Robigo Assist'].config(state='disabled')
                self.lab_ck['DSS Assist'].config(state='disabled')
                self.start_waypoint()

            elif self.checkboxvar['Waypoint Assist'].get() == 0 and self.WP_A_running == True:
                self.stop_waypoint()
                self.lab_ck['FSD Route Assist'].config(state='active')
                self.lab_ck['Supercruise Assist'].config(state='active')
                self.lab_ck['AFK Combat Assist'].config(state='active')
                self.lab_ck['Robigo Assist'].config(state='active')
                self.lab_ck['DSS Assist'].config(state='active')

        if field == 'Robigo Assist':
            if self.checkboxvar['Robigo Assist'].get() == 1 and self.RO_A_running == False:
                self.lab_ck['FSD Route Assist'].config(state='disabled')
                self.lab_ck['Supercruise Assist'].config(state='disabled')
                self.lab_ck['AFK Combat Assist'].config(state='disabled')
                self.lab_ck['Waypoint Assist'].config(state='disabled')
                self.lab_ck['DSS Assist'].config(state='disabled')
                self.start_robigo()

            elif self.checkboxvar['Robigo Assist'].get() == 0 and self.RO_A_running == True:
                self.stop_robigo()
                self.lab_ck['FSD Route Assist'].config(state='active')
                self.lab_ck['Supercruise Assist'].config(state='active')
                self.lab_ck['AFK Combat Assist'].config(state='active')
                self.lab_ck['Waypoint Assist'].config(state='active')
                self.lab_ck['DSS Assist'].config(state='active')

        if field == 'AFK Combat Assist':
            if self.checkboxvar['AFK Combat Assist'].get() == 1:
                self.ed_ap.set_afk_combat_assist(True)
                self.log_msg(self.locale["messages.afk_combat_assist_start"])
                self.lab_ck['FSD Route Assist'].config(state='disabled')
                self.lab_ck['Supercruise Assist'].config(state='disabled')
                self.lab_ck['Waypoint Assist'].config(state='disabled')
                self.lab_ck['Robigo Assist'].config(state='disabled')
                self.lab_ck['DSS Assist'].config(state='disabled')

            elif self.checkboxvar['AFK Combat Assist'].get() == 0:
                self.ed_ap.set_afk_combat_assist(False)
                self.log_msg(self.locale["messages.afk_combat_assist_stop"])
                self.lab_ck['FSD Route Assist'].config(state='active')
                self.lab_ck['Supercruise Assist'].config(state='active')
                self.lab_ck['Waypoint Assist'].config(state='active')
                self.lab_ck['Robigo Assist'].config(state='active')
                self.lab_ck['DSS Assist'].config(state='active')

        if field == 'DSS Assist':
            if self.checkboxvar['DSS Assist'].get() == 1:
                self.lab_ck['FSD Route Assist'].config(state='disabled')
                self.lab_ck['AFK Combat Assist'].config(state='disabled')
                self.lab_ck['Supercruise Assist'].config(state='disabled')
                self.lab_ck['Waypoint Assist'].config(state='disabled')
                self.lab_ck['Robigo Assist'].config(state='disabled')
                self.start_dss()

            elif self.checkboxvar['DSS Assist'].get() == 0:
                self.stop_dss()
                self.lab_ck['FSD Route Assist'].config(state='active')
                self.lab_ck['Supercruise Assist'].config(state='active')
                self.lab_ck['AFK Combat Assist'].config(state='active')
                self.lab_ck['Waypoint Assist'].config(state='active')
                self.lab_ck['Robigo Assist'].config(state='active')

        if self.checkboxvar['Enable Randomness'].get():
            self.ed_ap.set_randomness(True)
        else:
            self.ed_ap.set_randomness(False)

        if self.checkboxvar['Activate Elite for each key'].get():
            self.ed_ap.set_activate_elite_eachkey(True)
            self.ed_ap.keys.activate_window=True
        else:
            self.ed_ap.set_activate_elite_eachkey(False)
            self.ed_ap.keys.activate_window = False

        if self.checkboxvar['Automatic logout'].get():
            self.ed_ap.set_automatic_logout(True)
        else:
            self.ed_ap.set_automatic_logout(False)

        if self.checkboxvar['Enable Overlay'].get():
            self.ed_ap.set_overlay(True)
        else:
            self.ed_ap.set_overlay(False)

        if self.checkboxvar['Enable Voice'].get():
            self.ed_ap.set_voice(True)
        else:
            self.ed_ap.set_voice(False)

        if self.checkboxvar['ELW Scanner'].get():
            self.ed_ap.set_fss_scan(True)
        else:
            self.ed_ap.set_fss_scan(False)

        if self.checkboxvar['Enable CV View'].get() == 1:
            self.cv_view = True
            x = self.root.winfo_x() + self.root.winfo_width() + 4
            y = self.root.winfo_y()
            self.ed_ap.set_cv_view(True, x, y)
        else:
            self.cv_view = False
            self.ed_ap.set_cv_view(False)

        self.ed_ap.config['DSSButton'] = self.radiobuttonvar['dss_button'].get()

        if self.radiobuttonvar['debug_mode'].get() == "Error":
            self.ed_ap.set_log_error(True)
        elif self.radiobuttonvar['debug_mode'].get() == "Debug":
            self.ed_ap.set_log_debug(True)
        elif self.radiobuttonvar['debug_mode'].get() == "Info":
            self.ed_ap.set_log_info(True)

        if field == 'Single Waypoint Assist':
            if self.checkboxvar['Single Waypoint Assist'].get() == 1 and self.SWP_A_running == False:
                self.start_single_waypoint_assist()
            elif self.checkboxvar['Single Waypoint Assist'].get() == 0 and self.SWP_A_running == True:
                self.stop_single_waypoint_assist()

        if field == 'Debug Overlay':
            if self.checkboxvar['Debug Overlay'].get():
                self.ed_ap.debug_overlay = True
            else:
                self.ed_ap.debug_overlay = False

        self.ed_ap.config['AFKCombat_AttackAtWill'] = self.checkboxvar['AFKCombat AttackAtWill'].get()
        self.ed_ap.config['HotkeysEnable'] = self.checkboxvar['Enable Hotkeys'].get()

        if field == 'Debug OCR':
            self.ed_ap.debug_ocr = self.checkboxvar['Debug OCR'].get()

        if field == 'Debug Images':
            self.ed_ap.debug_images = self.checkboxvar['Debug Images'].get()

    def makeform(self, win, ftype, fields, r: int = 0, inc: float = 1, r_from: float = 0, rto: float = 1000):
        entries = {}
        win.columnconfigure(1, weight=1)

        for field in fields:
            if ftype == FORM_TYPE_CHECKBOX:
                self.checkboxvar[field] = tk.IntVar()
                lab = ttk.Checkbutton(win, text=field, variable=self.checkboxvar[field], command=(lambda field=field: self.check_cb(field)))
                self.lab_ck[field] = lab
                lab.grid(row=r, column=0, columnspan=2, padx=2, pady=2, sticky=tk.W)
            else:
                lab = ttk.Label(win, text=field + ": ")
                if ftype == FORM_TYPE_SPINBOX:
                    ent = ttk.Spinbox(win, width=10, from_=r_from, to=rto, increment=inc, justify=tk.RIGHT)
                else:
                    ent = ttk.Entry(win, width=10, justify=tk.RIGHT)
                ent.bind('<FocusOut>', self.entry_update)
                ent.insert(0, "0")
                lab.grid(row=r, column=0, padx=2, pady=2, sticky=tk.W)
                ent.grid(row=r, column=1, padx=2, pady=2, sticky=tk.E)
                entries[field] = ent

            lab = ToolTip(lab, msg=self.tooltips[field], delay=1.0, bg="#808080", fg="#FFFFFF")
            r += 1
        return entries

    # OCR calibration methods moved to before __init__

    def on_region_select(self, event):
        selected_region = self.calibration_region_var.get()
        if selected_region in self.ocr_calibration_data:
            rect = self.ocr_calibration_data[selected_region]['rect']
            self.calibration_rect_label_var.set(f"[{rect[0]:.4f}, {rect[1]:.4f}, {rect[2]:.4f}, {rect[3]:.4f}]")
            self.calibration_rect_text_var.set(f"{self.ocr_calibration_data[selected_region].get('text','')}")
            self.calibration_rect_left_var.set(rect[0])
            self.calibration_rect_top_var.set(rect[1])
            self.calibration_rect_right_var.set(rect[2])
            self.calibration_rect_bottom_var.set(rect[3])

            reg_f = Quad.from_rect(rect)
            self.ed_ap.overlay.overlay_quad_pct('region select', reg_f, (0, 255, 0), 2, 15)
            self.ed_ap.overlay.overlay_paint()

    def on_region_size_change(self):
        # Check if variables are valid
        l_str = self.calibration_rect_left_var.get()
        t_str = self.calibration_rect_top_var.get()
        r_str = self.calibration_rect_right_var.get()
        b_str = self.calibration_rect_bottom_var.get()
        # Check if any are empty
        if l_str == '' or r_str == '' or t_str == '' or b_str == '':
            return

        selected_region = self.calibration_region_var.get()
        if selected_region in self.ocr_calibration_data:
            rect = self.ocr_calibration_data[selected_region]['rect']
            rect[0] = str_to_float(l_str)
            rect[1] = str_to_float(t_str)
            rect[2] = str_to_float(r_str)
            rect[3] = str_to_float(b_str)

            self.calibration_rect_label_var.set(f"[{rect[0]:.4f}, {rect[1]:.4f}, {rect[2]:.4f}, {rect[3]:.4f}]")
            self.calibration_rect_text_var.set(f"{self.ocr_calibration_data[selected_region].get('text','')}")

            reg_f = Quad.from_rect(rect)
            self.ed_ap.overlay.overlay_quad_pct('region select', reg_f, (0, 255, 0), 2, 15)
            self.ed_ap.overlay.overlay_paint()

    @staticmethod
    def calibrate_region_help():
        # TODO - delete first line and enable the second.
        webbrowser.open_new("https://github.com/Stumpii/EDAPGui/blob/main/docs/Calibration.md")
        # webbrowser.open_new("https://github.com/SumZer0-git/EDAPGui/blob/main/docs/Calibration.md")

    def create_calibration_tab(self, tab):
        self.load_ocr_calibration_data()
        tab.columnconfigure(0, weight=1)

        # Region Calibration
        blk_region_cal = ttk.LabelFrame(tab, text=self.locale["gui.main.calibration"])
        blk_region_cal.grid(row=0, column=0, padx=10, pady=5, sticky="NSEW")
        blk_region_cal.columnconfigure(1, weight=1)

        region_keys = sorted([key for key, value in self.ocr_calibration_data.items() if isinstance(value, dict) and 'rect' in value and 'compass' not in key and 'target' not in key])
        self.calibration_region_var = tk.StringVar()
        self.calibration_region_combo = ttk.Combobox(blk_region_cal, textvariable=self.calibration_region_var, values=region_keys)
        self.calibration_region_combo.grid(row=0, column=1, padx=5, pady=5, sticky="EW")
        self.calibration_region_combo.bind("<<ComboboxSelected>>", self.on_region_select)

        ttk.Label(blk_region_cal, text=self.locale["calibration.region_label"]).grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)

        ttk.Label(blk_region_cal, text=self.locale["calibration.procedure_label"]).grid(row=1, column=0, padx=5, pady=5, sticky=tk.NW)
        self.calibration_rect_text_var = tk.StringVar()
        ttk.Label(blk_region_cal, textvariable=self.calibration_rect_text_var).grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)

        ttk.Label(blk_region_cal, text=self.locale["calibration.rect_label"]).grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)
        self.calibration_rect_label_var = tk.StringVar()
        ttk.Label(blk_region_cal, textvariable=self.calibration_rect_label_var).grid(row=2, column=1, padx=5, pady=5, sticky=tk.W)

        ttk.Label(blk_region_cal, text=self.locale["calibration.manual_change_hint"]).grid(row=3, column=0, columnspan=2, padx=5, pady=5, sticky=tk.W)

        self.calibration_rect_left_var = tk.StringVar()
        lbl_calibration_rect_left = ttk.Label(blk_region_cal, text=self.locale["calibration.left_label"])
        lbl_calibration_rect_left.grid(row=4, column=0, padx=5, pady=5, sticky=tk.W)
        spn_calibration_rect_left = ttk.Spinbox(blk_region_cal, textvariable=self.calibration_rect_left_var, width=10, from_=0, to=1, increment=0.001, justify=tk.RIGHT, command=self.on_region_size_change)
        spn_calibration_rect_left.grid(row=4, column=1, padx=5, pady=5, sticky=tk.W)

        self.calibration_rect_top_var = tk.StringVar()
        lbl_calibration_rect_top = ttk.Label(blk_region_cal, text=self.locale["calibration.top_label"])
        lbl_calibration_rect_top.grid(row=5, column=0, padx=5, pady=5, sticky=tk.W)
        spn_calibration_rect_top = ttk.Spinbox(blk_region_cal, textvariable=self.calibration_rect_top_var, width=10, from_=0, to=1, increment=0.001, justify=tk.RIGHT, command=self.on_region_size_change)
        spn_calibration_rect_top.grid(row=5, column=1, padx=5, pady=5, sticky=tk.W)

        self.calibration_rect_right_var = tk.StringVar()
        lbl_calibration_rect_right = ttk.Label(blk_region_cal, text=self.locale["calibration.right_label"])
        lbl_calibration_rect_right.grid(row=6, column=0, padx=5, pady=5, sticky=tk.W)
        spn_calibration_rect_right = ttk.Spinbox(blk_region_cal, textvariable=self.calibration_rect_right_var, width=10, from_=0, to=1, increment=0.001, justify=tk.RIGHT, command=self.on_region_size_change)
        spn_calibration_rect_right.grid(row=6, column=1, padx=5, pady=5, sticky=tk.W)

        self.calibration_rect_bottom_var = tk.StringVar()
        lbl_calibration_rect_bottom = ttk.Label(blk_region_cal, text=self.locale["calibration.bottom_label"])
        lbl_calibration_rect_bottom.grid(row=7, column=0, padx=5, pady=5, sticky=tk.W)
        spn_calibration_rect_bottom = ttk.Spinbox(blk_region_cal, textvariable=self.calibration_rect_bottom_var, width=10, from_=0, to=1, increment=0.001, justify=tk.RIGHT, command=self.on_region_size_change)
        spn_calibration_rect_bottom.grid(row=7, column=1, padx=5, pady=5, sticky=tk.W)

        # ttk.Button(blk_region_cal, text="Calibrate Region", command=self.calibrate_ocr_region).grid(row=8, column=0, padx=5, pady=10, sticky=tk.W)
        ttk.Button(blk_region_cal, text=self.locale["calibration.calibrate_region_help_online"], command=self.calibrate_region_help).grid(row=8, column=0, padx=5, pady=10, sticky=tk.W)

        # Compass and Target Calibrations
        blk_other_cal = ttk.LabelFrame(tab, text=self.locale["calibration.compass_and_target_calibrations"])
        blk_other_cal.grid(row=2, column=0, padx=10, pady=5, sticky="NSEW")

        btn_calibrate_compass = ttk.Button(blk_other_cal, text=self.locale["calibration.calibrate_compass"], command=self.calibrate_compass_callback)
        btn_calibrate_compass.grid(row=1, padx=10, pady=5, sticky="W")

        lbl_calibrate_compass = ttk.Label(blk_other_cal, wraplength=500, text=self.locale["calibration.calibrate_compass_description"])
        lbl_calibrate_compass.grid(row=1, column=1, padx=10, pady=5, sticky=tk.W)

        btn_calibrate_target = ttk.Button(blk_other_cal, text=self.locale["calibration.calibrate_target"], command=self.calibrate_callback)
        btn_calibrate_target.grid(row=2, padx=10, pady=5, sticky="W")

        lbl_calibrate_target = ttk.Label(blk_other_cal, wraplength=500, text=self.locale["calibration.calibrate_target_description"])
        lbl_calibrate_target.grid(row=2, column=1, padx=10, pady=5, sticky=tk.W)

        # Button Frame
        button_frame = ttk.Frame(tab)
        button_frame.grid(row=3, column=0, padx=10, pady=10, sticky=tk.W)
        ttk.Button(button_frame, text=self.locale["calibration.save_all_calibrations"], command=self.save_ocr_calibration_data, style="Accent.TButton").pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text=self.locale["calibration.reset_all_to_default"], command=self.reset_all_calibrations).pack(side=tk.LEFT, padx=5)

    def gui_gen(self, win):

        modes_check_fields = ('FSD Route Assist', 'Supercruise Assist', 'Waypoint Assist', 'Robigo Assist', 'AFK Combat Assist', 'DSS Assist')
        ship_entry_fields = (self.locale['gui.ship.roll_rate'], self.locale['gui.ship.pitch_rate'], self.locale['gui.ship.yaw_rate'], self.locale['gui.ship.roll_factor'], self.locale['gui.ship.pitch_factor'], self.locale['gui.ship.yaw_factor'])
        autopilot_entry_fields = (self.locale['gui.autopilot.sun_bright_threshold'], self.locale['gui.autopilot.nav_align_tries'], self.locale['gui.autopilot.jump_tries'], self.locale['gui.autopilot.docking_retries'], self.locale['gui.autopilot.wait_for_autodock'])
        buttons_entry_fields = (self.locale['gui.buttons.start_fsd'], self.locale['gui.buttons.start_sc'], self.locale['gui.buttons.start_robigo'], self.locale['gui.buttons.stop_all'])
        refuel_entry_fields = (self.locale['gui.refuel.refuel_threshold'], self.locale['gui.refuel.scoop_timeout'], self.locale['gui.refuel.fuel_threshold_abort'])
        overlay_entry_fields = (self.locale['gui.overlay.x_offset'], self.locale['gui.overlay.y_offset'], self.locale['gui.overlay.font_size'])
        keys_entry_fields = (self.locale['gui.keys.modifier_key_delay'], self.locale['gui.keys.default_hold_time'], self.locale['gui.keys.repeat_key_delay'])

        # notebook pages
        btn_save = ttk.Button(win, text=self.locale["messages.save_all_settings"], command=self.save_settings, style="Accent.TButton")
        btn_save.grid(row=0, padx=10, pady=5, sticky="W")

        nb = ttk.Notebook(win)
        nb.grid(row=1, padx=10, pady=5, sticky="NSEW")

        page0 = ttk.Frame(nb)
        page0.grid_columnconfigure(0, weight=1)
        page0.grid_rowconfigure(0, weight=0)
        page0.grid_rowconfigure(1, weight=0)
        page0.grid_rowconfigure(2, weight=1)  # Log row
        nb.add(page0, text=self.locale["gui.main.title"])  # main page

        page1 = ttk.Frame(nb)
        page1.grid_columnconfigure(0, weight=1)
        nb.add(page1, text=self.locale["gui.main.settings"])  # options page

        page2 = ttk.Frame(nb)
        page2.grid_columnconfigure([0, 1], weight=1)
        nb.add(page2, text=self.locale["gui.main.debug"])  # debug/test page

        # === Calibration Tab ===
        page_calibration = ttk.Frame(nb)
        page_calibration.grid_columnconfigure(0, weight=1)
        nb.add(page_calibration, text=self.locale["gui.main.calibration"])
        self.create_calibration_tab(page_calibration)

        # === Waypoint Editor Tab ===
        page_waypoint_editor = ttk.Frame(nb)
        page_waypoint_editor.grid_columnconfigure(0, weight=1)
        nb.add(page_waypoint_editor, text=self.locale["gui.main.waypoint_editor"])
        self.waypoint_editor_tab = WaypointEditorTab(page_waypoint_editor, self.ed_ap.waypoint)
        self.waypoint_editor_tab.frame.pack(fill="both", expand=True)

        # === TCE Integration ===
        page_tce_integration = ttk.Frame(nb)
        page_tce_integration.grid_columnconfigure(0, weight=1)
        nb.add(page_tce_integration, text="TCE")
        tce_integration_tab = self.ed_ap.tce_integration.create_gui_tab(self, page_tce_integration)

        # === MAIN TAB ===
        # main options block
        blk_main = ttk.Frame(page0)
        blk_main.grid(row=0, column=0, padx=10, pady=5, sticky="NSEW")
        blk_main.columnconfigure([0, 1], weight=1, minsize=100, uniform="group1")

        # ap mode checkboxes block
        blk_modes = ttk.LabelFrame(blk_main, text=self.locale["gui.mode_label"], padding=(10, 5))
        blk_modes.grid(row=0, column=0, padx=2, pady=2, sticky="NSEW")
        self.makeform(blk_modes, FORM_TYPE_CHECKBOX, modes_check_fields)

        # ship values block
        blk_ship = ttk.LabelFrame(blk_main, text=self.locale["gui.settings.ship"], padding=(10, 5))
        blk_ship.grid(row=0, column=1, padx=2, pady=2, sticky="NSEW")
        self.entries['ship'] = self.makeform(blk_ship, FORM_TYPE_SPINBOX, ship_entry_fields, 1, 0.5)

        lbl_sun_pitch_up = ttk.Label(blk_ship, text=self.locale["gui.settings.sun_pitch_up_time_label"])
        lbl_sun_pitch_up.grid(row=6, column=0, pady=3, sticky=tk.W)
        spn_sun_pitch_up = ttk.Spinbox(blk_ship, width=10, from_=-100, to=100, increment=0.5, justify=tk.RIGHT)
        spn_sun_pitch_up.grid(row=6, column=1, padx=2, pady=2, sticky=tk.E)
        spn_sun_pitch_up.bind('<FocusOut>', self.entry_update)
        self.entries['ship'][self.locale['gui.ship.sun_pitch_up_time']] = spn_sun_pitch_up
        ToolTip(lbl_sun_pitch_up, msg=self.tooltips[self.locale['gui.ship.sun_pitch_up_time']], delay=1.0, bg="#808080", fg="#FFFFFF")

        lbl_calibrate_note = ttk.Label(blk_ship, text=self.locale["calibration.calibrate_roll_instructions"])
        lbl_calibrate_note.grid(row=7, columnspan=2, pady=5, sticky=tk.W)
        btn_tst_roll = ttk.Button(blk_ship, text=self.locale["calibration.calibrate_roll_rate"], command=self.ship_tst_roll)
        btn_tst_roll.grid(row=8, column=0, padx=2, pady=2, columnspan=2, sticky="NSEW")

        lbl_calibrate_note2 = ttk.Label(blk_ship, text=self.locale["calibration.calibrate_pitch_yaw_instructions"])
        lbl_calibrate_note2.grid(row=9, columnspan=2, pady=5, sticky=tk.W)
        btn_tst_pitch = ttk.Button(blk_ship, text=self.locale["calibration.calibrate_pitch_rate"], command=self.ship_tst_pitch)
        btn_tst_pitch.grid(row=10, column=0, padx=2, pady=2, columnspan=2, sticky="NSEW")
        btn_tst_yaw = ttk.Button(blk_ship, text=self.locale["calibration.calibrate_yaw_rate"], command=self.ship_tst_yaw)
        btn_tst_yaw.grid(row=11, column=0, padx=2, pady=2, columnspan=2, sticky="NSEW")

        # log window
        log = ttk.LabelFrame(page0, text=self.locale["gui.main.log"], padding=(10, 5))
        log.grid(row=2, column=0, padx=10, pady=5, sticky="NSEW")
        log.grid_columnconfigure(0, weight=1)
        log.grid_rowconfigure(0, weight=1)
        y_scrollbar = ttk.Scrollbar(log)
        y_scrollbar.grid(row=0, column=1, sticky="NSE")
        x_scrollbar = ttk.Scrollbar(log, orient="horizontal")
        x_scrollbar.grid(row=1, column=0, sticky="EW")
        mylist = tk.Listbox(log, width=100, yscrollcommand=y_scrollbar.set, xscrollcommand=x_scrollbar.set)
        mylist.grid(row=0, column=0, sticky="NSEW")
        y_scrollbar.config(command=mylist.yview)
        x_scrollbar.config(command=mylist.xview)

        # === SETTINGS TAB ===
        # settings block
        blk_settings = ttk.Frame(page1)
        blk_settings.grid(row=0, column=0, padx=10, pady=5, sticky="EW")
        blk_settings.columnconfigure([0, 1], weight=1, minsize=100, uniform="group1")
        # autopilot settings block
        blk_ap = ttk.LabelFrame(blk_settings, text=self.locale["gui.settings.autopilot"], padding=(10, 5))
        blk_ap.grid(row=0, column=0, padx=2, pady=2, sticky="NSEW")
        self.entries['autopilot'] = self.makeform(blk_ap, FORM_TYPE_SPINBOX, autopilot_entry_fields)
        self.checkboxvar['Enable Randomness'] = tk.BooleanVar()
        cb_random = ttk.Checkbutton(blk_ap, text=self.locale["gui.settings.enable_randomness"], variable=self.checkboxvar['Enable Randomness'], command=(lambda field='Enable Randomness': self.check_cb(field)))
        cb_random.grid(row=5, column=0, columnspan=2, sticky=tk.W)
        self.checkboxvar['Automatic logout'] = tk.BooleanVar()
        cb_logout = ttk.Checkbutton(blk_ap, text=self.locale["gui.settings.automatic_logout"], variable=self.checkboxvar['Automatic logout'], command=(lambda field='Automatic logout': self.check_cb(field)))
        cb_logout.grid(row=6, column=0, columnspan=2, sticky=tk.W)

        # Language settings block
        blk_language = ttk.LabelFrame(blk_settings, text=self.locale["gui.settings.language"], padding=(10, 5))
        blk_language.grid(row=7, column=0, columnspan=2, padx=2, pady=2, sticky="NSEW")

        ttk.Label(blk_language, text=self.locale["gui.settings.select_language"]).grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.language_var = tk.StringVar()
        self.language_combo = ttk.Combobox(blk_language, textvariable=self.language_var, values=self.locale.get_available_languages(), state="readonly")
        self.language_combo.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        self.language_combo.bind("<<ComboboxSelected>>", self.on_language_change)
        self.language_var.set(self.locale.language)
        cb_logout.grid(row=6, column=0, columnspan=2, sticky=tk.W)

        # buttons settings block
        blk_buttons = ttk.LabelFrame(blk_settings, text=self.locale["gui.settings.buttons"], padding=(10, 5))
        blk_buttons.grid(row=0, column=1, padx=2, pady=2, sticky="NSEW")
        blk_dss = ttk.Frame(blk_buttons)
        blk_dss.grid(row=0, column=0, columnspan=2, padx=0, pady=0, sticky="NSEW")
        lb_dss = ttk.Label(blk_dss, text=self.locale["settings.dss_button_label"])
        lb_dss.grid(row=0, column=0, sticky=tk.W)
        self.radiobuttonvar['dss_button'] = tk.StringVar()
        rb_dss_primary = ttk.Radiobutton(blk_dss, text=self.locale["settings.primary"], variable=self.radiobuttonvar['dss_button'], value="Primary", command=(lambda field='dss_button': self.check_cb(field)))
        rb_dss_primary.grid(row=0, column=1, sticky=tk.W)
        rb_dss_secandary = ttk.Radiobutton(blk_dss, text=self.locale["settings.secondary"], variable=self.radiobuttonvar['dss_button'], value="Secondary", command=(lambda field='dss_button': self.check_cb(field)))
        rb_dss_secandary.grid(row=1, column=1, sticky=tk.W)
        self.checkboxvar['Enable Hotkeys'] = tk.BooleanVar()
        cb_enable = ttk.Checkbutton(blk_buttons, text=self.locale["settings.enable_hotkeys_restart"], variable=self.checkboxvar['Enable Hotkeys'], command=(lambda field='Enable Hotkeys': self.check_cb(field)))
        cb_enable.grid(row=2, column=0, columnspan=2, sticky=tk.W)
        self.entries['buttons'] = self.makeform(blk_buttons, FORM_TYPE_ENTRY, buttons_entry_fields, 3)

        # refuel settings block
        blk_fuel = ttk.LabelFrame(blk_settings, text=self.locale["gui.settings.refuel"], padding=(10, 5))
        blk_fuel.grid(row=1, column=0, padx=2, pady=2, sticky="NSEW")
        self.entries['refuel'] = self.makeform(blk_fuel, FORM_TYPE_SPINBOX, refuel_entry_fields)

        # overlay settings block
        blk_overlay = ttk.LabelFrame(blk_settings, text=self.locale["gui.settings.overlay"], padding=(10, 5))
        blk_overlay.grid(row=1, column=1, padx=2, pady=2, sticky="NSEW")
        self.checkboxvar['Enable Overlay'] = tk.BooleanVar()
        self.checkboxvar['Enable Overlay'] = tk.BooleanVar()
        cb_enable = ttk.Checkbutton(blk_overlay, text=self.locale["settings.enable"], variable=self.checkboxvar['Enable Overlay'], command=(lambda field='Enable Overlay': self.check_cb(field)))
        cb_enable.grid(row=0, column=0, columnspan=2, sticky=tk.W)
        self.entries['overlay'] = self.makeform(blk_overlay, FORM_TYPE_SPINBOX, overlay_entry_fields, 1, 1.0, 0.0, 3000.0)

        # Keys settings block
        blk_keys = ttk.LabelFrame(blk_settings, text=self.locale["gui.settings.keys"], padding=(10, 5))
        blk_keys.grid(row=2, column=0, padx=2, pady=2, sticky="NSEW")
        self.checkboxvar['Activate Elite for each key'] = tk.BooleanVar()
        cb_activate_elite = ttk.Checkbutton(blk_keys, text=self.locale["settings.activate_elite_each_key"], variable=self.checkboxvar['Activate Elite for each key'], command=(lambda field='Activate Elite for each key': self.check_cb(field)))
        cb_activate_elite.grid(row=0, column=0, columnspan=2, sticky=tk.W)
        self.entries['keys'] = self.makeform(blk_keys, FORM_TYPE_SPINBOX, keys_entry_fields, 1, 0.01)

        # voice settings block
        blk_voice = ttk.LabelFrame(blk_settings, text=self.locale["gui.settings.voice"], padding=(10, 5))
        blk_voice.grid(row=3, column=0, padx=2, pady=2, sticky="NSEW")
        self.checkboxvar['Enable Voice'] = tk.BooleanVar()
        cb_enable = ttk.Checkbutton(blk_voice, text=self.locale["settings.enable"], variable=self.checkboxvar['Enable Voice'], command=(lambda field='Enable Voice': self.check_cb(field)))
        cb_enable.grid(row=0, column=0, columnspan=2, sticky=tk.W)

        # ELW Scanner settings block
        blk_voice = ttk.LabelFrame(blk_settings, text=self.locale["settings.elw_scanner"], padding=(10, 5))
        blk_voice.grid(row=3, column=1, padx=2, pady=2, sticky="NSEW")
        self.checkboxvar['ELW Scanner'] = tk.BooleanVar()
        cb_enable = ttk.Checkbutton(blk_voice, text=self.locale["settings.enable"], variable=self.checkboxvar['ELW Scanner'], command=(lambda field='ELW Scanner': self.check_cb(field)))
        cb_enable.grid(row=0, column=0, columnspan=2, sticky=tk.W)

        # AFK Combat settings block
        blk_afk_combat = ttk.LabelFrame(blk_settings, text=self.locale["settings.afk_combat"], padding=(10, 5))
        blk_afk_combat.grid(row=4, column=0, padx=2, pady=2, sticky="NSEW")
        self.checkboxvar['AFKCombat AttackAtWill'] = tk.BooleanVar()
        cb_enable = ttk.Checkbutton(blk_afk_combat, text=self.locale["settings.command_slf_attack_at_will"], variable=self.checkboxvar['AFKCombat AttackAtWill'], command=(lambda field='AFKCombat AttackAtWill': self.check_cb(field)))
        cb_enable.grid(row=0, column=0, columnspan=2, sticky=tk.W)
        # settings button block
        blk_settings_buttons = ttk.Frame(page1)
        blk_settings_buttons.grid(row=5, column=0, padx=10, pady=5, sticky="NSEW")
        blk_settings_buttons.columnconfigure([0, 1], weight=1, minsize=100)
        btn_save = ttk.Button(blk_settings_buttons, text=self.locale["messages.save_all_settings"], command=self.save_settings, style="Accent.TButton")
        btn_save.grid(row=0, column=0, padx=2, pady=2, columnspan=2, sticky="NSEW")

        # ==== DEBUG/TEST TAB ====
        # File Actions
        # File Actions
        blk_file_actions = ttk.LabelFrame(page2, text=self.locale["debug.file_actions"], padding=(10, 5))
        blk_file_actions.grid(row=0, column=0, padx=10, pady=5, sticky="NSEW")
        self.checkboxvar['Enable CV View'] = tk.IntVar()
        self.checkboxvar['Enable CV View'].set(int(self.ed_ap.config['Enable_CV_View']))
        cb_enable_cv_view = ttk.Checkbutton(blk_file_actions, text=self.locale["debug.enable_cv_view"], variable=self.checkboxvar['Enable CV View'], command=(lambda field='Enable CV View': self.check_cb(field)))
        cb_enable_cv_view.grid(row=2, column=0, padx=2, pady=2, sticky=tk.W)
        btn_restart = ttk.Button(blk_file_actions, text=self.locale["debug.restart"], command=self.restart_program)
        btn_restart.grid(row=3, column=0, padx=2, pady=2, sticky=tk.W)
        btn_exit = ttk.Button(blk_file_actions, text=self.locale["debug.exit"], command=self.close_window)
        btn_exit.grid(row=4, column=0, padx=2, pady=2, sticky=tk.W)

        # Help Actions
        blk_help_actions = ttk.LabelFrame(page2, text=self.locale["debug.help_actions"], padding=(10, 5))
        blk_help_actions.grid(row=0, column=1, padx=10, pady=5, sticky="NSEW")
        btn_check_updates = ttk.Button(blk_help_actions, text=self.locale["debug.check_for_updates"], command=self.check_updates)
        btn_check_updates.grid(row=0, column=0, padx=2, pady=2, sticky=tk.W)
        btn_view_changelog = ttk.Button(blk_help_actions, text=self.locale["debug.view_changelog"], command=self.open_changelog)
        btn_view_changelog.grid(row=1, column=0, padx=2, pady=2, sticky=tk.W)
        btn_join_discord = ttk.Button(blk_help_actions, text=self.locale["debug.join_discord"], command=self.open_discord)
        btn_join_discord.grid(row=2, column=0, padx=2, pady=2, sticky=tk.W)
        btn_about = ttk.Button(blk_help_actions, text=self.locale["debug.about"], command=self.about)
        btn_about.grid(row=3, column=0, padx=2, pady=2, sticky=tk.W)

        # # debug block
        # blk_debug = ttk.Frame(page2)
        # blk_debug.grid(row=1, column=0, padx=10, pady=5, sticky=(tk.E, tk.W))
        # blk_debug.columnconfigure([0, 1], weight=1, minsize=100, uniform="group2")

        # Debug Settings frame
        blk_debug_settings = ttk.LabelFrame(page2, text=self.locale["debug.debug_settings"], padding=(10, 5))
        blk_debug_settings.grid(row=1, column=0, padx=10, pady=5, sticky="NSEW")
        self.radiobuttonvar['debug_mode'] = tk.StringVar()
        rb_debug_debug = ttk.Radiobutton(blk_debug_settings, text=self.locale["debug.debug_info_errors"], variable=self.radiobuttonvar['debug_mode'], value="Debug", command=(lambda field='debug_mode': self.check_cb(field)))
        rb_debug_debug.grid(row=0, column=1, columnspan=2, sticky=tk.W)
        rb_debug_info = ttk.Radiobutton(blk_debug_settings, text=self.locale["debug.info_errors"], variable=self.radiobuttonvar['debug_mode'], value="Info", command=(lambda field='debug_mode': self.check_cb(field)))
        rb_debug_info.grid(row=1, column=1, columnspan=2, sticky=tk.W)
        rb_debug_error = ttk.Radiobutton(blk_debug_settings, text=self.locale["debug.errors_only_default"], variable=self.radiobuttonvar['debug_mode'], value="Error", command=(lambda field='debug_mode': self.check_cb(field)))
        rb_debug_error.grid(row=2, column=1, columnspan=2, sticky=tk.W)
        btn_open_logfile = ttk.Button(blk_debug_settings, text=self.locale["debug.open_log_file"], command=self.open_logfile)
        btn_open_logfile.grid(row=3, column=0, padx=2, pady=2, columnspan=2, sticky="NSEW")

        # Single Waypoint Assist frame
        blk_single_waypoint_asst = ttk.LabelFrame(page2, text=self.locale["debug.single_waypoint_assist"], padding=(10, 5))
        blk_single_waypoint_asst.grid(row=1, column=1, padx=10, pady=5, sticky="NSEW")
        blk_single_waypoint_asst.columnconfigure(0, weight=1, minsize=10)
        blk_single_waypoint_asst.columnconfigure(1, weight=3, minsize=10)

        lbl_system = ttk.Label(blk_single_waypoint_asst, text=self.locale["debug.system_label"])
        lbl_system.grid(row=0, column=0, padx=2, pady=2, columnspan=1, sticky="NSEW")
        txt_system = ttk.Entry(blk_single_waypoint_asst, textvariable=self.single_waypoint_system)
        txt_system.grid(row=0, column=1, padx=2, pady=2, columnspan=1, sticky="NSEW")
        lbl_station = ttk.Label(blk_single_waypoint_asst, text=self.locale["debug.station_label"])
        lbl_station.grid(row=1, column=0, padx=2, pady=2, columnspan=1, sticky="NSEW")
        txt_station = ttk.Entry(blk_single_waypoint_asst, textvariable=self.single_waypoint_station)
        txt_station.grid(row=1, column=1, padx=2, pady=2, columnspan=1, sticky="NSEW")
        self.checkboxvar['Single Waypoint Assist'] = tk.BooleanVar()
        cb_single_waypoint = ttk.Checkbutton(blk_single_waypoint_asst, text=self.locale["debug.single_waypoint_assist"], variable=self.checkboxvar['Single Waypoint Assist'], command=(lambda field='Single Waypoint Assist': self.check_cb(field)))
        cb_single_waypoint.grid(row=2, column=0, padx=2, pady=2, columnspan=2, sticky="NSEW")

        blk_debug_buttons = ttk.Frame(page2)
        blk_debug_buttons.grid(row=2, column=0, columnspan=2, padx=10, pady=5, sticky="NSEW")
        blk_debug_buttons.columnconfigure([0, 1], weight=1, minsize=100)

        self.checkboxvar['Debug Overlay'] = tk.BooleanVar()
        cb_debug_overlay = ttk.Checkbutton(blk_debug_buttons, text=self.locale["debug.debug_overlay"], variable=self.checkboxvar['Debug Overlay'], command=(lambda field='Debug Overlay': self.check_cb(field)))
        cb_debug_overlay.grid(row=6, column=0, padx=2, pady=2, columnspan=2, sticky="NSEW")
        tip = ToolTip(cb_debug_overlay, msg=self.tooltips['Debug Overlay'], delay=1.0, bg="#808080", fg="#FFFFFF")

        self.checkboxvar['Debug OCR'] = tk.BooleanVar()
        cb_debug_ocr = ttk.Checkbutton(blk_debug_buttons, text=self.locale["debug.debug_ocr_description"], variable=self.checkboxvar['Debug OCR'], command=(lambda field='Debug OCR': self.check_cb(field)))
        cb_debug_ocr.grid(row=7, column=0, padx=2, pady=2, columnspan=2, sticky="NSEW")
        tip = ToolTip(cb_debug_ocr, msg=self.tooltips['Debug OCR'], delay=1.0, bg="#808080", fg="#FFFFFF")

        self.checkboxvar['Debug Images'] = tk.BooleanVar()
        cb_debug_images = ttk.Checkbutton(blk_debug_buttons, text=self.locale["debug.debug_images_description"], variable=self.checkboxvar['Debug Images'], command=(lambda field='Debug Images': self.check_cb(field)))
        cb_debug_images.grid(row=8, column=0, padx=2, pady=2, columnspan=2, sticky="NSEW")
        tip = ToolTip(cb_debug_images, msg=self.tooltips['Debug Images'], delay=1.0, bg="#808080", fg="#FFFFFF")

        btn_save = ttk.Button(blk_debug_buttons, text=self.locale["debug.save_all_settings"], command=self.save_settings, style="Accent.TButton")
        btn_save.grid(row=9, column=0, padx=2, pady=2, columnspan=2, sticky="NSEW")

        blk_rpy = ttk.LabelFrame(page2, text=self.locale["debug.rpy_test"], padding=(10, 5))
        blk_rpy.grid(row=10, column=0, columnspan=2, padx=2, pady=2, sticky="NSEW")
        blk_rpy.columnconfigure([0, 1, 2], weight=1, minsize=100)

        btn_tst_roll_30 = ttk.Button(blk_rpy, text=self.locale["debug.test_roll_rate_30"], command=self.ship_tst_roll_30)
        btn_tst_roll_30.grid(row=1, column=0, padx=2, pady=2, columnspan=1, sticky="NSEW")
        btn_tst_pitch_30 = ttk.Button(blk_rpy, text=self.locale["debug.test_pitch_rate_30"], command=self.ship_tst_pitch_30)
        btn_tst_pitch_30.grid(row=1, column=1, padx=2, pady=2, columnspan=1, sticky="NSEW")
        btn_tst_yaw_30 = ttk.Button(blk_rpy, text=self.locale["debug.test_yaw_rate_30"], command=self.ship_tst_yaw_30)
        btn_tst_yaw_30.grid(row=1, column=2, padx=2, pady=2, columnspan=1, sticky="NSEW")

        btn_tst_roll_45 = ttk.Button(blk_rpy, text=self.locale["debug.test_roll_rate_45"], command=self.ship_tst_roll_45)
        btn_tst_roll_45.grid(row=2, column=0, padx=2, pady=2, columnspan=1, sticky="NSEW")
        btn_tst_pitch_45 = ttk.Button(blk_rpy, text=self.locale["debug.test_pitch_rate_45"], command=self.ship_tst_pitch_45)
        btn_tst_pitch_45.grid(row=2, column=1, padx=2, pady=2, columnspan=1, sticky="NSEW")
        btn_tst_yaw_45 = ttk.Button(blk_rpy, text=self.locale["debug.test_yaw_rate_45"], command=self.ship_tst_yaw_45)
        btn_tst_yaw_45.grid(row=2, column=2, padx=2, pady=2, columnspan=1, sticky="NSEW")

        btn_tst_roll_90 = ttk.Button(blk_rpy, text=self.locale["debug.test_roll_rate_90"], command=self.ship_tst_roll_90)
        btn_tst_roll_90.grid(row=3, column=0, padx=2, pady=2, columnspan=1, sticky="NSEW")
        btn_tst_pitch_90 = ttk.Button(blk_rpy, text=self.locale["debug.test_pitch_rate_90"], command=self.ship_tst_pitch_90)
        btn_tst_pitch_90.grid(row=3, column=1, padx=2, pady=2, columnspan=1, sticky="NSEW")
        btn_tst_yaw_90 = ttk.Button(blk_rpy, text=self.locale["debug.test_yaw_rate_90"], command=self.ship_tst_yaw_90)
        btn_tst_yaw_90.grid(row=3, column=2, padx=2, pady=2, columnspan=1, sticky="NSEW")
        # === Status Bar ===
        statusbar = ttk.Frame(win)
        statusbar.grid(row=4, column=0)
        self.status = ttk.Label(win, text=self.locale["gui.main.status"] + ": ", relief=tk.SUNKEN, anchor=tk.W, justify=tk.LEFT, width=29)
        self.jumpcount = ttk.Label(statusbar, text="<info> ", relief=tk.SUNKEN, anchor=tk.W, justify=tk.LEFT, width=40)
        self.status.pack(in_=statusbar, side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.jumpcount.pack(in_=statusbar, side=tk.RIGHT, fill=tk.Y, expand=False)

        return mylist

    # def calibrate_ocr_region(self):
    #     selected_region = self.calibration_region_var.get()
    #     self.calibrator.calibrate_ocr_region(self.ocr_calibration_data, selected_region)

    def load_ocr_calibration_data(self):
        self.ocr_calibration_data = {}
        calibration_file = 'configs/ocr_calibration.json'

        default_regions = {
            # "Screen_Regions.sun": {"rect": [0.30, 0.30, 0.70, 0.68]},
            # "Screen_Regions.disengage": {"rect": [0.42, 0.65, 0.60, 0.80]},
            # "Screen_Regions.sco": {"rect": [0.42, 0.65, 0.60, 0.80]},
            # "Screen_Regions.fss": {"rect": [0.5045, 0.7545, 0.532, 0.7955]},
            # "Screen_Regions.mission_dest": {"rect": [0.46, 0.38, 0.65, 0.86]},
            # "Screen_Regions.missions": {"rect": [0.50, 0.78, 0.65, 0.85]},
            "EDCodex.full_panel": {"rect": [0.0589, 0.0983, 0.9406, 0.8617], "text": "1. Open the Codex from right hand cockpit panel.\n2. Draw a rectangle from the top left corner of the codex 'book' to the end \nof the line above the exit button at the bottom right."},
            "EDInternalStatusPanel.panel_bounds1": {"rect": [0.1197, 0.2733, 0.6937, 0.7125], "text": "1. Open Internal Status Panel (right hand panel).\n2. Draw a rectangle from the top left corner of the nav panel to the bottom right corner."},
            "EDInternalStatusPanel.panel_bounds2": {"rect": [0.1541, 0.2408, 0.6781, 0.8], "text": "1. Open Internal Status Panel (right hand panel).\n2. Draw a rectangle from the bottom left corner of the nav panel to the top right corner."},
            # "EDInternalStatusPanel.tab_bar": {"rect": [0.35, 0.2, 0.85, 0.26]},
            # "EDInternalStatusPanel.inventory_list": {"rect": [0.2, 0.3, 0.8, 0.9]},
            # "EDInternalStatusPanel.size.inventory_item": {"width": 100, "height": 20},
            # "EDInternalStatusPanel.size.nav_pnl_tab": {"width": 100, "height": 20},
            "EDStationServicesInShip.station_services": {"rect": [0.0809, 0.1136, 0.9186, 0.8464], "text": "1. Open Station Service.\n2. Draw a rectangle from the top left of the left panel box to the bottom right of the right panel box."},
            "EDStationServicesInShip.commodities_market": {"rect": [0.0479, 0.0983, 0.9516, 0.8617], "text": "This is calculated automatically from the Codex screen values. Do not change."},
            # "EDStationServicesInShip.connected_to": {"rect": [0.0, 0.0, 0.0, 0.0], "text": "This is calculated automatically from the Codex screen values. Do not change."},
            # "EDStationServicesInShip.carrier_admin_header": {"rect": [0.4, 0.1, 0.6, 0.2]},
            # "EDStationServicesInShip.commodities_list": {"rect": [0.2, 0.2, 0.8, 0.9]},
            # "EDStationServicesInShip.commodity_quantity": {"rect": [0.4, 0.5, 0.6, 0.6]},
            # "EDStationServicesInShip.size.commodity_item": {"width": 100, "height": 15},
            # "EDStationServicesInShip.mission_board_header": {"rect": [0.4, 0.1, 0.6, 0.2]},
            # "EDStationServicesInShip.missions_list": {"rect": [0.06, 0.25, 0.48, 0.8]},
            # "EDStationServicesInShip.mission_loaded": {"rect": [0.06, 0.25, 0.48, 0.35]},
            # "EDStationServicesInShip.size.mission_item": {"width": 100, "height": 15},
            # "EDSystemMap.cartographics": {"rect": [0.0, 0.0, 0.25, 0.25]},
            "EDGalaxyMap.full_panel": {"rect": [0.0, 0.0, 0.0, 0.0], "text": "This is calculated automatically from the Codex screen values. Do not change."},
            "EDSystemMap.full_panel": {"rect": [0.0, 0.0, 0.0, 0.0], "text": "This is calculated automatically from the Codex screen values. Do not change."},
            "EDNavigationPanel.panel_bounds1": {"rect": [0.1197, 0.2733, 0.6937, 0.7125], "text": "1. Open Navigation Panel.\n2. Draw a rectangle from the top left corner of the nav panel to the bottom right corner."},
            "EDNavigationPanel.panel_bounds2": {"rect": [0.1541, 0.2408, 0.6781, 0.8], "text": "1. Open Navigation Panel.\n2. Draw a rectangle from the bottom left corner of the nav panel to the top right corner."},
            # "EDNavigationPanel.tab_bar": {"rect": [0.0, 0.2, 0.7, 0.35]},
            # "EDNavigationPanel.size.nav_pnl_tab": {"width": 260, "height": 35},
            # "EDNavigationPanel.size.nav_pnl_location": {"width": 500, "height": 35},
            # "EDNavigationPanel.deskew_angle": -1.0
        }

        if not os.path.exists(calibration_file):
            # Create the file with default values if it doesn't exist
            with open(calibration_file, 'w') as f:
                json.dump(default_regions, f, indent=4)
            self.ocr_calibration_data = default_regions
        else:
            with open(calibration_file, 'r') as f:
                self.ocr_calibration_data = json.load(f)

            # Check for missing keys and add them
            updated = False
            for key, value in default_regions.items():
                if key not in self.ocr_calibration_data:
                    self.ocr_calibration_data[key] = value
                    updated = True

            # If we updated the data, save it back to the file
            if updated:
                with open(calibration_file, 'w') as f:
                    json.dump(self.ocr_calibration_data, f, indent=4)

    def save_ocr_calibration_data(self):
        # q = Quad.from_rect(self.ocr_calibration_data['EDCodex.full_panel']['rect'])
        # fx = 0.95
        # fy = 0.96
        # q.scale(fx, fy)
        # self.ocr_calibration_data['EDStationServicesInShip.station_services']['rect'] = q.to_rect_list(round_dp=4)

        q = Quad.from_rect(self.ocr_calibration_data['EDCodex.full_panel']['rect'])
        q.scale(fx=1.025, fy=1.0)
        self.ocr_calibration_data['EDStationServicesInShip.commodities_market']['rect'] = q.to_rect_list(round_dp=4)

        q = Quad.from_rect(self.ocr_calibration_data['EDCodex.full_panel']['rect'])
        q.scale(fx=1.05, fy=1.08)
        self.ocr_calibration_data['EDSystemMap.full_panel']['rect'] = q.to_rect_list(round_dp=4)

        q = Quad.from_rect(self.ocr_calibration_data['EDCodex.full_panel']['rect'])
        q.scale(fx=1.05, fy=1.08)
        self.ocr_calibration_data['EDGalaxyMap.full_panel']['rect'] = q.to_rect_list(round_dp=4)

        # q = Quad.from_rect(self.ocr_calibration_data['EDStationServicesInShip.station_services']['rect'])
        # q.crop(0.0, 0.0, 0.25, 0.25)
        # self.ocr_calibration_data['EDStationServicesInShip.connected_to']['rect'] = q.to_rect_list(round_dp=4)

        calibration_file = 'configs/ocr_calibration.json'
        with open(calibration_file, 'w') as f:
            json.dump(self.ocr_calibration_data, f, indent=4)
        self.log_msg(self.locale["messages.ocr_calibration_data_saved"])
        # messagebox.showinfo("Saved", "OCR calibration data saved.\nPlease restart the application for changes to take effect.")

    def reset_all_calibrations(self):
        if messagebox.askyesno(self.locale["calibration.reset_all_calibrations"], self.locale["calibration.reset_confirmation"]):
            calibration_file = 'configs/ocr_calibration.json'
            if os.path.exists(calibration_file):
                os.remove(calibration_file)
                self.log_msg(self.locale["messages.removed_ocr_calibration"])

            # This will recreate the file with defaults
            self.load_ocr_calibration_data()

            # --- Repopulate UI ---
            # Clear current selections
            self.calibration_region_var.set('')
            # self.calibration_size_var.set('')
            self.calibration_rect_label_var.set('')
            # self.calibration_rect_left_var.set('')
            # self.calibration_size_label_var.set('')

            # Repopulate region dropdown
            region_keys = sorted([key for key in self.ocr_calibration_data.keys() if '.size.' not in key and 'compass' not in key and 'target' not in key])
            self.calibration_region_combo['values'] = region_keys

            # Repopulate size dropdown
            # size_keys = sorted([key for key in self.ocr_calibration_data.keys() if '.size.' in key])
            # self.calibration_size_combo['values'] = size_keys

            self.log_msg(self.locale["messages.all_calibrations_reset"])
            messagebox.showinfo("Reset Complete", self.locale["calibration.reset_complete_message"])

    def restart_program(self):
        logger.debug("Entered: restart_program")
        print("restart now")

        self.stop_fsd()
        self.stop_sc()
        self.ed_ap.quit()
        sleep(0.1)

        import sys
        print("argv was", sys.argv)
        print("sys.executable was", sys.executable)
        print("restart now")

        import os
        os.execv(sys.executable, ['python'] + sys.argv)


def apply_theme_to_titlebar(root):
    version = sys.getwindowsversion()

    if version.major == 10 and version.build >= 22000:
        # Set the title bar color to the background color on Windows 11 for better appearance
        pywinstyles.change_header_color(root, "#1c1c1c" if sv_ttk.get_theme() == "dark" else "#fafafa")
    elif version.major == 10:
        pywinstyles.apply_style(root, "dark" if sv_ttk.get_theme() == "dark" else "normal")

        # A hacky way to update the title bar's color on Windows 10 (it doesn't update instantly like on Windows 11)
        root.wm_attributes("-alpha", 0.99)
        root.wm_attributes("-alpha", 1)


def main():
    #   handle = win32gui.FindWindow(0, "Elite - Dangerous (CLIENT)")
    #   if handle != None:
    #       win32gui.SetForegroundWindow(handle)  # put the window in foreground

    root = tk.Tk()
    app = APGui(root)

    sv_ttk.set_theme("dark")

    # Remove focus outline from tabs by setting focuscolor to the background color
    style = ttk.Style()
    bg_color = "#1c1c1c" if sv_ttk.get_theme() == "dark" else "#fafafa"
    style.configure("TNotebook.Tab", focuscolor=bg_color)

    # if sys.platform == "win32":
    #     apply_theme_to_titlebar(root)

    root.mainloop()


if __name__ == "__main__":
    main()
