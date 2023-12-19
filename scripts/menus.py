import pygame as pg
from scripts.buttons import *
import sys


class Menu:
    def __init__(self, game):
        self.game = game
        self.display = game.display
        self.screen = game.screen_overlay
        self.font_path = game.font_path
        self.font_clr = (56, 26, 147)
        self.language = game.language
        self.lang_dict = game.lang_strings
        self.buttons_dict = {}

    def update(self, game, xoffset=0, yoffset=0):
        changed = self.check_language(game)
        mouse = []
        for button in self.buttons_dict.values():
            mouse.append(button.check_mouseover(xoffset, yoffset))
        return changed, any(mouse)

    def check_language(self, game):
        if self.language != game.language:
            self.lang_dict = game.lang_strings
            self.set_buttons()
            self.language = game.language
            return True

    def set_buttons(self):
        pass
    
    def render(self, display):
        for button in self.buttons_dict.values():
            button.render(display)


class MainMenu(Menu):
    def __init__(self, game):
        super().__init__(game)
        self.font_size = 60
        self.buttons_list = ["001", "002", "003", "074"]
        self.set_buttons()
        self.keyboard_ctrl = False
        self.select = 0
        self.selected_button = None

    def set_buttons(self):
        x = self.screen.get_width() / 2
        y = self.screen.get_height() / 2 - 20
        y_incr = 0
        for index in self.buttons_list:
            self.buttons_dict[index] = Button(self.font_path, self.font_size, self.font_clr, self.lang_dict[index], centerx=x, centery=y + y_incr)
            y_incr += 80

    def select_button(self):
        if self.keyboard_ctrl:
            selection = self.select % len(self.buttons_list)
            b_index = self.buttons_list[selection]
            selected_button = self.buttons_dict[b_index]
            highlight_surf = selected_button.get_button_mask()
            self.buttons_dict[b_index].image = highlight_surf
            return b_index

    def execute_press_events(self, button_name):
        if button_name == 'play':
            self.game.start_game = True
            self.game.fade_state = 'fade_out'
        elif button_name == 'options':
            self.game.sfx_manager.play('paper')
            self.game.options_menu = True
            self.game.o_m.notice.target_y = 48
            self.game.o_m.notice.transition_vel_y = 0
        elif button_name == 'help':
            self.game.sfx_manager.play('paper')
            self.game.help_menu = True
        elif button_name == 'stats':
            self.game.sfx_manager.play('paper')
            self.game.st_m = StatsMenu(self.game)
            self.game.stats_menu = True
        self.game.main_menu = False

    def check_events(self, events):
        for event in events:
            if event.type == pg.MOUSEBUTTONDOWN:
                if event.button == 1 and self.game.main_menu:
                    if self.buttons_dict["001"].check_mouseover():
                        self.execute_press_events('play')
                    if self.buttons_dict["002"].check_mouseover():
                        self.execute_press_events('options')
                    if self.buttons_dict["003"].check_mouseover():
                        self.execute_press_events('help')
                    if self.buttons_dict["074"].check_mouseover():
                        self.execute_press_events('stats')
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_UP:
                    if not self.keyboard_ctrl:
                        self.keyboard_ctrl = True
                        self.select = 1
                    self.select -= 1
                if event.key == pg.K_DOWN:
                    if not self.keyboard_ctrl:
                        self.keyboard_ctrl = True
                        self.select = -1
                    self.select += 1
                if event.key == pg.K_SPACE or event.key == pg.K_RETURN:
                    if self.selected_button == '001':
                        self.execute_press_events('play')
                    if self.selected_button == '002':
                        self.execute_press_events('options')
                    if self.selected_button == '003':
                        self.execute_press_events('help')
                    if self.selected_button == '074':
                        self.execute_press_events('stats')
                    
                        
    def update(self, game):
        mouse = super().update(game)[1]
        if mouse and self.keyboard_ctrl:
            self.keyboard_ctrl = False
            for button in self.buttons_dict.values():
                button.set_image_rect()
        self.check_events(game.events)
        self.selected_button = self.select_button()
        

    def render(self, display):
        display.fill((0, 0, 0, 0))
        super().render(display)


