import pygame as pg
from perlin_noise import PerlinNoise
import random, json

SURFACE_TILES = ['grass', 'stone', 'grassystone']
MAX_Y = 6
ENEMY_VARIANTS = [4, 5, 6]
ENEMY_WEIGHTS = [5, 2, 1]
AUTOTILE_NEIGHBORS = [(-1, 0), (0, -1), (0, 1), (1, 0)]
AUTOTILE_DIAGONALS = [(-1, -1), (1, -1), (-1, 1), (1, 1)]
AUTOTILE_TYPES = {'grass', 'stone', 'grassystone', 'bg_grass'}
AUTOTILE_MAP_BASE = {
    tuple(sorted([(1, 0), (0, 1)])): 0,
    tuple(sorted([(1, 0), (0, 1), (-1, 0)])): 1,
    tuple(sorted([(-1, 0), (0, 1)])): 2,
    tuple(sorted([(-1, 0), (0, -1), (0, 1)])): 3,
    tuple(sorted([(-1, 0), (0, -1)])): 4,
    tuple(sorted([(-1, 0), (0, -1), (1, 0)])): 5,
    tuple(sorted([(1, 0), (0, -1)])): 6,
    tuple(sorted([(1, 0), (0, -1), (0, 1)])): 7,
    tuple(sorted([(1, 0), (-1, 0), (0, 1), (0, -1)])): 8,
    tuple(sorted([(1, 0), (-1, 0)])): 1,
    tuple(sorted([(-1, 0)])): 2,
    tuple(sorted([(0, -1), (0, 1)])): 3,
    tuple(sorted([(0, -1)])): 5
}
AUTOTILE_MAP_CORNERS = {
    9: {'exists': tuple(sorted([(-1, 1), (-1, 0), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)])), 'empty': tuple(sorted([(-1, -1)]))},
    10: {'exists': tuple(sorted([(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, 1), (1, 0)])), 'empty': tuple(sorted([(1, -1)]))}
}


def tile_types_gen():
    current_type = None
    while True:
        tile_type = random.choice(SURFACE_TILES)
        if tile_type != current_type:
            yield tile_type
            current_type = tile_type

def check_water_boundaries(loc_list, index):
    upcoming_ys = []
    for i in range(0, 11):
        upcoming_ys.append(loc_list[index + i][1])
    for _ in range(len(upcoming_ys) - 1):
        if upcoming_ys[_] > upcoming_ys[_ + 1]:
            return True
        if upcoming_ys[_] < upcoming_ys[_ + 1]:
            return False
        elif _ == len(upcoming_ys) - 2:
            return False

def check_platform_space(loc_list, index, plat_length):
    surface_heights = set()
    for n in range(-3, plat_length + 1):
        ground_height = loc_list[index + n][1]
        surface_heights.add(ground_height)
    fin_sorted = sorted(surface_heights)
    # smallest y is highest
    return fin_sorted[0]

def convert_strtup_to_list(string) -> list:
    tuple_string = string.strip('()').split(', ')
    return [int(tuple_string[0]), int(tuple_string[1])]


