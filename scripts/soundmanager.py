import os
import pygame as pg


class MusicManager:
    def __init__(self, game, path):
        audio_files = os.listdir(path)
        self.ambience_dict = {}
        for file in audio_files:
            self.ambience_dict[file] = os.path.join(path, file)
        self.load_next = True
        self.target_fade_out = 30
        self.fade_out = 30
        self.next_track_name = self.ambience_dict['Pixel_3.wav']

    def fadeout(self):
        if self.fade_out == self.target_fade_out:
            pg.mixer.music.fadeout(self.target_fade_out * 10)
        self.fade_out = max(self.fade_out - 1, 0)

    def prepare_next_music(self, track_name, fade_out_time):
        self.next_track_name = self.ambience_dict[track_name]
        self.target_fade_out = fade_out_time
        self.fade_out = fade_out_time
        self.load_next = True
    
    def load_next_music(self):
        if not self.fade_out and self.load_next:
            pg.mixer.music.load(self.next_track_name)
            pg.mixer.music.set_volume(0.15)
            pg.mixer.music.play(-1, fade_ms=500)
            self.load_next = False

    def stop_playing(self):
        pg.mixer.music.stop()

    def music_loop(self):
        self.fadeout()
        self.load_next_music()


class SfxManager:
    def __init__(self, path):
        self.sfx_dict = {}
        self.sound_dir = path
        self.initialize_sfx_dict()
        self.set_volumes()

    def initialize_sfx_dict(self):
        self.sfx_dict['chest_open'] = self.create_sound_object('chest_open.wav')
        self.sfx_dict['splash'] = self.create_sound_object('splash.wav')
        self.sfx_dict['paper'] = self.create_sound_object('paper.wav')
        self.sfx_dict['jump'] = self.create_sound_object('jump.wav')
        self.sfx_dict['hurt_enemy'] = self.create_sound_object('hurt_slime.wav')
        self.sfx_dict['loot'] = self.create_sound_object('loot.wav')
        self.sfx_dict['hurt_player'] = self.create_sound_object('hurt_player.wav')
        self.sfx_dict['attack_player'] = self.create_sound_object('attack_player.ogg')
        self.sfx_dict['attack_blob'] = self.create_sound_object('attack_blob.wav')


    def set_volumes(self):
        for sound in self.sfx_dict.values():
            sound.set_volume(0.2)
        self.sfx_dict['splash'].set_volume(0.05)
        self.sfx_dict['attack_blob'].set_volume(0.08)
        self.sfx_dict['hurt_enemy'].set_volume(0.1)
        self.sfx_dict['hurt_player'].set_volume(1)


    def create_sound_object(self, name):
        return pg.mixer.Sound(os.path.join(self.sound_dir, name))

    def play(self, name):
        self.sfx_dict[name].play()

