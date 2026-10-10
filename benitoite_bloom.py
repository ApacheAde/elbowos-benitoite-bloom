#!/usr/bin/env python3
"""Benitoite Bloom — full-colour Python 3 neon bloom pulse arcade for ElbowOS.
Expand a radiant pulse from the core to bloom orbiting crystals.
Python 3 + pygame. Autoplay 9:16 MP4 reel.
https://x.com/ElbowOS
"""
import math, os, random, subprocess, sys

RECORD = "--record" in sys.argv or os.environ.get("ELBOWOS_RECORD") == "1"
PLAY = "--play" in sys.argv

if RECORD or not PLAY:
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

# Record resolution 9:16
RW, RH, FPS, SECS = 1080, 1920, 30, 15
OUT = os.environ.get("ELBOWOS_MP4", "/workspace/artifacts/BENITOITE_BLOOM_ElbowOS.mp4")
TITLE, HANDLE = "BENITOITE BLOOM", "x.com/ElbowOS"

# Palette — deep void + benitoite blue / magenta / gold / cyan
VOID = (4, 8, 22)
INK = (10, 18, 40)
BLUE = (48, 140, 255)
MAGENTA = (255, 70, 190)
GOLD = (255, 210, 70)
CYAN = (60, 240, 255)
LIME = (140, 255, 110)
WHITE = (240, 248, 255)
ROSE = (255, 90, 120)

class Game:
    def __init__(self, record=False):
        pygame.init()
        self.record = record
        if record:
            self.screen = pygame.Surface((RW, RH))
            self.clock = pygame.time.Clock()
        else:
            self.screen = pygame.display.set_mode((540, 960))
            pygame.display.set_caption(TITLE)
            self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("monospace", 36 if not record else 64, bold=True)
        self.small = pygame.font.SysFont("monospace", 24 if not record else 42, bold=True)
        self.reset()

    def reset(self):
        self.score = 0
        self.tick = 0
        self.pulse_r = 0.0
        self.pulse_active = False
        self.pulse_speed = 12.0
        self.max_r = 480 if self.record else 240
        # Orbiting crystals: [angle, radius, speed, color, hit]
        self.crystals = []
        self.spawn_crystals(6)
        self.cx = (RW if self.record else 540) // 2
        self.cy = (RH if self.record else 960) // 2 + 40

    def spawn_crystals(self, n):
        for i in range(n):
            ang = random.uniform(0, math.pi * 2)
            rad = random.uniform(80, self.max_r * 0.85)
            spd = random.uniform(0.008, 0.022) * random.choice([-1, 1])
            col = random.choice([BLUE, MAGENTA, GOLD, CYAN, LIME])
            self.crystals.append([ang, rad, spd, col, False])

    def pulse(self):
        if not self.pulse_active:
            self.pulse_active = True
            self.pulse_r = 20.0

    def ai_step(self):
        # Auto-pulse when a crystal is in a good radial band and not recently hit
        if not self.pulse_active and random.random() < 0.12:
            for c in self.crystals:
                if not c[4] and 60 < c[1] < self.max_r * 0.7:
                    self.pulse()
                    break

    def step(self):
        self.tick += 1
        # Update crystals
        for c in self.crystals:
            c[0] += c[2]
            if c[4]:  # recently hit, shrink and respawn
                c[1] *= 0.92
                if c[1] < 10:
                    c[0] = random.uniform(0, math.pi * 2)
                    c[1] = random.uniform(100, self.max_r * 0.8)
                    c[2] = random.uniform(0.008, 0.025) * random.choice([-1, 1])
                    c[3] = random.choice([BLUE, MAGENTA, GOLD, CYAN, LIME])
                    c[4] = False
        # Pulse
        if self.pulse_active:
            self.pulse_r += self.pulse_speed
            # Check hits
            for c in self.crystals:
                if not c[4] and abs(self.pulse_r - c[1]) < 18:
                    c[4] = True
                    self.score += 25
            if self.pulse_r > self.max_r:
                self.pulse_active = False
                self.pulse_r = 0

    def draw(self):
        sw = RW if self.record else 540
        sh = RH if self.record else 960
        self.screen.fill(VOID)
        # Soft radial glow rings
        for r in range(40, int(self.max_r), 60):
            pygame.draw.circle(self.screen, INK, (self.cx, self.cy), r, 1)
        # Core
        pygame.draw.circle(self.screen, GOLD, (self.cx, self.cy), 28)
        pygame.draw.circle(self.screen, WHITE, (self.cx, self.cy), 16, 3)
        # Pulse
        if self.pulse_active and self.pulse_r > 0:
            alpha_r = min(255, int(180 * (1 - self.pulse_r / self.max_r)))
            pygame.draw.circle(self.screen, CYAN, (self.cx, self.cy), int(self.pulse_r), 4)
            pygame.draw.circle(self.screen, MAGENTA, (self.cx, self.cy), int(self.pulse_r * 0.85), 2)
        # Crystals
        for ang, rad, spd, col, hit in self.crystals:
            x = self.cx + math.cos(ang) * rad
            y = self.cy + math.sin(ang) * rad
            size = 18 if not hit else max(6, int(18 * rad / 100))
            pygame.draw.circle(self.screen, col, (int(x), int(y)), size)
            pygame.draw.circle(self.screen, WHITE, (int(x), int(y)), size // 2, 2)
            # Orbit trail hint
            pygame.draw.line(self.screen, INK, (self.cx, self.cy), (int(x), int(y)), 1)
        # Overlay
        title_s = self.font.render(TITLE, True, GOLD)
        self.screen.blit(title_s, (30, 40 if self.record else 20))
        score_s = self.font.render(f"SCORE {self.score:04d}", True, CYAN)
        self.screen.blit(score_s, (30, 120 if self.record else 70))
        handle_s = self.small.render(HANDLE, True, MAGENTA)
        self.screen.blit(handle_s, (30, sh - 70 if self.record else sh - 40))

    def record_video(self):
        cmd = [
            "ffmpeg", "-y", "-f", "rawvideo", "-vcodec", "rawvideo",
            "-s", f"{RW}x{RH}", "-pix_fmt", "rgb24", "-r", str(FPS),
            "-i", "-", "-an", "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            "-crf", "20", "-preset", "fast", "-movflags", "+faststart",
            OUT
        ]
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
        frames = FPS * SECS
        for f in range(frames):
            self.ai_step()
            self.step()
            self.draw()
            raw = pygame.image.tostring(self.screen, "RGB")
            try:
                proc.stdin.write(raw)
            except BrokenPipeError:
                break
            if f % 45 == 0:
                print(f"frame {f}/{frames} score={self.score}")
        proc.stdin.close()
        err = proc.stderr.read().decode("utf-8", "ignore") if proc.stderr else ""
        rc = proc.wait()
        if rc != 0:
            print("ffmpeg error:", err[-800:])
            raise SystemExit(f"ffmpeg failed ({rc})")
        print(f"Wrote {OUT}")

    def play_loop(self):
        running = True
        while running:
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    running = False
                if e.type == pygame.KEYDOWN:
                    if e.key in (pygame.K_SPACE, pygame.K_RETURN):
                        self.pulse()
                    if e.key == pygame.K_r:
                        self.reset()
            self.step()
            self.draw()
            pygame.display.flip()
            self.clock.tick(30)
        pygame.quit()

if __name__ == "__main__":
    g = Game(record=RECORD)
    if RECORD:
        g.record_video()
    else:
        g.play_loop()