class Notice:
    def __init__(self, game, variant):
        self.game = game
        self.screen = game.screen_overlay
        self.variant = variant
        self.image = game.ui_dict[self.variant].copy()
        self.rect = self.image.get_rect(centerx=self.screen.get_width() / 2, top=self.screen.get_height())
        self.buttons_dict = {}
        self.buttons_dict['x_button'] = ImgButton(game.ui_dict['close_button'].copy(), topleft=(self.image.get_width() - 96, 48))
        self.center_pos = pg.Rect(48, 48, self.image.get_width(), self.image.get_height())
        self.bottom_pos = self.rect
        self.right_pos = pg.Rect(self.screen.get_width(), 48, self.image.get_width(), self.image.get_height())
        self.left_pos = pg.Rect(48-self.screen.get_width(), 48, self.image.get_width(), self.image.get_height())
        self.transition_vel_x = 0
        self.transition_vel_y = 0
        self.target_y = 48
        self.target_x = self.screen.get_width()
        self.distance = 0
    
    def check_events(self, events, click_x_button):
        for button in self.buttons_dict.values():
            button.check_mouseover(48, 48)
        for event in events:
            if event.type == pg.MOUSEBUTTONDOWN:
                if event.button == 1 and click_x_button:
                    return True
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_ESCAPE or event.key == pg.K_BACKSPACE:
                    return True
                
    
    def check_close(self, events):
        click_close = self.buttons_dict['x_button'].check_mouseover(48, 48)
        return self.check_events(events, click_close)

    def refresh(self):
        self.image = self.game.ui_dict[self.variant].copy()

    def prepare_off_screen(self, direction):
        if direction == 'right':
            self.rect.x = 48 - self.screen.get_width()
            self.target_x = self.center_pos.x
        else:
            self.rect.x = self.screen.get_width()
            self.target_x = self.center_pos.x
    
    def send_off_screen(self, direction):
        if direction == 'right':
            self.target_x = self.right_pos.x
        else:
            self.target_x = self.left_pos.x

    def transition_vertical(self):
        current_distance = self.target_y - self.rect.y
        if self.transition_vel_y == 0 and current_distance != 0:
            self.distance = current_distance
        direction = abs(self.distance) / self.distance
        modifier = 0.8
        if current_distance * self.distance <= 0:
            self.transition_vel_y = 0
            self.rect.y = self.target_y
            if self.target_y == self.screen.get_height():
                return True
        else:
            accel = 15
            if abs(current_distance) / abs(self.distance) < 0.4 and self.distance < 0:
                accel = 0
            self.transition_vel_y += direction * accel
            self.transition_vel_y *= modifier
            self.rect.y += self.transition_vel_y
    
    def transition_horizontal(self):
        current_distance = self.target_x - self.rect.x
        if self.transition_vel_x == 0 and current_distance != 0:
            self.distance = current_distance
        if self.distance * current_distance <= 0:
            self.transition_vel_x = 0
            self.rect.x = self.target_x
            return True
        else:
            modifier = 0.9
            accel = 8
            if abs(current_distance) / abs(self.distance) < 0.5:
                accel = 0
            self.transition_vel_x += abs(self.distance) / self.distance * accel
            self.transition_vel_x *= modifier
            self.rect.x += self.transition_vel_x

    def render(self):
        for button in self.buttons_dict.values():
            self.image.blit(button.image, button.rect)


class OptionsMenu(Menu):
    def __init__(self, game):
        super().__init__(game)
        self.notice = Notice(game, 'notice')
        self.set_buttons()
        self.notice.target_y = 48
    
    def set_buttons(self):
        self.buttons_dict['language'] = StaticButton(self.font_path, 60, self.font_clr, self.lang_dict['005'], topleft=(100, 120))
        self.buttons_dict['current_lang'] = Button(self.font_path, 60, self.font_clr, self.lang_dict['006'], topleft=(400, 120))
        self.buttons_dict['reset'] = Button(self.font_path, 60, self.font_clr, self.lang_dict['036'], topleft=(100, 200))
        self.buttons_dict['reset_details'] = StaticButton(self.font_path, 30, self.font_clr, self.lang_dict['037'], topleft=(100, 280))

    def update(self, game):
        if super().update(game, 48, 48)[0]:
            self.notice.refresh()
            self.set_buttons()
        close = self.notice.check_close(game.events)
        done = self.notice.transition_vertical()
        if close:
            self.game.sfx_manager.play('paper')
            self.notice.target_y = self.screen.get_height()
            self.notice.transition_vel_y = 0
            self.game.main_menu = True
        if done:
            self.game.options_menu = False
        self.check_events(game.events)

    def check_events(self, events):
        for event in events:
            if event.type == pg.MOUSEBUTTONDOWN:
                if event.button == 1:
                    if self.buttons_dict['current_lang'].check_mouseover(48, 48):
                        self.game.lang_changed = True
                    if self.buttons_dict['reset'].check_mouseover(48, 48):
                        self.game.delete_save()
    
    def render(self, display):
        display.fill((0, 0, 0, 0))
        display.blit(self.notice.image, self.notice.rect)
        self.notice.render()
        for button in self.buttons_dict.values():
            self.notice.image.blit(button.image, button.rect)

class StatsMenu(Menu):
    def __init__(self, game):
        super().__init__(game)
        self.overlay_surf = pg.Surface(self.screen.get_size())
        self.overlay_surf.set_colorkey((0, 0, 0))
        self.notice = Notice(game, 'notice')
        self.notice.target_y = 48
        self.set_buttons(game)
    
    def set_buttons(self, game):
        self.stats_instance = GameOverStats(game.g_o, game)
        self.buttons_dict = self.stats_instance.buttons_dict.copy()
        for index, button in self.buttons_dict.items():
            button.color = (50, 25, 120)
            button.set_image_rect()
            if index.isdigit() and int(index) in range(51, 65):
                button.rect.x = 460

    def update(self, game):
        if super().update(game, 48, 48)[0]:
            self.notice.refresh()
            self.set_buttons()
        close = self.notice.check_close(game.events)
        done = self.notice.transition_vertical()
        if close:
            self.game.sfx_manager.play('paper')
            self.notice.target_y = self.screen.get_height()
            self.notice.transition_vel_y = 0
            if self.game.main_screen:
                self.game.main_menu = True
        if done:
            self.game.stats_menu = False
            if self.game.game_paused:
                self.game.p_m.display_stats = False

    def render(self, display):
        self.overlay_surf.fill((0, 0, 0))
        self.overlay_surf.blit(self.notice.image, self.notice.rect)
        self.notice.render()
        for button in self.buttons_dict.values():
            self.notice.image.blit(button.image, (button.rect.x, button.rect.y + 30))
        display.blit(self.overlay_surf, (0, 0))


