#!/usr/bin/env python

import sys

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

    def logged_in(self):
        """Check if player is logged in."""
        soup = self.get_soup("overview")
        found = soup.find("meta", {"name": "ogame-player-name"})
        if found is None: return False
        if str(found["content"]) == self.username: return True

    def fetch_resources(self, planet=None):
        """Build a dictonary of resources."""
        soup = self.get_soup("overview", planet=planet)

        resources = {}
        for res in ["metal", "crystal", "deuterium", "energy"]:
            found = soup.find("span", {"id": "resources_{}".format(res)})
            value = int(found.string.strip().replace(".", ""))
            resources[res] = value

        return resources

    def fetch_planet_ids(self):
        """Builds a dict with the names of the planets and their ids."""
        soup = self.get_soup("overview")

        planets = {}
        name_tags = soup.find_all("span", {"class": "planet-name"})
        for name in name_tags:
            id_tag = name.parent.parent
            planet_id = int(str(id_tag["id"]).replace("planet-", ""))

            planets[name.string] = planet_id

        return planets

    def fetch_technologies(self):
        """Get technology levels, using the same keys from codes dict."""
        soup = self.get_soup("research")
        rev_techs = {v: k for k, v in codes.techs.items()}
        techs = {}

        found = soup.find_all("a", {"class": "detail_button"})

        for tech in found:
            code = int(tech["ref"])
            level_text = tech.find("span", {"class": "level"}).text.strip()
            level = int(level_text.split()[-1])
            techs[rev_techs[code]] = level

        return techs

    def fetch_mines(self, planet=None):
        """Search watch the levels of the mines are on the planet."""
        soup = self.get_soup("resources", planet=planet)

        levels = []
        mines = soup.find_all("span", {"class": "ecke"})
        for mine in mines[0:4]:
            text = mine.find("span", {"class": "level"})
            level = int(text.text.split()[-1])
            levels.append(level)

        return dict(zip(["metal", "crystal", "deuterium", "solar"],
                    levels))

    def build_mine(self, mine, planet=None):
        """Upgrade, if possible, the specified mine or solar plant."""
        token = self.get_token("resources", planet)
        form = {"token": token,
                "type": codes.mines[mine],
                "modus": "1"}
        url = self.page_url("resources", planet)
        self.session.post(url, data=form)

    def build_storage(self, mine, planet=None):
        """Upgrade if possible, the storage for a type of mine."""
        token = self.get_token("resources", planet)
        form = {"token": token,
                "type": codes.storage[mine],
                "modus": "1"}
        url = self.page_url("resources", planet)
        self.session.post(url, data=form)

    def build_station(self, building, planet=None):
        """Upgrade building if possible."""
        token = self.get_token("station", planet)
        form = {"token": token,
                "type": codes.buildings[building],
                "modus": "1"}
        url = self.page_url("station", planet)
        self.session.post(url, data=form)

    def build_research(self, tech, planet=None):
        """Start upgrading research. Defaults to main planet."""
        form = {"type": codes.techs[tech],
                "modus": "1"}
        url = self.page_url("research", planet)
        self.session.post(url, data=form)

    def build_ship(self, ship, number=1, planet=None):
        """Build a given number of a given ship on a given planet."""
        token = self.get_token("shipyard", planet)
        menge = "" if number == 1 else str(number)
        form = {"token": token,
                "type": codes.ships[ship],
                "modus": "1",
                "menge": menge}
        url = self.page_url("shipyard", planet)
        self.session.post(url, data=form)

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
            self.crash(universe, "was not found.")

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
            self.crash(country, "was not found on the list.")
        if len(countries[country]) != 2:
            self.crash("Can't fetch code for", country)

        return countries[country]

    def crash(self, *args, error="OGameError", exit=True):
        """Print an error message and exits program."""
        print("{}:".format("OGameError"), *args)
        if exit: sys.exit()
