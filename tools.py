import math


base_cost = {
    # mines and stuff
    "metal": (60, 15), "crystal": (48, 24), "solar": (75, 30),
    "solar": (75, 30), "fusion": (900, 360, 180),
    "metal_sto": (1000), "crystal_sto": (1000, 500), "deuterium_sto": (1000, 1000),
    # station buildings
    "robots": (400, 120, 200), "shipyard": (400, 200, 100), "lab": (200, 400, 200),
    "depot": (20000, 40000), "silo": (20000, 20000, 1000), "nanite": (10**6, 500000, 10**5),
    "terraformer": (0, 50000, 100000, 1000), "dock": (1000, 0, 250, 125)
}

def needed_solar(metal, crystal, deut):
    metal_ene = ((10 * metal * 1.1**metal) // 1) + 1 # metal consumption
    crystal_ene = ((10 * crystal * 1.1**crystal) // 1) + 1 # crystal consumption
    deut_ene = ((20 * deut * 1.1**deut) // 1) + 1 # deut consumption
    total_ene = metal_ene + crystal_ene + deut_ene

    solar_lvl = 1
    while (20 * solar_lvl * 1.1**solar_lvl) // 1 < total_ene: solar_lvl += 1

    return solar_lvl

def build_time(building, level, storage=False, redesigned=True, robots=0, nanites=0, uni_speed=1):
    """Time (in hours) it takes to build something."""
    cost = build_cost(building, level, is_storage=storage)
    res = cost["metal"] + cost["crystal"]
    time = res / (2500 * (1 + robots) * (2 ** nanites) * uni_speed)
    if redesigned: time *= 2 / 7

    return time

def build_cost(building, level, is_storage=False):
    """Calculate how much building a certain level costs."""
    def cost(*args):
        if building in ["metal", "crystal", "deuterium", "solar", "dm"]:
            if building == "crystal": exp = 1.6
            else: exp = 1.5
        else: exp = 2

        return dict(zip(["metal", "crystal", "deuterium", "solar", "dm"],
                        [arg * exp ** (level - 1) for arg in args] + [0] * (5 - len(args))))

    if is_storage: building += "_sto"
    return cost(*base_cost[building])

def distance(start, dest):
    """The distance between two planets. Both arguments must be 3 tuples of the coordinates"""
    if start[0] != dest[0]: # different galaxies
        return 20000 * abs(start[0] - dest[0])
    elif start[1] != dest[1]: # different solar systems
        return 2700 + 95 * abs(start[1] - dest[1])
    else:
        return 1000 + 5 * abs(start[2] - dest[2])