class HelpMenu(Menu):
    def __init__(self, game):
        super().__init__(game)
        self.notice = Notice(game, 'notice')
        self.notice_pages = {}
        self.initialize_notices(game)
        self.side_transition = False
        self.font_clr = (47, 23, 123)
        self.set_buttons()
        self.overlay = pg.Surface(game.screen.get_size(), pg.SRCALPHA)

    def initialize_notices(self, game):
        self.notice_pages[0] = Notice(game, 'controls')
        self.notice_pages[1] = Notice(game, 'notice')
        self.notice_pages[2] = Notice(game, 'loot_n')
        self.notice_pages[3] = Notice(game, 'loot_r')
        for index in range(1, len(self.notice_pages)):
            self.notice_pages[index].rect.x = self.screen.get_width()
        self.notice_index = 0
        right_arrow = game.ui_dict['arrow'].copy()
        left_arrow = pg.transform.flip(right_arrow, True, False)
        for notice in self.notice_pages.values():
            notice.buttons_dict['right_arrow'] = ImgButton(right_arrow, centerx=int(self.notice.image.get_width() / 2 + 200), top=518)
            notice.buttons_dict['left_arrow'] = ImgButton(left_arrow, centerx=int(self.notice.image.get_width() / 2 - 200), top=518)

    def get_current_notice(self):
        return self.notice_pages[self.notice_index]

    def get_prev_notice(self):
        index = (self.notice_index - 1) % len(self.notice_pages)
        return self.notice_pages[index]
    
    def get_next_notice(self):
        index = (self.notice_index + 1) % len(self.notice_pages)
        return self.notice_pages[index]

    def add_button(self, size, index, x, y):
        return StaticButton(self.font_path, size, self.font_clr, self.lang_dict[index], left=x, centery=y)

    def set_buttons(self):
        size = 40
        notice_1_buttons = self.notice_pages[0].buttons_dict
        notice_1_buttons['008'] = self.add_button(size, '008', 256, 176)
        notice_1_buttons['009'] = self.add_button(size, '009', 214, 260)
        notice_1_buttons['010'] = self.add_button(size, '010', 214, 344)
        notice_1_buttons['011'] = self.add_button(size, '011', 214, 428)
        notice_1_buttons['012'] = self.add_button(size, '012', 628, 428)
        notice_1_buttons['013'] = self.add_button(size, '013', 546, 176)
        notice_1_buttons['007'] = self.add_button(size, '007', 546, 260)
        notice_1_buttons['014'] = self.add_button(size, '014', 615, 344)
        notice_1_buttons['015'] = StaticButton(self.font_path, 50, (28, 13, 75), self.lang_dict['015'], centerx=432, centery=70)
        size = 32
        notice_2_buttons = self.notice_pages[1].buttons_dict
        notice_2_buttons['016'] = StaticButton(self.font_path, 50, (28, 13, 75), self.lang_dict['016'], centerx=432, centery=70)
        notice_2_buttons['017'] = self.add_button(size, '017', 50, 160)
        notice_2_buttons['019'] = self.add_button(size, '019', 50, 220)
        notice_2_buttons['020'] = self.add_button(size, '020', 50, 280)
        notice_2_buttons['021'] = self.add_button(size, '021', 50, 340)
        notice_2_buttons['022'] = self.add_button(size, '022', 50, 400)
        notice_2_buttons['023'] = self.add_button(16, '023', 60, 440)
        notice_3_buttons = self.notice_pages[2].buttons_dict
        notice_3_buttons['075'] = StaticButton(self.font_path, 50, (28, 13, 75), self.lang_dict['075'], centerx=432, centery=70)
        notice_3_buttons['076'] = StaticButton(self.font_path, 40, self.font_clr, self.lang_dict['076'], centerx=432, centery=544)
        notice_3_buttons['077'] = self.add_button(32, '077', 215, 172)
        notice_3_buttons['078'] = self.add_button(32, '078', 215, 236)
        notice_3_buttons['079'] = self.add_button(32, '079', 215, 300)
        notice_3_buttons['080'] = self.add_button(32, '080', 215, 364)
        notice_3_buttons['081'] = self.add_button(32, '081', 215, 428)
        n4_buttons = self.notice_pages[3].buttons_dict
        n4_buttons['075'] = StaticButton(self.font_path, 50, (28, 13, 75), self.lang_dict['075'], centerx=432, centery=70)
        n4_buttons['082'] = StaticButton(self.font_path, 40, self.font_clr, self.lang_dict['082'], centerx=432, centery=544)
        n4_buttons['083'] = self.add_button(28, '083', 150, 142)
        n4_buttons['084'] = self.add_button(28, '084', 150, 206)
        n4_buttons['085'] = self.add_button(28, '085', 150, 270)
        n4_buttons['086'] = self.add_button(28, '086', 150, 334)
        n4_buttons['087'] = self.add_button(28, '087', 150, 398)
        n4_buttons['088'] = self.add_button(28, '088', 150, 462)
    
    def update(self, game):
        if super().update(game)[0]:
            for notice in self.notice_pages.values():
                notice.refresh()
            self.set_buttons()
        self.check_events(game.events)
        transition_check = []
        closed = []
        done = []
        for notice in self.notice_pages.values():
            closed.append(notice.check_close(game.events))
            done.append(notice.transition_vertical())
        if any(closed):
            self.game.sfx_manager.play('paper')
            self.get_current_notice().target_y = self.screen.get_height()
            self.get_current_notice().transition_vel_y = 0
            if self.game.main_screen:
                self.game.main_menu = True
        if any(done):
            self.initialize_notices(game)
            self.set_buttons()
            if self.game.main_screen:
                self.game.help_menu = False
            else:
                game.p_m.display_help = False
            if self.side_transition:
                    transition_check.append(notice.transition_horizontal())
        if transition_check.count(True) == len(self.notice_pages):
            self.side_transition = False
    
    def execute_left_transition(self):
        self.game.sfx_manager.play('paper')
        self.get_next_notice().prepare_off_screen('left')
        self.get_current_notice().send_off_screen('left')
        self.side_transition = True
        self.notice_index += 1
        self.notice_index %= len(self.notice_pages)

    def execute_right_transition(self):
        self.game.sfx_manager.play('paper')
        self.get_prev_notice().prepare_off_screen('right')
        self.get_current_notice().send_off_screen('right')
        self.side_transition = True
        self.notice_index -= 1
        self.notice_index %= len(self.notice_pages)


    def check_events(self, events):
        for event in events:
            if event.type == pg.MOUSEBUTTONDOWN:
                if event.button == 1:
                    if self.get_current_notice().buttons_dict['right_arrow'].check_mouseover(48, 48) and not self.side_transition:
                        self.execute_left_transition()
                    if self.get_current_notice().buttons_dict['left_arrow'].check_mouseover(48, 48) and not self.side_transition:
                        self.execute_right_transition()
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_LEFT and not self.side_transition:
                    self.execute_right_transition()
                if event.key == pg.K_RIGHT and not self.side_transition:
                    self.execute_left_transition()
            
    def render(self, display):
        self.overlay.fill((0, 0, 0, 0))
        for notice in self.notice_pages.values():
            self.overlay.blit(notice.image, notice.rect)
            for button in notice.buttons_dict.values():
                notice.image.blit(button.image, button.rect)
        display.blit(self.overlay, (0, 0))


