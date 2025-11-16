from __future__ import annotations
from time import sleep
from CargoParser import CargoParser
from EDAP_data import *
from EDKeys import EDKeys
from EDlogger import logger
import json
from MarketParser import MarketParser
from MousePt import MousePoint
from pathlib import Path

"""
File: EDWayPoint.py    

Description:
   Class will load file called waypoints.json which contains a list of System name to jump to.
   Provides methods to select a waypoint pass into it.  

Author: sumzer0@yahoo.com
"""


class EDWayPoint:
    def __init__(self, ed_ap, is_odyssey=True):
        self.ap = ed_ap
        self.is_odyssey = is_odyssey
        self.filename = self._get_default_waypoint_path()
        self.stats_log = {'Colonisation': 0, 'Construction': 0, 'Fleet Carrier': 0, 'Station': 0}
        self.waypoints = {}
        # Автоматично вмикаємо перемикання файлу лише для мовних шаблонів example_*.json
        self.using_default_file = Path(self.filename).name.startswith('example_')
        #  { "Ninabin": {"DockWithTarget": false, "TradeSeq": None, "Completed": false} }
        # for i, key in enumerate(self.waypoints):
        # self.waypoints[target]['DockWithTarget'] == True ... then go into SC Assist
        # self.waypoints[target]['Completed'] == True
        # if docked and self.waypoints[target]['Completed'] == False
        #    execute_seq(self.waypoints[target]['TradeSeq'])

        ss = self.read_waypoints(self.filename)

        if ss is None and self.filename != './waypoints/waypoints.json':
            # Якщо мовний шаблон недоступний, повертаємось до базового файлу.
            self.filename = './waypoints/waypoints.json'
            self.using_default_file = False
            ss = self.read_waypoints(self.filename)

        # if we read it then point to it, otherwise use the default table above
        if ss is not None:
            self.waypoints = ss
            logger.debug("EDWayPoint: read json:" + str(ss))

        self.num_waypoints = len(self.waypoints)

        # print("waypoints: "+str(self.waypoints))
        self.step = 0

        self.mouse = MousePoint()
        self.market_parser = MarketParser(log_func=self.ap.log_ui)
        self.cargo_parser = CargoParser(log_func=self.ap.log_ui)
        self.log_keys = getattr(self.ap, 'LOG_KEYS', {})
        self.voice_keys = getattr(self.ap, 'VOICE_KEYS', {})

    def _log(self, key_name: str, **kwargs):
        key = self.log_keys.get(key_name)
        if not key:
            logger.warning(f"Missing waypoint log key: {key_name}")
            return ''
        return self.ap.log_ui(key, **kwargs)

    def _log_and_speak(self, log_key_name: str, voice_key_name: str | None = None, **kwargs):
        text = self._log(log_key_name, **kwargs)
        voice_key = self.voice_keys.get(voice_key_name or log_key_name)
        if voice_key:
            self.ap.speak_ui(voice_key, **kwargs)
        return text

    def load_waypoint_file(self, filename=None) -> bool:
        if filename is None:
            return False

        ss = self.read_waypoints(filename)

        if ss is not None:
            self.waypoints = ss
            self.filename = filename
            self.using_default_file = False
            self._log('WAYPOINT_FILE_LOADED', filename=filename)
            logger.debug("EDWayPoint: read json:" + str(ss))
            return True

        self._log('WAYPOINT_FILE_INVALID')
        return False

    def read_waypoints(self, filename='./waypoints/waypoints.json'):
        s = None
        try:
            s = self._read_json_utf8(filename)

            # Perform any checks on the data returned
            # Check if the waypoint data contains the 'GlobalShoppingList' (new requirement)
            if 'GlobalShoppingList' not in s:
                self._log('WAYPOINT_GLOBAL_LIST_MISSING', filename=filename)
                s = None

            err = False
            if s is not None:
                for key, value in s.items():
                    if key == 'GlobalShoppingList':
                        # Special case
                        if 'BuyCommodities' not in value:
                            self._log('WAYPOINT_FIELD_MISSING', waypoint=key, field='BuyCommodities')
                            err = True
                        if 'UpdateCommodityCount' not in value:
                            self._log('WAYPOINT_FIELD_MISSING', waypoint=key, field='UpdateCommodityCount')
                            err = True
                        if 'Skip' not in value:
                            self._log('WAYPOINT_FIELD_MISSING', waypoint=key, field='Skip')
                            err = True
                    else:
                        # All other cases
                        if 'SystemName' not in value:
                            self._log('WAYPOINT_FIELD_MISSING', waypoint=key, field='SystemName')
                            err = True
                        if 'StationName' not in value:
                            self._log('WAYPOINT_FIELD_MISSING', waypoint=key, field='StationName')
                            err = True
                        if 'GalaxyBookmarkType' not in value:
                            self._log('WAYPOINT_FIELD_MISSING', waypoint=key, field='GalaxyBookmarkType')
                            err = True
                        if 'GalaxyBookmarkNumber' not in value:
                            self._log('WAYPOINT_FIELD_MISSING', waypoint=key, field='GalaxyBookmarkNumber')
                            err = True
                        if 'SystemBookmarkType' not in value:
                            self._log('WAYPOINT_FIELD_MISSING', waypoint=key, field='SystemBookmarkType')
                            err = True
                        if 'SystemBookmarkNumber' not in value:
                            self._log('WAYPOINT_FIELD_MISSING', waypoint=key, field='SystemBookmarkNumber')
                            err = True
                        if 'SellCommodities' not in value:
                            self._log('WAYPOINT_FIELD_MISSING', waypoint=key, field='SellCommodities')
                            err = True
                        if 'BuyCommodities' not in value:
                            self._log('WAYPOINT_FIELD_MISSING', waypoint=key, field='BuyCommodities')
                            err = True
                        if 'UpdateCommodityCount' not in value:
                            self._log('WAYPOINT_FIELD_MISSING', waypoint=key, field='UpdateCommodityCount')
                            err = True
                        if 'FleetCarrierTransfer' not in value:
                            self._log('WAYPOINT_FIELD_MISSING', waypoint=key, field='FleetCarrierTransfer')
                            err = True
                        if 'Skip' not in value:
                            self._log('WAYPOINT_FIELD_MISSING', waypoint=key, field='Skip')
                            err = True
                        if 'Completed' not in value:
                            self._log('WAYPOINT_FIELD_MISSING', waypoint=key, field='Completed')
                            err = True

            if err:
                s = None

        except Exception as e:
            self._log('WAYPOINT_READ_ERROR', filename=filename, error=str(e))
            s = None

        return s

    def write_waypoints(self, data, filename='./waypoints/waypoints.json'):
        if data is None:
            data = self.waypoints
        try:
            self._write_json_utf8(filename, data)
        except Exception as e:
            logger.warning("EDWayPoint.py write_waypoints error:" + str(e))

    def _get_default_waypoint_path(self, language: str | None = None) -> str:
        """Повертає типовий файл маршрутів з урахуванням мови OCR.

        Використовуємо окремі шаблони для ru/en, щоб користувач міг одразу
        працювати зі зрозумілим кодуванням і назвами товарів.
        """
        lang = language or getattr(self.ap, 'ocr_language', 'en')
        base_dir = Path('./waypoints')
        template_map = {
            'ru': base_dir / 'example_RU_repeat.json',
            'en': base_dir / 'example_EN_repeat.json',
        }

        user_primary = base_dir / 'waypoints.json'
        preferred = template_map.get(lang, user_primary)

        if user_primary.exists():
            return str(user_primary)

        if preferred.exists():
            return str(preferred)

        return str(preferred)

    def update_default_file_for_language(self, language: str) -> None:
        """Оновлює типовий файл маршрутів, якщо користувач ще не вибрав свій."""
        if not self.using_default_file:
            return

        new_default = self._get_default_waypoint_path(language)
        if new_default == self.filename:
            return

        ss = self.read_waypoints(new_default)
        if ss is None:
            return

        self.filename = new_default
        self.waypoints = ss
        self._log('WAYPOINT_FILE_LOADED', filename=new_default)
        logger.debug("EDWayPoint: read json:" + str(ss))

    @staticmethod
    def _read_json_utf8(filename: str):
        """Читаємо JSON у кодуванні UTF-8 без ручних перекодувань."""
        with open(filename, "r", encoding="utf-8") as fp:
            return json.load(fp)

    @staticmethod
    def _write_json_utf8(filename: str, data) -> None:
        """Зберігаємо JSON як UTF-8, не екранізуючи не-ASCII символи."""
        with open(filename, "w", encoding="utf-8") as fp:
            json.dump(data, fp, indent=4, ensure_ascii=False)

    def mark_waypoint_complete(self, key):
        self.waypoints[key]['Completed'] = True
        self.write_waypoints(data=None, filename='./waypoints/' + Path(self.filename).name)

    def get_waypoint(self) -> tuple[str, dict] | tuple[None, None]:
        """ Returns the next waypoint list or None if we are at the end of the waypoints.
        """
        dest_key = "-1"

        # loop back to beginning if last record is "REPEAT"
        while dest_key == "-1":
            for i, key in enumerate(self.waypoints):
                # skip records we already processed
                if i < self.step:
                    continue

                # if this entry is REPEAT (and not skipped), mark them all as Completed = False
                if ((self.waypoints[key].get('SystemName', "").upper() == "REPEAT")
                        and not self.waypoints[key]['Skip']):
                    self.mark_all_waypoints_not_complete()
                    break

                # if this step is marked to skip... i.e. completed, go to next step
                if (key == "GlobalShoppingList" or self.waypoints[key]['Completed']
                        or self.waypoints[key]['Skip']):
                    continue

                # This is the next uncompleted step
                self.step = i
                dest_key = key
                break
            else:
                return None, None

        return dest_key, self.waypoints[dest_key]

    def mark_all_waypoints_not_complete(self):
        for j, tkey in enumerate(self.waypoints):
            # Ensure 'Completed' key exists before trying to set it
            if 'Completed' in self.waypoints[tkey]:
                self.waypoints[tkey]['Completed'] = False
            else:
                # Handle legacy format where 'Completed' might be missing
                # Or log a warning if the structure is unexpected
                logger.warning(f"Waypoint {tkey} missing 'Completed' key during reset.")
            self.step = 0
        self.write_waypoints(data=None, filename='./waypoints/' + Path(self.filename).name)
        self.log_stats()

    def log_stats(self):
        calc1 = 1.5 ** self.stats_log['Colonisation']
        calc2 = 1.5 ** self.stats_log['Construction']
        sleep(max(calc1, calc2))

    def execute_trade(self, ap, dest_key):
        # Get trade commodities from waypoint
        sell_commodities = self.waypoints[dest_key]['SellCommodities']
        buy_commodities = self.waypoints[dest_key]['BuyCommodities']
        fleetcarrier_transfer = self.waypoints[dest_key]['FleetCarrierTransfer']
        global_buy_commodities = self.waypoints['GlobalShoppingList']['BuyCommodities']

        if len(sell_commodities) == 0 and len(buy_commodities) == 0 and len(global_buy_commodities) == 0:
            return

        # Does this place have commodities service?
        # From the journal, this works for stations (incl. outpost), colonisation ship and megaships
        if ap.jn.ship_state()['StationServices'] is not None:
            if 'commodities' not in ap.jn.ship_state()['StationServices']:
                self._log('WAYPOINT_NO_COMMODITIES_MARKET')
                return
        else:
            self._log('WAYPOINT_NO_STATION_SERVICES')
            return

        # Determine type of station we are at
        colonisation_ship = "ColonisationShip".upper() in ap.jn.ship_state()['cur_station'].upper()
        orbital_construction_site = ap.jn.ship_state()['cur_station_type'].upper() == "SpaceConstructionDepot".upper()
        fleet_carrier = ap.jn.ship_state()['cur_station_type'].upper() == "FleetCarrier".upper()
        outpost = ap.jn.ship_state()['cur_station_type'].upper() == "Outpost".upper()

        if colonisation_ship or orbital_construction_site:
            if colonisation_ship:
                # Colonisation Ship
                self.stats_log['Colonisation'] = self.stats_log['Colonisation'] + 1
                self._log('WAYPOINT_TRADE_COLONISATION')
                logger.debug(f"Execute Trade: On Colonisation Ship")
            if orbital_construction_site:
                # Construction Ship
                self.stats_log['Construction'] = self.stats_log['Construction'] + 1
                self._log('WAYPOINT_TRADE_CONSTRUCTION')
                logger.debug(f"Execute Trade: On Orbital Construction Site")

            # Go to station services
            self.ap.stn_svcs_in_ship.goto_construction_services()

            # --------- SELL ----------
            if len(sell_commodities) > 0:
                # Sell all to colonisation/construction ship
                self.sell_to_colonisation_ship(ap)

        elif fleet_carrier and fleetcarrier_transfer:
            # Fleet Carrier in Transfer mode
            self.stats_log['Fleet Carrier'] = self.stats_log['Fleet Carrier'] + 1
            # --------- SELL ----------
            if len(sell_commodities) > 0:
                # Transfer to Fleet Carrier
                self.ap.internal_panel.transfer_to_fleetcarrier(ap)

            # --------- BUY ----------
            if len(buy_commodities) > 0:
                self.ap.internal_panel.transfer_from_fleetcarrier(ap, buy_commodities)

        else:
            # Regular Station or Fleet Carrier in Buy/Sell mode
            self._log('WAYPOINT_TRADE_GENERIC')
            logger.debug(f"Execute Trade: On Regular Station")
            self.stats_log['Station'] = self.stats_log['Station'] + 1

            market_time_old = ""
            data = self.market_parser.get_market_data()
            if data is not None:
                market_time_old = self.market_parser.current_data['timestamp']

            # We start off on the Main Menu in the Station
            self.ap.stn_svcs_in_ship.goto_station_services()

            # CONNECTED TO menu is different between stations and fleet carriers
            if fleet_carrier:
                # Fleet Carrier COMMODITIES MARKET location top right, with:
                # uni cart, redemption, trit depot, shipyard, crew lounge
                ap.keys.send('UI_Right', repeat=2)
                ap.keys.send('UI_Select')  # Select Commodities

            elif outpost:
                # Outpost COMMODITIES MARKET location in middle column
                ap.keys.send('UI_Right')
                ap.keys.send('UI_Select')  # Select Commodities

            else:
                # Orbital station COMMODITIES MARKET location bottom left
                ap.keys.send('UI_Down')
                ap.keys.send('UI_Select')  # Select Commodities

            self._log_and_speak('TRADE_DOWNLOAD_MARKET_DATA')

            # Wait for market to update
            market_time_new = ""
            data = self.market_parser.get_market_data()
            if data is not None:
                market_time_new = self.market_parser.current_data['timestamp']

            while market_time_new == market_time_old:
                market_time_new = ""
                data = self.market_parser.get_market_data()
                if data is not None:
                    market_time_new = self.market_parser.current_data['timestamp']
                sleep(1)  # wait for new menu to finish rendering

            cargo_capacity = ap.jn.ship_state()['cargo_capacity']
            logger.info(f"Execute trade: Ship's max cargo capacity: {cargo_capacity}")

            # --------- SELL ----------
            if len(sell_commodities) > 0:
                # Select the SELL option
                self.ap.stn_svcs_in_ship.select_sell(ap.keys)

                for i, key in enumerate(sell_commodities):
                    # Check if we have any of the item to sell
                    self.cargo_parser.get_cargo_data()
                    cargo_item = self.cargo_parser.get_item(key)
                    if cargo_item is None:
                        logger.info(f"Unable to sell {key}. None in cargo hold.")
                        continue

                    # Sell the commodity
                    result, qty = self.ap.stn_svcs_in_ship.sell_commodity(ap.keys, key, sell_commodities[key],
                                                                          self.cargo_parser)

                    # Update counts if necessary
                    if qty > 0 and self.waypoints[dest_key]['UpdateCommodityCount']:
                        sell_commodities[key] = sell_commodities[key] - qty

                # Save changes
                self.write_waypoints(data=None, filename='./waypoints/' + Path(self.filename).name)

            sleep(1)

            # --------- BUY ----------
            if len(buy_commodities) > 0 or len(global_buy_commodities) > 0:
                # Select the BUY option
                self.ap.stn_svcs_in_ship.select_buy(ap.keys)

                # Go through buy commodities list
                for i, key in enumerate(buy_commodities):
                    curr_cargo_qty = int(ap.status.get_cleaned_data()['Cargo'])
                    cargo_timestamp = ap.status.current_data['timestamp']

                    free_cargo = cargo_capacity - curr_cargo_qty
                    logger.info(f"Execute trade: Free cargo space: {free_cargo}")

                    if free_cargo == 0:
                        logger.info(f"Execute trade: No space for additional cargo")
                        break

                    qty_to_buy = buy_commodities[key]
                    logger.info(f"Execute trade: Shopping list requests {qty_to_buy} units of {key}")

                    # Attempt to buy the commodity
                    result, qty = self.ap.stn_svcs_in_ship.buy_commodity(ap.keys, key, qty_to_buy, free_cargo)
                    logger.info(f"Execute trade: Bought {qty} units of {key}")

                    # If we bought any goods, wait for status file to update with
                    # new cargo count for next commodity
                    if qty > 0:
                        ap.status.wait_for_file_change(cargo_timestamp, 5)

                    # Update counts if necessary
                    if qty > 0 and self.waypoints[dest_key]['UpdateCommodityCount']:
                        buy_commodities[key] = qty_to_buy - qty

                # Go through global buy commodities list
                for i, key in enumerate(global_buy_commodities):
                    curr_cargo_qty = int(ap.status.get_cleaned_data()['Cargo'])
                    cargo_timestamp = ap.status.current_data['timestamp']

                    free_cargo = cargo_capacity - curr_cargo_qty
                    logger.info(f"Execute trade: Free cargo space: {free_cargo}")

                    if free_cargo == 0:
                        logger.info(f"Execute trade: No space for additional cargo")
                        break

                    qty_to_buy = global_buy_commodities[key]
                    logger.info(f"Execute trade: Global shopping list requests {qty_to_buy} units of {key}")

                    # Attempt to buy the commodity
                    result, qty = self.ap.stn_svcs_in_ship.buy_commodity(ap.keys, key, qty_to_buy, free_cargo)
                    logger.info(f"Execute trade: Bought {qty} units of {key}")

                    # If we bought any goods, wait for status file to update with
                    # new cargo count for next commodity
                    if qty > 0:
                        ap.status.wait_for_file_change(cargo_timestamp, 5)

                    # Update counts if necessary
                    if qty > 0 and self.waypoints['GlobalShoppingList']['UpdateCommodityCount']:
                        global_buy_commodities[key] = qty_to_buy - qty

                # Save changes
                self.write_waypoints(data=None, filename='./waypoints/' + Path(self.filename).name)

            sleep(1.5)  # give time to popdown
            # Go to ship view
            ap.ship_control.goto_cockpit_view()

    def sell_to_colonisation_ship(self, ap):
        """ Sell all cargo to a colonisation/construction ship.
        """
        ap.keys.send('UI_Left', repeat=3)  # Go to table
        ap.keys.send('UI_Down', hold=2)  # Go to bottom
        ap.keys.send('UI_Up')  # Select RESET/CONFIRM TRANSFER/TRANSFER ALL
        ap.keys.send('UI_Left', repeat=2)  # Go to RESET
        ap.keys.send('UI_Right', repeat=2)  # Go to TRANSFER ALL
        ap.keys.send('UI_Select')  # Select TRANSFER ALL
        sleep(0.5)

        ap.keys.send('UI_Left')  # Go to CONFIRM TRANSFER
        ap.keys.send('UI_Select')  # Select CONFIRM TRANSFER
        sleep(2)

        ap.keys.send('UI_Down')  # Go to EXIT
        ap.keys.send('UI_Select')  # Select EXIT

        sleep(2)  # give time to popdown menu

    def waypoint_assist(self, keys, scr_reg):
        """ Processes the waypoints, performing jumps and sc assist if going to a station
        also can then perform trades if specific in the waypoints file.
        """
        if len(self.waypoints) == 0:
            self._log_and_speak('WAYPOINT_NO_FILE_LOADED')
            return

        self.step = 0  # start at first waypoint
        self._log('WAYPOINT_FILE_SELECTED', filename=str(Path(self.filename).name))
        self.reset_stats()

        # Loop until complete, or error
        _abort = False
        while not _abort:
            # Current location
            cur_star_system = self.ap.jn.ship_state()['cur_star_system'].upper()
            cur_station = self.ap.jn.ship_state()['cur_station'].upper()
            cur_station_type = self.ap.jn.ship_state()['cur_station_type'].upper()

            # Current in game destination
            status = self.ap.status.get_cleaned_data()
            destination_system = status['Destination_System']  # The system ID
            destination_body = status['Destination_Body']  # The body number (0 for prim star)
            destination_name = status['Destination_Name']  # The system/body/station/settlement name

            # ====================================
            # Get next Waypoint
            # ====================================

            # Get the waypoint details
            old_step = self.step
            dest_key, next_waypoint = self.get_waypoint()
            if dest_key is None:
                self._log_and_speak('WAYPOINT_LIST_COMPLETED')
                break

            # Is this a new waypoint?
            if self.step != old_step:
                new_waypoint = True
            else:
                new_waypoint = False

            # Flag if we are using bookmarks
            gal_bookmark = next_waypoint.get('GalaxyBookmarkNumber', -1) > 0
            sys_bookmark = next_waypoint.get('SystemBookmarkNumber', -1) > 0
            gal_bookmark_type = next_waypoint.get('GalaxyBookmarkType', '')
            gal_bookmark_num = next_waypoint.get('GalaxyBookmarkNumber', 0)
            sys_bookmark_type = next_waypoint.get('SystemBookmarkType', '')
            sys_bookmark_num = next_waypoint.get('SystemBookmarkNumber', 0)

            next_wp_system = next_waypoint.get('SystemName', '').upper()
            next_wp_station = next_waypoint.get('StationName', '').upper()

            if new_waypoint:
                self._log_and_speak('WAYPOINT_NEXT', station=next_wp_station, system=next_wp_system)

            # ====================================
            # Target and travel to a System
            # ====================================

            # Check current system and go to next system if different and not blank
            if next_wp_system == "" or (cur_star_system == next_wp_system):
                if new_waypoint:
                    self._log_and_speak('WAYPOINT_ALREADY_IN_SYSTEM')
            else:
                # Check if the current nav route is to the target system
                last_nav_route_sys = self.ap.nav_route.get_last_system().upper()
                # Check we have a route and that we have a destination to a star (body 0).
                # We can have one without the other.
                if ((last_nav_route_sys == next_wp_system) and
                        (destination_body == 0 and destination_name != "")):
                    # No need to target system
                    self._log_and_speak('WAYPOINT_SYSTEM_ALREADY_TARGETED')
                else:
                    self._log_and_speak('WAYPOINT_TARGETING_SYSTEM', system=next_wp_system)
                    # Select destination in galaxy map based on name
                    res = self.ap.galaxy_map.set_gal_map_destination_text(self.ap, next_wp_system,
                                                                          self.ap.jn.ship_state)
                    if res:
                        self._log('WAYPOINT_SYSTEM_TARGETED')
                    else:
                        self._log_and_speak('WAYPOINT_TARGET_FAILED', system=next_wp_system)
                        _abort = True
                        break

                # Select next target system
                # TODO should this be in before every jump?
                keys.send('TargetNextRouteSystem')

                # Jump to the destination system
                self._log_and_speak('WAYPOINT_JUMPING', system=next_wp_system)
                res = self.ap.jump_to_system(scr_reg)
                if not res:
                    self._log('WAYPOINT_JUMP_FAILED', system=next_wp_system)
                    _abort = True
                    break

                continue

            # ====================================
            # Target and travel to a local Station
            # ====================================

            # If we are in the right system, check if we are already docked.
            docked_at_stn = False
            is_docked = self.ap.status.get_flag(FlagsDocked)
            if is_docked:
                # Check if we are at the correct station. Note that for FCs, the station name
                # reported by the Journal is only the ship identifier (ABC-123) and not the carrier name.
                # So we need to check if the ID (ABC-123) is at the end of the target ('Fleety McFleet ABC-123').
                if cur_station_type == 'FleetCarrier'.upper():
                    docked_at_stn = next_wp_station.endswith(cur_station)
                elif next_wp_station == 'System Colonisation Ship'.upper():
                    if (cur_station_type == 'SurfaceStation'.upper() and
                            'ColonisationShip'.upper() in cur_station.upper()):
                        docked_at_stn = True
                # elif next_wp_station.startswith('Orbital Construction Site'.upper()):
                #     if (cur_station_type == 'SurfaceStation'.upper() and
                #             'Orbital Construction Site'.upper() in cur_station.upper()):
                #         docked_at_stn = True
                elif cur_station == next_wp_station:
                    docked_at_stn = True

            # Check current station and go to it if different
            if docked_at_stn:
                if new_waypoint:
                    self._log_and_speak('WAYPOINT_ALREADY_AT_STATION', station=next_wp_station)
            else:
                # Check if we need to travel to a station, else we are done.
                # This may be by 1) System bookmark, 2) Galaxy bookmark or 3) by Station Name text
                if sys_bookmark or gal_bookmark or next_wp_station != "":
                    # If waypoint file has a Station Name associated then attempt targeting it
                    self._log_and_speak('WAYPOINT_TARGETING_STATION', station=next_wp_station)

                    if gal_bookmark:
                        # Set destination via gal bookmark, not system bookmark
                        res = self.ap.galaxy_map.set_gal_map_dest_bookmark(self.ap, gal_bookmark_type, gal_bookmark_num)
                        if not res:
                            self._log_and_speak('WAYPOINT_GALAXY_BOOKMARK_FAILED')
                            _abort = True
                            break

                    elif sys_bookmark:
                        # Set destination via system bookmark
                        res = self.ap.system_map.set_sys_map_dest_bookmark(self.ap, sys_bookmark_type, sys_bookmark_num)
                        if not res:
                            self._log_and_speak('WAYPOINT_SYSTEM_BOOKMARK_FAILED')
                            _abort = True
                            break

                    elif next_wp_station != "":
                        # Need OCR added in for this (WIP)
                        need_ocr = True
                        self._log_and_speak('WAYPOINT_NO_BOOKMARK_SUPPORT')
                        # res = self.nav_panel.lock_destination(station_name)
                        _abort = True
                        break

                    # Jump to the station by name
                    res = self.ap.supercruise_to_station(scr_reg, next_wp_station)
                    sleep(1)  # Allow status log to update
                    continue
                else:
                    self._log_and_speak('WAYPOINT_SYSTEM_ARRIVED', system=next_wp_system)

            # ====================================
            # Dock and Trade at Station
            # ====================================

            # Are we at the correct station to trade?
            if docked_at_stn:  # and (next_wp_station != "" or sys_bookmark):
                # Docked - let do trade
                self._log_and_speak('WAYPOINT_EXECUTE_TRADE', station=next_wp_station)
                self.execute_trade(self.ap, dest_key)

            # Mark this waypoint as completed
            self.mark_waypoint_complete(dest_key)
            self._log_and_speak('WAYPOINT_CURRENT_COMPLETE')

        # Done with waypoints
        if not _abort:
            distance = str(self.ap.total_dist_jumped)
            self._log_and_speak('WAYPOINT_ROUTE_COMPLETE', distance=distance)
            self.ap.update_ap_status(self.ap.STATUS_KEYS['IDLE'])
        else:
            self._log_and_speak('WAYPOINT_ROUTE_ABORTED')
            self.ap.update_ap_status(self.ap.STATUS_KEYS['IDLE'])

    def reset_stats(self):
        # Clear stats
        self.stats_log['Colonisation'] = 0
        self.stats_log['Construction'] = 0
        self.stats_log['Fleet Carrier'] = 0
        self.stats_log['Station'] = 0


