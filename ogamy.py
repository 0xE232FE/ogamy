#!/usr/bin/env python3

import sys
from collections import OrderedDict

import requests
from bs4 import BeautifulSoup

import codes

class OGamer:

    def __init__(self, uni, username, password, country="United Kingdom"):

        self.session = requests.session()

        self.country_code = self.get_country(country)
        self.server = self.get_server(uni)
        self.username = username
        self.password = password

        self.login()

        # setup planet codes needed for url building later
        self.planet_ids = self.fetch_planet_ids()

    def login(self):
        """Logs player into account."""
        login_form = {"kid": "",
                      "uni": self.server,
                      "login": self.username,
                      "pass": self.password}
        url = "https://%s.ogame.gameforge.com/main/login" % self.country_code
        result = self.session.post(url, data=login_form)

    def logout(self):
        """Logs out of account."""
        url = "https://%s/game/index.php?page=logout" % self.server
        self.session.get(url)

    def logged_in(self, use_page=None):
        """Check if player is logged in."""
        # allow page soup to be passed as argument to make get_soup calling this function faster
        if use_page is None: soup = self.get_soup("overview")
        else: soup = use_page

        found = soup.find("meta", {"name": "ogame-player-name"})
        if found is None: return False
        if str(found["content"]) == self.username: return True

    ########### fetch functions ##############

    def fetch_points(self):
        """Get point and general position of player in rankings."""
        soup = self.get_soup("highscore")

        # find correct line in rankings table
        line = soup.find("tr", {"class": "myrank"})

        rank = int(line.find("td", {"class": "position"}).contents[0].strip())
        points = int(line.find("td", {"class": "score"}).contents[0].strip().replace(".", ""))

        return OrderedDict([("ranking", rank), ("points", points)])

    def fetch_build_queue(self, planet=None):
        """Get the building, technology and ship/defence queue."""
        print("Not implemented yet!")

    def fetch_resources(self, planet=None):
        """Build a dictonary of resources."""
        soup = self.get_soup("overview", planet=planet)

        resources = [] # list of key/value pairs for ordered dict
        for res in ["metal", "crystal", "deuterium", "energy"]:
            found = soup.find("span", {"id": "resources_{}".format(res)})
            value = int(found.string.strip().replace(".", ""))
            resources.append((res, value))

        return OrderedDict(resources)

    def fetch_planet_ids(self):
        """Builds a dict with the names of the planets and their ids."""
        # TODO: big planet names dont work.
        # TODO: need to fetch from other part of the page
        soup = self.get_soup("overview")

        planet_list = [] # for creating the planet dict afterwards
        name_tags = soup.find_all("span", {"class": "planet-name"})
        for name in name_tags:
            id_tag = name.parent.parent
            planet_id = int(str(id_tag["id"]).replace("planet-", ""))

            planet_list.append((name.string, planet_id))

        return OrderedDict(planet_list)

    def fetch_planet_info(self, planet=None):
        """Get information for a specific planet like tempurature, position and fields."""
        soup = self.get_soup("overview", planet=planet)

        # grab planet id from the built dictionary
        if planet is None: planet_id = self.planet_ids[next(iter(self.planet_ids))] # first value of dict
        else: planet_id = self.planet_ids[planet]

        planet = soup.find("div", {"id": "planet-{}".format(planet_id)})
        info = planet.find("a")["title"]
        info = [x.split(">")[-1] for x in info.split("<")] # separate text from the tags
        info = [x for x in info if x != ""] # remove empty strings

        return OrderedDict(zip(["position", "diameter", "slots", "temperature"],
                   [info[0].split()[-1], info[1].split()[0], info[1].split()[-1], info[2]]))

    def fetch_mines(self, planet=None):
        """Search what the levels of the mines are on the planet."""
        return self.fetch_levels("resources", planet, codes.mines)

    def fetch_storage(self, planet=None):
        """Search the levels of the storage for resources."""
        return self.fetch_levels("resources", planet, codes.storage)

    def fetch_buildings(self, planet=None):
        """Get the level for each of the stations in buildings page."""
        return self.fetch_levels("station", planet, codes.buildings)

    def fetch_technologies(self):
        """Get technology levels, using the same keys from codes dict."""
        return self.fetch_levels("research", None, codes.techs)

    def fetch_ships(self, planet=None):
        """Get the number of each ship docked at a given planet."""
        return self.fetch_levels("shipyard", planet, codes.ships)

    def fetch_defenses(self, planet=None):
        return self.fetch_levels("defense", planet, codes.defences)

    def fetch_levels(self, page, planet, code_dict):
        """Generic function to get the level of something on a page."""
        soup = self.get_soup(page, planet)
        rev_codes = {v: k for k, v in code_dict.items()} # reverse the dict
        dict_items = [] # for creating OrderedDict at the end

        found = soup.find_all("a") # get all the a tags of the page
        for thing in found:
            try: code = int(thing["ref"])
            except KeyError: continue # we only care about the link tags with a level
            if code not in rev_codes: continue # discard other levels that might be on the page
            try: # need this to not catch some stuff i don't fully understand
                if "details" not in thing["id"]: continue
            except KeyError: continue

            level_text = thing.find("span", {"class": "level"}).text.strip()
            level = int(level_text.split()[-1])
            dict_items.append((rev_codes[code], level))

        return OrderedDict(dict_items)

    ########### build functions ##############

    def build_mine(self, mine, planet=None):
        """Upgrade, if possible, the specified mine or solar plant."""
        self.send_build_post("resources", planet, codes.mines[mine])

    def build_storage(self, mine, planet=None):
        """Upgrade if possible, the storage for a type of mine."""
        self.send_build_post("resources", planet, codes.storage[mine])

    def build_station(self, building, planet=None):
        """Upgrade building if possible."""
        self.send_build_post("station", planet, codes.buildings[building])

    def build_research(self, tech, planet=None):
        """Start upgrading research. Defaults to main planet."""
        self.send_build_post("research", planet, codes.techs[tech], get_token=False)

    def build_ships(self, ship, number=1, planet=None):
        """Build a given number of a given ship on a given planet."""
        menge = "" if number == 1 else str(number)
        self.send_build_post("shipyard", planet, codes.ships[ship], form={"menge": menge})

    def send_fleet(self, ships, res, dest, mission, speed=10, planet=None):
        """only works for one specific type of mission."""
        form = {"holdingtime": "1", # dont know what this is yet
                "expeditiontime": "1", # also dont know what this is yet
                "token": self.get_token("fleet3", planet),
                "galaxy": dest[0], "system": dest[1], "position": dest[2],
                "type": "1", # also dont know yet
                "mission": codes.mission[mission],
                "union2": "0", # dont know this one either
                "holdingOrExpTime": "0", # nope
                "speed": str(speed), # this one was easy
                "acsValues": "-", # no clue
                "prioMetal": "1", # nope
                "prioCrystal": "2", # nope
                "prioDeuterium": "3"} # aaaaand nope
        # now we add the ships
        for ship in ships: form["am{}".format(codes.ships[ship])] = ships[ship]
        # next we add the resources to take
        for r in res: form[r] = res[r]

        # now that the fleet cake is done we just give to the server
        url = self.page_url("movement", planet)
        self.session.post(url, data=form)

    def send_build_post(self, page, planet, code, form={}, get_token=True):
        """Grab a token and send a post request to a certain page with the provided form."""
        # add addional needed info to the form before sending it
        if get_token: form["token"] = self.get_token(page, planet)
        form["modus"] = "1" # prob refers if this constructing or destructing
        form["type"] = code

        url = self.page_url(page, planet)
        if not self.logged_in(): self.login()
        self.session.post(url, data=form)

    def rename(self, name, planet=None):
        """Rename a planet."""
        # TODO: make this work
        url = self.page_url("planetRename", planet=planet)
        form = {"newPlanetName": "+".join(name.split())}
        self.session.post(url, data=form)

        self.planet_ids = self.fetch_planet_ids() # needs updating

    def get_token(self, page, planet=None):
        """Search for the token for the POST form."""
        soup = self.get_soup(page, planet)
        post = soup.find("form", {"method": "POST"})

        token = post.find("input", {"name": "token"})["value"]
        return token

    def page_url(self, page, planet=None):
        """Build correct URL for a given page/planet."""
        url = "https://{}/game/index.php?page={}".format(self.server, page)
        if not planet is None: # to go to a specific planet
            if isinstance(planet, int): # using the planet code
                url += "&cp={}".format(planet)
            elif isinstance(planet, str): # using planet name instead
                url += "&cp={}".format(self.planet_ids[planet])

        return url

    def get_soup(self, page, planet=None):
        """Make BeautifulSoup object for this specific page."""
        url = self.page_url(page, planet)
        result = self.session.get(url)
        soup = BeautifulSoup(result.content, "html.parser")

        if not self.logged_in(use_page=soup):
            self.login()
            # i could do this recursively but i'm afraid of getting stuck because it couldn't
            # log in for some reason not related to this program. and this is prob faster
            result = self.session.get(url)
            soup = BeautifulSoup(result.content, "html.parser")

        return soup

    def get_server(self, universe):
        """Fetch server url for a given universe."""
        result = self.session.get("https://{}.ogame.gameforge.com".format(self.country_code))
        soup = BeautifulSoup(result.content, "html.parser")
        found = soup.find("select", {"id": "serverLogin"})

        servers = {}
        for sv in found.find_all("option"):
            servers[sv.string.strip()] = sv["value"]

        # check if server exists
        if not universe in servers.keys():
            self.crash("Universe", universe, "was not found.")

        return servers[universe]

    def get_country(self, country):
        """Get country specific URL."""
        if country == "United Kingdom": return "en"

        result = self.session.get("https://en.ogame.gameforge.com")
        soup = BeautifulSoup(result.content, "html.parser")

        code_list = soup.find("ul", {"id": "mmoList1"})
        countries = {}
        for tag in code_list.find_all("li"):
            link = tag.find("a")["href"]
            name = tag.string.strip() # name of the country
            code = link.split(".")[0].replace("//", "")
            countries[name] = code # save to the dict

        # check if input was ok
        if not country in countries.keys():
            self.crash("Country", country, "was not found on the list.")
        if len(countries[country]) != 2:
            self.crash("Can't fetch code for country", country)

        return countries[country]

    def crash(self, *args, error="OGameError", exit=True):
        """Print an error message and exits program."""
        print("{}:".format(error), *args)
        if exit: sys.exit()