class PauseMenu(Menu):
    def __init__(self, game):
        super().__init__(game)
        self.font_clr = (128, 106, 230)
        self.font_clr_2 = (140, 110, 240)
        self.font_clr_3 = (255, 250, 255)
        self.font_clr_4 = (110, 134, 242)
        self.hover_buttons = {}
        self.stats_dict = GameOverStats(game.g_o, game).combined_stat_dict.copy()
        self.stat_menu = StatsMenu(game)
        self.set_buttons()
        self.buttons_list = ["025", "034", "033", "026", "027", "089"]
        self.keyboard_ctrl = False
        self.select = 0
        self.selected_button = None
        self.to_mainmenu = False
        self.display_help = False
        self.display_stats = False

    def set_buttons(self):
        self.buttons_dict = {}
        self.hover_buttons = {}
        self.buttons_dict['024'] = StaticButton(self.font_path, 50, self.font_clr, self.lang_dict['024'], centerx=self.screen.get_width() / 2, top=60)
        self.buttons_dict['025'] = Button(self.font_path, 40, self.font_clr_2, self.lang_dict['025'], centerx=self.screen.get_width() / 2, centery=200)
        self.buttons_dict['034'] = Button(self.font_path, 40, self.font_clr_2, self.lang_dict['034'], centerx=self.screen.get_width() / 2, centery=270)
        self.buttons_dict['033'] = Button(self.font_path, 40, self.font_clr_2, self.lang_dict['033'], centerx=self.screen.get_width() / 2, centery=340)
        self.buttons_dict['026'] = Button(self.font_path, 40, self.font_clr_2, self.lang_dict['026'], centerx=self.screen.get_width() / 2, centery=410)
        self.buttons_dict['027'] = Button(self.font_path, 40, self.font_clr_2, self.lang_dict['027'], centerx=self.screen.get_width() / 2, centery=480)
        # stats
        self.buttons_dict['065'] = StaticButton(self.font_path, 26, self.font_clr_4, self.stats_dict['065'], left=30, centery=270)
        self.buttons_dict['066'] = StaticButton(self.font_path, 26, self.font_clr_4, self.stats_dict['066'], left=30, centery=300)
        self.buttons_dict['067'] = StaticButton(self.font_path, 26, self.font_clr_4, self.stats_dict['067'], left=30, centery=330)
        self.buttons_dict['068'] = StaticButton(self.font_path, 26, self.font_clr_4, self.stats_dict['068'], left=30, centery=360)
        self.buttons_dict['089'] = Button(self.font_path, 26, self.font_clr_4, self.lang_dict['089'], left=45, centery=410)
        if self.language == 'kor':
            hover_size = 28
        else:
            hover_size = 20
        self.hover_buttons['028'] = StaticButton(self.font_path, hover_size, self.font_clr_3, self.lang_dict['028'], centerx=self.screen.get_width() / 2, centery=540)
        self.hover_buttons['029'] = StaticButton(self.font_path, hover_size, self.font_clr_3, self.lang_dict['029'], centerx=self.screen.get_width() / 2, centery=580)
        self.hover_buttons['035'] = StaticButton(self.font_path, hover_size, self.font_clr_3, self.lang_dict['035'], centerx=self.screen.get_width() / 2, centery=540)
        self.buttons_dict['030'] = StaticButton(self.font_path, 28, self.font_clr, self.lang_dict['030'], centerx=self.screen.get_width() / 2, centery=650)


    def update_stats(self, game):
        self.stats_instance = GameOverStats(game.g_o, game)
        self.stats_dict = self.stats_instance.combined_stat_dict.copy()
        self.set_buttons()

    def on_close(self):
        self.set_buttons()
        self.display_help = False
        self.display_stats = False

    def select_button(self):
        if self.keyboard_ctrl:
            selection = self.select % len(self.buttons_list)
            b_index = self.buttons_list[selection]
            selected_button = self.buttons_dict[b_index]
            highlight_surf = selected_button.get_button_mask()
            self.buttons_dict[b_index].image = highlight_surf
            return b_index
    
    def execute_press_events(self, button_name):
        if button_name == 'resume':
            self.game.game_paused = False
            self.set_buttons()
        elif button_name == 'mainmenu':
            self.to_mainmenu = True
            self.game.music_manager.prepare_next_music('Pixel_3.wav', 80)
        elif button_name == 'help':
            self.game.sfx_manager.play('paper')
            self.display_help = True
        elif button_name == 'stats':
            self.game.st_m = StatsMenu(self.game)
            self.game.sfx_manager.play('paper')
            self.display_stats = True
        elif button_name == 'save':
            self.game.save_game_data()
            self.game.sfx_manager.play('loot')
            self.buttons_dict['saved'] = Button(self.font_path, 34, self.font_clr_3, self.lang_dict['038'], centerx=self.screen.get_width() / 2, top=130)
        elif button_name == 'quit':
            pg.quit()
            sys.exit()
        
    def check_events(self, events):
        for event in events:
            if event.type == pg.MOUSEBUTTONDOWN:
                if event.button == 1:
                    if self.buttons_dict["025"].check_mouseover():
                        self.execute_press_events('resume')
                    if self.buttons_dict["026"].check_mouseover():
                        self.execute_press_events('mainmenu')
                    if self.buttons_dict["027"].check_mouseover():
                        self.execute_press_events('quit')
                    if self.buttons_dict["033"].check_mouseover():
                        self.execute_press_events('help')
                    if self.buttons_dict["089"].check_mouseover():
                        self.execute_press_events('stats')
                    if self.buttons_dict["034"].check_mouseover():
                        self.execute_press_events('save')
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_UP:
                    if not self.keyboard_ctrl:
                        self.keyboard_ctrl = True
                        self.select = 1
                    self.select -= 1
                if event.key == pg.K_DOWN:
                    if not self.keyboard_ctrl:
                        self.keyboard_ctrl = True
                        self.select = -1
                    self.select += 1
                if event.key == pg.K_SPACE or event.key == pg.K_RETURN:
                    if self.selected_button == '025':
                        self.execute_press_events('resume')
                    if self.selected_button == '026':
                        self.execute_press_events('mainmenu')
                    if self.selected_button == '027':
                        self.execute_press_events('quit')
                    if self.selected_button == '033':
                        self.execute_press_events('help')
                    if self.selected_button == '089':
                        self.execute_press_events('stats')
                    if self.selected_button == '034':
                        self.execute_press_events('save')
                if event.key == pg.K_p or event.key == pg.K_BACKSPACE or event.key == pg.K_ESCAPE:
                    if not self.display_help and not self.display_stats:
                        self.on_close()
    
    def update(self, game):
        if not self.display_help and not self.display_stats:
            mouse = super().update(game)[1]
            if mouse and self.keyboard_ctrl:
                self.keyboard_ctrl = False
                for button in self.buttons_dict.values():
                    button.set_image_rect()
            self.check_events(game.events)
            self.selected_button = self.select_button()
        if self.to_mainmenu and game.fade_midpoint:
            self.game.playing = False
            self.game.initialize_menus()
        elif self.to_mainmenu:
            game.fade_state = 'fade_out'

    
    def render(self, display):
        display.fill((58, 56, 88, 210))
        super().render(display)
        if self.buttons_dict['027'].check_mouseover() or self.selected_button == '027' or self.buttons_dict['026'].check_mouseover() or self.selected_button == '026':
            self.hover_buttons['028'].render(display)
            self.hover_buttons['029'].render(display)
        if self.buttons_dict['034'].check_mouseover() or self.selected_button == '034':
            self.hover_buttons['035'].render(display)


