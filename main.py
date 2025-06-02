import pygame
import sys
import os

pygame.init()
MIN_WIDTH, MIN_HEIGHT = 1200, 800
STRIP_HEIGHT = 10
PANEL_WIDTH, PANEL_MARGIN = 320, 20
BOX_MARGIN, RIGHT_MARGIN = 50, 20
BUTTON_WIDTH, BUTTON_HEIGHT = 100, 30
NUM_BARS = 5

# Detect and round refresh rate
try:
    dm = pygame.display.get_desktop_display_mode()
    raw_rr = dm.refresh_rate if hasattr(dm, "refresh_rate") else dm["refresh_rate"]
    if raw_rr == 0:
        raw_rr = 60
except:
    raw_rr = 60.0
refresh_rate = int(round(raw_rr))

COMMON_REFRESH_RATES = [60, 75, 120, 144, 240]
WIDTH, HEIGHT = MIN_WIDTH, MIN_HEIGHT
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
pygame.display.set_caption("Leica Drum Light Strip Simulator")

strip_y_pos = 0
speed = 30
strip_active = False

multibeam_enabled = False
show_help = False
help_alpha = 0
show_warning = True
warning_acknowledged = False
ack_start_time = None
frozen_background = None
checkbox_rect = pygame.Rect(0, 0, 20, 20)

speed_warning_allowed = False
ignored_current_exceed = False
popup_active = False
speed_warning_alpha = 0

adjusting_up = False
adjusting_down = False
last_adjust_time = 0
ADJUST_INTERVAL = 200

class Colors:
    def __init__(self, mode=0):
        self.mode = mode
        self.update_colors()

    def update_colors(self):
        common = {
            "BLACK": (0, 0, 0),
            "WHITE": (255, 255, 255),
            "GREEN": (0, 255, 0),
            "RED": (255, 0, 0),
            "BLUE": (0, 100, 255),
        }
        if self.mode == 0:
            theme = {
                "GRAY": (100, 100, 100),
                "LIGHT_GRAY": (200, 200, 200),
                "DARK_GRAY": (50, 50, 50),
                "BACKGROUND": (0, 0, 0),
                "PANEL_BG": (50, 50, 50),
                "TEXT_PRIMARY": (200, 200, 200),
                "TEXT_SECONDARY": (150, 150, 150),
                "TITLE_COLOR": (255, 255, 0),
                "STRIP_COLOR": (255, 255, 255),
            }
        else:
            theme = {
                "GRAY": (128, 128, 128),
                "LIGHT_GRAY": (64, 64, 64),
                "DARK_GRAY": (240, 240, 240),
                "BACKGROUND": (255, 255, 255),
                "PANEL_BG": (240, 240, 240),
                "TEXT_PRIMARY": (50, 50, 50),
                "TEXT_SECONDARY": (100, 100, 100),
                "TITLE_COLOR": (51, 3, 179),
                "STRIP_COLOR": (52, 16, 178),
            }
        for name, col in {**common, **theme}.items():
            setattr(self, name, col)

    def toggle(self):
        self.mode = 1 - self.mode
        self.update_colors()

    def get_mode_name(self):
        return ["Dark", "Light"][self.mode]

class Layout:
    def __init__(self):
        self.update()

    def update(self):
        global WIDTH, HEIGHT
        self.box_x = BOX_MARGIN
        self.box_y = BOX_MARGIN
        self.box_width = WIDTH - BOX_MARGIN - PANEL_WIDTH - PANEL_MARGIN - RIGHT_MARGIN
        self.box_height = HEIGHT - 2 * BOX_MARGIN
        self.toggle_button = pygame.Rect(10, HEIGHT - BUTTON_HEIGHT - 10, BUTTON_WIDTH, BUTTON_HEIGHT)

