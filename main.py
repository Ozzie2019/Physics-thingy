import sys, pygame, random, math

pygame.init()

FPS = 60
BASE_DT = 1 / FPS
DT = BASE_DT
G = 1000

WIDTH, HEIGHT = 1000, 680
UI_WIDTH = 350
screen = pygame.display.set_mode((WIDTH + UI_WIDTH, HEIGHT))
fpsClock = pygame.time.Clock()

TEXT_COL = (255, 255, 255)
BG_COL = (20, 20, 20)
UI_BG = (30, 30, 30)
BUTTON_COL = (70, 70, 70)
BUTTON_HOVER = (100, 100, 100)
BUTTON_ACTIVE = (0, 200, 0)
INPUT_BG = (50, 50, 50)

class Planet:
    def __init__(self, x, y, mass, vx=0, vy=0):
        self.x = x; self.y = y; self.mass = mass
        self.radius = max(5, int(mass ** (1/3)))
        self.vx = vx; self.vy = vy
        self.trail = []
        self.fx = 0; self.fy = 0

    def draw(self, map_scale, show_field=False, trails_on=False, show_vel=False, show_pull=False):
        cx, cy = WIDTH / 2, HEIGHT / 2
        disp_x = cx + (self.x - cx) * map_scale
        disp_y = cy + (self.y - cy) * map_scale
        screen_y = HEIGHT - int(disp_y)

        if show_field:
            for angle in range(0, 360, 30):
                fx = math.cos(math.radians(angle))
                fy = math.sin(math.radians(angle))
                line_end_x = disp_x + fx * self.radius * 3
                line_end_y = screen_y - fy * self.radius * 3
                pygame.draw.line(screen, (50, 50, 100), (int(disp_x), screen_y),
                                 (int(line_end_x), int(line_end_y)), 1)
        if trails_on:
            self.trail.append((disp_x, disp_y))
            if len(self.trail) > 50: self.trail.pop(0)
            for i, pos in enumerate(self.trail):
                shade = 255 - int(255 * i / len(self.trail))
                pygame.draw.circle(screen, (shade, shade, shade), (int(pos[0]), HEIGHT - int(pos[1])), 2)

        pygame.draw.circle(screen, (255, 0, 0), (int(disp_x), screen_y), self.radius)

        if show_vel:
            end_x = disp_x + self.vx * 0.5 * map_scale
            end_y = screen_y - self.vy * 0.5 * map_scale
            pygame.draw.line(screen, (0, 255, 0), (int(disp_x), screen_y), (int(end_x), int(end_y)), 2)

        if show_pull:
            force_mag = math.hypot(self.fx, self.fy)
            if force_mag > 0:
                fx, fy = self.fx / force_mag, self.fy / force_mag
                scale = 0.01 * map_scale
                end_x = disp_x + fx * force_mag * scale
                end_y = screen_y - fy * force_mag * scale
                pygame.draw.line(screen, (0, 0, 255), (int(disp_x), screen_y), (int(end_x), int(end_y)), 2)

    def update(self):
        self.vx += (self.fx / self.mass) * DT
        self.vy += (self.fy / self.mass) * DT
        self.x += self.vx * DT
        self.y += self.vy * DT

def resolve_collision(p1, p2):
    dx, dy = p2.x - p1.x, p2.y - p1.y
    dist = math.hypot(dx, dy)
    if dist == 0: return
    overlap = p1.radius + p2.radius - dist
    if overlap > 0:
        nx, ny = dx/dist, dy/dist
        p1.x -= nx * overlap / 2; p1.y -= ny * overlap / 2
        p2.x += nx * overlap / 2; p2.y += ny * overlap / 2
        tx, ty = -ny, nx
        dpTan1 = p1.vx * tx + p1.vy * ty
        dpTan2 = p2.vx * tx + p2.vy * ty
        dpNorm1 = p1.vx * nx + p1.vy * ny
        dpNorm2 = p2.vx * nx + p2.vy * ny
        m1, m2 = p1.mass, p2.mass
        u1 = (dpNorm1 * (m1 - m2) + 2 * m2 * dpNorm2) / (m1 + m2)
        u2 = (dpNorm2 * (m2 - m1) + 2 * m1 * dpTan1) / (m1 + m2)
        p1.vx = tx * dpTan1 + nx * u1
        p1.vy = ty * dpTan1 + ny * u1
        p2.vx = tx * dpTan2 + nx * u2
        p2.vy = ty * dpTan2 + ny * u2

