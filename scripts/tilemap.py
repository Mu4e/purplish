import pygame as pg
from pygame.sprite import Sprite
from pygame import Vector2 as Vec
import json, copy, os

NEIGHBOR_OFFSETS = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 0), (0, 1), (1, -1), (1, 0), (1, 1)]
PHYSICS_TILES = {'grass', 'stone', 'grassystone', 'water'}


class Tilemap:
    def __init__(self, game, tile_size=16):
        self.game = game
        self.tile_size = tile_size
        self.tilemap = {}
        self.offgrid_tiles = []
    
    def copy(self):
        return copy.deepcopy(self.tilemap), copy.deepcopy(self.offgrid_tiles)

    def load(self, path):
        with open(path, 'r') as f:
            map_data = json.load(f)
            self.tilemap = map_data['tilemap']
            self.offgrid_tiles = map_data['offgrid']

    def get_map_edges(self):
        x_coords = set()
        y_coords = set()
        for tile_info in self.tilemap.values():
            pos = tile_info['pos']
            x_coords.add(pos[0])
            y_coords.add(pos[1])
        max_right = max(x_coords) * 16
        max_left = min(x_coords) * 16
        max_down = max(y_coords) * 16
        return max_right, max_left, max_down

        
    def save(self, filepath):
        with open(filepath, 'w') as f:
            json.dump({'tilemap': self.tilemap, 'offgrid': self.offgrid_tiles}, f)

    def extract(self, tv_pairs: list, keep=False):
        matches = []
        for tile in self.offgrid_tiles.copy():
            if (tile['type'], tile['variant']) in tv_pairs:
                matches.append(tile.copy())
                if not keep:
                    self.offgrid_tiles.remove(tile)
        for loc in copy.deepcopy(self.tilemap):
            tile = self.tilemap[loc]
            if (tile['type'], tile['variant']) in tv_pairs:
                matches.append(tile)
                matches[-1]['pos'][0] *= self.tile_size
                matches[-1]['pos'][1] *= self.tile_size
                if not keep:
                    del self.tilemap[loc]
        return matches

    
    def edge_check(self, mask_rect):
        left_check = False
        right_check = False
        check_below_l = (mask_rect.x // self.tile_size, mask_rect.bottom // self.tile_size + 1)
        check_below_r = (mask_rect.x // self.tile_size + 1, mask_rect.bottom // self.tile_size + 1)
        # check_below = [check_below_l, check_below_r]
        left_tile_loc = str((int(check_below_l[0]), int(check_below_l[1])))
        right_tile_loc = str((int(check_below_r[0]), int(check_below_r[1])))
        if left_tile_loc not in self.tilemap:
            left_check = True
        if right_tile_loc not in self.tilemap:
            right_check = True
        return left_check, right_check
    

    def neighbor_tiles(self, pos, size):
        grid_pos = (int(pos.x // self.tile_size), int(pos.y // self.tile_size))
        check_positions = [grid_pos]
        if size[0] > self.tile_size and size[1] > self.tile_size:
            check_positions.append((int(grid_pos[0] + size[0] // self.tile_size), int(grid_pos[1] + size[1] // self.tile_size)))
        elif size[0] > self.tile_size:
            extra_size_x = int(size[0] // self.tile_size)
            for i in range(extra_size_x):
                check_positions.append((grid_pos[0] + i + 1, grid_pos[1]))
        elif size[1] > self.tile_size:
            extra_size_y = int(size[1] // self.tile_size)
            for i in range(extra_size_y):
                check_positions.append((grid_pos[0], grid_pos[1] - i - 1))
        tiles = []
        for position in check_positions:
            tile_loc = (position[0], position[1])
            for offset in NEIGHBOR_OFFSETS:
                check_loc = str((tile_loc[0] + offset[0], tile_loc[1] + offset[1]))
                if check_loc in self.tilemap:
                    tiles.append(self.tilemap[check_loc])
        return tiles
    
    def neighbor_physics_rects(self, pos, size=(16, 16)):
        rects = []
        for tile in self.neighbor_tiles(pos, size):
            if tile['type'] in PHYSICS_TILES:
                rects.append(pg.Rect(tile['pos'][0] * self.tile_size, tile['pos'][1] * self.tile_size, self.tile_size, self.tile_size))
        return rects

    def water_check(self, pos):
        feet_tile_loc = str((pos[0], pos[1]))
        if feet_tile_loc in self.tilemap and self.tilemap[feet_tile_loc]['type'] == 'water':
            return pos
    
    def render(self, surf, offset=(0, 0)):
        for tile in self.offgrid_tiles:
            surf.blit(self.game.tile_dict[tile['type']][tile['variant']], (tile['pos'][0] - offset[0], tile['pos'][1] - offset[1]))

        for x in range(int(offset[0] // self.tile_size), (int(offset[0] + surf.get_width()) // self.tile_size + 1)):
            for y in range(int(offset[1] // self.tile_size), (int(offset[1] + surf.get_height()) // self.tile_size + 1)):
                loc = str((x, y))
                if loc in self.tilemap:
                    tile = self.tilemap[loc]
                    surf.blit(self.game.tile_dict[tile['type']][tile['variant']], (tile['pos'][0] * self.tile_size - offset[0], tile['pos'][1] * self.tile_size - offset[1]))
    

