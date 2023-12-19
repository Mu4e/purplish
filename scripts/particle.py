import pygame as pg
import random, math
from pygame import Vector2 as Vec
from pygame.sprite import Sprite


class Particle(Sprite):
    def __init__(self, game, p_type, pos, velocity=Vec(0, 0), frame=0):
        super().__init__()
        self.game = game
        self.type = p_type
        self.pos = Vec(pos)
        self.vel = velocity
        self.animation = self.game.particle_anims[p_type].copy()
        self.animation.frame = frame
        self.set_current_img()
        self.set_rect()
        self.destroy = False

    def set_current_img(self):
        self.image = self.animation.cur_img()
    
    def set_rect(self):
        self.rect = pg.Rect(self.pos.x, self.pos.y, self.image.get_width(), self.image.get_height())

    def update(self):
        if self.animation.done:
            self.destroy = True
        self.pos += self.vel

        self.animation.update()
        self.set_current_img()
        self.set_rect()
        if self.type == 'dash':
            self.image = pg.transform.rotate(self.image, random.random() * 360)

    def render(self, surf, offset=(0, 0)):  
        render_pos_x = self.rect.x - offset[0] - self.image.get_width() // 2
        render_pos_y = self.rect.y - offset[1] - self.image.get_height() // 2
        surf.blit(self.image, (render_pos_x, render_pos_y))


PROJECTILE_DAMAGE = {'fireball': 1, 'blob_sy': 2, 'blob_sr': 3}

class Projectile(Sprite):
    def __init__(self, game, pj_type, pos, velocity=Vec(0, 0)):
        super().__init__()
        self.game = game
        self.type = pj_type
        self.damage = PROJECTILE_DAMAGE[self.type]
        self.pos = Vec(pos)
        self.vel = velocity
        self.image_surf = self.game.projectile_dict[pj_type].copy()
        self.image = self.image_surf
        self.size = self.image.get_size()
        self.set_rect()
        
        self.destroy = False

    def set_rect(self):
        self.rect = pg.Rect(self.pos.x, self.pos.y, self.size[0], self.size[1])


    def check_collisions(self, tilemap):
        self.rect = pg.Rect(self.pos.x + 1, self.pos.y + 1, self.size[0] - 2, self.size[1] - 2)
        for rect in tilemap.neighbor_physics_rects(self.pos, self.size):
            if self.rect.colliderect(rect):
                return True
    
    def update(self):
        self.pos += self.vel
        self.set_rect()

    def render(self, surf, offset=(0, 0)):  
        render_pos_x = self.rect.x - offset[0]
        render_pos_y = self.rect.y - offset[1]
        surf.blit(self.image, (render_pos_x, render_pos_y))


class Fireball(Projectile):
    def __init__(self, game, pos, flip, velocity=Vec(0, 0)):
        super().__init__(game, 'fireball', pos, velocity)
        self.flip = flip
        if self.vel.y > 0:
            self.image = pg.transform.rotate(self.image_surf, 90)
        elif self.vel.y < 0:
            self.image = pg.transform.rotate(self.image_surf, 270)
        else:
            self.image = pg.transform.flip(self.image_surf, self.flip, False)
    
    def update(self, tilemap):
        accel = 0.1
        max_speed = 4
        if self.check_collisions(tilemap):
            self.destroy = True
            sp_color = (235, 88, 24)
            for i in range(10):
                if self.vel.y != 0:
                    loc_y = self.rect.bottom if self.vel.y > 0 else self.rect.top
                    loc = Vec(self.rect.centerx, loc_y)
                    angle = (random.uniform(-3, 0) if self.vel.y > 0 else random.uniform(0, 3))
                    self.game.sparks.add(Spark(loc, angle, 1 + random.random(), sp_color))
                else:
                    loc_x = self.rect.left if self.vel.x < 0 else self.rect.right
                    self.game.sparks.add(Spark((loc_x, self.pos.y), random.uniform(-1.4, 1.4) + (math.pi if self.vel.x > 0 else 0), 1 + random.random(), sp_color))
        if self.pos.x < self.game.map_left_boundary - 16 or self.pos.x > self.game.map_right_boundary or self.pos.y < -500:
            self.destroy = True
        coll_enemies = pg.sprite.spritecollide(self, self.game.enemies, False, collided=pg.sprite.collide_mask)
        if coll_enemies:
            for enemy in coll_enemies:
                if not enemy.die:
                    self.destroy = True
                    enemy.get_hit(self)
            loc = (self.rect.left if self.flip else self.rect.right, self.rect.centery)
            for i in range(15):
                self.game.sparks.add(Spark(loc, random.random() * math.pi * 2, random.random() + 1, (235, 88, 24)))
            

        if self.vel.x > 0:
            self.vel.x += accel
        elif self.vel.x < 0:
            self.vel.x -= accel
        if abs(self.vel.x) >= max_speed:
            self.vel.x = abs(self.vel.x) / self.vel.x * max_speed

        if self.vel.y > 0:
            self.vel.y = min(self.vel.y + 0.1, 4)
        elif self.vel.y < 0:
            self.vel.y = max(self.vel.y - 0.1, -4)

        super().update()