class RandomMapGenerator:
    def __init__(self, game):
        self.tiles_dict = game.tile_dict.copy()
        self.tilemap = game.tilemap  # tilemap: dict {"(0, 1)"": {'type': ...} ... }
        # offgrid: list [{'type: ...} ... ]
    
    def make_noise(self):
        y_values = []
        noise = PerlinNoise(octaves=80, seed=10)
        xpix, ypix = 100, 100
        y_line = random.randint(1, xpix)
        height_values = [noise([y_line, j/ypix]) for j in range(xpix)]
        for i in height_values:
            y_values.append(round(i * 10))
        return y_values
    
    def adjust_singles(self, y_list):
        mod = 0
        for i in range(1, len(y_list) - 1):
            if y_list[i+mod] != (y_list[i+mod-1] and y_list[i+mod+1]):
                y_list.insert(i+1+mod, y_list[i])
                mod += 1
                for _ in range(5):
                    if random.randint(1, 4) == 1:
                        y_list.insert(i+1+mod, y_list[i+mod+1])
                        mod += 1
    
    def adjust_heights(self, y_list):
        mod = 0
        for i in range(len(y_list) - 1):
            diff = y_list[i+mod] - y_list[i+mod+1]
            if abs(diff) >= 4:
                y_list.insert(i+1+mod, y_list[i+mod] - int(abs(diff) / diff / 2))
                y_list.insert(i+2+mod, y_list[i+mod] - int(abs(diff) / diff / 2))
                mod += 2
        for item in y_list:
            if item > MAX_Y:
                y_list.remove(item)
    
    def remove_singles(self, y_list):
        copied_list = []
        for i in range(1, len(y_list) - 1):
            if y_list[i] != y_list[i+1]:
                if y_list[i] == y_list[i-1]:
                    copied_list.append(y_list[i])
            else:
                copied_list.append(y_list[i])
        return copied_list
    
    def adjust_first_last(self, y_list):
        while y_list[0] != y_list[1]:
            y_list.pop(0)
        while y_list[-1] != y_list[-2]:
            y_list.pop()

    def add_x_locs(self, y_list):
        loc_list = []
        for x in range(len(y_list)):
            loc_tup = x, y_list[x]
            loc_list.append(loc_tup)
        return loc_list
    
    def make_noise_surface(self):
        ys_list = self.make_noise()
        self.adjust_singles(ys_list)
        self.adjust_heights(ys_list)
        final_ys_list = self.remove_singles(ys_list)
        self.adjust_first_last(final_ys_list)
        locations_list = self.add_x_locs(final_ys_list)
        # [(0, 1), (1, 1) ... ]
        return locations_list


    def set_surface_tile_types(self, loc_list):
        tile_picker = tile_types_gen()
        can_change_type = False
        t_type = next(tile_picker)
        tile_before_water = 0
        for index in range(len(loc_list)):
            water_variant = 1
            if (index + 1) % 30 == 0:
                can_change_type = True
            if can_change_type and index < len(loc_list) - 10:
                if loc_list[index][1] != loc_list[index - 1][1] and t_type != 'water':
                    t_type = next(tile_picker)
                    can_change_type = False
            if 10 < index < len(loc_list) - 10:
                if loc_list[index][1] == loc_list[index + 1][1] and loc_list[index][1] > 0 and loc_list[index][1] > loc_list[index - 1][1]:
                    if t_type != 'water' and random.randint(1, 2) == 1:
                        if check_water_boundaries(loc_list, index):
                            t_type = 'water'
            if t_type == 'water':
                tile_before_water += 1
                if loc_list[index][1] < loc_list[index - 1][1]:
                    t_type = self.tilemap.tilemap[str(loc_list[index - tile_before_water])]['type']
                    tile_before_water = 0
                elif index < len(loc_list) - 1 and loc_list[index][1] != loc_list[index + 1][1]:
                    water_variant = 2
            loc = loc_list[index]
            if t_type == 'water':
                if tile_before_water == 1:
                    self.tilemap.tilemap[str(loc)] = {'type': t_type, 'variant': 0, 'pos': [loc[0], loc[1]]}
                else:
                    self.tilemap.tilemap[str(loc)] = {'type': t_type, 'variant': water_variant, 'pos': [loc[0], loc[1]]}
            else:
                self.tilemap.tilemap[str(loc)] = {'type': t_type, 'variant': 1, 'pos': [loc[0], loc[1]]}

    def create_floating_platforms(self, loc_list):
        tile_picker = tile_types_gen()
        tile_type = next(tile_picker)
        platform_length = random.randint(2, 8)
        platform_height = random.randint(2, 5)
        placing = False
        for index in range(6, len(loc_list) - 10):
            if (index + 1) % 20 == 0:
                tile_type = next(tile_picker)
            loc = loc_list[index]  # (x, y)
            if random.randint(1, 4) == 1 and not placing:
                plat_bottom = loc[1] - random.randint(3, 8)
                plat_loc = loc[0], plat_bottom
                lowest_y = check_platform_space(loc_list, index, platform_length)
                if lowest_y > plat_bottom + 2:
                    placing = True
            if placing:
                for x in range(platform_length):
                    for y in range(platform_height):
                        self.tilemap.tilemap[str((plat_loc[0] + x, plat_loc[1] - y))] = {'type': tile_type, 'variant': 1, 'pos': [plat_loc[0] + x, plat_loc[1] - y]}
                placing = False
                platform_length = random.randint(2, 8)
                platform_height = random.randint(2, 5)
    
    def fill_ground(self, loc_list):
        for loc in loc_list:
            t_type = self.tilemap.tilemap[str(loc)]['type']
            for y in range(loc[1] + 1, MAX_Y + 1):
                self.tilemap.tilemap[str((loc[0], y))] = {'type': t_type, 'variant': 1, 'pos': [loc[0], y]}
    
    def check_flat_surface(self, tile_loc, length: int):
        t_loc = convert_strtup_to_list(tile_loc)
        cur_x = t_loc[0]
        cur_y = t_loc[1]
        if length == 2:
            locs_to_check = [str((cur_x + 1, cur_y))]
            locs_to_exclude = [str((cur_x + 1, cur_y - 1))]
        elif length == 3:
            locs_to_check = [str((cur_x - 1, cur_y)), str((cur_x + 1, cur_y))]
            locs_to_exclude = [str((cur_x - 1, cur_y - 1)), str((cur_x + 1, cur_y - 1))]
        elif length == 4:
            locs_to_check = [str((cur_x + 1, cur_y)), str((cur_x + 2, cur_y)), str((cur_x + 3, cur_y)), str((cur_x + 4, cur_y))]
            locs_to_exclude = [str((cur_x + 1, cur_y - 1)), str((cur_x + 2, cur_y - 1)), str((cur_x + 3, cur_y - 1)), str((cur_x + 4, cur_y - 1))]
        if all(loc in self.tilemap.tilemap for loc in locs_to_check):
            if not any(exloc in self.tilemap.tilemap for exloc in locs_to_exclude):
                return True
        else:
            return False

    def place_spawnpoints(self, loc_list):
        player_placed = False
        portal_placed = False
        r_chest_placed = False
        enemy_cooldown = 30
        n_chest_cooldown = 50
        t_x = set()
        t_y = set()
        for location in self.tilemap.tilemap.copy():
            t_x.add(convert_strtup_to_list(location)[0])
            t_y.add(convert_strtup_to_list(location)[1])
        tilemap_length = sorted(t_x, reverse=True)[0]
        tilemap_height = sorted(t_y)[0]
        for index in range(len(loc_list)):
            loc = loc_list[index]
            if 4 < index < 12 and self.check_flat_surface(str(loc_list[index]), 2) and not player_placed:
                self.tilemap.tilemap[str((loc[0], loc[1] - 1))] = {'type': 'spawnpoint', 'variant': 0, 'pos': [loc[0], loc[1] - 1]}
                player_placed = True
        for b_index in range(len(loc_list) - 4, len(loc_list) - 16, -1):
            b_loc = loc_list[b_index]
            if self.check_flat_surface(str(loc_list[b_index]), 3) and not portal_placed:
                self.tilemap.tilemap[str((b_loc[0], b_loc[1] - 2))] = {'type': 'spawnpoint', 'variant': 1, 'pos': [b_loc[0], b_loc[1] - 2]}
                portal_placed = True
        for location in self.tilemap.tilemap.copy():
            t_loc = convert_strtup_to_list(location)
            check_ys = [str((t_loc[0], t_loc[1] - 1)), str((t_loc[0], t_loc[1] - 2))]
            if not any(check in self.tilemap.tilemap for check in check_ys):
                if not r_chest_placed and t_loc[1] == tilemap_height:
                    self.tilemap.tilemap[str((t_loc[0] + 1, t_loc[1] - 1))] = {'type': 'spawnpoint', 'variant': 3, 'pos': [t_loc[0] + 1, t_loc[1] - 1]}
                    r_chest_placed = True
                if 15 < t_loc[0] < tilemap_length - 16:
                    if self.tilemap.tilemap[str((t_loc[0], t_loc[1]))]['type'] != 'water':
                        if self.check_flat_surface(location, 2):
                            if random.randint(1, 4) == 1 and not enemy_cooldown:
                                self.tilemap.tilemap[str((t_loc[0], t_loc[1] - 1))] = {'type': 'spawnpoint', 'variant': random.choices(ENEMY_VARIANTS, ENEMY_WEIGHTS)[0], 'pos': [t_loc[0], t_loc[1] - 1]}
                                enemy_cooldown = 30
                        if self.check_flat_surface(location, 3):
                            if random.randint(1, 8) == 1 and not n_chest_cooldown:
                                self.tilemap.tilemap[str((t_loc[0], t_loc[1] - 1))] = {'type': 'spawnpoint', 'variant': 2, 'pos': [t_loc[0], t_loc[1] - 1]}
                                n_chest_cooldown = 60
            enemy_cooldown = max(enemy_cooldown - 1, 0)
            n_chest_cooldown = max(n_chest_cooldown - 1, 0)
            if not player_placed:
                raise Exception("Player spawnpoint not in map!")
            if not portal_placed:
                raise Exception("No portal to exit the map!")
    
    def place_decor(self):
        for loc in self.tilemap.tilemap:
            tile = self.tilemap.tilemap[loc]
            list_loc = convert_strtup_to_list(loc)
            check_y = list_loc[0], list_loc[1] - 1
            if str(check_y) not in self.tilemap.tilemap:
                offgrid_loc = tile['pos'][0] * 16 + random.randint(1, 3), (tile['pos'][1] - 1) * 16
                if tile['type'] == 'grass':
                    if random.randint(1, 3) == 1:
                        self.tilemap.offgrid_tiles.append({"type": "decor", "variant": random.choice(range(0, 8)), "pos": [offgrid_loc[0], offgrid_loc[1]]})
                if tile['type'] == 'stone':
                    if random.randint(1, 4) == 1:
                        self.tilemap.offgrid_tiles.append({"type": "decor", "variant": random.choice(range(8, 12)), "pos": [offgrid_loc[0], offgrid_loc[1]]})
                if tile['type'] == 'grassystone':
                    if random.randint(1, 5) == 1:
                        self.tilemap.offgrid_tiles.append({"type": "decor", "variant": random.choice(list(range(11, 15)) + [6, 7]), "pos": [offgrid_loc[0], offgrid_loc[1]]})

    def check_flat_bottom(self, cd_list, index, length):
        cur_x = cd_list[index][0]
        cur_y = cd_list[index][1]
        if cur_y != MAX_Y and [cur_x, cur_y + 1] not in cd_list:
            if length == 2:
                locs_to_check = [[cur_x, cur_y], [cur_x + 1, cur_y]]
            elif length == 3:
                locs_to_check = [[cur_x, cur_y], [cur_x + 1, cur_y], [cur_x + 2, cur_y]]
            elif length == 4:
                locs_to_check = [[cur_x, cur_y], [cur_x + 1, cur_y], [cur_x + 2, cur_y], [cur_x + 3, cur_y]]
            if all(loc in cd_list for loc in locs_to_check):
                return True
        else:
            return False

    def place_bg_decor(self, loc_list):
        tree_cooldown = 0
        for ind in range(10, len(loc_list) - 15):
            if self.check_flat_surface(str(loc_list[ind]), 4) and not tree_cooldown:
                if random.randint(1, 2) == 1:
                    offgrid_loc = loc_list[ind][0] * 16 + random.randint(1, 5), loc_list[ind][1] * 16 - 147
                    self.tilemap.offgrid_tiles.append({"type": "bg_foliage", "variant": 0, "pos": [offgrid_loc[0], offgrid_loc[1]]})
                    tree_cooldown = 15
            tree_cooldown = max(tree_cooldown - 1, 0)
        all_coords = [tile['pos'] for tile in self.tilemap.tilemap.values()]
        # list containing lists
        all_coords.sort()
        for i in range(10, len(all_coords) - 15):
            offgrid_loc = all_coords[i][0] * 16, (all_coords[i][1] + 1) * 16
            if all_coords[i][1] < -2:
                if self.check_flat_bottom(all_coords, i, 3) and random.randint(1, 5) == 1:
                    self.tilemap.offgrid_tiles.append({"type": "bg_foliage", "variant": random.randint(1, 3), "pos": [offgrid_loc[0] + random.randint(-2, 2), offgrid_loc[1] - 5]})
                elif self.check_flat_bottom(all_coords, i, 4) and random.randint(1, 8) == 1:
                    self.tilemap.offgrid_tiles.append({"type": "bg_foliage", "variant": random.randint(4, 5), "pos": [offgrid_loc[0] + random.randint(-2, 2), offgrid_loc[1]]})
        t_x = set()
        t_y = set()
        for location in self.tilemap.tilemap:
            t_x.add(int(convert_strtup_to_list(location)[0]))
            t_y.add(int(convert_strtup_to_list(location)[1]))
        tilemap_x_locs = sorted(t_x)
        tilemap_length = len(t_x)
        tilemap_height = sorted(t_y)[0]
        bg_grass_length = random.randint(2, 6)
        bg_grass_height = random.randint(2, 4)
        placing = False
        for index in range(20, tilemap_length - 10):
            g_loc_x = tilemap_x_locs[index]
            g_loc_y = random.randint(tilemap_height - 1, tilemap_height + 15)
            offgrid_g_loc = g_loc_x * 16, g_loc_y * 16
            if random.randint(1, 11) == 1 and not placing:
                    placing = True
            if placing:
                for x in range(bg_grass_length):
                    for y in range(bg_grass_height):
                        self.tilemap.offgrid_tiles.append({"type": "bg_grass", "variant": 1, "pos": [offgrid_g_loc[0] + x * 16, offgrid_g_loc[1] - y * 16]})
                placing = False
                bg_grass_length = random.randint(2, 6)
                bg_grass_height = random.randint(2, 4)
    
    def auto_tile(self):
        for loc in self.tilemap.tilemap:
            tile = self.tilemap.tilemap[loc]
            existing_neighbors = set()
            empty_neighbors = set()
            if tile['type'] in AUTOTILE_TYPES:
                for shift in AUTOTILE_NEIGHBORS:
                    check_loc = str((tile['pos'][0] + shift[0], tile['pos'][1] + shift[1]))
                    if check_loc in self.tilemap.tilemap:
                        if self.tilemap.tilemap[check_loc]['type'] == tile['type']:
                            existing_neighbors.add(shift)
                    else:
                        empty_neighbors.add(shift)
                basic_neighbors = tuple(sorted(existing_neighbors))
                if basic_neighbors in AUTOTILE_MAP_BASE:
                    tile['variant'] = AUTOTILE_MAP_BASE[basic_neighbors]
                for shift in AUTOTILE_DIAGONALS:
                    check_loc = str((tile['pos'][0] + shift[0], tile['pos'][1] + shift[1]))
                    if check_loc in self.tilemap.tilemap:
                        if self.tilemap.tilemap[check_loc]['type'] == tile['type']:
                            existing_neighbors.add(shift)
                    else:
                        empty_neighbors.add(shift)
                all_neighbors = tuple(sorted(existing_neighbors))
                empty_neighbors = tuple(sorted(empty_neighbors))
                for variant, condition in AUTOTILE_MAP_CORNERS.items():
                    if all_neighbors == condition['exists'] and empty_neighbors == condition['empty']:
                        tile['variant'] = int(variant)
            tile_above = str((tile['pos'][0], tile['pos'][1] - 1))
            if self.tilemap.tilemap.get(tile_above) and self.tilemap.tilemap[tile_above]['type'] == 'water':
                tile['variant'] = 3
        og_grass_tiles = []
        og_grass_locs = []
        copied_og_tiles = self.tilemap.offgrid_tiles.copy()
        for index in range(len(copied_og_tiles)):
            og_tile = copied_og_tiles[index]
            if og_tile['type'] in AUTOTILE_TYPES:
                self.tilemap.offgrid_tiles.remove(og_tile)
                og_grass_tiles.append(og_tile)
                og_grass_locs.append(og_tile['pos'])
        for grass_tile in og_grass_tiles:
            og_neighbors = set()
            for shift in AUTOTILE_NEIGHBORS:
                check_og_loc = [grass_tile['pos'][0] + shift[0] * 16, grass_tile['pos'][1] + shift[1] * 16]
                if check_og_loc in og_grass_locs:
                    og_neighbors.add(shift)
            og_neighbors = tuple(sorted(og_neighbors))
            if og_neighbors in AUTOTILE_MAP_BASE:
                    grass_tile['variant'] = AUTOTILE_MAP_BASE[og_neighbors]
            self.tilemap.offgrid_tiles.insert(0, grass_tile)



    def generate_random_map(self):
        surf_list = self.make_noise_surface()
        self.set_surface_tile_types(surf_list)
        self.fill_ground(surf_list)
        self.create_floating_platforms(surf_list)
        while True:
            try:
                self.place_spawnpoints(surf_list)
            except:
                print("map_gen_error")
            else:
                break
        self.place_bg_decor(surf_list)
        self.place_decor()
        self.auto_tile()





    
    