class FontManager:
    def __init__(self):
        self.font, self.small_font, self.title_font, self.tiny_font = self._init_fonts()

    def _init_fonts(self):
        font_files = ["typeface.otf", "arial.ttf", "Arial.ttf", "calibri.ttf", 
                      "Calibri.ttf", "verdana.ttf", "Verdana.ttf"]
        for f in font_files:
            if os.path.exists(f):
                try:
                    return (
                        pygame.font.Font(f, 16),
                        pygame.font.Font(f, 14),
                        pygame.font.Font(f, 20),
                        pygame.font.Font(f, 12)
                    )
                except:
                    continue
        for name in ["Arial", "Calibri", "Verdana", "Helvetica", "DejaVu Sans"]:
            try:
                t = pygame.font.SysFont(name, 16)
                if t.render("Test", True, (255,255,255)).get_width() > 10:
                    return (
                        pygame.font.SysFont(name, 16),
                        pygame.font.SysFont(name, 14),
                        pygame.font.SysFont(name, 20),
                        pygame.font.SysFont(name, 12)
                    )
            except:
                continue
        return (
            pygame.font.Font(None, 18),
            pygame.font.Font(None, 16),
            pygame.font.Font(None, 22),
            pygame.font.Font(None, 14)
        )

class ImageLoader:
    @staticmethod
    def load_figure_image():
        names = ["figure_19_1.png", "figure_19_1.jpg", "figure_19_1.jpeg",
                 "figure19_1.png", "figure19_1.jpg", "drum_test.png", "drum_test.jpg",
                 "shutter_test.png", "shutter_test.jpg"]
        for name in names:
            if os.path.exists(name):
                try:
                    return pygame.image.load(name)
                except:
                    continue
        return None

