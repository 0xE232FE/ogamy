import sys

import requests
from bs4 import BeautifulSoup

class OGamer:

    def __init__(self, uni, username, password, country="EN"):

        self.session = requests.session()

        self.country_code = self.get_country(country)
        self.server = self.get_server(uni)
        self.username = username
        self.password = password

        self.login()

        self.planet_ids  = self.fetch_planet_ids()
        self.planets = list(sorted(self.planet_ids.keys()))

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

    def get_resources(self, planet=None):
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

    def get_soup(self, page, planet=None):
        """Make BeautifulSoup object for this specific page."""
        url = "https://{}/game/index.php?page={}".format(self.server, page)
        if not planet is None:
            if isinstance(planet, int):
                url += "&cp={}".format(planet)
            elif isinstance(planet, str):
                url += "&cp={}".format(self.planet_ids[planet])

        result = self.session.get(url)
        soup = BeautifulSoup(result.content, "html.parser")
        return soup

    def get_server(self, universe):
        """Fetch server url for a given universe."""
        print("inside get_server...")
        # TODO: atually get this from the page
        result = self.session.get("https://{}.ogame.gameforge.com".format(self.country_code))
        soup = BeautifulSoup(result.content, "html.parser")
        found = soup.find("select", {"id": "serverLogin"})
        for i, server in enumerate(found.find_all("option")):
            print("child", i, server["value"])
        print("found:", found)
        return "s139-en.ogame.gameforge.com"

    def get_country(self, code):
        """Get country specific URL."""
        # TODO: search on the page for the code
        return "en"

    def crash(self, message, error="OGameError", exit=True):
        """Logs out and exits program."""
        if self.logged_in(): self.logout()
        print("{}:".format(error), message)
        if exit: sys.exit()
