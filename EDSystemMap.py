from __future__ import annotations

from EDAP_data import GuiFocusSystemMap
from EDlogger import logger
from OCR import OCR
from Screen_Regions import reg_scale_for_station
from StatusParser import StatusParser
from time import sleep, time


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
        self.reg = {'cartographics': {'rect': [0.0, 0.0, 0.25, 0.25]},
                    }

    def set_sys_map_dest_bookmark(self, ap, bookmark_type: str, bookmark_position: int,
                                  expected_name: str | None = None) -> bool:
        """ Set the System Map destination using a bookmark.
        @param ap: ED_AP reference.
        @param bookmark_type: The bookmark type (Favorite, Body, Station, Settlement or Navigation), Favorite
         being the default if no match is made with the other options. Navigation is unique in that it uses
         the Nav Panel instead of the System Map.
        @param bookmark_position: The position in the bookmark list, starting at 1 for the first bookmark.
        @return: True if bookmark could be selected, else False
        """
        if self.is_odyssey and bookmark_position != -1:
            status = self.status_parser.get_cleaned_data()
            previous_destination = str(status.get('Destination_Name', '') or '')
            previous_mod_time = self.status_parser.last_mod_time
            expected_upper = expected_name.upper() if expected_name else None

            # Check if this is a nav-panel bookmark
            if not bookmark_type.lower().startswith("nav"):
                self.goto_system_map()

                ap.keys.send('UI_Left')  # Go to BOOKMARKS
                sleep(.5)
                ap.keys.send('UI_Select')  # Select BOOKMARKS
                sleep(.25)
                ap.keys.send('UI_Right')  # Go to FAVORITES
                sleep(.25)

                # If bookmark type is Fav, do nothing as this is the first item
                if bookmark_type.lower().startswith("bod"):
                    ap.keys.send('UI_Down', repeat=1)  # Go to BODIES
                elif bookmark_type.lower().startswith("sta"):
                    ap.keys.send('UI_Down', repeat=2)  # Go to STATIONS
                elif bookmark_type.lower().startswith("set"):
                    ap.keys.send('UI_Down', repeat=3)  # Go to SETTLEMENTS

                sleep(.25)
                ap.keys.send('UI_Select')  # Select bookmark type, moves you to bookmark list
                ap.keys.send('UI_Left')  # Sometimes the first bookmark is not selected, so we try to force it.
                ap.keys.send('UI_Right')
                sleep(.25)
                ap.keys.send('UI_Down', repeat=bookmark_position - 1)
                sleep(.25)
                ap.keys.send('UI_Select', hold=3.0)

                # Close System Map
                ap.keys.send('SystemMapOpen')
                sleep(0.5)

                if self._wait_for_destination_update(previous_destination, expected_upper, previous_mod_time):
                    return True

                logger.warning("System map bookmark selection failed to update destination.")
                return False

            elif bookmark_type.lower().startswith("nav"):
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

                if self._wait_for_destination_update(previous_destination, expected_upper, previous_mod_time):
                    return True

                logger.warning("Nav panel bookmark selection failed to update destination.")
                return False

        return False

    def _wait_for_destination_update(self, previous_destination: str, expected_upper: str | None,
                                      previous_mod_time: float | None, timeout: float = 5.0) -> bool:
        if expected_upper and previous_destination.upper() == expected_upper:
            return True

        end_time = time() + timeout
        while time() < end_time:
            data = self.status_parser.get_cleaned_data()
            dest_name = data.get('Destination_Name', '')

            if expected_upper:
                if dest_name.upper() == expected_upper:
                    return True
            else:
                if dest_name and dest_name != previous_destination:
                    return True
                if (previous_mod_time is not None and self.status_parser.last_mod_time is not None
                        and self.status_parser.last_mod_time > previous_mod_time and dest_name):
                    return True

            sleep(0.25)

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
