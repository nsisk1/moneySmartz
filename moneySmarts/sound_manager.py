import pygame
import os


class SoundManager:
    def __init__(self):
        self.available_music = {}  # name -> filepath
        self.available_sfx = {}    # name -> Sound object
        self.current_music = None
        self.music_volume = 0.5
        self.sfx_volume = 0.7
        self.mixer_ok = True
        # Try a few sensible mixer initialization attempts; fail gracefully
        try:
            pygame.mixer.init()
        except Exception:
            try:
                # Try common parameters
                pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
            except Exception:
                try:
                    pygame.mixer.init(frequency=22050, size=-16, channels=2)
                except Exception:
                    # mixer may fail in headless or missing audio env; continue but disable sound playback
                    self.mixer_ok = False

    def load_music(self, filepath, name):
        """Register a music file path by name (does not load into mixer until played)."""
        if not filepath:
            return
        self.available_music[name] = filepath

    def load_sfx(self, filepath, name):
        """Load a short sound effect into memory."""
        if not filepath:
            return
        if not self.mixer_ok:
            # still register the path so play_sfx can try to load later if mixer becomes available
            self.available_sfx[name] = None
            return
        try:
            snd = pygame.mixer.Sound(filepath)
            self.available_sfx[name] = snd
        except Exception:
            # keep None as placeholder
            self.available_sfx[name] = None

    def play_music(self, name, loops=-1):
        """Play background music by name."""
        if name not in self.available_music:
            return
        if not self.mixer_ok:
            return
        if self.current_music == name and pygame.mixer.music.get_busy():
            return
        try:
            path = self.available_music[name]
            # debug log
            try:
                import logging
                logging.debug(f"SoundManager: playing music {name} from {path}")
            except Exception:
                pass
            # visible debug print for user
            try:
                print(f"SoundManager: attempting to play music '{name}' from {path}")
            except Exception:
                pass
            pygame.mixer.music.load(path)
            pygame.mixer.music.set_volume(self.music_volume)
            pygame.mixer.music.play(loops)
            self.current_music = name
        except Exception:
            self.current_music = None

    def stop_music(self):
        if not self.mixer_ok:
            return
        try:
            pygame.mixer.music.stop()
        except Exception:
            pass
        self.current_music = None

    def set_volume(self, volume):
        self.music_volume = max(0.0, min(1.0, volume))
        if self.mixer_ok and pygame.mixer.music.get_busy():
            try:
                pygame.mixer.music.set_volume(self.music_volume)
            except Exception:
                pass

    def get_volume(self):
        return self.music_volume

    def get_available_music(self):
        return list(self.available_music.keys())

    def get_available_sfx(self):
        return list(self.available_sfx.keys())

    def set_active_music(self, name):
        if name in self.available_music:
            self.play_music(name)

    def _search_local_sfx(self, name):
        """Search assets/sfx and assets/audio for a filename that starts with `name` (case-insensitive).
        Returns the first matching filepath or None.
        """
        try:
            current_dir = os.path.dirname(os.path.dirname(__file__))
            candidates = [os.path.join(current_dir, 'assets', 'sfx'), os.path.join(current_dir, 'assets', 'audio'), os.path.join(current_dir, 'assets')]
            lname = name.lower()
            for d in candidates:
                if not os.path.isdir(d):
                    continue
                for fname in os.listdir(d):
                    base, ext = os.path.splitext(fname)
                    if ext.lower() not in ('.wav', '.ogg', '.mp3'):
                        continue
                    if base.lower().startswith(lname):
                        return os.path.join(d, fname)
        except Exception:
            pass
        return None

    def play_sfx(self, name):
        """Play a short sound effect by name.
        - If the sound is preloaded it will be played.
        - If not preloaded, and a matching asset file exists, it will attempt to load and play it.
        - If mixer is unavailable, this is a no-op.
        """
        if not self.mixer_ok:
            return
        snd = self.available_sfx.get(name)
        # If sfx not preloaded but a music filepath exists for the name, try loading it as a short Sound
        if snd is None:
            # try to find a registered music path with the same name
            if name in self.available_music:
                try:
                    snd = pygame.mixer.Sound(self.available_music[name])
                    self.available_sfx[name] = snd
                except Exception:
                    snd = None
            # If still none, search local assets directories for a matching filename prefix
            if snd is None:
                path = self._search_local_sfx(name)
                if path:
                    try:
                        snd = pygame.mixer.Sound(path)
                        self.available_sfx[name] = snd
                    except Exception:
                        snd = None
        if snd:
            try:
                # debug log and visible print
                try:
                    import logging
                    logging.debug(f"SoundManager: playing sfx {name}")
                except Exception:
                    pass
                try:
                    print(f"SoundManager: playing sfx '{name}'")
                except Exception:
                    pass
                snd.set_volume(self.sfx_volume)
                snd.play()
            except Exception:
                pass
        else:
            # nothing loaded for this name; quietly ignore
            try:
                import logging
                logging.debug(f"SoundManager: sfx '{name}' not available")
            except Exception:
                pass
            try:
                print(f"SoundManager: sfx '{name}' not available")
            except Exception:
                pass
