import pygame
import math
import numpy as np

pygame.init()

WIDTH, HEIGHT = 900, 700
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("HINDSIGHT")
clock = pygame.time.Clock()

# ---------- COLORS ----------
SKY = (135, 206, 235)
GRASS = (34, 139, 34)
ROAD = (55, 55, 55)
ALT_ROAD = (60, 60, 60)
LINE = (255, 255, 255)

DASH = (22, 22, 28)
DASH_HL = (60, 60, 70)
INTERIOR_DARK = (15, 15, 20)
INTERIOR_MID = (35, 35, 45)

BLACK = (0, 0, 0)
SKIN = (245, 205, 170)
HAIR = (40, 30, 20)

TINT_COLOR = (10, 10, 30)
TINT_ALPHA = 90

# ---------- DRIVER / CAMERA ----------
head_center = (WIDTH // 2, HEIGHT // 2 + 40)
head_radius = 220

lens_size = (260, 160)
lens_left_pos = (WIDTH // 2 - 190, HEIGHT // 2 - 70)
lens_right_pos = (WIDTH // 2 + 50, HEIGHT // 2 - 70)

# ---------- GAME STATE ----------
speed = 250
player_x = 0.0
position = 0.0
max_off_road = 2400.0
game_over = False
score = 0

font = pygame.font.SysFont("arial", 48, bold=True)
small_font = pygame.font.SysFont("arial", 26)

# ---------- ROAD ----------
def draw_pseudo3d_road(surf, offset_x, pos):
    w, h = surf.get_size()
    horizon = int(h * 0.22)
    segments = 240

    surf.fill(SKY)
    pygame.draw.rect(surf, GRASS, (0, horizon, w, h - horizon))

    pl = w / 2
    pr = w / 2
    py = horizon

    for i in range(1, segments + 1):
        y = horizon + (h - horizon) * i / segments
        scale = 90.0 / i
        curve = math.sin(pos * 0.0018 + i * 0.03) * 700 / i
        x = offset_x / i + curve

        rw = 1700 * scale
        l = w / 2 + x - rw / 2
        r = w / 2 + x + rw / 2

        col = ROAD if i % 2 == 0 else ALT_ROAD
        pygame.draw.polygon(surf, col, [(pl, py), (pr, py), (r, y), (l, y)])

        if i % 8 < 4:
            pygame.draw.line(
                surf, LINE,
                ((pl + pr) / 2, py),
                ((l + r) / 2, y),
                max(1, int(4 * scale))
            )

        pl, pr, py = l, r, y

# ---------- OPTICS ----------
def distort_lens(src):
    w, h = src.get_size()
    arr = pygame.surfarray.array3d(src)
    out = np.zeros_like(arr)

    cx, cy = w / 2, h / 2
    max_r = math.sqrt(cx * cx + cy * cy)
    k = 0.35

    for x in range(w):
        for y in range(h):
            dx = (x - cx) / max_r
            dy = (y - cy) / max_r
            r2 = dx * dx + dy * dy
            f = 1 + k * r2
            sx = int(cx + dx * max_r * f)
            sy = int(cy + dy * max_r * f)
            if 0 <= sx < w and 0 <= sy < h:
                out[x, y] = arr[sx, sy]

    surf = pygame.Surface((w, h))
    pygame.surfarray.blit_array(surf, out)
    return surf

def fresnel_mask(size):
    w, h = size
    surf = pygame.Surface(size, pygame.SRCALPHA)
    cx, cy = w / 2, h / 2
    max_r = math.sqrt(cx * cx + cy * cy)

    for x in range(w):
        for y in range(h):
            dx = x - cx
            dy = y - cy
            r = math.sqrt(dx * dx + dy * dy) / max_r
            a = int(140 * (r ** 1.8))
            surf.set_at((x, y), (255, 255, 255, a))
    return surf

fresnel = fresnel_mask(lens_size)

# ---------- MAIN LOOP ----------
running = True
while running:
    dt = clock.tick(60) / 1000

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if game_over and event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r:
                player_x = 0.0
                position = 0.0
                score = 0
                game_over = False

    keys = pygame.key.get_pressed()
    if not game_over:
        if keys[pygame.K_LEFT]:
            player_x -= 3600 * dt
        if keys[pygame.K_RIGHT]:
            player_x += 3600 * dt

        player_x += 1000 * math.sin(position * 0.002) * dt
        position += speed * dt
        score = int(position // 8)

        if abs(player_x) > max_off_road:
            game_over = True

    # ---------- INTERIOR ----------
    screen.fill(INTERIOR_DARK)

    # Windshield
    windshield = pygame.Surface((WIDTH, HEIGHT // 2), pygame.SRCALPHA)
    pygame.draw.polygon(
        windshield, (180, 200, 220, 30),
        [(0, 0), (WIDTH, 0), (WIDTH - 120, HEIGHT // 2), (120, HEIGHT // 2)]
    )
    screen.blit(windshield, (0, 0))

    # A-pillars
    pygame.draw.polygon(screen, INTERIOR_MID, [(0, 0), (120, HEIGHT // 2), (180, HEIGHT // 2), (40, 0)])
    pygame.draw.polygon(screen, INTERIOR_MID, [(WIDTH, 0), (WIDTH - 120, HEIGHT // 2), (WIDTH - 180, HEIGHT // 2), (WIDTH - 40, 0)])

    # Dashboard
    pygame.draw.rect(screen, DASH, (0, HEIGHT - 150, WIDTH, 150))
    pygame.draw.rect(screen, DASH_HL, (0, HEIGHT - 170, WIDTH, 20))

    # Steering wheel
    wheel_center = (WIDTH // 2, HEIGHT - 80)
    pygame.draw.circle(screen, BLACK, wheel_center, 95, 14)
    for a in range(0, 360, 45):
        rad = math.radians(a)
        pygame.draw.line(
            screen, BLACK, wheel_center,
            (wheel_center[0] + 85 * math.cos(rad), wheel_center[1] + 85 * math.sin(rad)), 8
        )

    # Hands
    pygame.draw.circle(screen, SKIN, (wheel_center[0] - 60, wheel_center[1] + 25), 34)
    pygame.draw.circle(screen, SKIN, (wheel_center[0] + 60, wheel_center[1] + 25), 34)

    # ---------- DRIVER ----------
    pygame.draw.circle(screen, SKIN, head_center, head_radius)
    pygame.draw.ellipse(
        screen, HAIR,
        (head_center[0] - head_radius * 0.9,
         head_center[1] - head_radius * 1.1,
         head_radius * 1.8,
         head_radius * 1.0)
    )

    # ---------- SUNGLASSES ----------
    pygame.draw.rect(screen, BLACK, (*lens_left_pos, *lens_size), 10, 18)
    pygame.draw.rect(screen, BLACK, (*lens_right_pos, *lens_size), 10, 18)

    road = pygame.Surface(lens_size)
    draw_pseudo3d_road(road, player_x / 12, position)
    road = pygame.transform.flip(road, True, False)
    road = distort_lens(road)

    screen.blit(road, lens_left_pos)
    screen.blit(road, lens_right_pos)

    tint = pygame.Surface(lens_size, pygame.SRCALPHA)
    tint.fill((*TINT_COLOR, TINT_ALPHA))
    screen.blit(tint, lens_left_pos)
    screen.blit(tint, lens_right_pos)

    screen.blit(fresnel, lens_left_pos)
    screen.blit(fresnel, lens_right_pos)

    # ---------- HUD ----------
    title = small_font.render("HINDSIGHT", True, (220, 220, 220))
    screen.blit(title, (20, 20))
    dist = font.render(f"{score} m", True, (200, 255, 200))
    screen.blit(dist, (20, 55))

    if game_over:
        over = font.render("CRASHED", True, (255, 60, 60))
        screen.blit(over, (WIDTH // 2 - over.get_width() // 2, HEIGHT // 2 - 40))
        restart = small_font.render("Press R to restart", True, (220, 220, 220))
        screen.blit(restart, (WIDTH // 2 - restart.get_width() // 2, HEIGHT // 2 + 10))

    pygame.display.flip()

pygame.quit()
