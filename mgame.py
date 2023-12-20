import pygame as pg
from pygame import Vector2 as Vec
import sys, os, math
from scripts.utils import *
from scripts.gameutils import *
from scripts.menus import MainMenu, OptionsMenu, HelpMenu, PauseMenu, Hud, GameOver, StatsMenu
from scripts.stars import Stars
from scripts.tilemap import Tilemap
from scripts.entities import *
from scripts.particle import *
from scripts.map_generator import RandomMapGenerator
from scripts.soundmanager import MusicManager, SfxManager


SCREEN_RES = (960, 720)
DISPLAY_RES = (320, 240)
SCALE_RATIO = DISPLAY_RES[0] / SCREEN_RES[0]
ASSETS_DIR = os.path.join(os.getcwd(), 'assets')
IMAGES_DIR = os.path.join(ASSETS_DIR, 'images')
SOUNDS_DIR = os.path.join(ASSETS_DIR, 'audio')
SAVES_DIR = os.path.join(os.getcwd(), 'savegames')
LOCALIZATION = os.path.join(ASSETS_DIR, 'localization.json')
SAVE_MAP_NAME = 'map_47.json'
SAVE_DATA_NAME = 'savegame.json'


class Game:
    def __init__(self):
        pg.init()
        pg.display.set_caption("Purplish")
        # set final screen
        self.screen = pg.display.set_mode(SCREEN_RES, pg.SCALED)
        pg.display.set_icon(load_image(os.path.join(IMAGES_DIR, 'icon.png')))
        # set "internal" screen to first render to
        self.display = pg.Surface(DISPLAY_RES, pg.SRCALPHA)

        self.main_screen_overlay = pg.Surface(SCREEN_RES, pg.SRCALPHA)
        self.screen_overlay = pg.Surface(SCREEN_RES, pg.SRCALPHA)
        self.screen_transition_overlay = pg.Surface(SCREEN_RES, pg.SRCALPHA)

        self.clock = pg.time.Clock()

        # game assets
        self.player_anims = get_animations(IMAGES_DIR, 'player', ('idle', 15, True), ('jump', 10, True), ('run', 5, True), ('wallslide', 10, True), ('attack_staff', 3, False), ('die', 15, False))
        self.enemy_slg_anims = get_animations(IMAGES_DIR, 'enemy_sl_g', ('idle', 20, True), ('run', 10, True), ('attack', 3, False), ('jump', 5, False), ('hurt', 30, False), ('die', 2, False))
        self.enemy_sly_anims = get_animations(IMAGES_DIR, 'enemy_sl_y', ('idle', 20, True), ('run', 10, True), ('attack', 5, False), ('hurt', 30, False), ('die', 2, False))
        self.enemy_slr_anims = get_animations(IMAGES_DIR, 'enemy_sl_r', ('idle', 20, True), ('run', 10, True), ('jump', 5, False), ('attack_a', 3, False), ('attack_b', 5, False), ('hurt', 30, False), ('die', 2, False))
        self.portal_anims = get_animations(IMAGES_DIR, 'portal', ('idle', 15, True))
        self.particle_anims = get_animations(IMAGES_DIR, 'particles', ('dash', 6, False), ('splash', 5, False))
        self.portrait_anims = get_animations(IMAGES_DIR, 'portrait', ('idle', 10, True), ('faces', 20, False))
        self.projectile_dict = load_images_dict(IMAGES_DIR, 'projectiles')
        self.loot_dict = load_images_dict(IMAGES_DIR, 'loot')
        self.star_images = load_images(IMAGES_DIR, 'stars')
        self.ui_dict = load_images_dict(IMAGES_DIR, 'ui')
        self.hud_dict = load_images_dict(IMAGES_DIR, 'hud')
        self.tile_dict = load_tiles(IMAGES_DIR)
        self.player_emote = load_images(IMAGES_DIR, 'emote')

        self.music_manager = MusicManager(self, SOUNDS_DIR)
        self.sfx_manager = SfxManager(SOUNDS_DIR)

        self.font_path = os.path.join(ASSETS_DIR, 'neodgm.ttf')
        self.language = "kor"
        self.lang_strings = get_lang_strings(LOCALIZATION, self.language)
        self.lang_changed = False

        self.playing = False

        self.tilemap = Tilemap(self)
        self.map_left_boundary = 0
        self.map_right_boundary = 0
        self.map_bottom_boundary = 0

        self.background = self.ui_dict['background']
        self.stars = Stars(self.star_images, 40)

        self.camera = Vec(0, 0)
        self.players = OffsetSpriteGroup()
        self.player = Player(self, (20, 20), (12, 16), self.player_anims)
        self.players.add(self.player)
        # bool values (e.g. 1, 0)
        self.x_movement = [False, False]
        self.y_direction = [False, False]
        self.into_portal = False
        self.new_record = False

        # save data
        self.stage_no = 0
        self.cleared_maps = 0
        self.clear_streak = 0
        self.killed_enemies = {'total': 0, 'sl_g': 0, 'sl_y': 0, 'sl_r': 0}
        self.looted_chests = {'total': 0, 'normal': 0, 'rare': 0}
        self.looted_items = {'total': 0, 'normal_loot': 0, 'goo': 0, 'ap': 0, 'hp': 0, 'l_hp': 0, 'l_ap': 0, 'rare_loot': 0, 'max_jump_book': 0, 'max_dash_book': 0, 'max_hp_book': 0, 'max_ap_book': 0, 'fill_ahp': 0, 'gold_goo': 0}
        self.deaths = 0
        self.saved_map = None

        # menus and transitions
        self.initialize_menus()
        self.transition_alpha = 255
        self.fade_state = "fade_in"
        self.fade_midpoint = False
        self.fade_delay = 50
        self.circle_transition_radius = 1
        self.screenshake = 0

        savefiles = check_existing_save(SAVES_DIR, SAVE_MAP_NAME, SAVE_DATA_NAME)
        if savefiles:
            if savefiles[1][1]:
                self.load_save_data(SAVES_DIR, SAVE_DATA_NAME)

        self.enemies = OffsetSpriteGroup()
        self.chests = OffsetSpriteGroup()
        self.portals = OffsetSpriteGroup()
        self.particles = OffsetSpriteGroup()
        self.projectiles = OffsetSpriteGroup()
        self.sparks = OffsetSpriteGroup()
        self.loot = OffsetSpriteGroup()
        self.ap_sparks = OffsetSpriteGroup()
        self.hp_sparks = OffsetSpriteGroup()

    def reset_game_stats(self):
        self.stage_no = 0
        self.cleared_maps = 0
        self.clear_streak = 0
        self.killed_enemies = {'total': 0, 'sl_g': 0, 'sl_y': 0, 'sl_r': 0}
        self.looted_chests = {'total': 0, 'normal': 0, 'rare': 0}
        self.looted_items = {'total': 0, 'normal_loot': 0, 'goo': 0, 'ap': 0, 'hp': 0, 'l_hp': 0, 'l_ap': 0, 'rare_loot': 0, 'max_jump_book': 0, 'max_dash_book': 0, 'max_hp_book': 0, 'max_ap_book': 0, 'fill_ahp': 0, 'gold_goo': 0}
        self.deaths = 0
        self.saved_map = None
        self.initialize_player()

    def initialize_menus(self):
        self.main_screen = True
        self.game_over = False
        self.game_over_delay = 120
        self.g_o = GameOver(self)
        self.stats_menu = False
        self.st_m = StatsMenu(self)
        self.game_paused = False
        self.p_m = PauseMenu(self)
        self.main_menu = True
        self.m_m = MainMenu(self)
        self.options_menu = False
        self.o_m = OptionsMenu(self)
        self.help_menu = False
        self.h_m = HelpMenu(self)
        self.start_game = False

    def initialize_player(self):
        self.players.empty()
        self.player = Player(self, (20, 20), (12, 16), self.player_anims)
        self.players.add(self.player)
    
    def display_help_menu(self):
        self.h_m.update(self)
        self.h_m.render(self.screen_overlay)

    def display_stats_menu(self):
        self.st_m.update(self)
        self.st_m.render(self.screen_overlay)

    def load_main_menu(self):
        self.fade_transition(self.screen_transition_overlay, 5)

        if self.main_menu:
            self.m_m.update(self)
        self.m_m.render(self.main_screen_overlay)

        if self.options_menu:
            self.o_m.update(self)
            self.o_m.render(self.screen_overlay)
            
        if self.help_menu:
            self.display_help_menu()
        
        if self.stats_menu:
            self.display_stats_menu()
    

    def delete_save(self):
        self.fade_state = 'fade_out'
        exists = check_existing_save(SAVES_DIR, SAVE_MAP_NAME, SAVE_DATA_NAME)
        for fp, exist in exists:
            if exist:
                os.remove(fp)
        self.reset_game_stats()
    
    def save_data(self, save_dir, fn):
        filepath = os.path.join(save_dir, fn)
        player_dict = self.player.save_attributes()
        game_stats = {'enemies': self.killed_enemies, 'chests': self.looted_chests, 'items': self.looted_items, 'cleared_num': self.cleared_maps, 'clear_streak': self.clear_streak, 'stage_no': self.stage_no, 'deaths': self.deaths, 'map': self.saved_map}
        with open(filepath, 'w') as f:
            json.dump({'player_stats': player_dict, 'game_stats': game_stats}, f)
        return True

    def load_save_data(self, save_dir, stats_file, reset=False):
        stats = os.path.join(save_dir, stats_file)
        with open(stats, 'r') as f:
            save_data = json.load(f)
            player_data = save_data['player_stats']
            game_stats = save_data['game_stats']
        self.player.load_attributes(player_data, reset)
        self.killed_enemies = game_stats['enemies']
        self.looted_chests = game_stats['chests']
        self.looted_items = game_stats['items']
        self.cleared_maps = game_stats['cleared_num']
        self.stage_no = game_stats['stage_no']
        self.clear_streak = game_stats['clear_streak']
        self.deaths = game_stats['deaths']

    def save_game_data(self, save_map=True):
        if save_map:
            saved_map_dir = save_current_map(self, SAVES_DIR, SAVE_MAP_NAME)
            self.saved_map = saved_map_dir
        else:
            self.saved_map = None
            files = check_existing_save(SAVES_DIR, SAVE_MAP_NAME, SAVE_DATA_NAME)
            if files[0][1]:
                os.remove(os.path.join(SAVES_DIR, SAVE_MAP_NAME))
        self.save_data(SAVES_DIR, SAVE_DATA_NAME)

    def load_existing_map(self):
        map_path = os.path.join(SAVES_DIR, SAVE_MAP_NAME)
        self.tilemap.load(map_path)

    def load_new_map(self):
        path = os.path.join(SAVES_DIR, 'map_99.json')
        self.tilemap = Tilemap(self)
        RandomMapGenerator(self).generate_random_map()
        self.tilemap.save(path)

    def set_map_data(self):
        self.map_right_boundary, self.map_left_boundary, self.map_bottom_boundary = self.tilemap.get_map_edges()
        self.enemies = OffsetSpriteGroup()
        self.chests = OffsetSpriteGroup()
        self.portals = OffsetSpriteGroup()
        for spawnpoint in self.tilemap.extract([('spawnpoint', 0), ('spawnpoint', 1), ('spawnpoint', 2), ('spawnpoint', 3), ('spawnpoint', 4), ('spawnpoint', 5), ('spawnpoint', 6)]):
            if spawnpoint['variant'] == 0:
                self.player.pos = Vec(spawnpoint['pos'])
            elif spawnpoint['variant'] == 1:
                self.portals.add(Portal(self, Vec(spawnpoint['pos'][0] - 8, spawnpoint['pos'][1]), (32, 32), self.portal_anims))
            # always put chests on grid.
            elif spawnpoint['variant'] == 2:
                self.chests.add(NormalChest(self, 'chest_n', 2, Vec(spawnpoint['pos']), (16, 16)))
            elif spawnpoint['variant'] == 3:
                self.chests.add(RareChest(self, 3, Vec(spawnpoint['pos']), (16, 16)))
            elif spawnpoint['variant'] == 4:
                self.enemies.add(SlimeGreen(self, 4, spawnpoint['pos'], (24, 32), self.enemy_slg_anims))
            elif spawnpoint['variant'] == 5 and self.stage_no > 2:
                self.enemies.add(SlimeYellow(self, 5, spawnpoint['pos'], (24, 32), self.enemy_sly_anims))
            elif spawnpoint['variant'] == 6 and self.stage_no > 4:
                self.enemies.add(SlimeRed(self, 6, spawnpoint['pos'], (24, 32), self.enemy_slr_anims))

    def circle_transition_out(self, player, display, offset=Vec(0, 0)):
        surf_overlay = pg.Surface(SCREEN_RES)
        surf_overlay.set_colorkey((0, 0, 0))
        centerpoint = (Vec(player.rect.center) - offset) * 3
        display_corners = [(0, 0), (0, 720), (960, 0), (960, 720)]
        radius_list = [int(centerpoint.distance_to(Vec(coords))) for coords in display_corners]
        radius_list.sort(reverse=True)
        radius = radius_list[0]
        if self.circle_transition_radius <= radius + 20:
            pg.draw.circle(surf_overlay, (10, 0, 10), centerpoint, self.circle_transition_radius)
            self.circle_transition_radius += 20
        else:
            self.transition_alpha = 255
            self.circle_transition_radius = 1
        display.blit(surf_overlay, (0, 0))
            
        
    def fade_transition(self, display, speed_1=4, speed_2=5):
        display.fill((0, 0, 0, self.transition_alpha))
        if self.fade_state == 'fade_out':
            self.transition_alpha = min(self.transition_alpha + speed_1, 255)
            if not self.fade_delay:
                self.fade_delay = 50
        elif self.fade_state == 'fade_in':
            self.transition_alpha = max(self.transition_alpha - speed_2, 0)
        if self.transition_alpha == 255:
            if self.fade_delay == 50:
                self.fade_midpoint = True
            else:
                self.fade_midpoint = False
            self.fade_delay = max(self.fade_delay - 1, 0)
            if not self.fade_delay:
                self.fade_state = 'fade_in'
                self.fade_delay = 50
        elif self.transition_alpha == 0:
            self.fade_state = None

    def run_interaction(self):
        for chest in self.chests:
            if pg.sprite.collide_mask(self.player, chest):
                if not chest.interacted:
                    self.sfx_manager.play('chest_open')
                    item = chest.open_chest()
                    self.loot.add(Loot(self, chest.rect.topleft, item, (16, 16)))
                    self.looted_chests['total'] += 1
                    if chest.variant == 2:
                        self.looted_chests['normal'] += 1
                    else:
                        self.looted_chests['rare'] += 1
        for item in self.loot:
            if pg.sprite.collide_mask(self.player, item) and item.lootable:
                self.player.take_loot(item)
                if item.type in 'gold_goo':
                    for i in range(8):
                        self.sparks.add(Spark(item.rect.center, random.random() * math.pi * 2, 1.5, (70, 115, 50)))
                elif item.rarity == 'normal':
                    self.sfx_manager.play('loot')
                    for i in range(11):
                        self.sparks.add(Spark(item.rect.center, random.random() * math.pi * 2, 1.5, (255, 240, 255)))
                else:
                    self.sfx_manager.play('loot')
                    for i in range(11):
                        self.sparks.add(Spark(item.rect.center, random.random() * math.pi * 2, 1.5, (230, 240, 70)))
                item.destroy = True
        if pg.sprite.collide_mask(self.player, self.portals.sprites()[0]):
            self.into_portal = True
                
    def update_camera(self, modifier=20):
            x_offset = int((self.player.rect.centerx - DISPLAY_RES[0] / 2 - self.camera.x) / modifier)
            y_offset = int((self.player.rect.centery - DISPLAY_RES[1] / 2 - self.camera.y) / modifier)
            combined_offset = Vec(x_offset, y_offset)
            self.camera += combined_offset
            self.camera.x = max(self.map_left_boundary, min(self.camera.x, self.map_right_boundary - DISPLAY_RES[0] + self.tilemap.tile_size))
            self.camera.y = min(self.map_bottom_boundary - DISPLAY_RES[1], self.camera.y)
            scroll_offset = Vec(int(self.camera.x), int(self.camera.y))
            return scroll_offset

    def run_game(self):
        
        while True:
            self.music_manager.music_loop()
            self.display.blit(self.background, (0, 0))
            self.screen_overlay.fill((0, 0, 0, 0))

            self.events = pg.event.get()

            scroll_offset = self.update_camera()

            self.stars.update()
            self.stars.render(self.display, scroll_offset)

            if self.lang_changed:
                if self.language == 'eng':
                    self.language = 'kor'
                else:
                    self.language = 'eng'
                self.lang_strings = get_lang_strings(LOCALIZATION, self.language)
                self.lang_changed = False

            if self.main_screen:
                if not self.start_game:
                    if self.fade_midpoint:
                        self.initialize_menus()
                
                pg.mouse.set_visible(True)
                self.load_main_menu()

            if self.start_game:
                self.fade_state = 'fade_out'
                self.music_manager.prepare_next_music('Pixel_11.wav', 60)
                if self.fade_midpoint:
                    self.main_screen = False
                    self.initialize_player()
                    self.main_menu = False
                    check_files = check_existing_save(SAVES_DIR, SAVE_MAP_NAME, SAVE_DATA_NAME)
                    if not check_files[0][1] and check_files[1][1]:
                        self.load_new_map()
                        self.load_save_data(SAVES_DIR, SAVE_DATA_NAME, True)
                        self.stage_no = 1
                    elif check_files[0][1] and check_files[1][1]:
                        self.load_existing_map()
                        self.load_save_data(SAVES_DIR, SAVE_DATA_NAME, False)
                    else:
                        self.load_new_map()
                        self.stage_no = 1
                    self.set_map_data()
                    self.playing = True
                    self.start_game = False
                    self.hud = Hud(self)
                    
            
            if self.into_portal:
                self.circle_transition_out(self.player, self.screen_overlay, scroll_offset)
                if self.fade_midpoint:
                    self.cleared_maps += 1
                    self.load_new_map()
                    self.set_map_data()
                    self.stage_no += 1
                    if self.stage_no > self.clear_streak:
                        self.clear_streak = self.stage_no
                        self.new_record = True
                    self.save_game_data()
                    self.into_portal = False
                    

            if self.playing:
                self.fade_transition(self.screen_transition_overlay, 5)
                if not self.game_paused:
                    pg.mouse.set_visible(False)

                    if self.game_over:
                        pg.mouse.set_visible(True)
                        self.g_o.update(self)
                        self.g_o.render(self.screen_overlay)
                        if self.fade_midpoint:
                            self.stage_no = 1
                            self.initialize_menus()
                            self.new_record = False
                            self.playing = False
                    
                    else:
                        if not self.player.dead:
                            self.movement = Vec(self.x_movement[1] - self.x_movement[0], 0) * 1.1
                            coll_list = get_collision_sprites(self.player, self.enemies, self.projectiles)
                            if coll_list:
                                self.player.get_hit(coll_list)
                            self.enemies.update(self.tilemap)
                            for enemy in self.enemies: 
                                if enemy.destroy:
                                    self.enemies.remove(enemy)
                        else:
                            self.movement *= 0
                            self.music_manager.stop_playing()
                            if self.game_over_delay:
                                if self.player.animation.done:
                                    self.game_over_delay -= 1
                                if self.game_over_delay == 0:
                                    self.fade_state = 'fade_out'
                            else:
                                if self.fade_midpoint:
                                    self.music_manager.prepare_next_music('Pixel_12.wav', 40)
                                    self.deaths += 1
                                    self.save_game_data(False)
                                    self.g_o = GameOver(self)
                                    self.game_over = True

                        self.player.update(self.tilemap, self.movement)
                        self.portals.update(self.tilemap)
                        self.chests.update()
                        self.loot.update(self.tilemap)
                        self.particles.update()         
                        self.projectiles.update(self.tilemap)
                        self.sparks.update()
                        self.ap_sparks.update(self)
                        self.hp_sparks.update(self)
                        self.hud.update(self)
                        
                else:
                    pg.mouse.set_visible(True)
                    self.p_m.update(self)
                    self.p_m.render(self.screen_overlay)
                    if self.p_m.display_help:
                        self.display_help_menu()
                    if self.p_m.display_stats:
                        self.display_stats_menu()
                    

                self.tilemap.render(self.display, scroll_offset)
                self.chests.draw(self.display, scroll_offset)
                self.portals.draw(self.display, scroll_offset)
                self.enemies.render(self.display, scroll_offset)
                self.player.render(self.display, scroll_offset)
                self.loot.draw(self.display, scroll_offset)
                self.projectiles.draw(self.display, scroll_offset)
                self.particles.draw(self.display, scroll_offset)
                self.sparks.render(self.display, scroll_offset)
                self.ap_sparks.render(self.display, scroll_offset)
                self.hp_sparks.render(self.display, scroll_offset)
            
                self.hud.render(self.display)
            
            for event in self.events:
                if event.type == pg.QUIT:
                    pg.quit()
                    sys.exit()
                if event.type == pg.KEYDOWN:
                    if event.key == pg.K_q:
                        pg.quit()
                        sys.exit()
                    if self.playing and not self.player.dead:
                        if event.key == pg.K_RIGHT:
                            self.x_movement[1] = True
                        if event.key == pg.K_LEFT:
                            self.x_movement[0] = True
                        if event.key == pg.K_z:
                            self.player.jump()
                        if event.key == pg.K_c:
                            self.player.dash()
                        if event.key == pg.K_x:
                            self.player.attack()
                        if event.key == pg.K_SPACE:
                            if not self.game_paused:
                                self.run_interaction()
                        if event.key == pg.K_DOWN:
                            self.y_direction[0] = True
                        if event.key == pg.K_UP:
                            self.y_direction[1] = True
                        if event.key == pg.K_p or event.key == pg.K_BACKSPACE or event.key == pg.K_ESCAPE:
                            if not self.p_m.display_help and not self.p_m.display_stats:
                                if not self.game_paused:
                                    self.p_m.update_stats(self)
                                self.game_paused = not self.game_paused
                if event.type == pg.KEYUP:
                    if self.playing and not self.player.dead:
                        if event.key == pg.K_RIGHT:
                            self.x_movement[1] = False
                        if event.key == pg.K_LEFT:
                            self.x_movement[0] = False
                        if event.key == pg.K_DOWN:
                            self.y_direction[0] = False
                        if event.key == pg.K_UP:
                            self.y_direction[1] = False
            
            
            scaled_display = pg.transform.scale(self.display, self.screen.get_size())

            if self.screenshake:
                shake_offset = (random.random() * self.screenshake - self.screenshake / 3)
                self.screen.blit(scaled_display, (shake_offset, shake_offset))
                self.screenshake = max(self.screenshake - 1, 0)
            else:
                self.screen.blit(scaled_display, (0, 0))

            if self.main_screen:
                self.screen.blit(self.main_screen_overlay, (0, 0))

            self.screen.blit(self.screen_overlay, (0, 0))
            
            if self.transition_alpha != 0:
                self.screen.blit(self.screen_transition_overlay, (0, 0))

            pg.display.flip()
            self.clock.tick(60)


if __name__ == '__main__':
    Game().run_game()