class Button:
    def __init__(self, rect, text): self.rect = pygame.Rect(rect); self.text = text
    def draw(self, hover=False, active=False):
        if active:
            col = BUTTON_ACTIVE
        else:
            col = BUTTON_HOVER if hover else BUTTON_COL
        pygame.draw.rect(screen, col, self.rect)
        txt = font.render(self.text, True, TEXT_COL)
        tr = txt.get_rect(center=self.rect.center)
        screen.blit(txt, tr)
    def is_hover(self, pos): return self.rect.collidepoint(pos)

class InputBox:
    def __init__(self, x, y, w, h, text=''):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text; self.active = False
        self.surface = font.render(text, True, TEXT_COL)
        self.cursor_visible = True; self.cursor_timer = pygame.time.get_ticks()
    def handle_event(self, e):
        if e.type == pygame.MOUSEBUTTONDOWN: self.active = self.rect.collidepoint(e.pos)
        if e.type == pygame.KEYDOWN and self.active:
            if e.key == pygame.K_RETURN: self.active = False
            elif e.key == pygame.K_BACKSPACE: self.text = self.text[:-1]
            else: self.text += e.unicode
            self.surface = font.render(self.text, True, TEXT_COL)
    def draw(self):
        pygame.draw.rect(screen, INPUT_BG, self.rect)
        screen.blit(self.surface, (self.rect.x + 5, self.rect.y + 5))
        if self.active:
            now = pygame.time.get_ticks()
            if now - self.cursor_timer >= 500:
                self.cursor_timer = now; self.cursor_visible = not self.cursor_visible
            if self.cursor_visible:
                xo = self.surface.get_width() + 5
                start = (self.rect.x + xo, self.rect.y + 5)
                end = (self.rect.x + xo, self.rect.y + self.rect.height - 5)
                pygame.draw.line(screen, TEXT_COL, start, end)
    def get(self):
        try: return float(self.text)
        except: return 0

def rescale_planets(old_scale, new_scale):
    cx, cy = WIDTH / 2, HEIGHT / 2
    scale_factor = new_scale / old_scale
    for p in planets:
        p.x = cx + (p.x - cx) * scale_factor
        p.y = cy + (p.y - cy) * scale_factor
        p.vx *= scale_factor
        p.vy *= scale_factor
        p.trail = []

planets = []
font = pygame.font.SysFont(None, 24)
paused = False; show_field = False; trails_on = False
show_vel = False; show_pull = False; show_grid = False
mass_input = InputBox(WIDTH+10, 100, 100, 30, '10')
speed_input = InputBox(WIDTH+10, 150, 100, 30, '0')

size_buttons = [
    Button((WIDTH+10, 200, 30, 30), '+'),
    Button((WIDTH+50, 200, 30, 30), '-')
]

speed_options = [0.1, 0.25, 0.5, 1, 2, 5, 10, 50]
speed_buttons = []
for i, spd in enumerate(speed_options):
    speed_buttons.append(Button((WIDTH+10 + i*45, 250, 40, 30), f'{spd}x'))

buttons = [
    Button((WIDTH+10, 10, 100, 30), 'Pause'),
    Button((WIDTH+120, 10, 100, 30), 'Reset'),
    Button((WIDTH+10, 50, 100, 30), 'Field'),
    Button((WIDTH+120, 50, 100, 30), 'Trails'),
    Button((WIDTH+10, 300, 100, 30), 'Vel'),
    Button((WIDTH+120, 300, 100, 30), 'Pull'),
    Button((WIDTH+10, 350, 100, 30), 'Grid'),
    Button((WIDTH+120, 150, 100, 30), 'Add'),
]

map_scale = 1.0
sim_speed = 1.0

