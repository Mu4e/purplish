import pygame as pg
from pygame.sprite import Sprite


# return surf, rect. add them to a dict in the menu.
# blit them in the menu.

class StaticButton(Sprite):
    def __init__(self, fontpath, size, color, msg, **kwargs):
        super().__init__()
        self.font_path = fontpath
        self.color = color
        self.size = size
        self.text = msg
        self.pos = kwargs
        self.set_image_rect()

    def set_image_rect(self):
        self.og_image = pg.font.Font(self.font_path, self.size).render(self.text, True, self.color)
        self.image = self.og_image
        self.rect = self.image.get_rect(**self.pos)

    def check_mouseover(self, offset_x=0, offset_y=0):
        pass

    def render(self, display):
        display.blit(self.image, self.rect)


class Button(StaticButton):
    def __init__(self, fontpath, size, color, msg, **kwargs):
        super().__init__(fontpath, size, color, msg, **kwargs)

    def check_mouseover(self, offset_x=0, offset_y=0):
        mpos = pg.mouse.get_pos()
        adjusted_mpos = (mpos[0] - offset_x, mpos[1] - offset_y)
        if self.rect.collidepoint(adjusted_mpos):
            self.image = self.get_button_mask()
            return True
        else:
            self.image = self.og_image

    def get_button_mask(self):
        return pg.mask.from_surface(self.image).to_surface(unsetcolor=None)


class ImgButton(Button):
    def __init__(self, img, **kwargs):
        self.og_image = img
        self.image = self.og_image
        self.pos = kwargs
        self.rect = self.image.get_rect(**self.pos)



