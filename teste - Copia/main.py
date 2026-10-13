import json
import os
import sys
from datetime import datetime
from pathlib import Path

import pygame


ROOT = Path(__file__).resolve().parent
STORY_PATH = ROOT / "story.json"
WIDTH, HEIGHT = 1280, 720
SLOT_COUNT = 9
RESOLUTIONS = [(960, 540), (1280, 720), (1600, 900), (1920, 1080)]

COLORS = {
    "ink": (18, 27, 39),
    "panel": (20, 31, 45),
    "panel_light": (33, 47, 61),
    "paper": (241, 236, 220),
    "muted": (172, 181, 181),
    "teal": (115, 207, 190),
    "coral": (235, 139, 115),
    "line": (97, 127, 130),
    "white": (255, 255, 255),
}

TEXT = {
    "pt": {
        "new_game": "Novo jogo",
        "continue": "Continuar",
        "load": "Carregar",
        "save": "Salvar",
        "settings": "Configurações",
        "quit": "Sair",
        "back": "Voltar",
        "empty": "Slot vazio",
        "clear": "Limpar",
        "confirm_clear": "Apagar este slot?",
        "choose": "O que você faz?",
        "next": "Continuar",
        "restart": "Recomeçar prólogo",
        "menu": "Voltar ao título",
        "resolution": "Resolução",
        "fullscreen": "Tela cheia",
        "windowed": "Janela",
        "language": "Idioma",
        "master": "Volume geral",
        "music": "Música",
        "sfx": "Efeitos",
        "on": "Ligada",
        "off": "Desligada",
        "save_title": "SALVAR PARTIDA",
        "load_title": "CARREGAR PARTIDA",
        "settings_title": "CONFIGURAÇÕES",
        "title_hint": "Uma história sobre os caminhos que escolhemos.",
        "slot_saved": "Partida salva.",
        "slot_cleared": "Slot apagado.",
        "no_save": "Ainda não há uma partida salva.",
        "language_name": "Português",
    },
    "en": {
        "new_game": "New game",
        "continue": "Continue",
        "load": "Load",
        "save": "Save",
        "settings": "Settings",
        "quit": "Quit",
        "back": "Back",
        "empty": "Empty slot",
        "clear": "Clear",
        "confirm_clear": "Delete this slot?",
        "choose": "What will you do?",
        "next": "Continue",
        "restart": "Restart prologue",
        "menu": "Return to title",
        "resolution": "Resolution",
        "fullscreen": "Fullscreen",
        "windowed": "Windowed",
        "language": "Language",
        "master": "Master volume",
        "music": "Music",
        "sfx": "Sound effects",
        "on": "On",
        "off": "Off",
        "save_title": "SAVE GAME",
        "load_title": "LOAD GAME",
        "settings_title": "SETTINGS",
        "title_hint": "A story about the paths we choose.",
        "slot_saved": "Game saved.",
        "slot_cleared": "Slot deleted.",
        "no_save": "There are no saved games yet.",
        "language_name": "English",
    },
}


def user_data_dir():
    base = os.environ.get("APPDATA")
    return Path(base) / "FioDeAmanha" if base else Path.home() / ".fio_de_amanha"


