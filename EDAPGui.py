import queue
import sys
import os
import threading
import kthread
from datetime import datetime
from time import sleep
import cv2
import json
from pathlib import Path
import keyboard
import webbrowser
import requests


from PIL import Image, ImageGrab, ImageTk
import tkinter as tk
from tkinter import *
from tkinter import filedialog as fd
from tkinter import messagebox
from tkinter import ttk
from idlelib.tooltip import Hovertip
from simple_localization.localization import LocalizationManager

from Voice import *
from MousePt import MousePoint

from Image_Templates import *
from Screen import *
from Screen_Regions import *
from EDKeys import *
from EDJournal import *
from ED_AP import *

from EDlogger import logger


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
EDAP_VERSION = "V1.7.0"
# depending on how release versions are best marked you could also change it to the release tag, see function check_update.
# ---------------------------------------------------------------------------

FORM_TYPE_CHECKBOX = 0
FORM_TYPE_SPINBOX = 1
FORM_TYPE_ENTRY = 2

NUMERIC_FIELD_WIDTH = 8
NUMERIC_LABEL_PADX = (8, 4)
NUMERIC_ENTRY_PADX = (0, 8)


def hyperlink_callback(url):
    webbrowser.open_new(url)


class APGui():
    def __init__(self, root):
        self.root = root
        self.gui_loaded = False
        self.log_buffer = queue.Queue()

        root.protocol("WM_DELETE_WINDOW", self.close_window)
        root.geometry("1000x820")
        root.resizable(False, False)
        root.rowconfigure(0, weight=1)
        root.rowconfigure(1, weight=0)
        root.columnconfigure(0, weight=1)

        self.ed_ap = EDAutopilot(cb=self.callback)
        self.localization = LocalizationManager('locales', self.ed_ap.config.get('Language', 'en'))
        self.ed_ap.config['Language'] = self.localization.language

        self.localization_bindings = []
        self.tooltip_instances = {}
        self.current_status_text = ''
        self.current_wp_filename = None
        self.jumpcount_placeholder = True

        allowed_ui_languages = ('en', 'uk')
        available_allowed = [lang for lang in allowed_ui_languages if lang in self.localization.available_languages]
        self.language_options = available_allowed if available_allowed else [allowed_ui_languages[0]]
        if self.localization.language not in self.language_options:
            fallback = self.language_options[0]
            try:
                self.localization.change_language(fallback)
            except Exception:
                pass
            else:
                self.ed_ap.config['Language'] = fallback

        self.language_var = tk.StringVar(master=self.root, value=self.localization.language)

        root.title(self._t('ui.window.title', version=EDAP_VERSION))
        # root.overrideredirect(True)
        # root.geometry("400x550")
        # root.configure(bg="blue")

        self.field_text_keys = {
            'FSD Route Assist': 'ui.mode.fsd_route',
            'Supercruise Assist': 'ui.mode.supercruise',
            'Waypoint Assist': 'ui.mode.waypoint',
            'Robigo Assist': 'ui.mode.robigo',
            'AFK Combat Assist': 'ui.mode.afk_combat',
            'DSS Assist': 'ui.mode.dss',
            'RollRate': 'ui.field.ship.roll_rate',
            'PitchRate': 'ui.field.ship.pitch_rate',
            'YawRate': 'ui.field.ship.yaw_rate',
            'Sun Bright Threshold': 'ui.field.autopilot.sun_bright_threshold',
            'Nav Align Tries': 'ui.field.autopilot.nav_align_tries',
            'Jump Tries': 'ui.field.autopilot.jump_tries',
            'Docking Retries': 'ui.field.autopilot.docking_retries',
            'Wait For Autodock': 'ui.field.autopilot.wait_for_autodock',
            'Start FSD': 'ui.field.buttons.start_fsd',
            'Start SC': 'ui.field.buttons.start_sc',
            'Start Robigo': 'ui.field.buttons.start_robigo',
            'Stop All': 'ui.field.buttons.stop_all',
            'Refuel Threshold': 'ui.field.fuel.refuel_threshold',
            'Scoop Timeout': 'ui.field.fuel.scoop_timeout',
            'Fuel Threshold Abort': 'ui.field.fuel.fuel_threshold_abort',
            'X Offset': 'ui.field.overlay.x_offset',
            'Y Offset': 'ui.field.overlay.y_offset',
            'Font Size': 'ui.field.overlay.font_size',
            'SunPitchUp+Time': 'ui.field.ship.sun_pitch_time'
        }

        self.tooltip_keys = {
            'FSD Route Assist': 'ui.tooltip.mode.fsd_route',
            'Supercruise Assist': 'ui.tooltip.mode.supercruise',
            'Waypoint Assist': 'ui.tooltip.mode.waypoint',
            'Robigo Assist': 'ui.tooltip.mode.robigo',
            'DSS Assist': 'ui.tooltip.mode.dss',
            'Single Waypoint Assist': 'ui.tooltip.mode.single_waypoint',
            'ELW Scanner': 'ui.tooltip.mode.elw_scanner',
            'AFK Combat Assist': 'ui.tooltip.mode.afk_combat',
            'RollRate': 'ui.tooltip.ship.roll_rate',
            'PitchRate': 'ui.tooltip.ship.pitch_rate',
            'YawRate': 'ui.tooltip.ship.yaw_rate',
            'SunPitchUp+Time': 'ui.tooltip.ship.sun_pitch_time',
            'Sun Bright Threshold': 'ui.tooltip.autopilot.sun_bright_threshold',
            'Nav Align Tries': 'ui.tooltip.autopilot.nav_align_tries',
            'Jump Tries': 'ui.tooltip.autopilot.jump_tries',
            'Docking Retries': 'ui.tooltip.autopilot.docking_retries',
            'Wait For Autodock': 'ui.tooltip.autopilot.wait_for_autodock',
            'Start FSD': 'ui.tooltip.buttons.start_fsd',
            'Start SC': 'ui.tooltip.buttons.start_sc',
            'Start Robigo': 'ui.tooltip.buttons.start_robigo',
            'Stop All': 'ui.tooltip.buttons.stop_all',
            'Refuel Threshold': 'ui.tooltip.fuel.refuel_threshold',
            'Scoop Timeout': 'ui.tooltip.fuel.scoop_timeout',
            'Fuel Threshold Abort': 'ui.tooltip.fuel.fuel_threshold_abort',
            'X Offset': 'ui.tooltip.overlay.x_offset',
            'Y Offset': 'ui.tooltip.overlay.y_offset',
            'Font Size': 'ui.tooltip.overlay.font_size',
            'Calibrate': 'ui.tooltip.calibrate',
            'Waypoint List Button': 'ui.tooltip.waypoint.button',
            'Cap Mouse XY': 'ui.tooltip.waypoint.cap_mouse',
            'Reset Waypoint List': 'ui.tooltip.waypoint.reset'
        }

        self.callback('log', self._t('ui.log.starting', version=EDAP_VERSION))

        self.ed_ap.robigo.set_single_loop(self.ed_ap.config['Robigo_Single_Loop'])
        self.ed_ap.robigo.set_single_loop(self.ed_ap.config['Robigo_Single_Loop'])

        self.mouse = MousePoint()

        self.checkboxvar = {}
        self.radiobuttonvar = {}
        self.entries = {}
        self.lab_ck = {}
        self.single_waypoint_system = StringVar()
        self.single_waypoint_station = StringVar()
        self.TCE_Destination_Filepath = StringVar()

        self.FSD_A_running = False
        self.SC_A_running = False
        self.WP_A_running = False
        self.RO_A_running = False
        self.DSS_A_running = False
        self.SWP_A_running = False

        self.cv_view = False

        self.TCE_Destination_Filepath.set(self.ed_ap.config['TCEDestinationFilepath'])

        self.msgList = self.gui_gen(root)

        self.checkboxvar['Enable Randomness'].set(self.ed_ap.config['EnableRandomness'])
        self.checkboxvar['Activate Elite for each key'].set(self.ed_ap.config['ActivateEliteEachKey'])
        self.checkboxvar['Automatic logout'].set(self.ed_ap.config['AutomaticLogout'])
        self.checkboxvar['Enable Overlay'].set(self.ed_ap.config['OverlayTextEnable'])
        self.checkboxvar['Enable Voice'].set(self.ed_ap.config['VoiceEnable'])

        self.radiobuttonvar['dss_button'].set(self.ed_ap.config['DSSButton'])

        self.entries['ship']['PitchRate'].delete(0, END)
        self.entries['ship']['RollRate'].delete(0, END)
        self.entries['ship']['YawRate'].delete(0, END)
        self.entries['ship']['SunPitchUp+Time'].delete(0, END)

        self.entries['autopilot']['Sun Bright Threshold'].delete(0, END)
        self.entries['autopilot']['Nav Align Tries'].delete(0, END)
        self.entries['autopilot']['Jump Tries'].delete(0, END)
        self.entries['autopilot']['Docking Retries'].delete(0, END)
        self.entries['autopilot']['Wait For Autodock'].delete(0, END)

        self.entries['refuel']['Refuel Threshold'].delete(0, END)
        self.entries['refuel']['Scoop Timeout'].delete(0, END)
        self.entries['refuel']['Fuel Threshold Abort'].delete(0, END)

        self.entries['overlay']['X Offset'].delete(0, END)
        self.entries['overlay']['Y Offset'].delete(0, END)
        self.entries['overlay']['Font Size'].delete(0, END)

        self.entries['buttons']['Start FSD'].delete(0, END)
        self.entries['buttons']['Start SC'].delete(0, END)
        self.entries['buttons']['Start Robigo'].delete(0, END)
        self.entries['buttons']['Stop All'].delete(0, END)

        self.entries['ship']['PitchRate'].insert(0, float(self.ed_ap.pitchrate))
        self.entries['ship']['RollRate'].insert(0, float(self.ed_ap.rollrate))
        self.entries['ship']['YawRate'].insert(0, float(self.ed_ap.yawrate))
        self.entries['ship']['SunPitchUp+Time'].insert(0, float(self.ed_ap.sunpitchuptime))

        self.entries['autopilot']['Sun Bright Threshold'].insert(0, int(self.ed_ap.config['SunBrightThreshold']))
        self.entries['autopilot']['Nav Align Tries'].insert(0, int(self.ed_ap.config['NavAlignTries']))
        self.entries['autopilot']['Jump Tries'].insert(0, int(self.ed_ap.config['JumpTries']))
        self.entries['autopilot']['Docking Retries'].insert(0, int(self.ed_ap.config['DockingRetries']))
        self.entries['autopilot']['Wait For Autodock'].insert(0, int(self.ed_ap.config['WaitForAutoDockTimer']))
        self.entries['refuel']['Refuel Threshold'].insert(0, int(self.ed_ap.config['RefuelThreshold']))
        self.entries['refuel']['Scoop Timeout'].insert(0, int(self.ed_ap.config['FuelScoopTimeOut']))
        self.entries['refuel']['Fuel Threshold Abort'].insert(0, int(self.ed_ap.config['FuelThreasholdAbortAP']))
        self.entries['overlay']['X Offset'].insert(0, int(self.ed_ap.config['OverlayTextXOffset']))
        self.entries['overlay']['Y Offset'].insert(0, int(self.ed_ap.config['OverlayTextYOffset']))
        self.entries['overlay']['Font Size'].insert(0, int(self.ed_ap.config['OverlayTextFontSize']))

        self.entries['buttons']['Start FSD'].insert(0, str(self.ed_ap.config['HotKey_StartFSD']))
        self.entries['buttons']['Start SC'].insert(0, str(self.ed_ap.config['HotKey_StartSC']))
        self.entries['buttons']['Start Robigo'].insert(0, str(self.ed_ap.config['HotKey_StartRobigo']))
        self.entries['buttons']['Stop All'].insert(0, str(self.ed_ap.config['HotKey_StopAllAssists']))

        if self.ed_ap.config['LogDEBUG']:
            self.radiobuttonvar['debug_mode'].set("Debug")
        elif self.ed_ap.config['LogINFO']:
            self.radiobuttonvar['debug_mode'].set("Info")
        else:
            self.radiobuttonvar['debug_mode'].set("Error")

        self.checkboxvar['Debug Overlay'].set(self.ed_ap.config['DebugOverlay'])

        # global trap for these keys, the 'end' key will stop any current AP action
        # the 'home' key will start the FSD Assist.  May want another to start SC Assist

        keyboard.add_hotkey(self.ed_ap.config['HotKey_StopAllAssists'], self.stop_all_assists)
        keyboard.add_hotkey(self.ed_ap.config['HotKey_StartFSD'], self.callback, args=('fsd_start', None))
        keyboard.add_hotkey(self.ed_ap.config['HotKey_StartSC'],  self.callback, args=('sc_start',  None))
        keyboard.add_hotkey(self.ed_ap.config['HotKey_StartRobigo'],  self.callback, args=('robigo_start',  None))

        # check for updates
        self.check_updates()

        self.ed_ap.gui_loaded = True
        self.gui_loaded = True
        # Send a log entry which will flush out the buffer.
        self.callback('log', self._t('ui.log.loaded'))

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
        self.entries['ship']['PitchRate'].delete(0, END)
        self.entries['ship']['RollRate'].delete(0, END)
        self.entries['ship']['YawRate'].delete(0, END)
        self.entries['ship']['SunPitchUp+Time'].delete(0, END)

        self.entries['ship']['PitchRate'].insert(0, self.ed_ap.pitchrate)
        self.entries['ship']['RollRate'].insert(0, self.ed_ap.rollrate)
        self.entries['ship']['YawRate'].insert(0, self.ed_ap.yawrate)
        self.entries['ship']['SunPitchUp+Time'].insert(0, self.ed_ap.sunpitchuptime)

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

    # this routine is to stop any current autopilot activity
    def stop_all_assists(self):
        logger.debug("Entered: stop_all_assists")
        self.callback('stop_all_assists')

    def start_fsd(self):
        logger.debug("Entered: start_fsd")
        self.ed_ap.set_fsd_assist(True)
        self.FSD_A_running = True
        self.log_msg(self._t('ui.log.fsd_start'))
        self.ed_ap.vce.say(self._t('ui.voice.fsd_on'))

    def stop_fsd(self):
        logger.debug("Entered: stop_fsd")
        self.ed_ap.set_fsd_assist(False)
        self.FSD_A_running = False
        self.log_msg(self._t('ui.log.fsd_stop'))
        self.ed_ap.vce.say(self._t('ui.voice.fsd_off'))
        self.update_statusline(self._t('ui.status.idle'))

    def start_sc(self):
        logger.debug("Entered: start_sc")
        self.ed_ap.set_sc_assist(True)
        self.SC_A_running = True
        self.log_msg(self._t('ui.log.sc_start'))
        self.ed_ap.vce.say(self._t('ui.voice.sc_on'))

    def stop_sc(self):
        logger.debug("Entered: stop_sc")
        self.ed_ap.set_sc_assist(False)
        self.SC_A_running = False
        self.log_msg(self._t('ui.log.sc_stop'))
        self.ed_ap.vce.say(self._t('ui.voice.sc_off'))
        self.update_statusline(self._t('ui.status.idle'))

    def start_waypoint(self):
        logger.debug("Entered: start_waypoint")
        self.ed_ap.set_waypoint_assist(True)
        self.WP_A_running = True
        self.log_msg(self._t('ui.log.waypoint_start'))
        self.ed_ap.vce.say(self._t('ui.voice.waypoint_on'))

    def stop_waypoint(self):
        logger.debug("Entered: stop_waypoint")
        self.ed_ap.set_waypoint_assist(False)
        self.WP_A_running = False
        self.log_msg(self._t('ui.log.waypoint_stop'))
        self.ed_ap.vce.say(self._t('ui.voice.waypoint_off'))
        self.update_statusline(self._t('ui.status.idle'))

    def start_robigo(self):
        logger.debug("Entered: start_robigo")
        self.ed_ap.set_robigo_assist(True)
        self.RO_A_running = True
        self.log_msg(self._t('ui.log.robigo_start'))
        self.ed_ap.vce.say(self._t('ui.voice.robigo_on'))

    def stop_robigo(self):
        logger.debug("Entered: stop_robigo")
        self.ed_ap.set_robigo_assist(False)
        self.RO_A_running = False
        self.log_msg(self._t('ui.log.robigo_stop'))
        self.ed_ap.vce.say(self._t('ui.voice.robigo_off'))
        self.update_statusline(self._t('ui.status.idle'))

    def start_dss(self):
        logger.debug("Entered: start_dss")
        self.ed_ap.set_dss_assist(True)
        self.DSS_A_running = True
        self.log_msg(self._t('ui.log.dss_start'))
        self.ed_ap.vce.say(self._t('ui.voice.dss_on'))

    def stop_dss(self):
        logger.debug("Entered: stop_dss")
        self.ed_ap.set_dss_assist(False)
        self.DSS_A_running = False
        self.log_msg(self._t('ui.log.dss_stop'))
        self.ed_ap.vce.say(self._t('ui.voice.dss_off'))
        self.update_statusline(self._t('ui.status.idle'))

    def start_single_waypoint_assist(self):
        """ The debug command to go to a system or station or both."""
        logger.debug("Entered: start_single_waypoint_assist")
        system = self.single_waypoint_system.get()
        station = self.single_waypoint_station.get()

        if system != "" or station != "":
            self.ed_ap.set_single_waypoint_assist(system, station, True)
            self.SWP_A_running = True
            self.log_msg(self._t('ui.log.single_waypoint_start'))
            self.ed_ap.vce.say(self._t('ui.voice.single_waypoint_on'))

    def stop_single_waypoint_assist(self):
        """ The debug command to go to a system or station or both."""
        logger.debug("Entered: stop_single_waypoint_assist")
        self.ed_ap.set_single_waypoint_assist("", "", False)
        self.SWP_A_running = False
        self.log_msg(self._t('ui.log.single_waypoint_stop'))
        self.ed_ap.vce.say(self._t('ui.voice.single_waypoint_off'))
        self.update_statusline(self._t('ui.status.idle'))

    def about(self):
        webbrowser.open_new("https://github.com/SumZer0-git/EDAPGui")

    def check_updates(self):
        # response = requests.get("https://api.github.com/repos/SumZer0-git/EDAPGui/releases/latest")
        # if EDAP_VERSION != response.json()["name"]:
        #     mb = messagebox.askokcancel("Update Check", "A new release version is available. Download now?")
        #     if mb == True:
        #         webbrowser.open_new("https://github.com/SumZer0-git/EDAPGui/releases/latest")
        pass

    def open_changelog(self):
        webbrowser.open_new("https://github.com/SumZer0-git/EDAPGui/blob/main/ChangeLog.md")

    def open_discord(self):
        webbrowser.open_new("https://discord.gg/HCgkfSc")

    def open_logfile(self):
        os.startfile('autopilot.log')

    def log_msg(self, msg):
        message = datetime.now().strftime("%H:%M:%S: ") + msg

        if not self.gui_loaded:
            # Store message in queue
            self.log_buffer.put(message)
            logger.info(msg)
        else:
            # Add queued messages to the list
            while not self.log_buffer.empty():
                self.msgList.insert(END, self.log_buffer.get())

            self.msgList.insert(END, message)
            self.msgList.yview(END)
            logger.info(msg)

    def set_statusbar(self, txt):
        self.statusbar.configure(text=txt)

    def update_jumpcount(self, txt):
        self.jumpcount_placeholder = False
        self.jumpcount.configure(text=txt)

    def update_statusline(self, txt):
        self.current_status_text = txt
        self.status.configure(text=self._t('ui.status.label', status=txt))
        self.log_msg(self._t('ui.log.status_update', status=txt))

    def ship_tst_pitch(self):
        self.ed_ap.ship_tst_pitch()

    def ship_tst_roll(self):
        self.ed_ap.ship_tst_roll()

    def ship_tst_yaw(self):
        self.ed_ap.ship_tst_yaw()

    def open_wp_file(self):
        filetypes = (
            (self._t('ui.file_dialog.json_files'), '*.json'),
            (self._t('ui.file_dialog.all_files'), '*.*')
        )
        filename = fd.askopenfilename(title=self._t('ui.file_dialog.waypoint_title'), initialdir='./waypoints/', filetypes=filetypes)
        if filename != "":
            res = self.ed_ap.waypoint.load_waypoint_file(filename)
            if res:
                self.current_wp_filename = filename
            else:
                self.current_wp_filename = None
            self._refresh_waypoint_label()

    def reset_wp_file(self):
        if self.WP_A_running != True:
            mb = messagebox.askokcancel(self._t('ui.message.reset_waypoint_title'), self._t('ui.message.reset_waypoint_body'))
            if mb == True:
                self.ed_ap.waypoint.mark_all_waypoints_not_complete()
        else:
            mb = messagebox.showerror(self._t('ui.message.reset_waypoint_error_title'), self._t('ui.message.reset_waypoint_error_body'))

    def save_settings(self):
        self.entry_update()
        self.ed_ap.update_config()
        self.ed_ap.update_ship_configs()

    def load_tce_dest(self):
        filename = self.ed_ap.config['TCEDestinationFilepath']
        if os.path.exists(filename):
            with open(filename, 'r') as json_file:
                f_details = json.load(json_file)

            self.single_waypoint_system.set(f_details['StarSystem'])
            self.single_waypoint_station.set(f_details['Station'])

    # new data was added to a field, re-read them all for simple logic
    def entry_update(self, event=''):
        try:
            self.ed_ap.pitchrate = float(self.entries['ship']['PitchRate'].get())
            self.ed_ap.rollrate = float(self.entries['ship']['RollRate'].get())
            self.ed_ap.yawrate = float(self.entries['ship']['YawRate'].get())
            self.ed_ap.sunpitchuptime = float(self.entries['ship']['SunPitchUp+Time'].get())

            self.ed_ap.config['SunBrightThreshold'] = int(self.entries['autopilot']['Sun Bright Threshold'].get())
            self.ed_ap.config['NavAlignTries'] = int(self.entries['autopilot']['Nav Align Tries'].get())
            self.ed_ap.config['JumpTries'] = int(self.entries['autopilot']['Jump Tries'].get())
            self.ed_ap.config['DockingRetries'] = int(self.entries['autopilot']['Docking Retries'].get())
            self.ed_ap.config['WaitForAutoDockTimer'] = int(self.entries['autopilot']['Wait For Autodock'].get())
            self.ed_ap.config['RefuelThreshold'] = int(self.entries['refuel']['Refuel Threshold'].get())
            self.ed_ap.config['FuelScoopTimeOut'] = int(self.entries['refuel']['Scoop Timeout'].get())
            self.ed_ap.config['FuelThreasholdAbortAP'] = int(self.entries['refuel']['Fuel Threshold Abort'].get())
            self.ed_ap.config['OverlayTextXOffset'] = int(self.entries['overlay']['X Offset'].get())
            self.ed_ap.config['OverlayTextYOffset'] = int(self.entries['overlay']['Y Offset'].get())
            self.ed_ap.config['OverlayTextFontSize'] = int(self.entries['overlay']['Font Size'].get())
            self.ed_ap.config['HotKey_StartFSD'] = str(self.entries['buttons']['Start FSD'].get())
            self.ed_ap.config['HotKey_StartSC'] = str(self.entries['buttons']['Start SC'].get())
            self.ed_ap.config['HotKey_StartRobigo'] = str(self.entries['buttons']['Start Robigo'].get())
            self.ed_ap.config['HotKey_StopAllAssists'] = str(self.entries['buttons']['Stop All'].get())
            self.ed_ap.config['VoiceEnable'] = self.checkboxvar['Enable Voice'].get()
            self.ed_ap.config['TCEDestinationFilepath'] = str(self.TCE_Destination_Filepath.get())
            self.ed_ap.config['DebugOverlay'] = self.checkboxvar['Debug Overlay'].get()
        except:
            messagebox.showinfo("Exception", "Invalid float entered")

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
                self.log_msg("AFK Combat Assist start")
                self.lab_ck['FSD Route Assist'].config(state='disabled')
                self.lab_ck['Supercruise Assist'].config(state='disabled')
                self.lab_ck['Waypoint Assist'].config(state='disabled')
                self.lab_ck['Robigo Assist'].config(state='disabled')
                self.lab_ck['DSS Assist'].config(state='disabled')

            elif self.checkboxvar['AFK Combat Assist'].get() == 0:
                self.ed_ap.set_afk_combat_assist(False)
                self.log_msg("AFK Combat Assist stop")
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

    def makeform(
        self,
        win,
        ftype,
        fields,
        r=0,
        inc=1,
        rfrom=0,
        rto=1000,
        entry_width=None,
        grid_columns=False,
        label_padx=(0, 0),
        entry_padx=(0, 0),
        label_sticky='w',
        entry_sticky=(N, S, E, W)
    ):
        entries = {}

        for field in fields:
            if grid_columns:
                row_container = win
                current_row = r
                r += 1
            else:
                row_container = tk.Frame(win)
                row_container.grid(row=r, column=0, padx=2, pady=2, sticky=(N, S, E, W))
                row_container.columnconfigure(0, weight=1)
                row_container.columnconfigure(1, weight=1)
                current_row = 0
                r += 1

            display_text = self._get_field_label(field)
            if ftype == FORM_TYPE_CHECKBOX:
                self.checkboxvar[field] = IntVar()
                lab = Checkbutton(row_container, text=display_text, anchor='w', justify=LEFT, wraplength=260, variable=self.checkboxvar[field], command=(lambda field=field: self.check_cb(field)))
                self.lab_ck[field] = lab
                self._register_widget_text(lab, self.field_text_keys.get(field))
                if grid_columns:
                    lab.grid(row=current_row, column=0, columnspan=2, sticky='w', padx=label_padx, pady=2)
                else:
                    lab.grid(row=0, column=0, sticky='w')
            else:
                lab = tk.Label(row_container, anchor='w', pady=3, text=display_text + ": ")
                self._register_widget_text(lab, self.field_text_keys.get(field), formatter=lambda txt: f"{txt}: ")
                if ftype == FORM_TYPE_SPINBOX:
                    spinbox_kwargs = {}
                    if entry_width:
                        spinbox_kwargs['width'] = entry_width
                    ent = tk.Spinbox(row_container, from_=rfrom, to=rto, increment=inc, **spinbox_kwargs)
                else:
                    entry_kwargs = {}
                    if entry_width:
                        entry_kwargs['width'] = entry_width
                    ent = tk.Entry(row_container, **entry_kwargs)
                ent.bind('<FocusOut>', self.entry_update)
                ent.insert(0, "0")
                if grid_columns:
                    lab.grid(row=current_row, column=0, sticky=label_sticky, padx=label_padx, pady=2)
                    ent.grid(row=current_row, column=1, sticky=entry_sticky, padx=entry_padx, pady=2)
                else:
                    lab.grid(row=0, column=0, sticky='w')
                    ent.grid(row=0, column=1, sticky=(N, S, E, W))

            tip_text = self._get_tooltip_text(field)
            if tip_text:
                tip_target = lab if grid_columns else row_container
                tip = Hovertip(tip_target, tip_text, hover_delay=1000)
                self._register_tooltip(field, tip)

            if ftype != FORM_TYPE_CHECKBOX:
                entries[field] = ent

        return entries

    def _get_field_label(self, field):
        key = self.field_text_keys.get(field)
        if key:
            return self._t(key)
        return field

    def _get_tooltip_text(self, field):
        key = self.tooltip_keys.get(field)
        if key:
            return self._t(key)
        return ''

    def _t(self, key, **kwargs):
        text = self.localization[key]
        if kwargs:
            return text.format(**kwargs)
        return text

    def _register_localization(self, key, setter, kwargs=None):
        self.localization_bindings.append({'key': key, 'setter': setter, 'kwargs': kwargs})

    def _register_widget_text(self, widget, key, attribute='text', formatter=None, kwargs=None):
        if not key:
            return

        def setter(value, widget=widget, attribute=attribute, formatter=formatter):
            if formatter:
                value = formatter(value)
            widget.configure(**{attribute: value})

        self._register_localization(key, setter, kwargs)

    def _register_menu_entry(self, menu, key, index=None):
        if not key:
            return

        if index is None:
            index = menu.index('end')

        def setter(value, menu=menu, index=index):
            menu.entryconfig(index, label=value)

        self._register_localization(key, setter)

    def _register_tooltip(self, field, tooltip):
        if not field:
            return
        self.tooltip_instances.setdefault(field, []).append(tooltip)

    def _language_display_name(self, code):
        key = f'ui.language.name.{code}'
        try:
            return self._t(key)
        except KeyError:
            return code

    def _refresh_waypoint_label(self):
        if not hasattr(self, 'wp_filelabel'):
            return
        if self.current_wp_filename:
            text = self._t('ui.waypoint.loaded', filename=Path(self.current_wp_filename).name)
        else:
            text = self._t('ui.waypoint.no_list_loaded')
        self.wp_filelabel.set(text)

    def _update_tooltips(self):
        for field, tooltips in self.tooltip_instances.items():
            text = self._get_tooltip_text(field)
            for tip in tooltips:
                tip.text = text

    def refresh_ui_texts(self):
        self.root.title(self._t('ui.window.title', version=EDAP_VERSION))
        for binding in self.localization_bindings:
            kwargs = binding['kwargs']
            if callable(kwargs):
                kwargs_value = kwargs()
            else:
                kwargs_value = kwargs or {}
            binding['setter'](self._t(binding['key'], **kwargs_value))
        self._refresh_waypoint_label()
        if self.jumpcount_placeholder:
            self.jumpcount.configure(text=self._t('ui.status.jump_placeholder'))
        self._update_tooltips()

    def set_language(self, lang):
        if lang == self.localization.language:
            return
        try:
            self.localization.change_language(lang)
        except Exception:
            messagebox.showerror(
                self._t('ui.message.language_switch_error_title'),
                self._t('ui.message.language_switch_error_body', language=self._language_display_name(lang))
            )
            return
        self.language_var.set(lang)
        self.ed_ap.config['Language'] = lang
        self.refresh_ui_texts()
        self.log_msg(self._t('ui.log.language_switched', language=self._language_display_name(lang)))

    def gui_gen(self, win):

        modes_check_fields = ('FSD Route Assist', 'Supercruise Assist', 'Waypoint Assist', 'Robigo Assist', 'AFK Combat Assist', 'DSS Assist')
        ship_entry_fields = ('RollRate', 'PitchRate', 'YawRate')
        autopilot_entry_fields = ('Sun Bright Threshold', 'Nav Align Tries', 'Jump Tries', 'Docking Retries', 'Wait For Autodock')
        buttons_entry_fields = ('Start FSD', 'Start SC', 'Start Robigo', 'Stop All')
        refuel_entry_fields = ('Refuel Threshold', 'Scoop Timeout', 'Fuel Threshold Abort')
        overlay_entry_fields = ('X Offset', 'Y Offset', 'Font Size')

        #
        # Define all the menus
        #
        menubar = Menu(win, background='#ff8000', foreground='black', activebackground='white', activeforeground='black')
        file = Menu(menubar, tearoff=0)
        file.add_command(label=self._t('ui.menu.file.calibrate_target'), command=self.calibrate_callback)
        self._register_menu_entry(file, 'ui.menu.file.calibrate_target')
        file.add_command(label=self._t('ui.menu.file.calibrate_compass'), command=self.calibrate_compass_callback)
        self._register_menu_entry(file, 'ui.menu.file.calibrate_compass')
        self.checkboxvar['Enable CV View'] = IntVar()
        self.checkboxvar['Enable CV View'].set(int(self.ed_ap.config['Enable_CV_View']))  # set IntVar value to the one from config
        file.add_checkbutton(label=self._t('ui.menu.file.enable_cv_view'), onvalue=1, offvalue=0, variable=self.checkboxvar['Enable CV View'], command=(lambda field='Enable CV View': self.check_cb(field)))
        self._register_menu_entry(file, 'ui.menu.file.enable_cv_view')
        file.add_separator()
        file.add_command(label=self._t('ui.menu.file.restart'), command=self.restart_program)
        self._register_menu_entry(file, 'ui.menu.file.restart')
        file.add_command(label=self._t('ui.menu.file.exit'), command=self.close_window)  # win.quit)
        self._register_menu_entry(file, 'ui.menu.file.exit')
        menubar.add_cascade(label=self._t('ui.menu.file'), menu=file)
        self._register_menu_entry(menubar, 'ui.menu.file')

        help_menu = Menu(menubar, tearoff=0)
        help_menu.add_command(label=self._t('ui.menu.help.check_updates'), command=self.check_updates)
        self._register_menu_entry(help_menu, 'ui.menu.help.check_updates')
        help_menu.add_command(label=self._t('ui.menu.help.view_changelog'), command=self.open_changelog)
        self._register_menu_entry(help_menu, 'ui.menu.help.view_changelog')

        language_menu = Menu(help_menu, tearoff=0)
        for lang in self.language_options:
            name_key = f'ui.language.name.{lang}'
            language_menu.add_radiobutton(
                label=self._t(name_key),
                variable=self.language_var,
                value=lang,
                command=lambda code=lang: self.set_language(code)
            )
            self._register_menu_entry(language_menu, name_key)
        help_menu.add_cascade(label=self._t('ui.menu.help.language'), menu=language_menu)
        self._register_menu_entry(help_menu, 'ui.menu.help.language')

        help_menu.add_separator()
        help_menu.add_command(label=self._t('ui.menu.help.join_discord'), command=self.open_discord)
        self._register_menu_entry(help_menu, 'ui.menu.help.join_discord')
        help_menu.add_command(label=self._t('ui.menu.help.about'), command=self.about)
        self._register_menu_entry(help_menu, 'ui.menu.help.about')
        menubar.add_cascade(label=self._t('ui.menu.help'), menu=help_menu)
        self._register_menu_entry(menubar, 'ui.menu.help')

        win.config(menu=menubar)

        # notebook pages
        nb = ttk.Notebook(win)
        nb.grid(row=0, column=0, sticky=(N, S, E, W))
        page0 = Frame(nb)
        page1 = Frame(nb)
        page2 = Frame(nb)
        nb.add(page0, text=self._t('ui.notebook.main'))  # main page
        self._register_localization('ui.notebook.main', lambda text, nb=nb, tab=page0: nb.tab(tab, text=text))
        nb.add(page1, text=self._t('ui.notebook.settings'))  # options page
        self._register_localization('ui.notebook.settings', lambda text, nb=nb, tab=page1: nb.tab(tab, text=text))
        nb.add(page2, text=self._t('ui.notebook.debug'))  # debug/test page
        self._register_localization('ui.notebook.debug', lambda text, nb=nb, tab=page2: nb.tab(tab, text=text))

        page0.columnconfigure(0, weight=1)
        page0.rowconfigure(0, weight=1)
        page0.rowconfigure(1, weight=0)
        page0.rowconfigure(2, weight=1)
        page1.columnconfigure(0, weight=1)
        page1.rowconfigure(0, weight=1)
        page1.rowconfigure(1, weight=0)
        page2.columnconfigure(0, weight=1)
        page2.rowconfigure(0, weight=0)
        page2.rowconfigure(1, weight=1)
        page2.rowconfigure(2, weight=0)

        # main options block
        blk_main = tk.Frame(page0)
        blk_main.grid(row=0, column=0, padx=10, pady=5, sticky=(N, S, E, W))
        blk_main.columnconfigure([0, 1], weight=1, uniform="group1")
        blk_main.rowconfigure(0, weight=1)

        # ap mode checkboxes block
        blk_modes = LabelFrame(blk_main, text=self._t('ui.frame.mode'))
        self._register_widget_text(blk_modes, 'ui.frame.mode')
        blk_modes.grid(row=0, column=0, padx=2, pady=2, sticky=(N, S, E, W))
        blk_modes.columnconfigure(0, weight=1)
        self.makeform(blk_modes, FORM_TYPE_CHECKBOX, modes_check_fields)

        # ship values block
        blk_ship = LabelFrame(blk_main, text=self._t('ui.frame.ship'))
        self._register_widget_text(blk_ship, 'ui.frame.ship')
        blk_ship.grid(row=0, column=1, padx=2, pady=2, sticky=(N, S, E, W))
        blk_ship.columnconfigure(0, weight=1, uniform='ship_cols')
        blk_ship.columnconfigure(1, weight=1, uniform='ship_cols')
        self.entries['ship'] = self.makeform(
            blk_ship,
            FORM_TYPE_SPINBOX,
            ship_entry_fields,
            0,
            0.5,
            entry_width=NUMERIC_FIELD_WIDTH,
            grid_columns=True,
            label_padx=NUMERIC_LABEL_PADX,
            entry_padx=NUMERIC_ENTRY_PADX,
            label_sticky='e',
            entry_sticky='w'
        )

        lbl_sun_pitch_up = tk.Label(blk_ship, text=self._t('ui.label.sun_pitch_time'), anchor='e')
        self._register_widget_text(lbl_sun_pitch_up, 'ui.label.sun_pitch_time')
        lbl_sun_pitch_up.grid(row=3, column=0, padx=NUMERIC_LABEL_PADX, pady=2, sticky='e')
        spn_sun_pitch_up = tk.Spinbox(blk_ship, from_=-100, to=100, increment=0.5, width=NUMERIC_FIELD_WIDTH)
        spn_sun_pitch_up.grid(row=3, column=1, padx=NUMERIC_ENTRY_PADX, pady=2, sticky='w')
        spn_sun_pitch_up.bind('<FocusOut>', self.entry_update)
        self.entries['ship']['SunPitchUp+Time'] = spn_sun_pitch_up
        tip = Hovertip(lbl_sun_pitch_up, self._get_tooltip_text('SunPitchUp+Time'), hover_delay=1000)
        self._register_tooltip('SunPitchUp+Time', tip)

        btn_tst_roll = Button(blk_ship, text=self._t('ui.button.test_roll_rate'), command=self.ship_tst_roll)
        self._register_widget_text(btn_tst_roll, 'ui.button.test_roll_rate')
        btn_tst_roll.grid(row=4, column=0, padx=2, pady=2, columnspan=2, sticky=(N, E, W, S))
        btn_tst_pitch = Button(blk_ship, text=self._t('ui.button.test_pitch_rate'), command=self.ship_tst_pitch)
        self._register_widget_text(btn_tst_pitch, 'ui.button.test_pitch_rate')
        btn_tst_pitch.grid(row=5, column=0, padx=2, pady=2, columnspan=2, sticky=(N, E, W, S))
        btn_tst_yaw = Button(blk_ship, text=self._t('ui.button.test_yaw_rate'), command=self.ship_tst_yaw)
        self._register_widget_text(btn_tst_yaw, 'ui.button.test_yaw_rate')
        btn_tst_yaw.grid(row=6, column=0, padx=2, pady=2, columnspan=2, sticky=(N, E, W, S))

        # waypoints button block
        blk_wp_buttons = tk.LabelFrame(page0, text=self._t('ui.frame.waypoints'))
        self._register_widget_text(blk_wp_buttons, 'ui.frame.waypoints')
        blk_wp_buttons.grid(row=1, column=0, padx=10, pady=5, sticky=(N, S, E, W))
        blk_wp_buttons.columnconfigure([0, 1], weight=1, uniform="group1")

        self.wp_filelabel = tk.StringVar(master=self.root)
        self._refresh_waypoint_label()
        btn_wp_file = Button(blk_wp_buttons, textvariable=self.wp_filelabel, command=self.open_wp_file)
        btn_wp_file.grid(row=0, column=0, padx=2, pady=2, columnspan=2, sticky=(N, E, W, S))
        tip_wp_file = self._get_tooltip_text('Waypoint List Button')
        if tip_wp_file:
            tip = Hovertip(btn_wp_file, tip_wp_file, hover_delay=1000)
            self._register_tooltip('Waypoint List Button', tip)

        btn_reset = Button(blk_wp_buttons, text=self._t('ui.button.reset_list'), command=self.reset_wp_file)
        self._register_widget_text(btn_reset, 'ui.button.reset_list')
        btn_reset.grid(row=1, column=0, padx=2, pady=2, columnspan=2, sticky=(N, E, W, S))
        tip_reset = self._get_tooltip_text('Reset Waypoint List')
        if tip_reset:
            tip = Hovertip(btn_reset, tip_reset, hover_delay=1000)
            self._register_tooltip('Reset Waypoint List', tip)

        # log window
        log = LabelFrame(page0, text=self._t('ui.frame.log'))
        self._register_widget_text(log, 'ui.frame.log')
        log.grid(row=2, column=0, padx=12, pady=5, sticky=(N, S, E, W))
        log.columnconfigure(0, weight=1)
        log.rowconfigure(0, weight=1)
        scrollbar = Scrollbar(log)
        scrollbar.grid(row=0, column=1, sticky=(N, S))
        mylist = Listbox(log, height=10, yscrollcommand=scrollbar.set)
        mylist.grid(row=0, column=0, sticky=(N, S, E, W))
        scrollbar.config(command=mylist.yview)

        # settings block
        blk_settings = tk.Frame(page1)
        blk_settings.grid(row=0, column=0, padx=10, pady=5, sticky=(N, S, E, W))
        blk_settings.columnconfigure([0, 1], weight=1, uniform="group1")
        for idx in range(3):
            blk_settings.rowconfigure(idx, weight=1)

        # autopilot settings block
        blk_ap = LabelFrame(blk_settings, text=self._t('ui.frame.autopilot'))
        self._register_widget_text(blk_ap, 'ui.frame.autopilot')
        blk_ap.grid(row=0, column=0, padx=2, pady=2, sticky=(N, S, E, W))
        blk_ap.columnconfigure(0, weight=1, uniform='ap_cols')
        blk_ap.columnconfigure(1, weight=1, uniform='ap_cols')
        self.entries['autopilot'] = self.makeform(
            blk_ap,
            FORM_TYPE_SPINBOX,
            autopilot_entry_fields,
            entry_width=NUMERIC_FIELD_WIDTH,
            grid_columns=True,
            label_padx=NUMERIC_LABEL_PADX,
            entry_padx=NUMERIC_ENTRY_PADX,
            label_sticky='e',
            entry_sticky='w'
        )
        self.checkboxvar['Enable Randomness'] = BooleanVar()
        cb_random = Checkbutton(blk_ap, text=self._t('ui.checkbox.enable_randomness'), anchor='w', pady=3, justify=LEFT, wraplength=260, onvalue=1, offvalue=0, variable=self.checkboxvar['Enable Randomness'], command=(lambda field='Enable Randomness': self.check_cb(field)))
        self._register_widget_text(cb_random, 'ui.checkbox.enable_randomness')
        cb_random.grid(row=5, column=0, columnspan=2, sticky=(N, S, E, W))
        self.checkboxvar['Activate Elite for each key'] = BooleanVar()
        cb_activate_elite = Checkbutton(blk_ap, text=self._t('ui.checkbox.activate_elite_each_key'), anchor='w', pady=3, justify=LEFT, wraplength=260, onvalue=1, offvalue=0, variable=self.checkboxvar['Activate Elite for each key'], command=(lambda field='Activate Elite for each key': self.check_cb(field)))
        self._register_widget_text(cb_activate_elite, 'ui.checkbox.activate_elite_each_key')
        cb_activate_elite.grid(row=6, column=0, columnspan=2, sticky=(N, S, E, W))
        self.checkboxvar['Automatic logout'] = BooleanVar()
        cb_logout = Checkbutton(blk_ap, text=self._t('ui.checkbox.automatic_logout'), anchor='w', pady=3, justify=LEFT, wraplength=260, onvalue=1, offvalue=0, variable=self.checkboxvar['Automatic logout'], command=(lambda field='Automatic logout': self.check_cb(field)))
        self._register_widget_text(cb_logout, 'ui.checkbox.automatic_logout')
        cb_logout.grid(row=7, column=0, columnspan=2, sticky=(N, S, E, W))

        # buttons settings block
        blk_buttons = LabelFrame(blk_settings, text=self._t('ui.frame.buttons'))
        self._register_widget_text(blk_buttons, 'ui.frame.buttons')
        blk_buttons.grid(row=0, column=1, padx=2, pady=2, sticky=(N, S, E, W))
        blk_buttons.columnconfigure(0, weight=0, uniform='buttons_cols')
        blk_buttons.columnconfigure(1, weight=1, uniform='buttons_cols')

        lb_dss = Label(blk_buttons, anchor='e', pady=3, text=self._t('ui.label.dss_button'))
        self._register_widget_text(lb_dss, 'ui.label.dss_button')
        lb_dss.grid(row=0, column=0, sticky='e', padx=NUMERIC_LABEL_PADX, pady=2)

        blk_dss = Frame(blk_buttons)
        blk_dss.grid(row=0, column=1, sticky='w', padx=NUMERIC_ENTRY_PADX, pady=2)
        self.radiobuttonvar['dss_button'] = StringVar()
        rb_dss_primary = Radiobutton(
            blk_dss,
            pady=3,
            text=self._t('ui.radio.primary'),
            variable=self.radiobuttonvar['dss_button'],
            value="Primary",
            command=(lambda field='dss_button': self.check_cb(field))
        )
        self._register_widget_text(rb_dss_primary, 'ui.radio.primary')
        rb_dss_primary.grid(row=0, column=0, sticky='w')
        rb_dss_secandary = Radiobutton(
            blk_dss,
            pady=3,
            text=self._t('ui.radio.secondary'),
            variable=self.radiobuttonvar['dss_button'],
            value="Secondary",
            command=(lambda field='dss_button': self.check_cb(field))
        )
        self._register_widget_text(rb_dss_secandary, 'ui.radio.secondary')
        rb_dss_secandary.grid(row=1, column=0, sticky='w')

        self.entries['buttons'] = self.makeform(
            blk_buttons,
            FORM_TYPE_ENTRY,
            buttons_entry_fields,
            r=1,
            grid_columns=True,
            label_padx=NUMERIC_LABEL_PADX,
            entry_padx=NUMERIC_ENTRY_PADX,
            label_sticky='e',
            entry_sticky='w'
        )

        # refuel settings block
        blk_fuel = LabelFrame(blk_settings, text=self._t('ui.frame.fuel'))
        self._register_widget_text(blk_fuel, 'ui.frame.fuel')
        blk_fuel.grid(row=1, column=0, padx=2, pady=2, sticky=(N, S, E, W))
        blk_fuel.columnconfigure(0, weight=1, uniform='fuel_cols')
        blk_fuel.columnconfigure(1, weight=1, uniform='fuel_cols')
        self.entries['refuel'] = self.makeform(
            blk_fuel,
            FORM_TYPE_SPINBOX,
            refuel_entry_fields,
            entry_width=NUMERIC_FIELD_WIDTH,
            grid_columns=True,
            label_padx=NUMERIC_LABEL_PADX,
            entry_padx=NUMERIC_ENTRY_PADX,
            label_sticky='e',
            entry_sticky='w'
        )

        # overlay settings block
        blk_overlay = LabelFrame(blk_settings, text=self._t('ui.frame.overlay'))
        self._register_widget_text(blk_overlay, 'ui.frame.overlay')
        blk_overlay.grid(row=1, column=1, padx=2, pady=2, sticky=(N, S, E, W))
        blk_overlay.columnconfigure(0, weight=1, uniform='overlay_cols')
        blk_overlay.columnconfigure(1, weight=1, uniform='overlay_cols')
        self.checkboxvar['Enable Overlay'] = BooleanVar()
        cb_enable = Checkbutton(blk_overlay, text=self._t('ui.checkbox.enable_overlay_restart'), onvalue=1, offvalue=0, anchor='w', pady=3, justify=LEFT, wraplength=260, variable=self.checkboxvar['Enable Overlay'], command=(lambda field='Enable Overlay': self.check_cb(field)))
        self._register_widget_text(cb_enable, 'ui.checkbox.enable_overlay_restart')
        cb_enable.grid(row=0, column=0, columnspan=2, sticky=(N, S, E, W))
        self.entries['overlay'] = self.makeform(
            blk_overlay,
            FORM_TYPE_SPINBOX,
            overlay_entry_fields,
            1,
            1.0,
            0.0,
            3000.0,
            entry_width=NUMERIC_FIELD_WIDTH,
            grid_columns=True,
            label_padx=NUMERIC_LABEL_PADX,
            entry_padx=NUMERIC_ENTRY_PADX,
            label_sticky='e',
            entry_sticky='w'
        )

        # tts / voice settings block
        blk_voice = LabelFrame(blk_settings, text=self._t('ui.frame.voice'))
        self._register_widget_text(blk_voice, 'ui.frame.voice')
        blk_voice.grid(row=2, column=0, padx=2, pady=2, sticky=(N, S, E, W))
        blk_voice.columnconfigure(0, weight=1)
        self.checkboxvar['Enable Voice'] = BooleanVar()
        cb_enable = Checkbutton(blk_voice, text=self._t('ui.checkbox.enable'), onvalue=1, offvalue=0, anchor='w', pady=3, justify=LEFT, wraplength=260, variable=self.checkboxvar['Enable Voice'], command=(lambda field='Enable Voice': self.check_cb(field)))
        self._register_widget_text(cb_enable, 'ui.checkbox.enable')
        cb_enable.grid(row=0, column=0, columnspan=2, sticky=(N, S, E, W))

        # Scanner settings block
        blk_voice = LabelFrame(blk_settings, text=self._t('ui.frame.elw_scanner'))
        self._register_widget_text(blk_voice, 'ui.frame.elw_scanner')
        blk_voice.grid(row=2, column=1, padx=2, pady=2, sticky=(N, S, E, W))
        blk_voice.columnconfigure(0, weight=1)
        self.checkboxvar['ELW Scanner'] = BooleanVar()
        cb_enable = Checkbutton(blk_voice, text=self._t('ui.checkbox.enable'), onvalue=1, offvalue=0, anchor='w', pady=3, justify=LEFT, wraplength=260, variable=self.checkboxvar['ELW Scanner'], command=(lambda field='ELW Scanner': self.check_cb(field)))
        self._register_widget_text(cb_enable, 'ui.checkbox.enable')
        cb_enable.grid(row=0, column=0, columnspan=2, sticky=(N, S, E, W))

        # settings button block
        blk_settings_buttons = tk.Frame(page1)
        blk_settings_buttons.grid(row=1, column=0, padx=10, pady=5, sticky=(N, S, E, W))
        blk_settings_buttons.columnconfigure([0, 1], weight=1)
        btn_save = Button(blk_settings_buttons, text=self._t('ui.button.save_all'), command=self.save_settings)
        self._register_widget_text(btn_save, 'ui.button.save_all')
        btn_save.grid(row=0, column=0, padx=2, pady=2, columnspan=2, sticky=(N, E, W, S))

        # debug block
        blk_debug = tk.Frame(page2)
        blk_debug.grid(row=0, column=0, padx=10, pady=5, sticky=(N, S, E, W))
        blk_debug.columnconfigure([0, 1], weight=1, uniform="group2")

        # debug settings block
        blk_debug_settings = LabelFrame(blk_debug, text=self._t('ui.frame.debug'))
        self._register_widget_text(blk_debug_settings, 'ui.frame.debug')
        blk_debug_settings.grid(row=0, column=0, padx=2, pady=2, sticky=(N, S, E, W))
        blk_debug_settings.columnconfigure(0, weight=1)
        self.radiobuttonvar['debug_mode'] = StringVar()
        rb_debug_debug = Radiobutton(blk_debug_settings, pady=3, text=self._t('ui.radio.debug_all'), variable=self.radiobuttonvar['debug_mode'], value="Debug", command=(lambda field='debug_mode': self.check_cb(field)))
        self._register_widget_text(rb_debug_debug, 'ui.radio.debug_all')
        rb_debug_debug.grid(row=0, column=1, columnspan=2, sticky=(W))
        rb_debug_info = Radiobutton(blk_debug_settings, pady=3, text=self._t('ui.radio.debug_info'), variable=self.radiobuttonvar['debug_mode'], value="Info", command=(lambda field='debug_mode': self.check_cb(field)))
        self._register_widget_text(rb_debug_info, 'ui.radio.debug_info')
        rb_debug_info.grid(row=1, column=1, columnspan=2, sticky=(W))
        rb_debug_error = Radiobutton(blk_debug_settings, pady=3, text=self._t('ui.radio.debug_error'), variable=self.radiobuttonvar['debug_mode'], value="Error", command=(lambda field='debug_mode': self.check_cb(field)))
        self._register_widget_text(rb_debug_error, 'ui.radio.debug_error')
        rb_debug_error.grid(row=2, column=1, columnspan=2, sticky=(W))
        btn_open_logfile = Button(blk_debug_settings, text=self._t('ui.button.open_log_file'), command=self.open_logfile)
        self._register_widget_text(btn_open_logfile, 'ui.button.open_log_file')
        btn_open_logfile.grid(row=3, column=0, padx=2, pady=2, columnspan=2, sticky=(N, E, W, S))

        # debug settings block
        blk_single_waypoint_asst = LabelFrame(page2, text=self._t('ui.frame.single_waypoint'))
        self._register_widget_text(blk_single_waypoint_asst, 'ui.frame.single_waypoint')
        blk_single_waypoint_asst.grid(row=1, column=0, padx=10, pady=5, sticky=(N, S, E, W))
        blk_single_waypoint_asst.columnconfigure(0, weight=1, minsize=10, uniform="group1")
        blk_single_waypoint_asst.columnconfigure(1, weight=3, minsize=10, uniform="group1")

        lbl_system = tk.Label(blk_single_waypoint_asst, text=self._t('ui.label.system'))
        self._register_widget_text(lbl_system, 'ui.label.system')
        lbl_system.grid(row=0, column=0, padx=2, pady=2, columnspan=1, sticky=(N, E, W, S))
        txt_system = Entry(blk_single_waypoint_asst, textvariable=self.single_waypoint_system)
        txt_system.grid(row=0, column=1, padx=2, pady=2, columnspan=1, sticky=(N, E, W, S))
        lbl_station = tk.Label(blk_single_waypoint_asst, text=self._t('ui.label.station'))
        self._register_widget_text(lbl_station, 'ui.label.station')
        lbl_station.grid(row=1, column=0, padx=2, pady=2, columnspan=1, sticky=(N, E, W, S))
        txt_station = Entry(blk_single_waypoint_asst, textvariable=self.single_waypoint_station)
        txt_station.grid(row=1, column=1, padx=2, pady=2, columnspan=1, sticky=(N, E, W, S))
        self.checkboxvar['Single Waypoint Assist'] = BooleanVar()
        cb_single_waypoint = Checkbutton(blk_single_waypoint_asst, text=self._t('ui.checkbox.single_waypoint'), onvalue=1, offvalue=0, anchor='w', pady=3, justify=LEFT, wraplength=260, variable=self.checkboxvar['Single Waypoint Assist'], command=(lambda field='Single Waypoint Assist': self.check_cb(field)))
        self._register_widget_text(cb_single_waypoint, 'ui.checkbox.single_waypoint')
        cb_single_waypoint.grid(row=2, column=0, padx=2, pady=2, columnspan=2, sticky=(N, E, W, S))

        lbl_tce = tk.Label(blk_single_waypoint_asst, text=self._t('ui.label.tce'), fg="blue", cursor="hand2")
        self._register_widget_text(lbl_tce, 'ui.label.tce')
        lbl_tce.bind("<Button-1>", lambda e: hyperlink_callback("https://forums.frontier.co.uk/threads/trade-computer-extension-mk-ii.223056/"))
        lbl_tce.grid(row=3, column=0, padx=2, pady=2, columnspan=2, sticky=(N, E, W, S))
        lbl_tce_dest = tk.Label(blk_single_waypoint_asst, text=self._t('ui.label.tce_dest'))
        self._register_widget_text(lbl_tce_dest, 'ui.label.tce_dest')
        lbl_tce_dest.grid(row=4, column=0, padx=2, pady=2, columnspan=1, sticky=(N, E, W, S))
        txt_tce_dest = Entry(blk_single_waypoint_asst, textvariable=self.TCE_Destination_Filepath)
        txt_tce_dest.bind('<FocusOut>', self.entry_update)
        txt_tce_dest.grid(row=4, column=1, padx=2, pady=2, columnspan=1, sticky=(N, E, W, S))

        btn_load_tce = Button(blk_single_waypoint_asst, text=self._t('ui.button.load_tce_destination'), command=self.load_tce_dest)
        self._register_widget_text(btn_load_tce, 'ui.button.load_tce_destination')
        btn_load_tce.grid(row=5, column=0, padx=2, pady=2, columnspan=2, sticky=(N, E, W, S))

        blk_debug_buttons = tk.Frame(page2)
        blk_debug_buttons.grid(row=2, column=0, padx=10, pady=5, sticky=(N, S, E, W))
        blk_debug_buttons.columnconfigure([0, 1], weight=1)

        self.checkboxvar['Debug Overlay'] = BooleanVar()
        cb_debug_overlay = Checkbutton(blk_debug_buttons, text=self._t('ui.checkbox.debug_overlay'), onvalue=1, offvalue=0, anchor='w', pady=3, justify=LEFT, wraplength=260, variable=self.checkboxvar['Debug Overlay'], command=(lambda field='Debug Overlay': self.check_cb(field)))
        self._register_widget_text(cb_debug_overlay, 'ui.checkbox.debug_overlay')
        cb_debug_overlay.grid(row=6, column=0, padx=2, pady=2, columnspan=2, sticky=(N, E, W, S))

        btn_save = Button(blk_debug_buttons, text=self._t('ui.button.save_all'), command=self.save_settings)
        self._register_widget_text(btn_save, 'ui.button.save_all')
        btn_save.grid(row=7, column=0, padx=2, pady=2, columnspan=2, sticky=(N, E, W, S))

        # Statusbar
        statusbar = Frame(win)
        statusbar.grid(row=1, column=0, sticky=(E, W))
        statusbar.columnconfigure(0, weight=1)
        self.status = tk.Label(statusbar, text=self._t('ui.status.label', status=''), bd=1, relief=tk.SUNKEN, anchor=tk.W, justify=LEFT)
        self._register_widget_text(self.status, 'ui.status.label', kwargs=lambda: {'status': self.current_status_text})
        self.jumpcount = tk.Label(statusbar, text=self._t('ui.status.jump_placeholder'), bd=1, relief=tk.SUNKEN, anchor=tk.W, justify=LEFT)
        self.status.pack(in_=statusbar, side=LEFT, fill=BOTH, expand=True)
        self.jumpcount.pack(in_=statusbar, side=RIGHT, fill=Y, expand=False)

        return mylist

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

def main():
    #   handle = win32gui.FindWindow(0, "Elite - Dangerous (CLIENT)")
    #   if handle != None:
    #       win32gui.SetForegroundWindow(handle)  # put the window in foreground

    root = tk.Tk()
    app = APGui(root)

    root.mainloop()


if __name__ == "__main__":
    main()
