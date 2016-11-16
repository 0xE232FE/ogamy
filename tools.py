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
    """not working. need to round stuff and add all the other buildings"""
    res = {"metal": (60, 15), "crystal": (48, 24), "solar": (75, 30)}
    def cost(*args):
        exp = 1.5 if building == "metal" else 1.6
        return dict(zip(["metal", "crystal", "deut", "solar"], [arg*exp**(level -1) for arg in args]))
    return cost(*res[building])

def distance(start, dest):
    """The distance between two planets. Both arguments must 3 tuples."""
    if start[0] != dest[0]: # different galaxies
        return 20000 * abs(start[0] - dest[0])
    elif start[1] != dest[1]: # different solar systems
        return 2700 + 95 * abs(start[1] - dest[1])
    else:
        return 1000 + 5 * abs(start[2] - dest[2])