drag = None
while True:
    mx, my = pygame.mouse.get_pos()
    screen.fill(BG_COL)
    if show_grid:
        for x in range(0, WIDTH, 50):
            pygame.draw.line(screen, (40,40,40), (x,0), (x,HEIGHT))
        for y in range(0, HEIGHT, 50):
            pygame.draw.line(screen, (40,40,40), (0,y), (WIDTH,y))
    pygame.draw.rect(screen, UI_BG, (WIDTH, 0, UI_WIDTH, HEIGHT))
    screen.blit(font.render('Mass:', True, TEXT_COL), (WIDTH+10, 80))
    mass_input.draw()
    screen.blit(font.render('Speed:', True, TEXT_COL), (WIDTH+10, 130))
    speed_input.draw()
    screen.blit(font.render('Map Size:', True, TEXT_COL), (WIDTH+10, 180))
    for btn in size_buttons: btn.draw(btn.is_hover((mx,my)))

    screen.blit(font.render('Sim Speed:', True, TEXT_COL), (WIDTH+10, 230))
    for i, btn in enumerate(speed_buttons):
        btn.draw(btn.is_hover((mx,my)), active=(speed_options[i]==sim_speed))

    y0 = 400
    remove_buttons = []
    for i, p in enumerate(planets):
        info = f'{i}: m{p.mass} r{p.radius} v{int(math.hypot(p.vx,p.vy))}m/s'
        screen.blit(font.render(info, True, TEXT_COL), (WIDTH+10, y0))
        btn = Button((WIDTH+230, y0, 80, 20), 'Remove')
        btn.draw()
        remove_buttons.append((btn, p))
        y0 += 30

    for event in pygame.event.get():
        mass_input.handle_event(event)
        speed_input.handle_event(event)
        if event.type == pygame.QUIT:
            sys.exit()
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for btn in buttons:
                if btn.is_hover((mx, my)):
                    if btn.text == 'Pause': paused = not paused
                    if btn.text == 'Reset':
                        planets.clear()
                        map_scale = 1.0
                        DT = BASE_DT * sim_speed
                    if btn.text == 'Field': show_field = not show_field
                    if btn.text == 'Trails': trails_on = not trails_on
                    if btn.text == 'Grid': show_grid = not show_grid
                    if btn.text == 'Add':
                        cx, cy = WIDTH/2, HEIGHT/2
                        angle = random.uniform(0, 2*math.pi)
                        r = random.uniform(100, min(WIDTH, HEIGHT)/2 - 50)*map_scale
                        x = cx + math.cos(angle)*r; y = cy + math.sin(angle)*r
                        speed = speed_input.get()
                        vx = -math.sin(angle)*speed
                        vy = math.cos(angle)*speed
                        m = mass_input.get()
                        planets.append(Planet(x, y, m, vx, vy))
                    break
            for btn in size_buttons:
                if btn.is_hover((mx, my)):
                    old_scale = map_scale
                    if btn.text == '+': map_scale *= 1.1
                    if btn.text == '-': map_scale /= 1.1
                    rescale_planets(old_scale, map_scale)
            for i, btn in enumerate(speed_buttons):
                if btn.is_hover((mx,my)):
                    sim_speed = speed_options[i]
                    DT = BASE_DT * sim_speed
            else:
                for btn, p in remove_buttons:
                    if btn.is_hover((mx, my)):
                        planets.remove(p)
                        break
                else:
                    for p in planets:
                        dx, dy = p.x - mx, p.y - (HEIGHT-my)
                        if math.hypot(dx, dy) <= p.radius:
                            drag = p
                            break
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            drag = None
        if event.type == pygame.MOUSEMOTION and drag:
            drag.x, drag.y = mx, HEIGHT-my

    if not paused:
        forces = {p:[0,0] for p in planets}
        for i, p1 in enumerate(planets):
            for p2 in planets[i+1:]:
                dx, dy = p2.x-p1.x, p2.y-p1.y
                dist_sq = dx*dx + dy*dy + 1e-5
                dist = math.sqrt(dist_sq)
                f = G * p1.mass * p2.mass / dist_sq
                fx, fy = f*dx/dist, f*dy/dist
                forces[p1][0] += fx; forces[p1][1] += fy
                forces[p2][0] -= fx; forces[p2][1] -= fy
        for p in planets:
            p.fx, p.fy = forces[p]
            p.update()
        for i in range(len(planets)):
            for j in range(i+1, len(planets)):
                resolve_collision(planets[i], planets[j])

    for p in planets:
        p.draw(map_scale, show_field, trails_on, show_vel, show_pull)
    for btn in buttons:
        btn.draw(btn.is_hover((mx, my)))
    for btn in size_buttons:
        btn.draw(btn.is_hover((mx,my)))
    for btn in speed_buttons:
        btn.draw(btn.is_hover((mx,my)), active=(btn.text[:-1] == f"{sim_speed}"))

    pygame.display.flip()
    fpsClock.tick(FPS)