class GameOver(Menu):
    def __init__(self, game):
        super().__init__(game)
        self.font_clr = (116, 86, 207)
        self.font_clr_2 = (170, 170, 250)
        tombstone_image = self.game.player_anims['die'].images[4].copy()
        self.tombstone_image = pg.transform.scale_by(tombstone_image, 14)
        self.tombstone_rect = self.tombstone_image.get_rect()
        self.tombstone_rect.center = self.screen.get_width() / 2, self.screen.get_height() / 2 - 10
        self.display_stats = False
        self.stats_screen = GameOverStats(self, game)
        self.overlay_surf = pg.Surface(self.screen.get_size())
        self.set_buttons()

    def set_buttons(self):
        self.buttons_dict['40'] = StaticButton(self.font_path, 24, self.font_clr, self.stats_screen.combined_stat_dict['040'], left=30, centery = 40)
        self.buttons_dict['41'] = StaticButton(self.font_path, 24, self.font_clr, self.stats_screen.combined_stat_dict['041'], left=30, centery = 70)
        self.buttons_dict['039'] = StaticButton(self.font_path, 80, self.font_clr, self.lang_dict['039'], centerx= self.screen.get_width() / 2, top=70)
        self.buttons_dict['069'] = StaticButton(self.font_path, 28, self.font_clr, self.lang_dict['069'], centerx= self.screen.get_width() / 2, top=180)
        self.buttons_dict['070'] = StaticButton(self.font_path, 28, self.font_clr, self.lang_dict['070'], centerx= self.screen.get_width() / 2, top=220)
        self.buttons_dict['031'] = StaticButton(self.font_path, 36, self.font_clr, self.lang_dict['031'], centerx= self.screen.get_width() / 2, top=510)
        self.buttons_dict['032'] = StaticButton(self.font_path, 36, self.font_clr, self.lang_dict['032'], centerx= self.screen.get_width() / 2, top=560)
        self.buttons_dict['072'] = Button(self.font_path, 36, self.font_clr, self.lang_dict['072'], centerx= self.screen.get_width() / 2, top=640)
        if self.game.new_record:
            self.buttons_dict['071'] = StaticButton(self.font_path, 44, self.font_clr_2, self.lang_dict['071'], centerx=self.screen.get_width() / 2, top=20)

    def check_events(self, events):
        for event in events:
            if event.type == pg.KEYDOWN:
                if event.key != pg.K_q:
                    self.game.music_manager.prepare_next_music('Pixel_3.wav', 60)
                    self.game.fade_state = 'fade_out'
            if event.type == pg.MOUSEBUTTONDOWN:
                if event.button == 1:
                    if self.buttons_dict['072'].check_mouseover() and not self.display_stats:
                        self.display_stats = True
    
    def update(self, game):
        super().update(game)
        if self.display_stats:
            self.stats_screen.update(game)
        else:
            self.check_events(game.events)

    def render(self, surf):
        self.overlay_surf.fill((4, 3, 18))
        if self.display_stats:
            self.stats_screen.render(self.overlay_surf)
        else:
            self.overlay_surf.blit(self.tombstone_image, self.tombstone_rect)
            super().render(self.overlay_surf)
        surf.blit(self.overlay_surf, (0, 0))


