import pygame as pg
from pygame import Vector2 as Vec
from pygame.sprite import Sprite
from scripts.particle import Particle, Fireball, Spark, SlimeBlobYellow, SlimeBlobRed, AetherSpark, HealthSpark
from scripts.utils import *
from scripts.gameutils import *
import math, random



class PhysicsEntity(Sprite):
    def __init__(self, game, e_type, pos, size, anims):
        super().__init__()
        self.game = game
        self.type = e_type
        self.pos = Vec(pos)  # topleft
        self.vel = Vec(0, 0)
        self.size = size

        self.collisions = {'up': False, 'down': False, 'right': False, 'left': False}
        self.action = ''
        self.anims = anims
        self.flip = True
        self.set_action('idle')

        self.water_tiles = []

        # for compulsory sprite attributes
        self.image = pg.transform.flip(self.animation.cur_img(), self.flip, False)
        self.rect = self.current_rect()

        self.destroy = False


    def set_action(self, action):
        if action != self.action:
            self.action = action
            self.animation = self.anims[self.action].copy()

    def current_rect(self):
        return pg.Rect(self.pos.x, self.pos.y, self.size[0], self.size[1])
        

    def get_tile_below(self, tilemap):
        return (int((self.pos.x + self.size[0] / 2) // tilemap.tile_size), int((self.pos.y + self.size[1] / 2) // tilemap.tile_size + 1))
        
    def update(self, tilemap, movement=Vec(0, 0)):
        self.collisions = {'up': False, 'down': False, 'right': False, 'left': False}
        frame_movement = movement + self.vel

        # updating x position
        self.pos.x += frame_movement.x
        self.rect = self.current_rect()
        for rect in tilemap.neighbor_physics_rects(self.pos, self.size):
            if self.rect.colliderect(rect):
                if frame_movement.x < 0:
                    self.rect.left = rect.right
                    self.collisions['left'] = True
                if frame_movement.x > 0:
                    self.rect.right = rect.left
                    self.collisions['right'] = True
                self.pos.x = self.rect.x
        min_x_pos = self.game.map_left_boundary
        max_x_pos = self.game.map_right_boundary
        if self.pos.x <= min_x_pos:
            self.pos.x = min_x_pos
        if self.pos.x >= max_x_pos:
            self.pos.x = max_x_pos

        # updating y position
        self.pos.y += frame_movement.y
        self.rect = self.current_rect()
        for rect in tilemap.neighbor_physics_rects(self.pos, self.size):
            if self.rect.colliderect(rect):
                if frame_movement.y > 0:
                    self.rect.bottom = rect.top
                    self.collisions['down'] = True
                if frame_movement.y < 0:
                    self.rect.top = rect.bottom
                    self.collisions['up'] = True
                self.pos.y = self.rect.y

        if movement.x > 0:
            self.flip = True
        elif movement.x < 0:
            self.flip = False

        self.last_movement = movement

        self.vel.y = min(5, self.vel.y + 0.1)
        if self.collisions['down'] or self.collisions['up']:
            self.vel.y = 0

        friction = 0.95
        if self.vel.x != 0:
            self.vel.x *= friction
            if self.vel.x * movement.x < 0:
                self.vel.x -= 0.1 if movement.x < 0 else -0.1
        if abs(self.vel.x) < 1e-10 or self.collisions['left'] or self.collisions['right']:
            self.vel.x = 0

        feet_loc = self.get_tile_below(tilemap)
        if self.collisions['down'] and tilemap.water_check(feet_loc):
            if feet_loc not in self.water_tiles:
                self.water_tiles.append(feet_loc)
                self.game.particles.add(Particle(self.game, 'splash', (self.rect.centerx - 8, self.rect.bottom - 16), ((self.last_movement.x / 2, 0))))
                if self.type == 'player':
                    self.game.sfx_manager.play('splash')
        if self.water_tiles:
            if len(self.water_tiles) > 1:
                self.water_tiles.pop(0)
            if self.get_tile_below(tilemap) not in self.water_tiles:
                self.water_tiles.pop(0)

        self.animation.update()
        self.image = pg.transform.flip(self.animation.cur_img(), self.flip, False)

        if self.image.get_width() != self.size[0]:
            temp_pos_x = self.get_adjusted_x_pos()
            self.rect = pg.Rect(temp_pos_x, self.pos.y, self.image.get_width(), self.image.get_height())
        else:
            self.rect = self.current_rect()
    
    def get_mask_rect(self):
        mask_rect = pg.mask.from_surface(self.image).get_rect(centerx=self.rect.centerx, bottom=self.rect.bottom)
        return mask_rect
    
    def get_adjusted_x_pos(self):
        adj_pos_x = self.pos.x - (self.image.get_width() - self.size[0]) / 2
        return adj_pos_x
        
    def render(self, surf, offset=(0, 0)):
        if self.image.get_width() != self.size[0]:
            temp_pos_x = self.get_adjusted_x_pos()
            surf.blit(self.image, (temp_pos_x - offset[0], self.pos.y - offset[1]))
        else:
            surf.blit(self.image, (self.pos.x - offset[0], self.pos.y - offset[1]))


class Player(PhysicsEntity):
    def __init__(self, game, pos, size, anims):
        super().__init__(game, 'player', pos, size, anims)
        self.max_health = 10
        self.health = self.max_health
        self.max_mana = 10
        self.mana = self.max_mana
        self.air_time = 0
        self.max_jumps = 2
        self.jumps = self.max_jumps
        self.max_dashes = 1
        self.dashes = self.max_dashes
        self.dash_time = 0
        self.dash_cooldowns = []
        self.visible = True
        self.flicker_countdown = 0
        self.attacking = False
        self.aim_vertical = 0
        self.display_emote = 0
        self.emote = self.game.player_emote[0]
        self.dead = False

    def load_attributes(self, save_dict, reset=False):
        self.max_health = save_dict['mh']
        self.max_mana = save_dict['mm']
        self.max_jumps = save_dict['mj']
        self.max_dashes = save_dict['md']
        self.jumps = self.max_jumps
        self.dashes = self.max_dashes
        if not reset:
            self.health = save_dict['ch']
            self.mana = save_dict['cm']
        else:
            self.health = self.max_health
            self.mana = self.max_mana

    def save_attributes(self):
        pl_dict = {}
        pl_dict['mh'] = self.max_health
        pl_dict['ch'] = round(self.health, 1)
        pl_dict['mm'] = self.max_mana
        pl_dict['cm'] = round(self.mana, 1)
        pl_dict['mj'] = self.max_jumps
        pl_dict['md'] = self.max_dashes
        return pl_dict

    def set_action(self, action):
        if action != self.action:
            self.action = action
            self.animation = self.anims[self.action].copy()
            if action == 'die':
                self.game.screenshake = 30

    
    def update(self, tilemap, movement=Vec(0, 0)):

        self.aim_vertical = self.game.y_direction[0] - self.game.y_direction[1]

        if round(self.health) <= 0:
            self.dead = True
        
        self.mana = min(self.mana + 0.01, self.max_mana)
        self.display_emote = max(self.display_emote - 1, 0)

        super().update(tilemap, movement=movement)

        self.flicker()
        self.air_time += 1

        if self.collisions['down']:
            self.air_time = 0
            self.jumps = self.max_jumps
        
        self.wallslide = False
        if (self.collisions['right'] or self.collisions['left']) and self.air_time > 4:
            self.wallslide = True
            self.jumps = self.max_jumps - 1
            self.vel.y = min(self.vel.y, 0.5)
            self.air_time = 5
            if self.collisions['right']:
                self.flip = True
            else:
                self.flip = False
        
        if self.dead:
            self.set_action('die')
        elif self.wallslide:
            self.attacking = False
            self.set_action('wallslide')
        else:
            if self.attacking:
                self.set_action('attack_staff')
                if self.animation.done:
                    self.attacking = False
            elif self.air_time > 4:
                self.set_action('jump')
            elif movement.x != 0:
                self.set_action('run')
            else:
                self.set_action('idle')

        if self.dash_cooldowns:
            for i in range(len(self.dash_cooldowns)):
                self.dash_cooldowns[i] -= 1
                if self.dash_cooldowns[i] == 0:
                    self.dashes = min(self.dashes + 1, self.max_dashes)
            if 0 in self.dash_cooldowns:
                self.dash_cooldowns.remove(0)
        if self.dash_time > 0:
            self.dash_time = max(0, self.dash_time - 1)
        elif self.dash_time < 0:
            self.dash_time = min(0, self.dash_time + 1)
        if abs(self.dash_time) > 1:
            self.vel.x = abs(self.dash_time) / self.dash_time * 8
            self.visible = False
            if abs(self.dash_time) == 2:
                self.vel.x *= 0.1
            p_vel = Vec(abs(self.dash_time) / self.dash_time * random.random() * 2, 0)
            self.game.particles.add(Particle(self.game, 'dash', self.pos, velocity=p_vel, frame=random.randint(0, 5)))
        
        if abs(self.dash_time) in {12, 1}:
            for i in range(15):
                angle = random.random() * math.pi * 2
                speed = random.random() * 0.5 + 0.5
                p_vel = Vec(math.cos(angle) * speed, math.sin(angle) * speed)
                self.game.particles.add(Particle(self.game, 'dash', self.pos, velocity=p_vel, frame=random.randint(0, 5)))
        
    def jump(self):
        if self.wallslide:
            if self.flip and self.last_movement.x > 0:
                self.vel.x = -2
                self.vel.y = -2.2
            elif not self.flip and self.last_movement.x < 0:
                self.vel.x = 2
                self.vel.y = -2.2
            self.air_time += 1
            self.jumps -= 1
            self.game.sfx_manager.play('jump')
        elif self.jumps:
            self.vel.y = -2.5
            self.jumps -= 1
            self.air_time += 1
            self.game.sfx_manager.play('jump')
            return True

    def dash(self):
        if self.dashes:
            if self.flip:
                self.dash_time = 12
            else:
                self.dash_time = -12
            self.dashes = max(self.dashes - 1, 0)
            self.dash_cooldowns.append(100)

    def attack(self):
        if not self.attacking and not self.wallslide:
            if self.mana >= 2:
                self.game.sfx_manager.play('attack_player')
                if self.aim_vertical == 1:
                    self.game.projectiles.add(Fireball(self.game, (self.rect.x, self.rect.centery), False, Vec(0, 0.4)))
                elif self.aim_vertical == -1:
                    self.game.projectiles.add(Fireball(self.game, (self.rect.x, self.rect.top), False, Vec(0, -0.4)))
                elif self.flip:
                    self.game.projectiles.add(Fireball(self.game, (self.rect.x + 2, self.rect.centery - 2), True, Vec(1, 0)))
                else:
                    self.game.projectiles.add(Fireball(self.game, (self.rect.x - 2, self.rect.centery - 2), False, Vec(-1, 0)))
                self.attacking = True
                self.mana -= 2
    
    def flicker(self):
        self.flicker_countdown = max(self.flicker_countdown - 1, 0)
        if self.flicker_countdown == 0:
            self.visible = True
        elif self.flicker_countdown % 5 == 0:
            self.visible = not self.visible
            

    def get_hit(self, sprite_list):
        if abs(self.dash_time) < 50 and not self.flicker_countdown:
            for entity in sprite_list:
                if entity.type in ('enemy_sl_g', 'enemy_sl_y', 'enemy_sl_r'):
                    if not entity.die:
                        self.vel = Vec(get_reflect_vec(self.rect.center, (entity.rect.centerx, entity.rect.bottom), 2, 2))
                        if entity.type == 'enemy_sl_g':
                            if entity.action == 'attack':
                                self.health = max(self.health - 2, 0)
                            else:
                                self.health = max(self.health - 1, 0)
                        elif entity.type == 'enemy_sl_y':
                            self.health = max(self.health - 2, 0)
                        elif entity.type == 'enemy_sl_r':
                            if entity.action == 'attack_a':
                                self.health = max(self.health - 4, 0)
                            else:
                                self.health = max(self.health - 3, 0)
                        if self.health > 0:
                            self.game.sfx_manager.play('hurt_player')
                            self.flicker_countdown = 120
                if 'blob' in entity.type:
                    self.vel = Vec(get_reflect_vec(self.rect.center, (entity.rect.center), 1, 2))
                    self.health = max(self.health - entity.damage, 0)
                    entity.destroy = True
                    if entity.type == 'blob_sy':
                        for i in range(6):
                            self.game.sparks.add(Spark(self.pos, random.random() * math.pi * 2, random.random() + 0.5, entity.spark_clr))
                    else:
                        for i in range(8):
                            self.game.sparks.add(Spark(self.pos, random.random() * math.pi * 2, random.random() + 0.5, entity.spark_clr))
                    if self.health > 0:
                        self.game.sfx_manager.play('hurt_player')
                        self.flicker_countdown = 120
    
    ['goo', 'ap', 'hp', 'l_hp', 'l_ap']
    ['max_jump_book', 'max_dash_book', 'max_hp_book', 'max_ap_book', 'fill_ahp', 'gold_goo']

    def take_loot(self, loot):
        self.game.looted_items['total'] += 1
        normal_loot = N_CHEST_ITEMS
        rare_loot = R_CHEST_ITEMS
        if loot.type in normal_loot:
            self.game.looted_items['normal_loot'] += 1
            if loot.type == 'hp':
                self.health = min(self.health + 2, self.max_health)
                self.game.looted_items['hp'] += 1
            elif loot.type == 'ap':
                self.mana = min(self.mana + 4, self.max_mana)
                self.game.looted_items['ap'] += 1
            elif loot.type == 'l_hp':
                self.health = min(self.health + 4, self.max_health)
                self.game.looted_items['l_hp'] += 1
            elif loot.type == 'l_ap':
                self.mana += min(self.mana + 8, self.max_mana)
                self.game.looted_items['l_ap'] += 1
            else:
                self.game.looted_items['goo'] += 1
                self.display_emote = 100
        if loot.type in rare_loot:
            self.game.looted_items['rare_loot'] += 1
            if loot.type == 'max_jump_book':
                self.max_jumps = min(self.max_jumps + 1, 4)
                self.jumps = self.max_jumps
                self.game.looted_items['max_jump_book'] += 1
            elif loot.type == 'max_dash_book':
                self.max_dashes = min(self.max_dashes + 1, 4)
                self.dashes = self.max_dashes
                self.game.looted_items['max_dash_book'] += 1
            elif loot.type == 'max_hp_book':
                self.max_health = min(self.max_health + 2, 30)
                self.game.looted_items['max_hp_book'] += 1
            elif loot.type == 'max_ap_book':
                self.max_mana = min(self.max_mana + 4, 30)
                self.game.looted_items['max_ap_book'] += 1
            elif loot.type == 'fill_ahp':
                self.health = self.max_health
                self.mana = self.max_mana
                self.game.looted_items['fill_ahp'] += 1
            else:
                self.game.looted_items['gold_goo'] += 1
                self.display_emote = 120


    def update_animation(self):
        self.image = self.animation.cur_img()

    def render(self, surf, offset=(0, 0)):
        if self.visible:
            super().render(surf, offset=offset)
        if self.display_emote:
            rect_x = 2
            rect_y = -15
            surf.blit(self.emote, (self.pos.x + rect_x - offset[0], self.pos.y + rect_y - offset[1]))


class Enemy(PhysicsEntity):
    def __init__(self, game, e_type, variant, pos, size, health, anims):
        super().__init__(game, e_type, pos, size, anims)
        self.variant = variant
        self.max_health = health
        self.health = self.max_health

        self.detected_player = False
        self.detect_cooldown = 80

        self.moving = 0
        self.jumping = False
        self.jump_cooldown = 200
        self.attacking = False
        self.attack_cooldown = 120
        self.hurt = False
        self.die = False

        self.show_hp = False
        self.hp_og = game.hud_dict['enemy_hp_base'].copy()
        self.hp_base = self.hp_og.copy()
        self.hp_bar = pg.Surface((14, 1))
        self.hp_bar.fill((255, 0, 68))

    def update_hp_bar(self):
        hp_percent = self.health / self.max_health
        hp_length = hp_percent * 14
        self.hp_base = self.hp_og.copy()
        if hp_percent >= 0:
            self.hp_subsurf = self.hp_bar.subsurface((0, 0), (hp_length, 1))

    def update_hp_display(self):
        if self.health < self.max_health:
            self.show_hp = True
            self.update_hp_bar()

    def destroy_action(self):
        self.game.killed_enemies['total'] += 1
        if self.type == 'enemy_sl_g':
            ap_num = 20
            hp_num = 0
        elif self.type == 'enemy_sl_y':
            ap_num = 25
            hp_num = 10
        elif self.type == 'enemy_sl_r':
            ap_num = 30
            hp_num = 20
        for i in range(ap_num):
            self.game.ap_sparks.add(AetherSpark((self.rect.centerx, self.rect.bottom), random.random() * math.pi * 2, random.random() + 1))
        for i in range(hp_num):
            self.game.hp_sparks.add(HealthSpark((self.rect.centerx, self.rect.bottom), random.random() * math.pi * 2, random.random() + 1))
    
    def reset_detect_cd(self, amount=80):
        self.detect_cooldown = amount

    def reset_atk_cd(self, amount):
        self.attack_cooldown = amount

    def reset_jmp_cd(self, amount):
        self.jump_cooldown = amount

    def check_visibility(self, tilemap, entity_rect):
        x1 = self.rect.centerx // 16
        x2 = entity_rect.centerx // 16
        y1 = self.rect.centery // 16
        y2 = entity_rect.top // 16
        points = []
        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        sx = 1 if x1 < x2 else -1
        sy = 1 if y1 < y2 else -1
        
        error = dx - dy
        
        while x1 != x2 or y1 != y2:
            double_error = error * 2
            if double_error > -dy:
                error -= dy
                x1 += sx
            if double_error < dx:
                error += dx
                y1 += sy
            points.append((int(x1), int(y1)))
        
        for point in points:
            loc = str(point)
            if tilemap.tilemap.get(loc):
                if tilemap.tilemap[loc]['type'] in {'stone', 'grass', 'grassystone', 'water'}:
                    return False
                
        self.detected_player = True
        return True

    def get_hit(self, entity):
        self.game.sfx_manager.play('hurt_enemy')
        self.health -= entity.damage
        self.vel = Vec(get_reflect_vec(self.pos, entity.pos, 1.5, 1.5))
        self.hurt = True
        if self.health <= 0:
            self.die = True
    
    def render(self, surf, offset=Vec(0, 0)):
        super().render(surf, offset=offset)
        if self.show_hp:
            hp_pos = self.rect.centerx - 8 - offset[0], self.rect.top + 4 - offset[1]
            self.hp_base.blit(self.hp_subsurf, (1, 1))
            surf.blit(self.hp_base, hp_pos)


class SlimeGreen(Enemy):
    def __init__(self, game, variant, pos, size, anims):
        super().__init__(game, 'enemy_sl_g', variant, pos, size, 2, anims)

    def update(self, tilemap, movement=Vec(0, 0)):

        super().update_hp_display()

        player = self.game.player
        x_distance = self.rect.centerx - player.rect.centerx
        y_distance = self.rect.centery - player.rect.centery
        xy_distance = self.pos.distance_to(player.pos)
                
        if not self.hurt and not self.die:
            if xy_distance < 150:
                if self.check_visibility(tilemap, player.rect) or xy_distance < 20:
                    self.moving = 30
                    if xy_distance < 80:
                        if x_distance < -12 and not self.flip:
                            self.flip = True
                        elif x_distance > 12 and self.flip:
                            self.flip = False
                        movement.x = -0.6 if not self.flip else 0.6
                        self.jump(y_distance, xy_distance)
                        self.attack(xy_distance)
            
                elif self.detected_player:
                    self.moving = random.randint(10, 30)
                    if self.detect_cooldown:
                        movement.x = -0.5 if not self.flip else 0.5
                        self.detect_cooldown = max(self.detect_cooldown - 1, 0)
                    else:
                        self.detected_player = False
                        self.reset_detect_cd()
                
            elif self.moving:
                if all(tilemap.edge_check(self.get_mask_rect())):
                    self.moving = 0
                    movement = Vec(0, 0)
                elif self.collisions['right'] or tilemap.edge_check(self.get_mask_rect())[1]:
                    self.flip = False
                elif self.collisions['left'] or tilemap.edge_check(self.get_mask_rect())[0]:
                    self.flip = True
                movement.x = -0.5 if not self.flip else 0.5
                
            elif random.random() < 0.01:
                self.moving = random.randint(30, 120)
            else:
                movement = Vec(0, 0)

            self.jump_cooldown = max(0, self.jump_cooldown - 1)
            self.attack_cooldown = max(0, self.attack_cooldown - 1)
            self.moving = max(0, self.moving - 1)
            
        if self.die:
            self.set_action('die')
            if self.animation.done:
                self.destroy = True
        elif self.hurt:
            self.set_action('hurt')
            movement *= 0
            self.reset_atk_cd(30)
            self.attacking = False
            self.reset_jmp_cd(50)
            self.jumping = False
            if self.animation.done:
                self.hurt = False
        elif self.jumping:
            self.set_action('jump')
            if self.animation.done:
                self.jumping = False
        elif self.attacking:
            self.set_action('attack')
            if self.animation.done:
                self.attacking = False
        elif movement.x != 0:
            self.set_action('run')
        else:
            self.set_action('idle')
    
        if self.destroy:
            self.destroy_action()
            self.game.killed_enemies['sl_g'] += 1

        super().update(tilemap, movement=movement)

    def attack(self, xy_dis):
        if not self.jumping and not self.attack_cooldown and xy_dis <= 50:
            self.attacking = True
            self.reset_atk_cd(100)
    
    def jump(self, y_dis, xy_dis):
        if y_dis > 7 and xy_dis < 60 and not self.jump_cooldown and self.collisions['down']:
            if y_dis > 24:
                self.vel.y = -3.2
            else:
                self.vel.y = -2.5
            self.vel.x = (1 if self.flip else -1)
            self.jumping = True
            self.reset_jmp_cd(200)


class SlimeYellow(Enemy):
    def __init__(self, game, variant, pos, size, anims):
        super().__init__(game, 'enemy_sl_y', variant, pos, size, 3, anims)

    def update(self, tilemap, movement=Vec(0, 0)):
        
        super().update_hp_display()

        player = self.game.player
        x_distance = self.rect.centerx - player.rect.centerx
        y_distance = self.rect.centery - player.rect.centery
        xy_distance = self.pos.distance_to(player.pos)
                
        if not self.hurt and not self.die:
            if xy_distance < 150:
                if self.check_visibility(tilemap, player.rect) or xy_distance < 20:
                    self.moving = 20
                    if xy_distance < 100:
                        if x_distance < -10 and not self.flip:
                            self.flip = True
                        elif x_distance > 10 and self.flip:
                            self.flip = False
                        movement.x = -0.5 if not self.flip else 0.5
                        self.attack(xy_distance)

            elif self.moving:
                if all(tilemap.edge_check(self.get_mask_rect())):
                    self.moving = 0
                    movement = Vec(0, 0)
                elif self.collisions['right'] or tilemap.edge_check(self.get_mask_rect())[1]:
                    self.flip = False
                elif self.collisions['left'] or tilemap.edge_check(self.get_mask_rect())[0]:
                    self.flip = True
                movement.x = -0.4 if not self.flip else 0.4
            elif random.random() < 0.005:
                self.moving = random.randint(30, 90)
            else:
                movement = Vec(0, 0)

            self.attack_cooldown = max(0, self.attack_cooldown - 1)
            self.moving = max(0, self.moving - 1)


        if self.die:
            self.set_action('die')
            if self.animation.done:
                self.destroy = True
        elif self.hurt:
            self.set_action('hurt')
            movement *= 0
            self.reset_atk_cd(5)
            self.attacking = False
            if self.animation.done:
                self.hurt = False
        elif self.attacking:
            movement *= 0
            self.set_action('attack')
            if self.animation.cur_img() == self.animation.images[4] and not self.attack_cooldown:
                self.shoot_blob(self.game.player.rect.center)
                self.reset_atk_cd(80)
            if self.animation.done:
                self.attacking = False
        elif movement.x != 0:
            self.set_action('run')
        else:
            self.set_action('idle')
        
        if self.destroy:
            self.destroy_action()
            self.game.killed_enemies['sl_y'] += 1
        
        super().update(tilemap, movement=movement)


    def shoot_blob(self, player_pos):
        self.game.sfx_manager.play('attack_blob')
        start_x = self.rect.centerx
        start_y = self.rect.centery + 4
        self.game.projectiles.add(SlimeBlobYellow(self.game, (start_x, start_y), player_pos))

    def attack(self, xy_dis):
        if not self.jumping and not self.attack_cooldown and xy_dis <= 80:
            self.attacking = True


class SlimeRed(Enemy):
    def __init__(self, game, variant, pos, size, anims):
        super().__init__(game, 'enemy_sl_r', variant, pos, size, 4, anims)
        self.blob_attack_cooldown = 120
        self.attacking_blob = False

    def reset_blb_atk_cd(self, amount):
        self.blob_attack_cooldown = amount

    def update(self, tilemap, movement=Vec(0, 0)):
        super().update_hp_display()

        player = self.game.player
        x_distance = self.rect.centerx - player.rect.centerx
        y_distance = self.rect.centery - player.rect.centery
        xy_distance = self.pos.distance_to(player.pos)
                
        if not self.hurt and not self.die:
            if xy_distance < 200:
                if self.check_visibility(tilemap, player.rect) or xy_distance < 22:
                    if xy_distance < 140:
                        self.moving = 40
                        if x_distance < -8 and not self.flip:
                            self.flip = True
                        elif x_distance > 8 and self.flip:
                            self.flip = False
                        movement.x = -0.7 if not self.flip else 0.7
                        self.jump(y_distance, xy_distance)
                        self.attack_melee(xy_distance)
                        self.attack_blob(xy_distance)

            elif self.moving:
                if all(tilemap.edge_check(self.get_mask_rect())):
                    self.moving = 0
                    movement = Vec(0, 0)
                elif self.collisions['right'] or tilemap.edge_check(self.get_mask_rect())[1]:
                    self.flip = False
                elif self.collisions['left'] or tilemap.edge_check(self.get_mask_rect())[0]:
                    self.flip = True
                movement.x = -0.5 if not self.flip else 0.5
            elif random.random() < 0.02:
                self.moving = random.randint(30, 90)
            else:
                movement = Vec(0, 0)

            self.attack_cooldown = max(0, self.attack_cooldown - 1)
            self.blob_attack_cooldown = max(0, self.blob_attack_cooldown - 1)
            self.jump_cooldown = max(0, self.jump_cooldown - 1)
            self.moving = max(0, self.moving - 1)


        if self.die:
            self.set_action('die')
            if self.animation.done:
                self.destroy = True
        elif self.hurt:
            self.set_action('hurt')
            movement *= 0
            self.reset_atk_cd(20)
            self.attacking = False
            self.reset_blb_atk_cd(15)
            self.attacking_blob = False
            self.reset_jmp_cd(90)
            self.jumping = False
            if self.animation.done:
                self.hurt = False
        elif self.jumping:
            self.set_action('jump')
            if self.animation.done:
                self.jumping = False
        elif self.attacking:
            self.set_action('attack_a')
            if self.animation.done:
                self.attacking = False
        elif self.attacking_blob:
            self.set_action('attack_b')
            movement *= 0
            if self.animation.cur_img() == self.animation.images[4] and not self.blob_attack_cooldown:
                self.shoot_blob(self.game.player.rect.center)
                self.reset_blb_atk_cd(90)
            if self.animation.done:
                self.attacking_blob = False
        elif movement.x != 0:
            self.set_action('run')
        else:
            self.set_action('idle')
        
        if self.destroy:
            self.destroy_action()
            self.game.killed_enemies['sl_r'] += 1
        
        super().update(tilemap, movement=movement)


    def jump(self, y_dis, xy_dis):
        if y_dis > 7 and xy_dis < 80 and not self.jump_cooldown and self.collisions['down']:
            if y_dis > 44:
                self.vel.y = -4.3
                self.vel.x = (1.5 if self.flip else -1.5)
            elif y_dis > 30:
                self.vel.y = -3.6
                self.vel.x = (1.3 if self.flip else -1.3)
            elif y_dis > 14:
                self.vel.y = -3.2
                self.vel.x = (1.2 if self.flip else -1.2)
            else:
                self.vel.y = -2.8
                self.vel.x = (1 if self.flip else -1)
            self.jumping = True
            self.reset_jmp_cd(160)
    
    def attack_melee(self, xy_dis):
        if not self.jumping and not self.attack_cooldown and xy_dis <= 30:
            self.attacking = True
            self.reset_atk_cd(120)
    
    def attack_blob(self, xy_dis):
        if not self.jumping and not self.attacking and not self.blob_attack_cooldown and xy_dis <= 100:
            self.attacking_blob = True

    
    def shoot_blob(self, player_pos):
        self.game.sfx_manager.play('attack_blob')
        start_x = self.rect.centerx
        start_y = self.rect.centery + 4
        self.game.projectiles.add(SlimeBlobRed(self.game, 'blob_sr', (start_x, start_y), player_pos))



class NormalChest(Sprite):
    def __init__(self, game, c_type, variant, pos, size):
        super().__init__()
        self.game = game
        self.variant = variant
        self.pos = pos
        self.size = size
        self.type = c_type
        self.images = game.tile_dict.copy()
        self.anims = Animation(self.images[self.type], 4, False)
        self.static_closed = self.images[self.type][0]
        self.static_open = self.images[self.type][-1]
        self.interacted = False
        self.destroy = False

        self.image = self.static_closed
        self.rect = self.get_current_rect()
        
    def get_current_rect(self):
        return pg.Rect(self.pos.x, self.pos.y, self.image.get_width(), self.image.get_height())
    
    def open_chest(self):
        self.interacted = True
        item = random.choices(N_CHEST_ITEMS, N_CHEST_WEIGHTS, k=1)
        return item[0]

    def update(self):
        if self.interacted:
            self.anims.update()
            self.image = self.anims.cur_img()
        if self.anims.done:
            self.image = self.static_open
        self.rect = self.get_current_rect()



class RareChest(NormalChest):
    def __init__(self, game, variant, pos, size):
        super().__init__(game, 'chest_r', variant, pos, size)

    def open_chest(self):
        self.interacted = True
        item = random.choices(R_CHEST_ITEMS, R_CHEST_WEIGHTS, k=1)
        return item[0]


N_CHEST_ITEMS = ['goo', 'ap', 'hp', 'l_hp', 'l_ap']
N_CHEST_WEIGHTS = [3, 3, 2, 1, 1]
R_CHEST_ITEMS = ['max_jump_book', 'max_dash_book', 'max_hp_book', 'max_ap_book', 'fill_ahp', 'gold_goo']
R_CHEST_WEIGHTS = [1, 1, 2, 3, 3, 4]


class Loot(Sprite):
    def __init__(self, game, pos, lt_type, size):
        super().__init__()
        self.game = game
        self.size = size
        self.pos = Vec(pos)
        self.vel = Vec(1, -1.5)
        self.type = lt_type
        self.set_rarity()
        image = self.game.loot_dict[lt_type].copy()
        self.image = pg.transform.scale_by(image, 0.8)
        self.size = (self.image.get_width(), self.image.get_height())
        self.rect = self.current_rect()
        self.lootable = False
        self.destroy = False

    def current_rect(self):
        return pg.Rect(self.pos, self.size)
    
    def set_rarity(self):
        if self.type in N_CHEST_ITEMS:
            self.rarity = 'normal'
        else:
            self.rarity = 'rare'

    def update(self, tilemap):
        self.vel.x = max(self.vel.x - 0.1, 0)
        self.vel.y = min(self.vel.y + 0.1, 5)
        self.pos += self.vel
        self.rect = self.current_rect()
        for rect in tilemap.neighbor_physics_rects(self.pos, self.size):
            if self.rect.colliderect(rect):
                if self.vel.y > 0:
                    self.rect.bottom = rect.top
                    self.vel.y = 0
                self.pos.y = self.rect.y
                self.lootable = True

        self.rect = self.current_rect()



class Portal(PhysicsEntity):
    def __init__(self, game, pos, size, anims):
        super().__init__(game, 'portal', pos, size, anims)


    def update(self, tilemap):
        super().update(tilemap)
