import re
import random
from pathlib import Path

try:
    import pygame
    HAS_PYGAME = True
except ImportError:
    HAS_PYGAME = False

class TEHAudio:
    def __init__(self, base_dir, master=0.8, music=0.5, sfx=0.8, hb=0.3):
        self.base_dir = Path(base_dir)
        self.enable = HAS_PYGAME
        self.master, self.music_vol, self.sfx_vol, self.hb_vol = master, music, sfx, hb
        
        self.current_music = None
        self.sfx_cache = {}
        self.music_cache = {}
        self.sfx_index = {}
        self.music_index = {}
        
        if self.enable:
            try:
                pygame.mixer.pre_init(44100, -16, 2, 512)
                pygame.mixer.init()
                pygame.mixer.set_num_channels(16)
                pygame.mixer.set_reserved(2)
                self.ch_bgm = pygame.mixer.Channel(0)
                self.ch_hb = pygame.mixer.Channel(1)
            except Exception as e:
                self.enable = False
                return
        else:
            return

        self.scan(self.base_dir)

    def _norm(self, s): return re.sub(r'[\s\-_]+', '', s.lower())

    def scan(self, target_dir):
        self.base_dir = Path(target_dir)
        self.sfx_index.clear(); self.music_index.clear()
        self.music_cache.clear(); self.sfx_cache.clear()
        
        exts = [".mp3", ".ogg", ".wav", ".m4a"]
        for f in self.base_dir.rglob("*"):
            if f.is_file() and f.suffix.lower() in exts:
                name = self._norm(f.stem)
                fpath = f.resolve()
                if any(x in name for x in ["bip", "message", "heart", "carriage", "typing"]):
                    self.sfx_index[name] = fpath
                else:
                    for key in ["start", "calm", "tension", "urgency", "climax", "resolution", "defeat", "victory"]:
                        if key in name or f.parent.name.lower() == key:
                            k = key
                            if k not in self.music_index: self.music_index[k] = []
                            self.music_index[k].append(fpath)
                            break

    def set_volumes(self, m, mu, sfx, hb):
        self.master, self.music_vol, self.sfx_vol, self.hb_vol = m, mu, sfx, hb
        if self.ch_bgm.get_busy(): self.ch_bgm.set_volume(self.music_vol * self.master)
        if self.ch_hb.get_busy(): self.ch_hb.set_volume(self.hb_vol * self.master)

    def play_sfx(self, name):
        if not self.enable: return
        path = self.sfx_index.get(self._norm(name))
        if not path: return
        try:
            if name not in self.sfx_cache: 
                self.sfx_cache[name] = pygame.mixer.Sound(str(path))
            s = self.sfx_cache[name]
            s.set_volume(self.sfx_vol * self.master)
            ch = pygame.mixer.find_channel(True) 
            if ch: ch.play(s)
        except Exception as e:
            print(f"[音效失败] {name}: {e}")

    def play_music(self, seg):
        if not self.enable: return
        files = self.music_index.get(seg.lower())
        if not files: return
        try:
            path = random.choice(files)
            if str(path) not in self.music_cache:
                self.music_cache[str(path)] = pygame.mixer.Sound(str(path))
            s = self.music_cache[str(path)]
            
            self.ch_bgm.stop()  # 核心修复：每次强制截断并重播
            self.ch_bgm.set_volume(self.music_vol * self.master)
            self.ch_bgm.play(s, loops=-1) 
            self.current_music = seg
            print(f"[BGM] 切歌 -> {seg}")
        except Exception as e:
            print(f"[BGM失败] {seg}: {e}")

    def stop_music(self):
        if not self.enable: return
        self.ch_bgm.stop()
        self.current_music = None

    def start_heartbeat(self):
        if not self.enable or self.ch_hb.get_busy(): return
        path = self.sfx_index.get(self._norm("steadyheartbeatloop"))
        if not path: return
        try:
            if "hb" not in self.sfx_cache: 
                self.sfx_cache["hb"] = pygame.mixer.Sound(str(path))
            s = self.sfx_cache["hb"]
            s.set_volume(self.hb_vol * self.master)
            self.ch_hb.play(s, loops=-1)
        except: pass

    def stop_heartbeat(self):
        if self.enable: self.ch_hb.stop()

    def stop_all(self):
        if not self.enable: return
        pygame.mixer.stop()
        self.current_music = None

    def set_tension(self, tension):
        # 核心修复：高度紧张强制切 climax，中高切 urgency
        if tension >= 7: seg = "climax"
        elif tension >= 5: seg = "urgency"
        elif tension == 4: seg = "tension"
        else: seg = "calm"
        self.play_music(seg)