class GameOverStats(Menu):
    def __init__(self, gom, game):
        super().__init__(game)
        self.gom = gom
        self.font_clr = (116, 86, 207)
        self.stats_dict = {}
        self.combined_stat_dict = {}
        self.overlay = pg.Surface(self.screen.get_size())
        self.get_stats()
        self.get_final_stats()
        self.set_buttons()

    def get_final_stats(self):
        for i in range(40, 69):
            str_ind = f"{i:03}"
            self.combined_stat_dict[str_ind] = (self.lang_dict[str_ind] + str(self.stats_dict[str_ind]))

    def set_buttons(self):
        left_x = 100
        top_y = 60
        top_y_2 = 60
        first_column = [ind for ind in range(65, 69)] + [i for i in range(40, 51)]
        second_column = [_ for _ in range(51, 65)]
        for i in first_column:
            str_ind = f"{i:03}"
            self.buttons_dict[str_ind] = StaticButton(self.font_path, 24, self.font_clr, self.combined_stat_dict[str_ind], left=left_x, top=top_y)
            top_y += 30
        for i in second_column:
            str_ind = f"{i:03}"
            left_x = 530
            self.buttons_dict[str_ind] = StaticButton(self.font_path, 24, self.font_clr, self.combined_stat_dict[str_ind], left=left_x, top=top_y_2)
            top_y_2 += 30

        self.buttons_dict['return'] = Button(self.font_path, 40, self.font_clr, self.lang_dict['073'], centerx=self.screen.get_width() / 2, top=640)
    

    def get_stats(self):
        self.stats_dict['040'] = self.game.stage_no
        self.stats_dict['041'] = self.game.clear_streak
        self.stats_dict['042'] = self.game.cleared_maps
        self.stats_dict['043'] = self.game.deaths
        self.stats_dict['044'] = self.game.killed_enemies['total']
        self.stats_dict['045'] = self.game.killed_enemies['sl_g']
        self.stats_dict['046'] = self.game.killed_enemies['sl_y']
        self.stats_dict['047'] = self.game.killed_enemies['sl_r']
        self.stats_dict['048'] = self.game.looted_chests['total']
        self.stats_dict['049'] = self.game.looted_chests['normal']
        self.stats_dict['050'] = self.game.looted_chests['rare']
        self.stats_dict['051'] = self.game.looted_items['total']
        self.stats_dict['052'] = self.game.looted_items['normal_loot']
        self.stats_dict['053'] = self.game.looted_items['goo']
        self.stats_dict['054'] = self.game.looted_items['hp']
        self.stats_dict['055'] = self.game.looted_items['ap']
        self.stats_dict['056'] = self.game.looted_items['l_hp']
        self.stats_dict['057'] = self.game.looted_items['l_ap']
        self.stats_dict['058'] = self.game.looted_items['rare_loot']
        self.stats_dict['059'] = self.game.looted_items['gold_goo']
        self.stats_dict['060'] = self.game.looted_items['fill_ahp']
        self.stats_dict['061'] = self.game.looted_items['max_jump_book']
        self.stats_dict['062'] = self.game.looted_items['max_dash_book']
        self.stats_dict['063'] = self.game.looted_items['max_hp_book']
        self.stats_dict['064'] = self.game.looted_items['max_ap_book']
        self.stats_dict['065'] = self.game.player.max_health
        self.stats_dict['066'] = self.game.player.max_mana
        self.stats_dict['067'] = self.game.player.max_jumps
        self.stats_dict['068'] = self.game.player.max_dashes


    def check_events(self, events):
        for event in events:
            if event.type == pg.MOUSEBUTTONDOWN:
                if event.button == 1:
                    if self.buttons_dict['return'].check_mouseover():
                        self.gom.display_stats = False


    def update(self, game):
        super().update(game)
        self.check_events(game.events)

    
    def render(self, surf):
        self.overlay.fill((4, 3, 18))
        for button in self.buttons_dict.values():
            button.render(self.overlay)
        super().render(surf)