class Renderer:
    def __init__(self, colors, fonts, layout):
        self.colors = colors
        self.fonts = fonts
        self.layout = layout

    def draw_toggle_button(self):
        label = "Stop" if strip_active else "Start"
        color = self.colors.RED if strip_active else self.colors.GREEN
        pygame.draw.rect(screen, color, self.layout.toggle_button)
        pygame.draw.rect(screen, self.colors.TEXT_PRIMARY, self.layout.toggle_button, 2)
        ts = self.fonts.small_font.render(label, True, self.colors.BLACK)
        screen.blit(ts, ts.get_rect(center=self.layout.toggle_button.center))

    def draw_instructions_and_table(self):
        x = self.layout.box_x + self.layout.box_width + PANEL_MARGIN
        y = self.layout.box_y + 10
        lh = 18

        screen.blit(self.fonts.title_font.render("Leica Speedtest", True, self.colors.TITLE_COLOR), (x, y))
        y += lh * 2

        parts = [
            ("Controls:", self.fonts.small_font, self.colors.TEXT_PRIMARY),
            ("- Press and hold UP to increase speed", self.fonts.tiny_font, self.colors.TEXT_SECONDARY),
            ("- Press and hold DOWN to decrease speed", self.fonts.tiny_font, self.colors.TEXT_SECONDARY),
            ("- Ctrl UP for faster increase", self.fonts.tiny_font, self.colors.TEXT_SECONDARY),
            ("- Ctrl DOWN for faster decrease", self.fonts.tiny_font, self.colors.TEXT_SECONDARY),
            ("- Click button to toggle Start/Stop", self.fonts.tiny_font, self.colors.TEXT_SECONDARY),
            ("- Press H to toggle help", self.fonts.tiny_font, self.colors.TEXT_SECONDARY),
            ("- Press T to cycle themes", self.fonts.tiny_font, self.colors.TEXT_SECONDARY),
            ("- Press M to toggle multibeam", self.fonts.tiny_font, self.colors.TEXT_SECONDARY),
            ("- Resize window to adjust area", self.fonts.tiny_font, self.colors.TEXT_SECONDARY),
            ("- Press ESC or close window to exit", self.fonts.tiny_font, self.colors.TEXT_SECONDARY),
            ("", self.fonts.tiny_font, self.colors.TEXT_SECONDARY),
            ("About:", self.fonts.small_font, self.colors.TEXT_PRIMARY),
            ("This simulates the light strip used to test", self.fonts.tiny_font, self.colors.TEXT_SECONDARY),
            ("Leica camera shutter speeds. The moving", self.fonts.tiny_font, self.colors.TEXT_SECONDARY),
            ("strip helps visualize shutter blade timing", self.fonts.tiny_font, self.colors.TEXT_SECONDARY),
            ("and slit width at different speeds. Speed", self.fonts.tiny_font, self.colors.TEXT_SECONDARY),
            ("up or down the simulation until the camera", self.fonts.tiny_font, self.colors.TEXT_SECONDARY),
            ("produces the rough image that is shown", self.fonts.tiny_font, self.colors.TEXT_SECONDARY),
            ("in the help box.", self.fonts.tiny_font, self.colors.TEXT_SECONDARY),
            ("", self.fonts.tiny_font, self.colors.TEXT_SECONDARY),
        ]
        for txt, fnt, col in parts:
            screen.blit(fnt.render(txt, True, col), (x, y))
            y += lh

        status = [
            (f"Current Speed: {speed} px/frame", self.fonts.small_font, self.colors.TEXT_PRIMARY),
            (f"Strip Status: {'Active' if strip_active else 'Stopped'}", self.fonts.small_font, self.colors.TEXT_PRIMARY),
            (f"Mode: {self.colors.get_mode_name()}", self.fonts.small_font, self.colors.TEXT_PRIMARY),
            (f"Beam Mode: {'Multibeam' if multibeam_enabled else 'Single'}", self.fonts.small_font, self.colors.TEXT_PRIMARY),
            ("", self.fonts.small_font, self.colors.TEXT_SECONDARY)
        ]
        for txt, fnt, col in status:
            screen.blit(fnt.render(txt, True, col), (x, y))
            y += lh

        screen.blit(self.fonts.small_font.render("Recommended Speeds:", True, self.colors.TITLE_COLOR), (x, y))
        y += lh * 1.5

        col1, col2 = x, x + 140
        screen.blit(self.fonts.small_font.render("Refresh Rate", True, self.colors.TEXT_PRIMARY), (col1, y))
        screen.blit(self.fonts.small_font.render("Max px/frame", True, self.colors.TEXT_PRIMARY), (col2, y))
        y += lh

        for rr in COMMON_REFRESH_RATES:
            screen.blit(self.fonts.tiny_font.render(f"{rr} Hz", True, self.colors.TEXT_SECONDARY), (col1, y))
            screen.blit(self.fonts.tiny_font.render(f"{rr}", True, self.colors.TEXT_SECONDARY), (col2, y))
            y += lh

    def draw_shutter_test_area(self):
        bw, bh = self.layout.box_width, self.layout.box_height
        pygame.draw.rect(screen, self.colors.GRAY, (self.layout.box_x, self.layout.box_y, bw, bh), 2)
        screen.blit(self.fonts.tiny_font.render("Shutter Test Area", True, self.colors.GRAY), (self.layout.box_x, self.layout.box_y - 15))

        if strip_active:
            if multibeam_enabled:
                self.draw_multibeam(bw, bh)
            else:
                self.draw_single_beam(bw, bh)

    def draw_single_beam(self, bw, bh):
        sy = self.layout.box_y + strip_y_pos
        if sy + STRIP_HEIGHT > self.layout.box_y and sy < self.layout.box_y + bh:
            ct = max(sy, self.layout.box_y)
            cb = min(sy + STRIP_HEIGHT, self.layout.box_y + bh)
            h = cb - ct
            if h > 0:
                pygame.draw.rect(screen, self.colors.STRIP_COLOR, (self.layout.box_x, ct, bw, h))

    def draw_multibeam(self, bw, bh):
        cycle = bh + STRIP_HEIGHT
        spacing = cycle / NUM_BARS
        for i in range(NUM_BARS):
            raw_y = strip_y_pos + i * spacing
            wrapped = raw_y % cycle
            bar_top = int(self.layout.box_y + wrapped - STRIP_HEIGHT)
            bar_bottom = bar_top + STRIP_HEIGHT
            if bar_bottom > self.layout.box_y and bar_top < self.layout.box_y + bh:
                ct = max(bar_top, self.layout.box_y)
                cb = min(bar_bottom, self.layout.box_y + bh)
                h = cb - ct
                if h > 0:
                    pygame.draw.rect(screen, self.colors.STRIP_COLOR, (self.layout.box_x, ct, bw, h))

    def draw_figure_on_surface(self, surf, x_off=0, y_off=0):
        if figure_image:
            return self._draw_image_figure(surf, x_off, y_off)
        return self._draw_generated_figure(surf, x_off, y_off)

    def _draw_image_figure(self, surf, x_off, y_off):
        ix, iy = 40 + x_off, 60 + y_off
        mw, mh = 450, 250
        rect = figure_image.get_rect()
        scale = min(mw / rect.width if rect.width > mw else 1, mh / rect.height if rect.height > mh else 1)
        img = (
            pygame.transform.scale(figure_image, (int(rect.width * scale), int(rect.height * scale)))
            if scale < 1 else
            figure_image
        )
        surf.blit(img, (ix, iy))
        surf.blit(self.fonts.font.render("Figure 19.1 - Drum Test Images at Different Shutter Speeds", True, self.colors.TITLE_COLOR), (ix, iy - 35))
        return iy + img.get_height() + 5

    def _draw_generated_figure(self, surf, x_off, y_off):
        fx, fy = 40 + x_off, 60 + y_off
        speeds = ["1/250", "1/500", "1/1000"]
        slit_w = {"1/250": 30, "1/500": 22, "1/1000": 16}
        slit_c = {"1/250": (180, 180, 180), "1/500": (140, 140, 140), "1/1000": (100, 100, 100)}
        for i, spd in enumerate(speeds):
            x = fx + i * 120
            y = fy
            fw, fh = 100, 65
            pygame.draw.rect(surf, self.colors.TEXT_PRIMARY, (x, y, fw, fh), 2)
            sw = 12
            for j in range(8):
                sx = x + j * sw
                pts = [(sx, y), (sx + sw, y), (sx + sw + 15, y + fh), (sx + 15, y + fh)]
                col = self.colors.DARK_GRAY if j % 2 == 0 else self.colors.LIGHT_GRAY
                pygame.draw.polygon(surf, col, pts)
            swt = slit_w[spd]
            slx = x + (fw - swt)//2
            ov = pygame.Surface((swt, fh))
            ov.set_alpha(120)
            ov.fill(slit_c[spd])
            surf.blit(ov, (slx, y))
            pygame.draw.line(surf, self.colors.TEXT_PRIMARY, (slx, y), (slx, y + fh), 1)
            pygame.draw.line(surf, self.colors.TEXT_PRIMARY, (slx + swt, y), (slx + swt, y + fh), 1)
            lbl = self.fonts.small_font.render(spd, True, self.colors.TEXT_PRIMARY)
            surf.blit(lbl, (x + (fw - lbl.get_width())//2, y + fh + 10))
        surf.blit(self.fonts.font.render("Figure 19.1 - Drum Test Images at Different Shutter Speeds", True, self.colors.TITLE_COLOR), (fx, fy - 35))
        ey = fy + 110
        expl = [
            "The drum images show the required pattern for proper shutter operation.",
            "Notice how faster speeds create narrower effective slit widths.",
            "The diagonal pattern helps visualize shutter curtain movement timing."
        ]
        for i, line in enumerate(expl):
            surf.blit(self.fonts.tiny_font.render(line, True, self.colors.TEXT_SECONDARY), (fx, ey + i * 16))
        return 235

    def draw_help_overlay(self):
        if help_alpha <= 0:
            return
        if frozen_background and help_alpha > 0:
            screen.blit(frozen_background, (0, 0))
        overlay = pygame.Surface((WIDTH, HEIGHT))
        overlay.set_alpha(int(help_alpha * 0.8))
        overlay.fill((0, 0, 0))
        screen.blit(overlay, (0, 0))

        hw, hh = min(750, WIDTH - 30), min(550, HEIGHT - 30)
        hx, hy = (WIDTH - hw)//2, (HEIGHT - hh)//2
        help_surf = pygame.Surface((hw, hh))
        help_surf.fill(self.colors.PANEL_BG)
        pygame.draw.rect(help_surf, self.colors.TEXT_PRIMARY, (0, 0, hw, hh), 3)
        help_surf.blit(self.fonts.font.render("Leica M3 Shutter Speed Testing - Figure 19.1", True, self.colors.TITLE_COLOR), (15, 15))
        end_y = self.draw_figure_on_surface(help_surf, -25, 15)
        lines = [
            "Understanding Focal Plane Shutter Testing:", "",
            "The drum test images show diagonal stripe patterns photographed at different speeds",
            "Each image reveals how the focal plane shutter creates an effective 'slit' traveling across film",
            "Faster shutter speeds (1/1000) create narrower slits in the exposure pattern",
            "Slower speeds (1/250) create wider slits, allowing more light through over time",
            "The moving light strip in this simulator represents the test pattern motion", "",
            "From the Leica M3 Service Manual:", "",
            "The image of the slit of the shutter must be slightly wider at the",
            "lower edge of the picture frame than at the top. Increasing the tension",
            "of the spring roller of the first shutter blind widens the slit image.", "",
            "Press H again to close this help window"
        ]
        oy, lh = end_y, 14
        for line in lines:
            txt = self.fonts.small_font.render(line, True, self.colors.TITLE_COLOR) if line.startswith(("Understanding", "From the Leica")) else self.fonts.tiny_font.render(line, True, self.colors.TEXT_SECONDARY)
            if oy < hh - 25:
                help_surf.blit(txt, (15, oy))
            oy += lh
        help_surf.set_alpha(int(help_alpha))
        screen.blit(help_surf, (hx, hy))

    def draw_warning_screen(self):
        global ack_start_time
        screen.fill(self.colors.BACKGROUND)
        ww, wh = min(600, WIDTH - 40), min(500, HEIGHT - 40)
        wx, wy = (WIDTH - ww)//2, (HEIGHT - wh)//2
        pygame.draw.rect(screen, self.colors.PANEL_BG, (wx, wy, ww, wh))
        pygame.draw.rect(screen, self.colors.RED, (wx, wy, ww, wh), 2)

        cy = wy + 30
        screen.blit(self.fonts.title_font.render("Epilepsy Warning", True, self.colors.TEXT_PRIMARY), (wx + 25, cy))
        cy += 50
        screen.blit(self.fonts.font.render("Before you start:", True, self.colors.TEXT_PRIMARY), (wx + 25, cy))
        cy += 35

        texts = [
            ["This application contains rapidly flashing lights and moving",
             "visual elements that may trigger seizures in individuals with",
             "photosensitive epilepsy."],
            ["Please do not use this application if you:"],
            ["- Have a history of epilepsy or seizures", "- Are sensitive to flashing lights", "- Experience discomfort from rapid visual changes"],
            ["By continuing you acknowledge that you understand these",
             "risks and use this application at your own discretion."],
            ["In case you feel any discomfort while using the application",
             "press ESC to exit the app immediately and consult a",
             "certified physician."]
        ]

        for section in texts:
            for line in section:
                screen.blit(self.fonts.small_font.render(line, True, self.colors.TEXT_PRIMARY), (wx + 25, cy))
                cy += 20
            cy += 15

        checkbox_x, checkbox_y = wx + 25, cy
        global checkbox_rect
        checkbox_rect = pygame.Rect(checkbox_x, checkbox_y, 18, 18)
        pygame.draw.rect(screen, self.colors.TEXT_PRIMARY, checkbox_rect, 2)
        if warning_acknowledged:
            pygame.draw.line(screen, self.colors.GREEN, (checkbox_x + 3, checkbox_y + 9), (checkbox_x + 7, checkbox_y + 13), 2)
            pygame.draw.line(screen, self.colors.GREEN, (checkbox_x + 7, checkbox_y + 13), (checkbox_x + 15, checkbox_y + 5), 2)
        screen.blit(self.fonts.small_font.render("I acknowledge the risks and wish to continue", True, self.colors.TEXT_PRIMARY), (checkbox_x + 25, checkbox_y - 1))

        if warning_acknowledged:
            if ack_start_time is None:
                ack_start_time = pygame.time.get_ticks()
            elapsed = (pygame.time.get_ticks() - ack_start_time) // 1000
            remaining = 15 - elapsed
            button_w, button_h = 220, 30
            bx, by = wx + ww - button_w - 10, wy + wh - button_h - 10
            btn = pygame.Rect(bx, by, button_w, button_h)
            if remaining > 0:
                pygame.draw.rect(screen, self.colors.LIGHT_GRAY, btn)
                pygame.draw.rect(screen, self.colors.TEXT_PRIMARY, btn, 2)
                txt = f"Continue after {remaining}s"
                ts = self.fonts.small_font.render(txt, True, self.colors.BLACK)
                screen.blit(ts, ts.get_rect(center=btn.center))
                return None
            else:
                pygame.draw.rect(screen, self.colors.GREEN, btn)
                pygame.draw.rect(screen, self.colors.TEXT_PRIMARY, btn, 2)
                ts = self.fonts.small_font.render("Continue", True, self.colors.BLACK)
                screen.blit(ts, ts.get_rect(center=btn.center))
                return btn
        return None

    def draw_speed_warning_popup(self):
        global speed_warning_alpha
        popup_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        popup_surf.fill((0, 0, 0, int(speed_warning_alpha * 0.8)))

        # Enlarged box (550×300) to fit all lines
        box_w, box_h = 550, 300
        bx, by = (WIDTH - box_w)//2, (HEIGHT - box_h)//2

        pygame.draw.rect(popup_surf, self.colors.PANEL_BG, (bx, by, box_w, box_h))
        pygame.draw.rect(popup_surf, self.colors.RED, (bx, by, box_w, box_h), 2)

        cy = by + 20
        # Title
        popup_surf.blit(
            self.fonts.title_font.render("Speed Warning", True, self.colors.RED),
            (bx + 20, cy)
        )
        cy += 40

        # First line
        popup_surf.blit(
            self.fonts.small_font.render("You have exceeded the recommended speed", True, self.colors.TEXT_PRIMARY),
            (bx + 20, cy)
        )
        cy += 30

        # Max‐speed line
        recommended = RECOMMENDED_PX_FRAME.get(refresh_rate, refresh_rate)
        max_line = f"Max for {refresh_rate}Hz is {recommended} px/frame"
        popup_surf.blit(
            self.fonts.small_font.render(max_line, True, self.colors.TEXT_PRIMARY),
            (bx + 20, cy)
        )
        cy += 40

        # Explanatory paragraph without commas
        explanation = [
            "Speed too fast for effective testing. The refresh rate cannot",
            "adapt to refresh revolving lines. This leads to still lines on",
            "the screen that will not register an image usable for speed testing.",
            "Continue at your own risk."
        ]
        for line in explanation:
            popup_surf.blit(
                self.fonts.tiny_font.render(line, True, self.colors.TEXT_PRIMARY),
                (bx + 20, cy)
            )
            cy += 22

        cy += 30  # Extra space before "Ignore"

        # "Ignore" button: red frame, deep‐blue text
        ign_btn = pygame.Rect(bx + box_w - 160, by + box_h - 50, 140, 40)
        pygame.draw.rect(popup_surf, self.colors.LIGHT_GRAY, ign_btn)   # button background
        pygame.draw.rect(popup_surf, self.colors.RED, ign_btn, 2)        # red frame

        # Deep-blue text (RGB (0, 0, 139))
        deep_blue = (0, 0, 139)
        t4 = self.fonts.small_font.render("Ignore", True, deep_blue)
        popup_surf.blit(t4, t4.get_rect(center=ign_btn.center))

        popup_surf.set_alpha(int(speed_warning_alpha))
        screen.blit(popup_surf, (0, 0))
        return ign_btn


RECOMMENDED_PX_FRAME = {rr: rr for rr in COMMON_REFRESH_RATES}

class GameLogic:
    @staticmethod
    def update_strip_animation():
        global strip_y_pos
        if strip_active:
            strip_y_pos += speed
            if not multibeam_enabled and strip_y_pos > layout.box_height:
                strip_y_pos = -STRIP_HEIGHT

    @staticmethod
    def update_help_animation():
        global help_alpha
        if show_help and help_alpha < 255:
            help_alpha = min(255, help_alpha + 15)
        elif not show_help and help_alpha > 0:
            help_alpha = max(0, help_alpha - 15)

    @staticmethod
    def capture_background():
        global frozen_background
        frozen_background = screen.copy()

    @staticmethod
    def handle_resize(new_w, new_h):
        global WIDTH, HEIGHT, screen, frozen_background
        WIDTH = max(new_w, MIN_WIDTH)
        HEIGHT = max(new_h, MIN_HEIGHT)
        screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
        frozen_background = None
        layout.update()

colors = Colors()
layout = Layout()
fonts = FontManager()
renderer = Renderer(colors, fonts, layout)
game_logic = GameLogic()
figure_image = ImageLoader.load_figure_image()

def main():
    global strip_active, show_help, show_warning, warning_acknowledged, ack_start_time
    global speed, strip_y_pos, adjusting_up, adjusting_down, last_adjust_time
    global speed_warning_allowed, ignored_current_exceed, popup_active, speed_warning_alpha
    global multibeam_enabled

    clock = pygame.time.Clock()
    running = True
    cont_btn = None
    ign_btn = None

    while running:
        current_time = pygame.time.get_ticks()
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (
                event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE
            ):
                running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_h and not show_warning:
                    if not show_help:
                        game_logic.capture_background()
                    show_help = not show_help

                elif event.key == pygame.K_t and not show_warning:
                    colors.toggle()
                    renderer.colors = colors

                elif event.key == pygame.K_m and not show_warning:
                    multibeam_enabled = not multibeam_enabled
                    if not multibeam_enabled:
                        strip_y_pos %= (layout.box_height + STRIP_HEIGHT)

                elif event.key == pygame.K_UP and not show_warning:
                    adjusting_up = True
                elif event.key == pygame.K_DOWN and not show_warning:
                    adjusting_down = True

            elif event.type == pygame.KEYUP:
                if event.key == pygame.K_UP:
                    adjusting_up = False
                elif event.key == pygame.K_DOWN:
                    adjusting_down = False

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if show_warning:
                    if checkbox_rect.collidepoint(event.pos):
                        warning_acknowledged = not warning_acknowledged
                        if warning_acknowledged:
                            ack_start_time = pygame.time.get_ticks()
                        else:
                            ack_start_time = None
                    elif cont_btn and cont_btn.collidepoint(event.pos) and not popup_active:
                        show_warning = False
                        speed_warning_allowed = True
                    continue

                if popup_active:
                    if ign_btn and ign_btn.collidepoint(event.pos):
                        ignored_current_exceed = True
                        popup_active = False
                    continue

                if renderer.layout.toggle_button.collidepoint(event.pos) and not show_help:
                    strip_active = not strip_active
                    if strip_active:
                        strip_y_pos = 0
                elif event.type == pygame.VIDEORESIZE and not show_warning and not popup_active:
                    game_logic.handle_resize(event.w, event.h)

            elif event.type == pygame.VIDEORESIZE:
                if not show_warning and not popup_active:
                    game_logic.handle_resize(event.w, event.h)

        if not show_warning and not show_help:
            if adjusting_up and current_time - last_adjust_time > ADJUST_INTERVAL:
                delta = 5 if (pygame.key.get_mods() & (pygame.KMOD_LCTRL | pygame.KMOD_RCTRL)) else 1
                speed = min(speed + delta, 200)
                last_adjust_time = current_time
            if adjusting_down and current_time - last_adjust_time > ADJUST_INTERVAL:
                delta = 5 if (pygame.key.get_mods() & (pygame.KMOD_LCTRL | pygame.KMOD_RCTRL)) else 1
                speed = max(speed - delta, 1)
                last_adjust_time = current_time

        if speed_warning_allowed:
            recommended = RECOMMENDED_PX_FRAME.get(refresh_rate, refresh_rate)
            if speed <= recommended:
                ignored_current_exceed = False
                popup_active = False
            else:
                if not ignored_current_exceed and not popup_active:
                    popup_active = True

        if popup_active and speed_warning_alpha < 255:
            speed_warning_alpha = min(255, speed_warning_alpha + 15)
        elif not popup_active and speed_warning_alpha > 0:
            speed_warning_alpha = max(0, speed_warning_alpha - 15)

        if show_warning:
            screen.fill(colors.BACKGROUND)
            cont_btn = renderer.draw_warning_screen()
        else:
            screen.fill(colors.BACKGROUND)
            game_logic.update_strip_animation()
            renderer.draw_shutter_test_area()
            renderer.draw_toggle_button()
            renderer.draw_instructions_and_table()
            if show_help:
                game_logic.update_help_animation()
                renderer.draw_help_overlay()

        if speed_warning_alpha > 0:
            ign_btn = renderer.draw_speed_warning_popup()

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
