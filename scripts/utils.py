import json, glob, os
import pygame as pg
from scripts.tilemap import Tilemap

def get_lang_strings(filepath, language) -> dict:
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data[language]

def load_image(filepath) -> pg.Surface:
    image = pg.image.load(filepath).convert_alpha()
    return image

def load_images(*folders) -> list:
    target_dir = os.path.join(*folders)
    images_list = os.listdir(target_dir)
    images_list.sort()
    img_surf_list = []
    for image in images_list:
        rel_path = os.path.join(target_dir, image)
        img_surf_list.append(load_image(rel_path))
    return img_surf_list

def load_images_dict(*folders) -> dict:
    target_dir = os.path.join(*folders)
    image_list = os.listdir(target_dir)
    image_list.sort()
    imgs_dict = {}
    for image in image_list:
        rel_path = os.path.join(target_dir, image)
        img_name = os.path.splitext(image)[0]
        img_surf = load_image(rel_path)
        imgs_dict[img_name] = img_surf
    return imgs_dict

def get_animations(path, img_type, *args) -> dict:
    images_dict = {}
    type_dir = os.path.join(path, img_type)
    action_list = os.listdir(type_dir)
    action_list.sort()
    for action in action_list:
        action_dir = os.path.join(type_dir, action)
        image_list = os.listdir(action_dir)
        image_list.sort()
        surf_list = []
        for image in image_list:
            rel_path = os.path.join(action_dir, image)
            img_surf = load_image(rel_path)
            surf_list.append(img_surf)
        images_dict[action] = surf_list
    animations_dict = {}
    for (action, length, loop) in args:
        animations_dict[action] = (Animation(images_dict[action], length, loop))
    return animations_dict

def load_tiles(path) -> dict:
    root_dir = os.path.join(path, 'tiles')
    image_list = glob.glob('*/*.png', root_dir=root_dir)
    image_list.sort()
    # image_list: ['decor\\00.png', ...]
    # {'grass': 9}
    type_no_dict = {}
    for image in image_list:
        img_type = os.path.dirname(image)
        type_no_dict[img_type] = image_list.count(img_type)
    # {'grass': [<surf>, <surf> ...]}
    tiles_dict = {}
    for tile_type in type_no_dict.keys():
        variant_surfs = []
        for image in image_list:
            img_type = os.path.dirname(image)
            full_path = os.path.join(root_dir, image)
            if tile_type == img_type:
                variant_surfs.append(load_image(full_path))
        tiles_dict[tile_type] = variant_surfs
    return tiles_dict

def check_existing_save(save_folder, map_fn, data_fn):
    if os.path.exists(save_folder):
        check_list = [os.path.join(save_folder, map_fn), os.path.join(save_folder, data_fn)]
        return [(fp, os.path.exists(fp)) for fp in check_list]
    else:
        os.mkdir(save_folder)


def save_current_map(game, save_dir, fn):
    path = os.path.join(save_dir, fn)
    tilemap = Tilemap(game)
    tilemap.tilemap, tilemap.offgrid_tiles = game.tilemap.copy()
    player_pos = int(game.player.pos.x // 16), int(game.player.pos.y // 16)
    player_loc = str(tuple(player_pos))
    tilemap.tilemap[player_loc] = {"type": "spawnpoint", "variant": 0, "pos": [player_pos[0], player_pos[1]]}
    for enemy in game.enemies:
        enemy_pos = int(enemy.pos.x // 16), int(enemy.pos.y // 16)
        enemy_loc = str(tuple(enemy_pos))
        tilemap.tilemap[enemy_loc] = {"type": "spawnpoint", "variant": enemy.variant, "pos": [enemy_pos[0], enemy_pos[1]]}
    for chest in game.chests:
        chest_pos = int(chest.pos.x // 16), int(chest.pos.y // 16)
        chest_loc = str(tuple(chest_pos))
        tilemap.tilemap[chest_loc] = {"type": "spawnpoint", "variant": chest.variant, "pos": [chest_pos[0], chest_pos[1]]}
    for portal in game.portals:
        portal_pos = int(portal.pos.x // 16 + 1), int(portal.pos.y // 16)
        portal_loc = str(tuple(portal_pos))
        tilemap.tilemap[portal_loc] = {"type": "spawnpoint", "variant": 1, "pos": [portal_pos[0], portal_pos[1]]}
    with open(path, 'w') as f:
        json.dump({'tilemap': tilemap.tilemap, 'offgrid': tilemap.offgrid_tiles}, f)
    return path

        
      
class Animation:
    def __init__(self, images, img_dur=5, loop=True):
        self.images = images
        self.loop = loop
        self.dur = img_dur
        self.done = False
        self.frame = 0
    
    def copy(self):
        return Animation(self.images, self.dur, self.loop)
    
    def update(self):
        total_frames = self.dur * len(self.images)
        if self.loop:
            self.frame = (self.frame + 1) % total_frames
        else:
            self.frame = min(self.frame + 1, total_frames - 1)
            if self.frame >= total_frames - 1:
                self.done = True
    
    def cur_img(self) -> pg.Surface:
        # gets current image surface for frame.
        image_index = int(self.frame / self.dur)
        return self.images[image_index]



            

