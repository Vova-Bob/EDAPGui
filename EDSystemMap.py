from __future__ import annotations

from EDAP_data import GuiFocusSystemMap
from EDlogger import logger
from OCR import OCR
from Screen_Regions import reg_scale_for_station
from StatusParser import StatusParser
from time import sleep


class EDSystemMap:
    """ Handles the System Map. """
    def __init__(self, ed_ap, screen, keys, cb, is_odyssey=True):
        self.ap = ed_ap
        self.ocr = ed_ap.ocr
        self.is_odyssey = is_odyssey
        self.screen = screen
        self.keys = keys
        self.status_parser = StatusParser()
        self.ap_ckb = cb
        # The rect is top left x, y, and bottom right x, y in fraction of screen resolution
        self.reg = {
            'cartographics': {'rect': [0.0, 0.0, 0.25, 0.25]},
        }

    def set_sys_map_dest_bookmark(self, ap, bookmark_type: str, bookmark_position: int) -> bool:
        """ Set the System Map destination using a bookmark.
        @param ap: ED_AP reference.
        @param bookmark_type: The bookmark type (Favorite, Body, Station, Settlement or Navigation), Favorite
         being the default if no match is made with the other options. Navigation is unique in that it uses
         the Nav Panel instead of the System Map.
        @param bookmark_position: The position in the bookmark list, starting at 1 for the first bookmark.
        @return: True if bookmark could be selected, else False
        """
        if self.is_odyssey and bookmark_position != -1:
            # Check if this is a nav-panel bookmark
            bt_lower = bookmark_type.lower()
            if not bt_lower.startswith("nav"):
                # ---------- System map bookmarks (Bodies / Stations / Settlements) ----------
                self.goto_system_map()

                # Go to BOOKMARKS
                ap.keys.send('UI_Left')
                sleep(0.5)
                ap.keys.send('UI_Select')  # Select BOOKMARKS
                sleep(0.25)
                ap.keys.send('UI_Right')  # Go to FAVORITES / LOCAL BOOKMARKS
                sleep(0.25)

                # If bookmark type is Fav, do nothing as this is the first item
                if bt_lower.startswith("bod"):
                    ap.keys.send('UI_Down', repeat=1)  # Go to BODIES
                elif bt_lower.startswith("sta"):
                    ap.keys.send('UI_Down', repeat=2)  # Go to STATIONS
                elif bt_lower.startswith("set"):
                    ap.keys.send('UI_Down', repeat=3)  # Go to SETTLEMENTS

                sleep(0.25)

                # Enter the bookmark list (focus moves to the first entry)
                ap.keys.send('UI_Select')
                sleep(0.25)

                # Move to the requested bookmark entry (first item already selected)
                if bookmark_position > 1:
                    ap.keys.send('UI_Down', repeat=bookmark_position - 1)
                    sleep(0.25)

                # Manual plotting sequence:
                # 1) Move left to ensure the card is focused
                ap.keys.send('UI_Left')
                sleep(0.25)
                # 2) Short select to focus the card / open the right panel
                ap.keys.send('UI_Select')
                sleep(0.25)
                # 3) Hold select to trigger "HOLD TO PLOT ROUTE"
                ap.keys.send('UI_Select', hold=3.0)
                sleep(1.0)

                # Close System Map
                ap.keys.send('SystemMapOpen')
                sleep(0.5)
                return True

            elif bt_lower.startswith("nav"):
                # TODO - Move to, or call Nav Panel code instead?
                # This is a nav-panel bookmark
                # Goto cockpit view
                self.ap.ship_control.goto_cockpit_view()

                # get to the Left Panel menu: Navigation
                ap.keys.send("HeadLookReset")
                ap.keys.send("UIFocus", state=1)
                ap.keys.send("UI_Left")
                ap.keys.send("UIFocus", state=0)  # this gets us over to the Nav panel

                ap.keys.send('UI_Up', hold=4)
                ap.keys.send('UI_Down', repeat=bookmark_position - 1)
                sleep(1.0)
                ap.keys.send('UI_Select')
                sleep(0.25)
                ap.keys.send('UI_Select')
                ap.keys.send("UI_Back")
                ap.keys.send("HeadLookReset")
                return True

        return False

    def goto_system_map(self):
        """ Open System Map if we are not there.
        """
        if self.status_parser.get_gui_focus() != GuiFocusSystemMap:
            logger.debug("Opening System Map")
            # Goto cockpit view
            self.ap.ship_control.goto_cockpit_view()
            # Goto System Map
            self.ap.keys.send('SystemMapOpen')

            # Wait for map to load
            # if not self.status_parser.wait_for_gui_focus(GuiFocusSystemMap):
            #     logger.debug("goto_galaxy_map: System map did not open.")

            # TODO - Add OCR to check screen loaded
            # Scale the regions based on the target resolution.
            scl_reg = reg_scale_for_station(self.reg['cartographics'], self.screen.screen_width,
                                            self.screen.screen_height)

            # Wait for screen to appear. The text is the same, regardless of language.
            res = self.ocr.wait_for_text(self.ap, ["CARTOGRAPHICS"], scl_reg)

            # sleep(3.5)
        else:
            logger.debug("System Map is already open")
            self.keys.send('UI_Left')
            self.keys.send('UI_Up', hold=2)
            self.keys.send('UI_Left')
