from __future__ import annotations

import logging
from time import sleep

from EDAP_data import GuiFocusExternalPanel
from EDKeys import EDKeys
from EDlogger import logger
from OCR import OCR, normalize_ocr_text
from Screen import Screen
from Screen_Regions import size_scale_for_station
from StatusParser import StatusParser

"""
File:navPanel.py    

Description:
  TBD 

Author: Stumpii
"""


class EDNavigationPanel:
    """ The Navigation (Left hand) Ship Status Panel. """
    def __init__(self, ed_ap, screen, keys, cb):
        self.ap = ed_ap
        self.ocr = ed_ap.ocr
        self.screen = screen
        self.keys = keys
        self.ap_ckb = cb
        self.ocr_tokens = self.ap.ocr_tokens
        self.status_parser = StatusParser()
        self.ocr_language = self.ap.config.get('OCRLanguage', 'en')
        self._load_tab_texts()
        self.nav_pnl_coords = None  # [top left, top right, bottom left, bottom right]

        # The rect is [L, T, R, B], top left x, y, and bottom right x, y in fraction of screen resolution
        # Nav Panel region covers the entire navigation panel.
        self.reg = {'nav_panel': {'rect': [0.11, 0.21, 0.70, 0.86]},
                    'temp_tab_bar': {'rect': [0.0, 0.2, 0.7, 0.35]}}
        self.sub_reg = {'tab_bar': {'rect': [0.0, 0.0, 1.0, 0.08]},
                        'location_panel': {'rect': [0.2218, 0.3, 0.8, 1.0]}}

        self.nav_pnl_tab_width = 260  # Nav panel tab width in pixels at 1920x1080
        self.nav_pnl_tab_height = 35  # Nav panel tab height in pixels at 1920x1080
        self.nav_pnl_location_width = 500  # Nav panel location width in pixels at 1920x1080
        self.nav_pnl_location_height = 35  # Nav panel location height in pixels at 1920x1080

    def _load_tab_texts(self):
        self.navigation_tab_text = self.ocr_tokens["ocr.nav_panel.tab.navigation"]
        self.transactions_tab_text = self.ocr_tokens["ocr.nav_panel.tab.transactions"]
        self.contacts_tab_text = self.ocr_tokens["ocr.nav_panel.tab.contacts"]
        self.target_tab_text = self.ocr_tokens["ocr.nav_panel.tab.target"]
        self._normalized_tabs = {
            'navigation': normalize_ocr_text(self.navigation_tab_text, self.ocr_language),
            'transactions': normalize_ocr_text(self.transactions_tab_text, self.ocr_language),
            'contacts': normalize_ocr_text(self.contacts_tab_text, self.ocr_language),
            'target': normalize_ocr_text(self.target_tab_text, self.ocr_language),
        }

    def update_ocr_language(self):
        self.ocr_language = self.ap.config.get('OCRLanguage', 'en')
        self.ocr_tokens = self.ap.ocr_tokens
        self._load_tab_texts()

    def request_docking_ocr(self) -> bool:
        """ Try to request docking with OCR.
        """
        # res = self.show_contacts_tab()
        # if res is None:
        #     return None
        # if not res:
        #     print("Contacts Panel could not be opened")
        #     return False
        #
        # # On the CONTACT TAB, go to top selection, do this 4 seconds to ensure at top
        # # then go right, which will be "REQUEST DOCKING" and select it
        # self.keys.send("UI_Down")  # go down
        # self.keys.send('UI_Up', hold=2)  # got to top row
        # self.keys.send('UI_Right')
        # self.keys.send('UI_Select')
        # sleep(0.3)
        #
        # self.hide_nav_panel()
        # return True
        pass

    def request_docking(self):
        """ Request docking from Nav Panel. """
        self.keys.send('UI_Back', repeat=10)
        self.keys.send('HeadLookReset')
        self.keys.send('UIFocus', state=1)
        self.keys.send('UI_Left')
        self.keys.send('UIFocus', state=0)
        sleep(0.5)

        # Draw box around region
        abs_rect = self.screen.screen_rect_to_abs(self.reg['temp_tab_bar']['rect'])
        if self.ap.debug_overlay:
            self.ap.overlay.overlay_rect1('nav_panel_active', abs_rect, (0, 255, 0), 2)
            self.ap.overlay.overlay_paint()

        tab_text = ""

        # Take screenshot of the panel
        image = self.ocr.capture_region_pct(self.reg['temp_tab_bar'])

        # Determine the nav panel tab size at this resolution
        scl_row_w, scl_row_h = size_scale_for_station(self.nav_pnl_tab_width, self.nav_pnl_tab_height,
                                                      self.screen.screen_width, self.screen.screen_height)

        img_selected, ocr_data, ocr_textlist = self.ocr.get_highlighted_item_data(image, scl_row_w, scl_row_h)
        if img_selected is not None:
            logger.debug("is_nav_panel_active: image selected")
            logger.debug(f"is_nav_panel_active: OCR: {ocr_textlist}")

            # Overlay OCR result
            if self.ap.debug_overlay:
                self.ap.overlay.overlay_floating_text('nav_panel_text', f'{ocr_textlist}', abs_rect[0], abs_rect[1] - 25, (0, 255, 0))
                self.ap.overlay.overlay_paint()

            normalized_tab_text = normalize_ocr_text(' '.join(ocr_textlist) if ocr_textlist else '', self.ocr_language)
            logger.debug(f"Nav panel tab normalized='{normalized_tab_text}'")

            # Test OCR string
            if self._normalized_tabs['navigation'] and self._normalized_tabs['navigation'] in normalized_tab_text:
                tab_text = self.navigation_tab_text
            if self._normalized_tabs['transactions'] and self._normalized_tabs['transactions'] in normalized_tab_text:
                tab_text = self.transactions_tab_text
            if self._normalized_tabs['contacts'] and self._normalized_tabs['contacts'] in normalized_tab_text:
                tab_text = self.contacts_tab_text
            if self._normalized_tabs['target'] and self._normalized_tabs['target'] in normalized_tab_text:
                tab_text = self.target_tab_text
        else:
            logger.debug("is_right_panel_active: no image selected")

        if tab_text == "":
            # we start with the Left Panel having "NAVIGATION" highlighted, we then need to right
            # twice to "CONTACTS".  Notice of a FSD run, the LEFT panel is reset to "NAVIGATION"
            # otherwise it is on the last tab you selected. Thus must start AP with "NAVIGATION" selected
            self.keys.send('CycleNextPanel', hold=0.2)
            sleep(0.2)
            self.keys.send('CycleNextPanel', hold=0.2)
        elif tab_text is self.navigation_tab_text:
            self.keys.send('CycleNextPanel', repeat=2)
        elif tab_text is self.transactions_tab_text:
            self.keys.send('CycleNextPanel', repeat=1)
        elif tab_text is self.contacts_tab_text:
            pass
        elif tab_text is self.target_tab_text:
            self.keys.send('CycleNextPanel', repeat=4)

        # On the CONTACT TAB, go to top selection, do this 4 seconds to ensure at top
        # then go right, which will be "REQUEST DOCKING" and select it
        self.keys.send('UI_Up', hold=4)
        self.keys.send('UI_Right')
        self.keys.send('UI_Select')

        sleep(0.5)
        # Go back to NAVIGATION tab
        self.keys.send('CycleNextPanel', hold=0.2)  # STATS tab
        sleep(0.2)
        self.keys.send('CycleNextPanel', hold=0.2)  # NAVIGATION tab

        # Clean up screen
        if self.ap.debug_overlay:
            sleep(2)
            self.ap.overlay.overlay_remove_rect('nav_panel_active')
            self.ap.overlay.overlay_remove_floating_text('nav_panel_text')
            self.ap.overlay.overlay_paint()

        sleep(0.3)
        self.keys.send('UI_Back')
        self.keys.send('HeadLookReset')

    def hide_nav_panel(self):
        """ Hides the Nav Panel if open.
        """
        # Is nav panel active?
        if self.status_parser.get_gui_focus() == GuiFocusExternalPanel:
            self.ap.ship_control.goto_cockpit_view()


def dummy_cb(msg, body=None):
    pass


# Usage Example
if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)  # Default to log all debug when running this file.
    from ED_AP import EDAutopilot
    ap = EDAutopilot(cb=dummy_cb)
    ap.keys.activate_window = True  # Helps with single steps testing

    from Screen import set_focus_elite_window
    set_focus_elite_window()
    nav_pnl = EDNavigationPanel(ap, ap.scr, ap.keys, dummy_cb)
    nav_pnl.request_docking()