class Hud:
    def __init__(self, game):
        self.game = game
        self.display = self.game.display
        self.font_path = self.game.font_path
        self.player = self.game.player
        self.images = self.game.hud_dict.copy()
        self.stage_no = self.game.stage_no
        self.pl_hp = self.player.health
        self.pl_max_hp = self.player.max_health
        self.pl_ap = self.player.mana
        self.pl_max_ap = self.player.max_mana
        self.show_low_hp = False
        self.show_low_ap = False
        self.show_death_hud = False
        self.jump_frame_no = self.player.max_jumps
        self.current_jumps = self.player.jumps
        self.dash_frame_no = self.player.max_dashes
        self.ready_dashes = self.player.dashes
        self.dash_cds = self.player.dash_cooldowns

        self.portrait_anims = self.game.portrait_anims['idle'].copy()
        self.portrait_image = self.portrait_anims.cur_img()
        self.stage_image = self.portrait_anims.cur_img()
        self.portrait_faces = self.game.portrait_anims['faces'].images.copy()
        self.portrait_face = self.portrait_faces[0]
        self.portrait_dead = self.images['portrait_dead']
        self.bars_dead = self.images['bars_dead']
        self.hp_frame = self.images['hp_frame']
        self.ap_frame = self.images['ap_frame']
        self.hp_bar = self.images['hp_bar']
        self.ap_bar = self.images['ap_bar']
        self.hp_low_bar = self.images['hp_low']
        self.ap_low_bar = self.images['ap_low']
        self.jump_frame = self.images['jump_frame']
        self.jump_bar = pg.Surface((12, 2))
        self.jump_bar.fill((204, 246, 246))
        self.dash_frame = self.images['dash_frame']
        self.dash_cd = self.images['dash_cd']
        self.dash_ready = self.images['dash_ready']
        self.dash_cd_subsurfs = []
        self.jumps_dead = self.images['jumps_dead']
        self.dashes_dead = self.images['dashes_dead']

        self.stage_image_topleft = (self.display.get_width() - 36, 10)
        self.stage_image_rect = self.stage_image.get_rect()
        self.portrait_topleft = (10, 10)
        self.portrait_face_topleft = (14, 14)
        self.hp_frame_topleft = (36, 15)
        self.ap_frame_topleft = (36, 25)
        self.hp_bar_topleft = (36, 16)
        self.ap_bar_topleft = (36, 26)
        self.dead_bars_topleft = (36, 13)
        self.jump_frame_topleft = (10, 41)
        self.jump_bar_topleft = (11, 42)
        self.dash_icon_topleft = (12, 50)
        self.dead_jumps_topleft = (11, 42)
        self.dead_dashes_topleft = (14, 50)

        self.set_stage_no_text()
        self.set_hp_bars()
        self.set_ap_bars()


    def set_hp_bars(self):
        self.hp_frame_length = round((self.pl_max_hp - 10) * 2.5 + 51)
        self.hp_bar_length = round((self.hp_frame_length - 1) / self.pl_max_hp * self.pl_hp)
        self.hp_frame_area = (101 - self.hp_frame_length, 0, self.hp_frame_length, 8)
        self.hp_bar_area = (100 - self.hp_bar_length, 0, self.hp_bar_length, 6)

    def set_ap_bars(self):
        self.ap_frame_length = round((self.pl_max_ap - 10) * 2.5 + 51)
        self.ap_bar_length = round((self.ap_frame_length - 1) / self.pl_max_ap * self.pl_ap)
        self.ap_frame_area = (101 - self.ap_frame_length, 0, self.ap_frame_length, 8)
        self.ap_bar_area = (100 - self.ap_bar_length, 0, self.ap_bar_length, 6)

    def set_bar_subsurfaces(self):
        self.hp_frame_subsurf = self.hp_frame.subsurface(self.hp_frame_area)
        self.ap_frame_subsurf = self.ap_frame.subsurface(self.ap_frame_area)
        if self.show_low_hp:
            self.hp_bar_subsurf = self.hp_low_bar.subsurface(self.hp_bar_area)
        else:
            self.hp_bar_subsurf = self.hp_bar.subsurface(self.hp_bar_area)
        if self.show_low_ap:
            self.ap_bar_subsurf = self.ap_low_bar.subsurface(self.ap_bar_area)
        else:
            self.ap_bar_subsurf = self.ap_bar.subsurface(self.ap_bar_area)

    def set_stage_no_text(self):
        self.stage_text = str(self.stage_no)
        self.stage_text_image = pg.font.Font(self.font_path, 16).render(self.stage_text, True, (200, 190, 240), None)
        self.stage_text_rect = self.stage_text_image.get_rect()

    def update_bars(self, game):
        if self.pl_max_hp != game.player.max_health or self.pl_hp != game.player.health:
            self.pl_max_hp = game.player.max_health
            self.pl_hp = game.player.health
            self.set_hp_bars()
        if self.pl_max_ap != game.player.max_mana or self.pl_ap != game.player.mana:
            self.pl_max_ap = game.player.max_mana
            self.pl_ap = game.player.mana
            self.set_ap_bars()
        if self.pl_hp < 4:
            self.show_low_hp = True
        else:
            self.show_low_hp = False
        if self.pl_ap < 4:
            self.show_low_ap = True
        else:
            self.show_low_ap = False

    def update_face(self, game):
        self.player = game.player
        if self.player.dead:
            self.portrait_face = self.portrait_faces[4]
        elif self.player.flicker_countdown:
            self.portrait_face = self.portrait_faces[2]
        elif self.player.display_emote:
            self.portrait_face = self.portrait_faces[3]
        elif self.player.health == self.player.max_health and self.player.mana == self.player.max_mana:
            self.portrait_face = self.portrait_faces[1]
        else:
            self.portrait_face = self.portrait_faces[0]

    def update_jumps(self, game):
        if self.jump_frame_no != game.player.max_jumps:
            self.jump_frame_no = game.player.max_jumps
        if self.current_jumps != game.player.jumps:
            self.current_jumps = game.player.jumps
    
    def update_dash_subsurfaces(self):
        self.dash_cd_subsurfs = []
        for cd in self.dash_cds:
            self.dash_cd_subsurfs.append(self.dash_cd.copy().subsurface(0, int(cd / 10), 10, 10 - int(cd / 10)))
    
    def update_dashes(self, game):
        if self.dash_frame_no != game.player.max_dashes:
            self.dash_frame_no = game.player.max_dashes
        self.ready_dashes = game.player.dashes

    def set_dead_jump_bars(self, game):
        total_jumps = game.player.max_jumps
        self.dead_jumps_subsurf = self.jumps_dead.subsurface(0, 0, min(total_jumps * 18, 71), 5)
    
    def set_dead_dash_bars(self, game):
        total_dashes = game.player.max_dashes
        self.dead_dashes_subsurf = self.dashes_dead.subsurface(0, 0, min(total_dashes * 17, 64), 13)

    def update_stage_number(self, game):
        if self.stage_no != game.stage_no:
            self.stage_no = game.stage_no
        self.set_stage_no_text()

    def update(self, game):
        if game.player.dead:
            self.show_death_hud = True
            self.portrait_image = self.portrait_dead
            self.stage_image = self.portrait_image
            self.set_dead_jump_bars(game)
            self.set_dead_dash_bars(game)
        else:
            self.portrait_anims.update()
            self.portrait_image = self.portrait_anims.cur_img()
            self.stage_image = self.portrait_image
            self.update_jumps(game)
            self.update_dashes(game)
            self.update_dash_subsurfaces()
        self.update_stage_number(game)
        self.update_face(game)
        self.update_bars(game)
        self.set_bar_subsurfaces()

    def draw_dash_hud(self, display):
        for i in range(self.dash_frame_no):
            display.blit(self.dash_frame, (self.dash_icon_topleft[0] + i * 13, self.dash_icon_topleft[1]))
        for i in range(self.ready_dashes):
            display.blit(self.dash_ready, (self.dash_icon_topleft[0] + i * 13, self.dash_icon_topleft[1]))
        for i, surf in enumerate(self.dash_cd_subsurfs):
            top_y = 10 - surf.get_height()
            display.blit(surf, (self.dash_icon_topleft[0] + (self.ready_dashes + i) * 13, self.dash_icon_topleft[1] + top_y))

    def draw_jump_hud(self, display):
        for i in range(self.jump_frame_no):
            display.blit(self.jump_frame, (self.jump_frame_topleft[0] + i * 13, self.jump_frame_topleft[1]))
        for i in range(self.current_jumps):
            display.blit(self.jump_bar, (self.jump_bar_topleft[0] + i * 13, self.jump_bar_topleft[1]))

    def draw_ap_hp_hud(self, display):
        display.blit(self.hp_frame_subsurf, self.hp_frame_topleft)
        display.blit(self.ap_frame_subsurf, self.ap_frame_topleft)
        display.blit(self.hp_bar_subsurf, self.hp_bar_topleft)
        display.blit(self.ap_bar_subsurf, self.ap_bar_topleft)

    def draw_stage_no_hud(self, display):
        stage_image_copy = self.stage_image.copy()
        self.stage_text_rect.center = self.stage_image_rect.center
        stage_image_copy.blit(self.stage_text_image, (self.stage_text_rect.x, self.stage_text_rect.y + 1))
        display.blit(stage_image_copy, self.stage_image_topleft)

    def render(self, display):
        display.blit(self.portrait_image, self.portrait_topleft)
        display.blit(self.portrait_face, self.portrait_face_topleft)
        display.blit(self.stage_image, self.stage_image_topleft)
        self.draw_stage_no_hud(display)
        if self.show_death_hud:
            display.blit(self.bars_dead, self.dead_bars_topleft)
            display.blit(self.dead_jumps_subsurf, self.dead_jumps_topleft)
            display.blit(self.dead_dashes_subsurf, self.dead_dashes_topleft)
        else:
            self.draw_ap_hp_hud(display)
            self.draw_jump_hud(display)
            self.draw_dash_hud(display)
            
            
       