def main():
    from ED_AP import EDAutopilot

    ed_ap = EDAutopilot(cb=None)
    wp = EDWayPoint(ed_ap, True)  # False = Horizons
    wp.step = 0  # start at first waypoint
    keys = EDKeys(cb=None)
    keys.activate_window = True
    wp.ap.stn_svcs_in_ship.select_sell(keys)
    wp.ap.stn_svcs_in_ship.sell_commodity(keys, "Aluminium", 1, wp.cargo_parser)
    wp.ap.stn_svcs_in_ship.sell_commodity(keys, "Beryllium", 1, wp.cargo_parser)
    wp.ap.stn_svcs_in_ship.sell_commodity(keys, "Cobalt", 1, wp.cargo_parser)
    #wp.ap.stn_svcs_in_ship.buy_commodity(keys, "Titanium", 5, 200)

    # dest = 'Enayex'
    #print(dest)

    #print("In waypoint_assist, at:"+str(dest))

    # already in doc config, test the trade
    #wp.execute_trade(keys, dest)

    # Set the Route for the waypoint^#
    #dest = wp.waypoint_next(ap=None)

    #while dest != "":

    #  print("Doing: "+str(dest))
    #  print(wp.waypoints[dest])

    #wp.set_station_target(None, dest)

    # Mark this waypoint as complated
    #wp.mark_waypoint_complete(dest)

    # set target to next waypoint and loop
    #dest = wp.waypoint_next(ap=None)


if __name__ == "__main__":
    main()
