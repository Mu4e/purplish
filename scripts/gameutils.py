from pygame.sprite import Group
import math
import pygame as pg

class OffsetSpriteGroup(Group):
    def __init__(self):
        super().__init__()

    def update(self, *args, **kwargs):
        for sprite in self.sprites():
            sprite.update(*args, **kwargs)
        for sprite in self.sprites():
            if sprite.destroy:
                sprite.kill()

    def draw(self, surf, offset=(0, 0)):
        sprites = self.sprites()
        if hasattr(surf, "blits"):
            self.spritedict.update(
                zip(sprites, surf.blits((spr.image, (spr.rect.x - offset[0], spr.rect.y - offset[1])) for spr in sprites))
            )
        else:
            for spr in sprites:
                self.spritedict[spr] = surf.blit(spr.image, (spr.rect.x - offset[0], spr.rect.y - offset[1]))
            
    def render(self, surf, offset=(0, 0)):
        sprites = self.sprites()
        for sprite in sprites:
            sprite.render(surf, offset)


def get_reflect_vec(pos1, pos2, forcex, forcey):
    diff_x = pos1[0] - pos2[0]
    diff_y = pos1[1] - pos2[1]
    angle = math.atan2(diff_y, diff_x)
    return math.cos(angle) * forcex, math.sin(angle) * forcey


def get_collision_sprites(player, *args):
    coll_list = []
    for group in args:
        coll_list.extend(pg.sprite.spritecollide(player, group, False, pg.sprite.collide_mask))
    return coll_list