class VisualNovel:
    def __init__(self):
        pygame.init()
        self.data_dir = user_data_dir()
        self.save_dir = self.data_dir / "saves"
        self.save_dir.mkdir(parents=True, exist_ok=True)
        self.story = json.loads(STORY_PATH.read_text(encoding="utf-8"))
        self.settings = self.load_settings()
        self.window = pygame.display.set_mode(self.window_size(), self.display_flags())
        pygame.display.set_caption("Fio de Amanhã | Visual Novel Base")
        self.canvas = pygame.Surface((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("segoeui", 22)
        self.small_font = pygame.font.SysFont("segoeui", 16)
        self.medium_font = pygame.font.SysFont("segoeui", 28, bold=True)
        self.title_font = pygame.font.SysFont("georgia", 62, bold=True)
        self.background_cache = {}
        self.sprite_cache = {}
        self.screen = "title"
        self.return_screen = "title"
        self.slot_mode = "load"
        self.scene_id = self.story["start"]
        self.line_index = 0
        self.flags = {}
        self.hotspots = []
        self.dragging = None
        self.notice = ""
        self.notice_until = 0
        self.audio_ready = False
        self.init_audio()

    def load_settings(self):
        defaults = {
            "language": "pt",
            "resolution": [1280, 720],
            "fullscreen": False,
            "master_volume": 0.85,
            "music_volume": 0.65,
            "sfx_volume": 0.8,
        }
        path = self.data_dir / "settings.json"
        try:
            saved = json.loads(path.read_text(encoding="utf-8"))
            defaults.update(saved)
        except (OSError, json.JSONDecodeError):
            pass
        if self.settings_language(defaults.get("language")) not in TEXT:
            defaults["language"] = "pt"
        return defaults

    @staticmethod
    def settings_language(language):
        return language if language in TEXT else "pt"

    def save_settings(self):
        self.data_dir.mkdir(parents=True, exist_ok=True)
        (self.data_dir / "settings.json").write_text(
            json.dumps(self.settings, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def window_size(self):
        size = self.settings.get("resolution", [1280, 720])
        if tuple(size) not in RESOLUTIONS:
            size = [1280, 720]
        return tuple(size)

    def display_flags(self):
        return pygame.FULLSCREEN if self.settings.get("fullscreen") else 0

    def recreate_window(self):
        self.window = pygame.display.set_mode(self.window_size(), self.display_flags())

    def tr(self, key):
        return TEXT[self.settings_language(self.settings.get("language"))].get(key, key)

    def init_audio(self):
        try:
            pygame.mixer.init()
            self.audio_ready = True
            self.apply_audio_volumes()
            self.play_music()
        except pygame.error:
            self.audio_ready = False

    def apply_audio_volumes(self):
        if not self.audio_ready:
            return
        master = float(self.settings["master_volume"])
        pygame.mixer.music.set_volume(master * float(self.settings["music_volume"]))

    def play_music(self):
        music_path = ROOT / self.story.get("audio", {}).get("music", "")
        if self.audio_ready and music_path.is_file():
            try:
                pygame.mixer.music.load(str(music_path))
                pygame.mixer.music.play(-1)
            except pygame.error:
                pass

    def play_sfx(self, name):
        if not self.audio_ready:
            return
        path = ROOT / self.story.get("audio", {}).get("sfx", {}).get(name, "")
        if not path.is_file():
            return
        try:
            sound = pygame.mixer.Sound(str(path))
            sound.set_volume(
                float(self.settings["master_volume"]) * float(self.settings["sfx_volume"])
            )
            sound.play()
        except pygame.error:
            pass

    def slot_path(self, slot):
        return self.save_dir / f"slot_{slot:02d}.json"

    def slot_data(self, slot):
        try:
            return json.loads(self.slot_path(slot).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None

    def save_slot(self, slot):
        payload = {
            "scene_id": self.scene_id,
            "line_index": self.line_index,
            "flags": self.flags,
            "saved_at": datetime.now().isoformat(timespec="minutes"),
            "chapter": self.story["scenes"].get(self.scene_id, {}).get("title", "Prólogo"),
        }
        self.slot_path(slot).write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        self.show_notice(self.tr("slot_saved"))

    def load_slot(self, slot):
        data = self.slot_data(slot)
        if not data or data.get("scene_id") not in self.story["scenes"]:
            return
        self.scene_id = data["scene_id"]
        self.line_index = max(0, int(data.get("line_index", 0)))
        self.flags = data.get("flags", {})
        self.screen = "game"

    def clear_slot(self, slot):
        try:
            self.slot_path(slot).unlink()
            self.show_notice(self.tr("slot_cleared"))
        except FileNotFoundError:
            pass

    def new_game(self):
        self.scene_id = self.story["start"]
        self.line_index = 0
        self.flags = {}
        self.screen = "game"

    def show_notice(self, message):
        self.notice = message
        self.notice_until = pygame.time.get_ticks() + 1800

    def localized(self, value):
        if isinstance(value, dict):
            language = self.settings_language(self.settings.get("language"))
            return value.get(language, value.get("pt", next(iter(value.values()), "")))
        return str(value)

    def add_hotspot(self, rect, action):
        self.hotspots.append((pygame.Rect(rect), action))

    def draw_button(self, label, rect, action, *, selected=False, compact=False):
        rect = pygame.Rect(rect)
        hovered = rect.collidepoint(self.mouse_pos())
        fill = COLORS["teal"] if selected or hovered else COLORS["panel_light"]
        text_color = COLORS["ink"] if selected or hovered else COLORS["paper"]
        pygame.draw.rect(self.canvas, fill, rect, border_radius=5)
        pygame.draw.rect(self.canvas, COLORS["line"], rect, width=1, border_radius=5)
        font = self.small_font if compact else self.font
        rendered = font.render(label, True, text_color)
        self.canvas.blit(rendered, rendered.get_rect(center=rect.center))
        self.add_hotspot(rect, action)

    def draw_text(self, text, pos, font=None, color=None):
        font = font or self.font
        color = color or COLORS["paper"]
        rendered = font.render(str(text), True, color)
        self.canvas.blit(rendered, pos)

    def wrap_text(self, text, font, max_width):
        lines = []
        for paragraph in str(text).split("\n"):
            words = paragraph.split()
            current = ""
            for word in words:
                candidate = f"{current} {word}".strip()
                if current and font.size(candidate)[0] > max_width:
                    lines.append(current)
                    current = word
                else:
                    current = candidate
            lines.append(current)
        return lines

    def draw_wrapped(self, text, rect, font=None, color=None, line_gap=7):
        font = font or self.font
        color = color or COLORS["paper"]
        y = rect[1]
        for line in self.wrap_text(text, font, rect[2]):
            self.draw_text(line, (rect[0], y), font, color)
            y += font.get_linesize() + line_gap
        return y

    def mouse_pos(self):
        window_w, window_h = self.window.get_size()
        scale = min(window_w / WIDTH, window_h / HEIGHT)
        shown_w, shown_h = int(WIDTH * scale), int(HEIGHT * scale)
        offset_x, offset_y = (window_w - shown_w) // 2, (window_h - shown_h) // 2
        x, y = pygame.mouse.get_pos()
        return ((x - offset_x) / scale, (y - offset_y) / scale)

    def draw_background(self, background_id):
        path = self.story.get("assets", {}).get("backgrounds", {}).get(background_id)
        if path:
            full_path = ROOT / path
            if background_id not in self.background_cache and full_path.is_file():
                try:
                    self.background_cache[background_id] = pygame.image.load(
                        str(full_path)
                    ).convert()
                except pygame.error:
                    pass
            image = self.background_cache.get(background_id)
            if image:
                scale = max(WIDTH / image.get_width(), HEIGHT / image.get_height())
                size = (int(image.get_width() * scale), int(image.get_height() * scale))
                scaled = pygame.transform.smoothscale(image, size)
                self.canvas.blit(scaled, scaled.get_rect(center=(WIDTH // 2, HEIGHT // 2)))
                return
        self.draw_placeholder_background(background_id)

    def draw_placeholder_background(self, background_id):
        sky = pygame.Surface((WIDTH, HEIGHT))
        top = (36, 61, 79) if "noite" in background_id else (87, 130, 137)
        bottom = (210, 151, 117) if "noite" not in background_id else (63, 76, 95)
        for y in range(HEIGHT):
            amount = y / HEIGHT
            color = tuple(int(top[i] * (1 - amount) + bottom[i] * amount) for i in range(3))
            pygame.draw.line(sky, color, (0, y), (WIDTH, y))
        self.canvas.blit(sky, (0, 0))
        pygame.draw.circle(self.canvas, (246, 199, 145), (995, 175), 66)
        pygame.draw.rect(self.canvas, (45, 58, 64), (0, 414, WIDTH, 186))
        pygame.draw.polygon(
            self.canvas, (37, 48, 57), [(0, 430), (180, 324), (520, 430), (520, 580), (0, 580)]
        )
        pygame.draw.polygon(
            self.canvas, (48, 59, 65), [(760, 420), (1040, 300), (1280, 410), (1280, 590), (760, 590)]
        )
        for x in range(-40, WIDTH + 80, 220):
            pygame.draw.rect(self.canvas, (29, 42, 52), (x, 345, 12, 190))
        pygame.draw.line(self.canvas, (190, 166, 136), (0, 538), (WIDTH, 538), 4)
        pygame.draw.line(self.canvas, (190, 166, 136), (0, 558), (WIDTH, 558), 2)
        for x in range(80, WIDTH, 110):
            pygame.draw.line(self.canvas, (30, 40, 46), (x, 542), (x - 24, 566), 3)
        for x in range(0, WIDTH, 2):
            pygame.draw.line(self.canvas, (21, 34, 43), (x, 590), (x + 1, HEIGHT), 1)

    def draw_character(self, sprite_id):
        sprite_path = self.story.get("assets", {}).get("sprites", {}).get(sprite_id)
        if sprite_path:
            full_path = ROOT / sprite_path
            if sprite_id not in self.sprite_cache and full_path.is_file():
                try:
                    self.sprite_cache[sprite_id] = pygame.image.load(str(full_path)).convert_alpha()
                except pygame.error:
                    pass
            image = self.sprite_cache.get(sprite_id)
            if image:
                target_h = 560
                scale = target_h / image.get_height()
                image = pygame.transform.smoothscale(
                    image, (int(image.get_width() * scale), target_h)
                )
                self.canvas.blit(image, image.get_rect(midbottom=(900, 615)))
                return
        self.draw_placeholder_character(sprite_id)

    def draw_placeholder_character(self, sprite_id):
        accent = COLORS["coral"] if "lia" in sprite_id.lower() else (129, 177, 189)
        pygame.draw.ellipse(self.canvas, (25, 35, 42), (710, 560, 365, 54))
        pygame.draw.ellipse(self.canvas, accent, (777, 111, 206, 235))
        pygame.draw.ellipse(self.canvas, (216, 166, 137), (814, 133, 133, 174))
        pygame.draw.ellipse(self.canvas, (48, 39, 43), (804, 105, 151, 104))
        pygame.draw.polygon(
            self.canvas,
            accent,
            [(807, 289), (950, 289), (1040, 599), (717, 599)],
        )
        pygame.draw.polygon(
            self.canvas, (244, 221, 191), [(843, 300), (919, 300), (946, 485), (820, 485)]
        )
        pygame.draw.circle(self.canvas, (47, 45, 48), (858, 219), 5)
        pygame.draw.circle(self.canvas, (47, 45, 48), (906, 219), 5)
        pygame.draw.arc(self.canvas, (133, 74, 71), (862, 235, 39, 22), 3.4, 6.0, 2)

    def draw_title(self):
        self.canvas.fill(COLORS["ink"])
        self.draw_placeholder_background("amanhecer_estacao")
        veil = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        veil.fill((9, 19, 28, 138))
        self.canvas.blit(veil, (0, 0))
        self.draw_character("lia")
        self.draw_text("FIO DE", (88, 135), self.title_font, COLORS["paper"])
        self.draw_text("AMANHÃ", (88, 202), self.title_font, COLORS["teal"])
        self.draw_text(self.tr("title_hint"), (95, 292), self.font, COLORS["muted"])
        menu = [
            ("new_game", "new_game"),
            ("continue", "continue"),
            ("load", "load"),
            ("settings", "settings"),
            ("quit", "quit"),
        ]
        for index, (label, action) in enumerate(menu):
            self.draw_button(self.tr(label), (94, 365 + index * 53, 260, 43), action)
        if not any(self.slot_data(slot) for slot in range(1, SLOT_COUNT + 1)):
            self.draw_text(self.tr("no_save"), (94, 648), self.small_font, COLORS["muted"])

    def draw_dialogue(self):
        scene = self.story["scenes"][self.scene_id]
        self.draw_background(scene.get("background", "default"))
        if self.line_index < len(scene.get("lines", [])):
            line = scene["lines"][self.line_index]
            sprite = line.get("sprite")
            if sprite:
                self.draw_character(sprite)
        shade = pygame.Surface((WIDTH, 194), pygame.SRCALPHA)
        shade.fill((13, 22, 31, 232))
        self.canvas.blit(shade, (0, 526))
        pygame.draw.line(self.canvas, COLORS["teal"], (60, 526), (1220, 526), 2)
        if self.line_index < len(scene.get("lines", [])):
            line = scene["lines"][self.line_index]
            speaker = self.localized(line.get("speaker", ""))
            if speaker:
                self.draw_text(speaker, (86, 544), self.medium_font, COLORS["coral"])
            self.draw_wrapped(
                self.localized(line.get("text", "")), (88, 586, 1090), self.font, COLORS["paper"]
            )
            self.draw_button(self.tr("next") + "  ›", (1073, 650, 145, 42), "advance", compact=True)
        elif scene.get("choices"):
            self.draw_text(self.tr("choose"), (86, 544), self.medium_font, COLORS["coral"])
            for index, choice in enumerate(scene["choices"]):
                self.draw_button(
                    self.localized(choice["text"]),
                    (88, 590 + index * 48, 1080, 39),
                    ("choice", index),
                    compact=True,
                )
        elif scene.get("ending"):
            self.draw_text(self.localized(scene.get("ending_title", "Fim do prólogo")),
                           (86, 548), self.medium_font, COLORS["coral"])
            self.draw_button(self.tr("restart"), (86, 628, 220, 44), "new_game", compact=True)
            self.draw_button(self.tr("menu"), (322, 628, 220, 44), "title", compact=True)
        else:
            self.draw_button(self.tr("next") + "  ›", (1073, 650, 145, 42), "advance", compact=True)

        self.draw_button("Ⅱ", (1172, 26, 44, 42), "settings", compact=True)
        self.draw_button("▣", (1120, 26, 44, 42), "save_menu", compact=True)
        self.draw_button("⌂", (1068, 26, 44, 42), "title", compact=True)

    def draw_settings(self):
        self.draw_menu_background()
        self.draw_text(self.tr("settings_title"), (82, 62), self.title_font, COLORS["paper"])
        self.draw_text(self.tr("resolution"), (100, 182), self.font, COLORS["muted"])
        resolution = self.window_size()
        self.draw_button(
            f"{resolution[0]} × {resolution[1]}  ‹  ›", (550, 165, 340, 48), "resolution"
        )
        self.draw_text(self.tr("fullscreen"), (100, 250), self.font, COLORS["muted"])
        self.draw_button(
            self.tr("on") if self.settings["fullscreen"] else self.tr("off"),
            (550, 233, 340, 48), "fullscreen"
        )
        self.draw_text(self.tr("language"), (100, 318), self.font, COLORS["muted"])
        for index, language in enumerate(("pt", "en")):
            self.draw_button(
                "Português" if language == "pt" else "English",
                (550 + index * 174, 301, 166, 48), ("language", language),
                selected=self.settings["language"] == language,
            )
        sliders = [
            ("master_volume", "master", 392),
            ("music_volume", "music", 462),
            ("sfx_volume", "sfx", 532),
        ]
        for key, label, y in sliders:
            self.draw_text(self.tr(label), (100, y), self.font, COLORS["muted"])
            self.draw_slider(key, (550, y + 4, 340, 22))
        self.draw_button(self.tr("back"), (100, 620, 180, 48), "back")

    def draw_slider(self, key, rect):
        rect = pygame.Rect(rect)
        value = max(0.0, min(1.0, float(self.settings[key])))
        pygame.draw.rect(self.canvas, COLORS["panel_light"], rect, border_radius=8)
        fill = pygame.Rect(rect.x, rect.y, int(rect.width * value), rect.height)
        pygame.draw.rect(self.canvas, COLORS["teal"], fill, border_radius=8)
        knob_x = rect.x + int(rect.width * value)
        pygame.draw.circle(self.canvas, COLORS["paper"], (knob_x, rect.centery), 12)
        self.draw_text(f"{round(value * 100)}%", (910, rect.y - 4), self.small_font, COLORS["paper"])
        self.add_hotspot(rect.inflate(20, 20), ("slider", key))

    def draw_slots(self):
        self.draw_menu_background()
        title = self.tr("save_title" if self.slot_mode == "save" else "load_title")
        self.draw_text(title, (82, 48), self.title_font, COLORS["paper"])
        for index in range(SLOT_COUNT):
            slot = index + 1
            col, row = index % 3, index // 3
            x, y = 82 + col * 378, 170 + row * 138
            rect = pygame.Rect(x, y, 350, 112)
            data = self.slot_data(slot)
            pygame.draw.rect(self.canvas, COLORS["panel"], rect, border_radius=5)
            pygame.draw.rect(self.canvas, COLORS["line"], rect, width=1, border_radius=5)
            self.draw_text(f"{slot:02d}", (x + 16, y + 14), self.medium_font, COLORS["teal"])
            if data:
                chapter = self.localized(data.get("chapter", "Prólogo"))
                self.draw_text(chapter[:28], (x + 68, y + 16), self.font, COLORS["paper"])
                self.draw_text(data.get("saved_at", ""), (x + 68, y + 48), self.small_font, COLORS["muted"])
                self.draw_button("×", (x + 298, y + 10, 36, 32), ("clear", slot), compact=True)
            else:
                self.draw_text(self.tr("empty"), (x + 68, y + 23), self.font, COLORS["muted"])
            action = ("save_slot", slot) if self.slot_mode == "save" else ("load_slot", slot)
            self.add_hotspot(rect, action)
            if data:
                self.add_hotspot((x + 298, y + 10, 36, 32), ("clear", slot))
        self.draw_button(self.tr("back"), (82, 602, 170, 48), "back")

    def draw_menu_background(self):
        self.canvas.fill(COLORS["ink"])
        for y in range(0, HEIGHT, 56):
            pygame.draw.line(self.canvas, (26, 39, 51), (0, y), (WIDTH, y), 1)
        pygame.draw.rect(self.canvas, (30, 50, 59), (1000, 0, 280, HEIGHT))
        pygame.draw.line(self.canvas, COLORS["coral"], (1000, 0), (1000, HEIGHT), 2)
        pygame.draw.circle(self.canvas, (41, 67, 75), (1130, 175), 98)
        pygame.draw.circle(self.canvas, (55, 87, 90), (1130, 175), 72, 2)

    def draw(self):
        self.hotspots = []
        if self.screen == "title":
            self.draw_title()
        elif self.screen == "game":
            self.draw_dialogue()
        elif self.screen == "settings":
            self.draw_settings()
        elif self.screen in ("saves", "loads"):
            self.draw_slots()
        if self.notice and pygame.time.get_ticks() < self.notice_until:
            box = pygame.Rect(460, 22, 360, 44)
            pygame.draw.rect(self.canvas, COLORS["teal"], box, border_radius=4)
            rendered = self.font.render(self.notice, True, COLORS["ink"])
            self.canvas.blit(rendered, rendered.get_rect(center=box.center))
        window_w, window_h = self.window.get_size()
        scale = min(window_w / WIDTH, window_h / HEIGHT)
        size = (int(WIDTH * scale), int(HEIGHT * scale))
        scaled = pygame.transform.smoothscale(self.canvas, size)
        self.window.fill((0, 0, 0))
        self.window.blit(scaled, scaled.get_rect(center=self.window.get_rect().center))
        pygame.display.flip()

    def set_slider(self, key, mouse_x):
        rect = pygame.Rect(550, {"master_volume": 396, "music_volume": 466, "sfx_volume": 536}[key], 340, 22)
        self.settings[key] = max(0.0, min(1.0, (mouse_x - rect.x) / rect.width))
        self.apply_audio_volumes()
        self.save_settings()

    def advance(self):
        scene = self.story["scenes"][self.scene_id]
        if self.line_index < len(scene.get("lines", [])):
            self.line_index += 1
        elif scene.get("next"):
            self.scene_id = scene["next"]
            self.line_index = 0

    def choose(self, index):
        scene = self.story["scenes"][self.scene_id]
        choice = scene["choices"][index]
        self.flags.update(choice.get("set", {}))
        self.scene_id = choice["goto"]
        self.line_index = 0

    def dispatch(self, action):
        if action == "new_game":
            self.new_game()
        elif action == "continue":
            latest = []
            for slot in range(1, SLOT_COUNT + 1):
                data = self.slot_data(slot)
                if data:
                    latest.append((data.get("saved_at", ""), slot))
            if latest:
                self.load_slot(max(latest)[1])
            else:
                self.new_game()
        elif action == "load":
            self.slot_mode, self.screen = "load", "loads"
        elif action == "save_menu":
            self.slot_mode, self.screen = "save", "saves"
        elif action == "settings":
            self.return_screen = self.screen
            self.screen = "settings"
        elif action == "title":
            self.screen = "title"
        elif action == "quit":
            pygame.event.post(pygame.event.Event(pygame.QUIT))
        elif action == "back":
            self.screen = self.return_screen if self.screen == "settings" else (
                "game" if self.slot_mode == "save" else "title"
            )
        elif action == "advance":
            self.advance()
        elif isinstance(action, tuple):
            kind, value = action
            if kind == "choice":
                self.choose(value)
            elif kind == "save_slot":
                self.save_slot(value)
            elif kind == "load_slot":
                self.load_slot(value)
            elif kind == "clear":
                self.clear_slot(value)
            elif kind == "language":
                self.settings["language"] = value
                self.save_settings()
            elif kind == "slider":
                self.dragging = value
                self.set_slider(value, self.mouse_pos()[0])
            elif kind == "fullscreen":
                self.settings["fullscreen"] = not self.settings["fullscreen"]
                self.save_settings()
                self.recreate_window()
            elif kind == "resolution":
                current = self.window_size()
                index = RESOLUTIONS.index(current) if current in RESOLUTIONS else 1
                self.settings["resolution"] = list(RESOLUTIONS[(index + 1) % len(RESOLUTIONS)])
                self.save_settings()
                self.recreate_window()

    def run(self):
        running = True
        while running:
            self.clock.tick(60)
            self.draw()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        if self.screen == "settings":
                            self.screen = self.return_screen
                        elif self.screen == "game":
                            self.screen = "title"
                        elif self.screen in ("saves", "loads"):
                            self.screen = "game" if self.slot_mode == "save" else "title"
                    elif event.key in (pygame.K_RETURN, pygame.K_SPACE) and self.screen == "game":
                        self.advance()
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    point = self.mouse_pos()
                    for rect, action in reversed(self.hotspots):
                        if rect.collidepoint(point):
                            self.play_sfx("click")
                            self.dispatch(action)
                            break
                elif event.type == pygame.MOUSEMOTION and self.dragging:
                    self.set_slider(self.dragging, self.mouse_pos()[0])
                elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                    self.dragging = None
        pygame.quit()
        return 0


if __name__ == "__main__":
    try:
        raise SystemExit(VisualNovel().run())
    except (OSError, json.JSONDecodeError) as error:
        print(f"Não foi possível iniciar a visual novel: {error}", file=sys.stderr)
        raise SystemExit(1)