class SlimeBlobYellow(Projectile):
    def __init__(self, game, pos, target_pos):
        super().__init__(game, 'blob_sy', pos)
        self.start_pos = self.pos
        self.target_pos = Vec(target_pos)
        self.time = 0
        self.start_x = self.pos.x
        self.start_y = self.pos.y
        self.angle, self.speed, height = self.get_angle()
        self.vel.x = math.cos(self.angle) * self.speed
        self.vel.y = self.get_init_y_vel(height)
        self.spark_clr = (230, 205, 50)

    def get_angle(self):
        distance = self.target_pos.x - self.start_pos.x
        height = self.target_pos.y - 20 - self.start_pos.y
        
        angle = math.atan2(height, distance)
        speed = self.start_pos.distance_to(self.target_pos) / 40
        return angle, speed, height
    
    def get_init_y_vel(self, height):
        if height <= -49:
            return -3.5
        elif height <= -36:
            return -3
        elif height < -26:
            return -2.5
        else:
            return -2

    def update(self, tilemap):
        self.set_rect()
        if self.check_collisions(tilemap):
            self.destroy = True
            for i in range(4):
                if self.vel.x < 0:
                    angle = random.uniform(-1.4, 1.4)
                    self.game.sparks.add(Spark(self.pos, angle, 1 + random.random(), self.spark_clr))
                elif self.vel.x > 0:
                    angle = random.uniform(-1.4, 1.4) + math.pi
                    self.game.sparks.add(Spark(self.pos, angle, 1 + random.random(), self.spark_clr))
                if self.vel.y < 0:
                    angle = random.uniform(0, 3)
                    self.game.sparks.add(Spark(self.pos, angle, 1 + random.random(), self.spark_clr))
                elif self.vel.y > 0:
                    angle = random.uniform(-3, 0)
                    self.game.sparks.add(Spark(self.pos, angle, 1 + random.random(), self.spark_clr))


        grav = 0.1
        self.vel.y = min(self.vel.y + grav, 4)

        self.pos += self.vel
        self.set_rect()

class SlimeBlobRed(SlimeBlobYellow):
    def __init__(self, game, pj_type, pos, target_pos):
        super().__init__(game, pos, target_pos)
        self.type = pj_type
        self.damage = PROJECTILE_DAMAGE[self.type]
        self.image = self.game.projectile_dict[pj_type].copy()
        self.spark_clr = (200, 65, 65)


class Spark(Sprite):
    def __init__(self, pos, angle, speed, color):
        super().__init__()
        self.pos = Vec(pos)
        # angle in radians
        self.angle = angle
        self.speed = speed
        self.destroy = False
        self.color = color

    def update(self):
        self.pos.x += math.cos(self.angle) * self.speed
        self.pos.y += math.sin(self.angle) * self.speed
        self.speed = max(0, self.speed - 0.1)
        if self.speed == 0:
            self.destroy = True
    
    def render(self, surf, offset=Vec(0, 0)):
        pg.draw.circle(surf, self.color, self.pos - offset, 1)


class AetherSpark(Spark):
    def __init__(self, pos, angle, speed):
        super().__init__(pos, angle, speed, (50, 50, 240))
        self.absorb_speed = 1
        self.max_speed = 4

    def update(self, game):
        self.pos.x += math.cos(self.angle) * self.speed
        self.pos.y += math.sin(self.angle) * self.speed
        self.speed = max(0, self.speed - 0.1)
        if self.speed == 0:
            player_pos = Vec(game.player.pos.x + 4, game.player.pos.y + 8)
            diff_vec = player_pos - self.pos
            new_angle = math.atan2(diff_vec.y, diff_vec.x)
            self.pos.x += math.cos(new_angle) * self.absorb_speed
            self.pos.y += math.sin(new_angle) * self.absorb_speed
            self.absorb_speed = min(self.absorb_speed + 0.2, self.max_speed)
            if self.pos.distance_to(player_pos) < 8:
                self.destroy = True
        if self.destroy:
            game.player.mana = min(game.player.mana + 0.1, game.player.max_mana)
    
    def render(self, surf, offset=Vec(0, 0)):
        rot = random.random() * 360
        p1_vec = Vec(0, 1.5)
        p1_vec.rotate_ip(rot)
        p2_vec = p1_vec.rotate(120)
        p3_vec = p1_vec.rotate(-120)
        points = [
            p1_vec + self.pos,
            p2_vec + self.pos,
            p3_vec + self.pos
        ]
        pg.draw.polygon(surf, self.color, [i - offset for i in points])


class HealthSpark(Spark):
    def __init__(self, pos, angle, speed):
        super().__init__(pos, angle, speed, (240, 50, 50))
        self.absorb_speed = 1.5
        self.max_speed = 4

    def update(self, game):
        self.pos.x += math.cos(self.angle) * self.speed
        self.pos.y += math.sin(self.angle) * self.speed
        self.speed = max(0, self.speed - 0.1)
        if self.speed == 0:
            player_pos = Vec(game.player.pos.x + 4, game.player.pos.y + 8)
            diff_vec = player_pos - self.pos
            new_angle = math.atan2(diff_vec.y, diff_vec.x)
            self.pos.x += math.cos(new_angle) * self.absorb_speed
            self.pos.y += math.sin(new_angle) * self.absorb_speed
            self.absorb_speed = min(self.absorb_speed + 0.2, self.max_speed)
            if self.pos.distance_to(player_pos) < 8:
                self.destroy = True
        if self.destroy:
            game.player.health = min(game.player.health + 0.1, game.player.max_health)


    def render(self, surf, offset=Vec(0, 0)):
        rot = random.random() * 360
        p1_vec = Vec(0, 1.2)
        p1_vec.rotate_ip(rot)
        p2_vec = p1_vec.rotate(90)
        p3_vec = p1_vec.rotate(180)
        p4_vec = p1_vec.rotate(270)
        points = [
            p1_vec + self.pos,
            p2_vec + self.pos,
            p3_vec + self.pos,
            p4_vec + self.pos
        ]
        pg.draw.polygon(surf, self.color, [i - offset for i in points])