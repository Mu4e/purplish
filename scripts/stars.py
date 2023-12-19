import random
from pygame import Vector2 as Vec

class Star:
    def __init__(self, pos, img, speed, depth):
        self.pos = Vec(pos)
        self.img = img
        self.speed = speed
        self.depth = depth
        self.img_w = self.img.get_width()
        self.img_h = self.img.get_height()
    
    def update(self):
        self.pos.x += self.speed

    def render(self, surf, offset=(0, 0)):
        render_pos = (self.pos.x - offset[0] * self.depth, self.pos.y - offset[1] * self.depth)
        surf_w = surf.get_width()
        surf_h = surf.get_height()
        target_pos = (render_pos[0] % surf_w), (render_pos[1] % (surf_h + self.img_h)) / 2 - self.img_h
        surf.blit(self.img, target_pos)

class Stars:
    """Class to store all of the stars."""
    def __init__(self, star_images, count=30):
        self.stars = []

        for i in range(count):
            self.stars.append(Star((random.random() * 99999, random.random() * 99999), random.choice(star_images), random.random() * 0.05 + 0.02, random.random() * 0.4  + 0.03))

        self.stars.sort(key=lambda x: x.depth)
    
    def update(self):
        for star in self.stars:
            star.update()
        
    def render(self, surf, offset=(0, 0)):
        for star in self.stars:
            star.render(surf, offset=offset)