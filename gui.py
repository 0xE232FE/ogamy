#!/usr/bin/env python3
import sys
import math
import time
import getpass
import curses
from collections import OrderedDict

from ogamy import OGamer

class Viewer:
    def __init__(self, game, screen):
        self.screen = screen
        self.game = game
        self.planets = list(self.game.planet_ids.keys())
        self.planet = self.planets[0]
        self.station = "overview"
        self.stations = ["overview",
                         "mines",
                         "buildings",
                         "technologies",
                         "shipyard",
                         "defenses",
                         "fleet"]
        self.menu_len = dict(zip(self.stations, [4, 8, 8, 16, 14, 9, 1]))

        self.cursor = [0, 0]
        self.station_info = self.game.fetch_planet_info(planet=self.planet)

        self.cache = {"planets": list(self.game.planet_ids.keys())}

    def grab_cache(self, grab):
        """Return cached version of requested if it exists. If not make cached entry."""
        if grab in self.cache.keys(): return self.cache[grab]
        else: # fetch from internet and save in cache
            function = getattr(self.game, "fetch_{}".format(grab)) # get the function object
            if grab == "technologies": # the techs function does not need the planet argument
                fetched = function()
            else:
                fetched = function(planet=self.planet) # get what we want

            self.cache[grab] = fetched # save in cache
            return fetched

    def draw_header(self):
        """The header contains the planets name and resources."""
        # created padded string with name on the middle and add to screen
        planet_string = "{} - {}".format(self.planet, self.station.capitalize())
        planet_x = (self.screen.getmaxyx()[1] - len(planet_string)) // 2
        self.screen.addstr(0, planet_x, planet_string, curses.A_BOLD)

        # create string with resources, and colors if storage is full for them
        self.draw_pretty_res()

    def draw_pretty_res(self):
        """Show current planet's resources to the screen.
        Show resources in red if storage is full for that resource."""
        storage_level = self.grab_cache("storage")
        storage = {}
        for mine, lvl in storage_level.items(): # replace level with max capacity
            storage[mine] = 5000 * int(2.5 * math.e ** (20 * lvl / 33)) # formula for storage per level

        res = self.grab_cache("resources")

        # calculate number of spaces between resource, for prettiness
        maxx = self.screen.getmaxyx()[1] # horizontal size of screen
        spaces = maxx - (sum(map(lambda t: len(t[0]) + 2 + len(str(t[1])), res.items())))
        spaces //= len(res.keys()) - 1

        x = 0
        for mine, stored in res.items():
            self.screen.addstr(1, x, "{}: ".format(mine.capitalize()))
            x += len(mine) + 2 # move cursor forward

            if mine != "energy" and stored >= storage[mine]: pair_num = 2 # red text on black
            elif mine == "energy" and res["energy"] < 0: pair_num = 2
            else: pair_num = 0 # normal white text on black
            self.screen.addstr(1, x, str(stored), curses.color_pair(pair_num))

            x += len(str(stored)) + spaces # move forward and add spaces

    def draw_bottom(self):
        """Draw the bottom line of the screen with player rank and points."""
        maxy, maxx = self.screen.getmaxyx()

        # get the info from the game object
        info = tuple(self.game.fetch_points().values())
        info_str = "Points: {} | Rank: {}".format(info[1], info[0])

        # calculate starting x for centering
        start_x = (maxx - len(info_str)) // 2
        self.screen.addstr(maxy - 1, start_x, info_str)

    def draw_planets(self):
        """Draw the right sidebar with all the planets."""
        screen_size = self.screen.getmaxyx()[1]
        # check if planets is a dict
        if isinstance(self.planets, OrderedDict): planets = (self.planets.keys())
        else: planets = self.planets
        for i, planet in enumerate(self.planets):
            x = screen_size - len(planet) - 1
            pair_num = 1 if self.cursor == [2, i] else 0 # reverse text if its the cursor
            self.screen.addstr(i + 4, x, planet, curses.color_pair(pair_num))

    def draw_stations(self):
        """Draw the left sidebar with all the possible stations."""
        for i, station in enumerate(self.stations):
            pair_num = 1 if self.cursor == [0, i] else 0 # reverse text if its on the cursor
            self.screen.addstr(i + 4, 1, station.capitalize(), curses.color_pair(pair_num))

    def draw_station_info(self, info, bold_titles=True):
        """Generic function to draw the info for a given station.
        Info is a list where titles correspond to list of key value pairs."""
        longest_title = max(map(lambda i: len(i[0]), info))
        longest_option = max(map(lambda i: max(map(lambda j: len(j[0]) + 2 + len(str(j[1])), i[1])), info))

        title_x = (self.screen.getmaxyx()[1] - longest_title - 2 - longest_option) // 2
        block_x = title_x + 2 + longest_title

        line = 0 # used for highlighting where the cursor is
        y = 4 # position on screen
        for block in info:
            title = block[0].capitalize()
            if bold_titles: self.screen.addstr(y, title_x, title, curses.A_BOLD)
            else: self.screen.addstr(y, title_x, title)

            for pair in block[1]:
                thing, value = tuple(pair)
                spaces = " " * (longest_option - len(thing) - len(str(value)))
                string = "{}: {}{}".format(thing.capitalize(), spaces, value)

                pair_num = 1 if self.cursor == [1, line] else 0 # reverse color, it's the cursor's line
                self.screen.addstr(y, block_x, string, curses.color_pair(pair_num))

                line += 1
                y += 1

            y += 1 # leave one line between blocks

    def draw_overview(self):
        """Show planet information like space left, tempurature."""
        info = self.grab_cache("planet_info")
        self.draw_station_info([["", list(info.items())]])

    def draw_mines(self):
        levels = self.grab_cache("mines")
        storage = self.grab_cache("storage")
        self.draw_station_info([["mines", levels.items()], ["storage", storage.items()]])

    def draw_buildings(self):
        builds = self.grab_cache("buildings")
        self.draw_station_info([["", list(builds.items())]])

    def draw_technologies(self):
        techs = self.grab_cache("technologies")
        tech_list = list(techs.items())
        self.draw_station_info([["basic", tech_list[0:5]],
                                ["drives", tech_list[5:8]],
                                ["advanced", tech_list[8:12]],
                                ["combat", tech_list[12:]]])

    def draw_shipyard(self):
        ships = self.grab_cache("ships")
        ship_list = list(ships.items())
        self.draw_station_info([["combat", ship_list[0:9]],
                                ["civil", ship_list[9:]]])

    def draw_defenses(self): pass
    def draw_fleet(self): pass

    def draw_middle(self):
        """Draw the middle station info."""
        func_name = "draw_{}".format(self.station)
        draw_function = getattr(self, func_name) # get the function object
        draw_function() # call the function

    def draw_all(self):
        """Draw all the parts of the screen."""
        self.screen.clear()
        self.draw_header()
        self.draw_middle()
        self.draw_stations() # left sidebar
        self.draw_planets() # right sidebar
        self.draw_bottom() # player rank/point info
        self.screen.refresh()

    def move_cursor(self, x_diff, y_diff):
        """Move cursor and normalize it afterwards."""
        # not proud of this code. very ugly and hard to read. but it works so far, and i'm lazy
        self.cursor[0] += x_diff
        self.cursor[1] += y_diff
        if self.cursor[0] < 0: self.cursor[0] = 0
        if self.cursor[1] < 0: self.cursor[1] = 0
        if self.cursor[0] > 2: self.cursor[0] = 2
        elif self.cursor[0] == 0: # cursor on the left, choosing station
            if self.cursor[1] > 6: self.cursor[1] = 6
        elif self.cursor[0] == 1: # cursor on the middle
            if self.cursor[1] >= self.menu_len[self.station]: self.cursor[1] = self.menu_len[self.station] - 1
        elif self.cursor[0] == 2: # cursor on the right choosing planet
            if self.cursor[1] >= len(self.planets): self.cursor[1] = len(self.planets) - 1

        # redraw stuff if needed
        if x_diff == 0: # the cursor only moved up or down
            if self.cursor[0] == 0: self.draw_stations() # redraw the left sidebar
            elif self.cursor[0] == 1: self.draw_middle() # redraw the middle
            elif self.cursor[0] == 2: self.draw_planets() # redraw the right sidebar
        else: # the cursor also moved to the side
            self.draw_middle() # draw the middle
            if self.cursor[0] == 1: # cursor is in the middle
                if x_diff == 1: self.draw_stations() # it came from the left
                else: self.draw_planets() # it came from the right
            elif self.cursor[0] == 2: self.draw_planets() # it went to the right
            else: self.draw_stations() # it went to the left

        #self.screen.addstr(22, 0, "{}, {}".format(self.cursor[0], self.cursor[1]))
        self.screen.refresh()

    def change_station(self):
        self.station = self.stations[self.cursor[1]]
        # redraw stuff
        self.draw_all()

    def change_planet(self):
        self.planet = self.cache["planets"][self.cursor[1]]

        # re init the cache with the planet names
        cache = {"planets": self.cache["planets"]}
        # also keep the techs if they were already in cache. these dont depend on the planet
        if "technologies" in self.cache.keys(): cache["technologies"] = self.cache["technologies"]
        self.cache = cache # replace the cache

        # redraw everything
        self.draw_all()

    def refresh(self):
        """Refetch the info for the current station, planet list and resources and redraw the screen."""
        self.cache["planets"] = list(self.game.fetch_planet_ids().keys())
        self.cache["resources"] = self.game.fetch_resources(planet=self.planet)
        self.draw_all() # redraw the station info

    def run(self):
        self.draw_all()

        self.done = False
        while not self.done:
            key = self.screen.getch() # wait for user input
            if key == ord("q"): # quit
                self.done = True

            elif key == ord("r"): # refresh everything that is in cache
                self.refresh()

            elif key == curses.KEY_ENTER or key == 10 or key == 13: # change planet or station
                if self.cursor[0] == 0: self.change_station()
                elif self.cursor[0] == 2: self.change_planet()

            # move cursor with vim keys
            elif key == ord("h"): self.move_cursor(-1, 0) # left
            elif key == ord("j"): self.move_cursor(0, 1) # down
            elif key == ord("k"): self.move_cursor(0, -1) # up
            elif key == ord("l"): self.move_cursor(1, 0) # right

            # move cursor with arrow keys
            elif key == curses.KEY_LEFT: self.move_cursor(-1, 0) # left
            elif key == curses.KEY_DOWN: self.move_cursor(0, 1) # down
            elif key == curses.KEY_UP: self.move_cursor(0, -1) # up
            elif key == curses.KEY_RIGHT: self.move_cursor(1, 0) # right


def init_curses(stdscr, game):
    curses.curs_set(0) # make cursor invisible
    # set color pairs
    curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE) # black text on white
    curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK) # red text on black

    viewer = Viewer(game, stdscr)
    viewer.run()

def main():
    pw = getpass.getpass(prompt='Password: ', stream=None)

    # load ogame profile
    game = OGamer(sys.argv[1], sys.argv[2], pw)
    curses.wrapper(init_curses, game)

if __name__ == "__main__": main()
