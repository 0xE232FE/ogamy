import math


base_cost = {
    # mines and stuff
    "metal": (60, 15), "crystal": (48, 24), "deuterium": (225, 75), "solar": (75, 30),
    "solar": (75, 30), "fusion": (900, 360, 180),
    "metal_sto": (1000), "crystal_sto": (1000, 500), "deuterium_sto": (1000, 1000),
    # station buildings
    "robot": (400, 120, 200), "shipyard": (400, 200, 100), "lab": (200, 400, 200),
    "depot": (20000, 40000), "silo": (20000, 20000, 1000), "nanite": (10**6, 500000, 10**5),
    "terraformer": (0, 50000, 100000, 1000), "dock": (1000, 0, 250, 125),
    # technologies
    "energy": (0, 800, 400), "laser": (200, 100), "ion": (1000, 300, 100),
    "hyperspace": (0, 4000, 2000), "plasma": (2000, 4000, 1000),
    "combustion": (400, 0, 600), "impulse": (2000, 4000, 600), "hyperdrive": (10000, 20000, 6000),
    "espionage": (200, 1000, 200), "computer": (0, 400, 600), "astro": (4000, 8000, 4000),
    "intergalactic": (240000, 400000, 160000), "graviton": (0, 0, 0, 300000),
    "weapons": (800, 200), "shield": (200, 600), "armour": (1000,)
    # ships

    # defenses
}

def can_build(res, cost):
    return all(res[key] >= value for key, value in cost.items() if value > 0)

def needed_solar(metal, crystal, deut):
    """Needed solar to power mines."""
    metal_ene = ((10 * metal * 1.1**metal) // 1) + 1 # metal consumption
    crystal_ene = ((10 * crystal * 1.1**crystal) // 1) + 1 # crystal consumption
    deut_ene = ((20 * deut * 1.1**deut) // 1) + 1 # deut consumption
    total_ene = metal_ene + crystal_ene + deut_ene

    solar_lvl = 1
    while int(20 * solar_lvl * 1.1**solar_lvl) < total_ene: solar_lvl += 1

    return solar_lvl

def build_time(building, level, storage=False, redesigned=True, robots=0, nanites=0, uni_speed=1):
    """Time (in seconds) it takes to build something."""
    cost = build_cost(building, level, is_storage=storage)
    res = cost["metal"] + cost["crystal"]
    time = res / (2500 * (1 + robots) * (2 ** nanites) * uni_speed)
    if redesigned: time *= 2 / 7

    return max(time * 3600, 1)

def cost(building, level, is_storage=False):
    """Calculate how much building/researching a certain level costs."""
    def cost(*args):
        if building in ["metal", "deuterium", "solar", "fusion"]: exp = 1.5
        elif building == "crystal": exp = 1.6
        elif building == "astro": exp = 1.75
        else: exp = 2

        return dict(zip(["metal", "crystal", "deuterium", "energy"],
                        [arg * exp ** (level - 1) for arg in args] + [0] * (5 - len(args))))

    if is_storage: building += "_sto"
    return cost(*base_cost[building])

def research_time(tech, level, lab=0):
    """Time to research a tech. If you have 'intergalactic research network'
    level needs to be the sum of the levels."""
    pass

def distance(start, dest):
    """The distance between two planets. Both arguments must be 3 tuples of the coordinates"""
    if start[0] != dest[0]: # different galaxies
        return 20000 * abs(start[0] - dest[0])
    elif start[1] != dest[1]: # different solar systems
        return 2700 + 95 * abs(start[1] - dest[1])
    else:
        return 1000 + 5 * abs(start[2] - dest[2])
