import math

def needed_solar(metal, crystal, deut):
    metal_ene = ((10 * metal * 1.1**metal) // 1) + 1 # metal consumption
    crystal_ene = ((10 * crystal * 1.1**crystal) // 1) + 1 # crystal consumption
    deut_ene = ((20 * deut * 1.1**deut) // 1) + 1 # deut consumption
    total_ene = metal_ene + crystal_ene + deut_ene

    solar_lvl = 1
    while (20 * solar_lvl * 1.1**solar_lvl) // 1 < total_ene: solar_lvl += 1

    return solar_lvl

def build_time(building, level, is_storage=False): pass

def build_cost(building, level, is_storage=False):
    """Calculate how much building a certain level costs."""
    base_cost = {
        # mines and stuff
        "metal": (60, 15), "crystal": (48, 24), "solar": (75, 30),
        "solar": (75, 30), "fusion": (900, 360, 180),
        # station buildings
        "robots": (400, 120, 200), "shipyard": (400, 200, 100), "lab": (200, 400, 200),
        "depot": (20000, 40000), "silo": (20000, 20000, 1000), "nanite": (10**6, 500000, 10**5),
        "terraformer": (0, 50000, 100000, 1000), "dock": (1000, 0, 250, 125)}
    base_sto = {"metal": (1000), "crystal": (1000, 500), "deuterium": (1000, 1000)}

    def cost(*args):
        if building in res.keys():
            if building == "crystal" and not is_storage: exp = 1.6
            else: exp = 1.5
        else: exp = 2

        return dict(zip(["metal", "crystal", "deuterium", "solar", "dm"],
                        [arg * exp ** (level - 1) for arg in args] + [0] * (5 - len(args))))

    if is_storage: return cost(*base_sto[building])
    else: return cost(*base_cost[building])

def distance(start, dest):
    """The distance between two planets. Both arguments must be 3 tuples of the coordinates"""
    if start[0] != dest[0]: # different galaxies
        return 20000 * abs(start[0] - dest[0])
    elif start[1] != dest[1]: # different solar systems
        return 2700 + 95 * abs(start[1] - dest[1])
    else:
        return 1000 + 5 * abs(start[2] - dest[2])
