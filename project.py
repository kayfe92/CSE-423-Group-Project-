from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import math
import random

playerZ = 0.0
position = [0.0, 0.0]
# player's height
onEscalator = None  # None, 'up', or 'down'
ESCALATOR_BOTTOM_Y = 350  # where escalator starts (world space after transform)
ESCALATOR_TOP_Y = -1050  # where escalator ends
ESCALATOR_BOTTOM_Z = 0
ESCALATOR_TOP_Z = 625
ESCALATOR_RIGHT_X = 130  # right lane x (goes up)
ESCALATOR_LEFT_X = -130  # left lane x (goes down)
ESCALATOR_LANE_W = 115  # half width of each lane
escalatorOffset = 0.0
camForward = 0.0
DEFAULT_FONT = GLUT_BITMAP_HELVETICA_18
camMode = 3  # 1 = first floor, 2 = second floor, 3 = current (3rd person), 4 = FPS
showManual = True
camRadius = 1000.0
camAngle = 90.0
camHeight = 1500.0
fpMode = False

fovY = 122
WORLD_LIMIT = 2000
GRID_LENGTH = 600
TILE_SIZE = 100

PLAYER_SCALE = 0.45

enemies = []
bullets = []

MAX_ENEMIES = 15
spawnTimer = 0
spawnDelay = 180

ALT_COST = 5
ALT_RADIUS = 350

speedBullet = 10.0

gunFwd = 265.0 * PLAYER_SCALE
gunH = 180.0 * PLAYER_SCALE

playerAngle = 90.0
gunAngle = 90.0
health = 5
score = 0
missed = 0
gameOver = False

frame = 0
lastShot = 0

cheatMode = False
autoCam = False


def draw_text(x, y, text, font=None):
    if font is None:
        font = DEFAULT_FONT
    glColor3f(1, 1, 1)
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()

    gluOrtho2D(0, 1000, 0, 800)

    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()

    glRasterPos2f(x, y)
    for ch in text:
        glutBitmapCharacter(font, ord(ch))

    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)


def enemy_initialize():
    global enemies
    enemies = []

    for i in range(5):
        createEnemy()

def getMaxEnemiesForWave():
    wave = getCurrentWave()

    if wave == 1:
        return 5

    if wave == 2:
        return 10

    return 15

def getCurrentWave():
    # Wave 3 start
    if score >= 15 or missed >= 4:
        return 3

    # Wave 2 start
    if score >= 10 or missed >= 2 or playerZ > 300:
        return 2

    # Default
    return 1


def chooseZombieType():
    wave = getCurrentWave()
    r = random.random()

    # Wave 1: only brute zombies
    if wave == 1:
        return {
            "type": "brute",
            "scale": 1.0,
            "speed": 0.08,
        }

    # Wave 2: brute + runner zombies
    if wave == 2:
        if r < 0.65:
            return {
                "type": "brute",
                "scale": 1.0,
                "speed": 0.08,
            }
        else:
            return {
                "type": "runner",
                "scale": 1.0,
                "speed": 0.16,
            }

    # Wave 3: brute + runner + normal zombies
    if r < 0.40:
        return {
            "type": "brute",
            "scale": 1.0,
            "speed": 0.08,
        }
    elif r < 0.70:
        return {
            "type": "runner",
            "scale": 1.0,
            "speed": 0.16,
        }
    else:
        return {
            "type": "normal",
            "scale": 1.0,
            "speed": 0.28,
        }


def createEnemy():
    zombie = chooseZombieType()

    # Zombies always spawn on ground floor only
    x = random.uniform(-1800, 1800)
    y = random.uniform(-1800, 1800)

    # Prevent unfair spawn directly on top of player
    while math.hypot(x - position[0], y - position[1]) < 500:
        x = random.uniform(-1800, 1800)
        y = random.uniform(-1800, 1800)

    enemies.append({
        "x": x,
        "y": y,
        "z": 0,                         # starts on first floor only
        "type": zombie["type"],         # zombie type
        "scale": zombie["scale"],       # current animated scale
        "baseScale": zombie["scale"],   # original scale
        "speed": zombie["speed"],       # individual speed
        "phase": random.uniform(0, 3.14)
    })

def updateEnemyFloor(enemy):
    ex, ey = enemy["x"], enemy["y"]

    in_esc_y = ESCALATOR_TOP_Y <= ey <= ESCALATOR_BOTTOM_Y

    on_right = in_esc_y and abs(ex - ESCALATOR_RIGHT_X) < ESCALATOR_LANE_W
    on_left = in_esc_y and abs(ex - ESCALATOR_LEFT_X) < ESCALATOR_LANE_W

    if on_right:
        t = (ESCALATOR_BOTTOM_Y - ey) / (ESCALATOR_BOTTOM_Y - ESCALATOR_TOP_Y)
        t = max(0.0, min(1.0, t))
        enemy["z"] = ESCALATOR_BOTTOM_Z + t * (ESCALATOR_TOP_Z - ESCALATOR_BOTTOM_Z)

    elif on_left:
        t = (ESCALATOR_BOTTOM_Y - ey) / (ESCALATOR_BOTTOM_Y - ESCALATOR_TOP_Y)
        t = max(0.0, min(1.0, t))
        enemy["z"] = ESCALATOR_TOP_Z - t * (ESCALATOR_TOP_Z - ESCALATOR_BOTTOM_Z)

    else:
        if enemy["z"] > 300:
            enemy["z"] = ESCALATOR_TOP_Z
        else:
            enemy["z"] = ESCALATOR_BOTTOM_Z

def resetGame():
    global bullets, playerAngle, score, position
    global cheatMode, health, missed
    global gameOver, autoCam, gunAngle

    health = 5
    position = [0.0, 0.0]
    cheatMode = autoCam = gameOver = False

    bullets = []
    score = 0
    gunAngle = 90.0
    missed = 0

    playerAngle = 90.0

    enemy_initialize()


def playerBound():
    margin = 50.0

    # Escalator zone detection
    in_esc_y = ESCALATOR_TOP_Y <= position[1] <= ESCALATOR_BOTTOM_Y
    near_right = abs(position[0] - ESCALATOR_RIGHT_X) < ESCALATOR_LANE_W
    near_left  = abs(position[0] - ESCALATOR_LEFT_X)  < ESCALATOR_LANE_W
    on_escalator = in_esc_y and (near_right or near_left)

    if on_escalator:
        # Lock player inside their escalator lane
        cx = ESCALATOR_RIGHT_X if near_right else ESCALATOR_LEFT_X
        if position[0] < cx - ESCALATOR_LANE_W + margin:
            position[0] = cx - ESCALATOR_LANE_W + margin
        elif position[0] > cx + ESCALATOR_LANE_W - margin:
            position[0] = cx + ESCALATOR_LANE_W - margin
        if position[1] < ESCALATOR_TOP_Y:
            position[1] = ESCALATOR_TOP_Y
        elif position[1] > ESCALATOR_BOTTOM_Y:
            position[1] = ESCALATOR_BOTTOM_Y
        return  # skip floor bounds while on escalator

    if playerZ > 300:
        # 2nd floor bounds
        x_limit = 2000
        y_min = -3000 + margin
        y_max = -1000 - margin   # -1050, aligns with escalator top

        if position[0] < -x_limit + margin:
            position[0] = -x_limit + margin
        elif position[0] > x_limit - margin:
            position[0] = x_limit - margin
        if position[1] < y_min:
            position[1] = y_min
        elif position[1] > y_max:
            position[1] = y_max
    else:
        # 1st floor bounds
        x_limit = 2000
        y_limit = 2000

        if position[0] < -x_limit + margin:
            position[0] = -x_limit + margin
        elif position[0] > x_limit - margin:
            position[0] = x_limit - margin
        if position[1] < -y_limit + margin:
            position[1] = -y_limit + margin
        elif position[1] > y_limit - margin:
            position[1] = y_limit - margin


def setupCamera():
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(fovY, 1.25, 0.1, 3000)

    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

    # ---- FIRST PERSON (mode 4) ----
    if camMode == 4:
        look_ang = gunAngle if cheatMode and autoCam else playerAngle
        rad = math.radians(look_ang)

        dir_x = math.cos(rad)
        dir_y = math.sin(rad)

        cam_x = position[0] + dir_x * 20
        cam_y = position[1] + dir_y * 20
        cam_z = playerZ + 270.0 * PLAYER_SCALE  # add playerZ here

        look_x = position[0] + dir_x * 600
        look_y = position[1] + dir_y * 600
        look_z = playerZ  # look at same floor level

        gluLookAt(cam_x, cam_y, cam_z,
                  look_x, look_y, look_z,
                  0, 0, 1)

    else:
        rad = math.radians(camAngle)
        base_x = math.cos(rad) * camRadius
        base_y = math.sin(rad) * camRadius

        # apply forward/back offset
        forward_x = -math.cos(rad) * camForward
        forward_y = -math.sin(rad) * camForward

        cx = base_x + forward_x
        cy = base_y + forward_y

        # ---- MODE 2: FIXED RAILING CAMERA ----
        if camMode == 2:
            rad = math.radians(camAngle)

            # forward/back direction
            dir_x = -math.cos(rad)
            dir_y = -math.sin(rad)

            cam_x = dir_x * camForward
            cam_y = -1100 + dir_y * camForward
            cam_z = 750

            look_x = cam_x + dir_x * 600
            look_y = cam_y + dir_y * 600

            gluLookAt(cam_x, cam_y, cam_z,
                      look_x, look_y, 200,
                      0, 0, 1)

        else:
            # ---- HEIGHT CONTROL ----
            if camMode == 1:
                height = 500
            else:  # camMode == 3
                height = camHeight

            # ---- FORWARD LOOK ----
            dir_x = -math.cos(rad)
            dir_y = -math.sin(rad)

            look_distance = 1200  # increase this for more front/back view

            look_x = dir_x * look_distance
            look_y = dir_y * look_distance

            gluLookAt(cx, cy, height,
                      look_x, look_y, 0,
                      0, 0, 1)


def collisionCheacker():
    global health, score, missed, gameOver, bullets, enemies

    activeBullets = []

    for bullet in bullets:
        x_out = abs(bullet["x"]) > WORLD_LIMIT
        y_out = abs(bullet["y"]) > WORLD_LIMIT

        if (x_out or y_out):
            missed += 1
            if missed >= 5:
                gameOver = True
            continue

        hitEnemy = None
        for enemy in enemies:
            gap = math.hypot(bullet["x"] - enemy["x"], bullet["y"] - enemy["y"])
            if gap < 40:
                hitEnemy = enemy
                break

        if hitEnemy:
            enemies.remove(hitEnemy)
            score += 1
        else:
            activeBullets.append(bullet)

    bullets = activeBullets

    for enemy in enemies[:]:
        gap_xy = math.hypot(position[0] - enemy["x"], position[1] - enemy["y"])
        gap_z = abs(playerZ - enemy["z"])

        if gap_xy < 70 and gap_z < 120:
            enemies.remove(enemy)
            health -= 1
            if health <= 0:
                gameOver = True
                return
def cheatShoot():
    global gunAngle, lastShot, frame

    # Rotate gun automatically
    gunAngle = (gunAngle + 3) % 360

    # Fire only every few frames to prevent spam
    if frame - lastShot < 20:
        return

    rad = math.radians(gunAngle)

    # Spawn bullet in front of player
    bx, by, bz = bulletSpawn(gunAngle)

    bullets.append({
        "x": bx,
        "y": by,
        "z": bz,
        "dx": math.cos(rad) * speedBullet,
        "dy": math.sin(rad) * speedBullet
    })

    lastShot = frame

def idle():
    global frame, gunAngle, bullets, lastShot, escalatorOffset
    global playerZ, onEscalator, spawnTimer

    if gameOver:
        glutPostRedisplay()
        return

    frame += 1
    escalatorOffset = (escalatorOffset + 0.75) % NUM_STEPS

    # Escalator detection
    px, py = position[0], position[1]

    # check if player is within escalator zone (Y range in world space)
    in_esc_y = ESCALATOR_TOP_Y <= py <= ESCALATOR_BOTTOM_Y

    on_right = in_esc_y and abs(px - ESCALATOR_RIGHT_X) < ESCALATOR_LANE_W
    on_left = in_esc_y and abs(px - ESCALATOR_LEFT_X) < ESCALATOR_LANE_W

    if on_right:
        onEscalator = 'up'
    elif on_left:
        onEscalator = 'down'
    else:
        onEscalator = None

    #Move player Z based on escalator
    if onEscalator == 'up':
        # interpolate Z based on Y position along escalator
        t = (ESCALATOR_BOTTOM_Y - py) / (ESCALATOR_BOTTOM_Y - ESCALATOR_TOP_Y)
        t = max(0.0, min(1.0, t))
        playerZ = ESCALATOR_BOTTOM_Z + t * (ESCALATOR_TOP_Z - ESCALATOR_BOTTOM_Z)

    elif onEscalator == 'down':
        t = (ESCALATOR_BOTTOM_Y - py) / (ESCALATOR_BOTTOM_Y - ESCALATOR_TOP_Y)
        t = max(0.0, min(1.0, t))
        playerZ = ESCALATOR_BOTTOM_Z + t * (ESCALATOR_TOP_Z - ESCALATOR_BOTTOM_Z)

    else:
        # snap to correct floor based on Z
        if playerZ > 300:
            playerZ = ESCALATOR_TOP_Z  # on second floor
        else:
            playerZ = ESCALATOR_BOTTOM_Z  # on ground floor

    for bullet in bullets:
        bullet["x"] += bullet["dx"]
        bullet["y"] += bullet["dy"]

    for enemy in enemies:
        dx = position[0] - enemy["x"]
        dy = position[1] - enemy["y"]
        dist = math.hypot(dx, dy)

        if dist > 0:
            enemy["x"] += (dx / dist) * enemy["speed"]
            enemy["y"] += (dy / dist) * enemy["speed"]

        updateEnemyFloor(enemy)

        enemy["scale"] = enemy["baseScale"] + 0.08 * math.sin(frame * 0.04 + enemy["phase"])

    if cheatMode:
        cheatShoot()
    else:
        gunAngle = playerAngle
    spawnTimer += 1

    currentSpawnDelay = max(60, spawnDelay - score * 3)

    if spawnTimer >= currentSpawnDelay and len(enemies) < getMaxEnemiesForWave():
        createEnemy()
        spawnTimer = 0

    collisionCheacker()
    glutPostRedisplay()


def draw_grid():
    cols = int((2 * GRID_LENGTH) / TILE_SIZE)
    rows = cols
    start = -GRID_LENGTH

    glBegin(GL_QUADS)

    for row in range(rows):
        for col in range(cols):
            x = start + col * TILE_SIZE
            y = start + row * TILE_SIZE

            if (row + col) % 2 == 0:
                draw_tile(x, y, TILE_SIZE, (1.0, 1.0, 1.0))
            else:
                draw_tile(x, y, TILE_SIZE, (0.7, 0.5, 0.95))

    glEnd()


def draw_tile(x0, y0, size, color):
    x1 = x0 + size
    y1 = y0 + size

    glColor3f(*color)

    glVertex3f(x0, y0, 0)
    glVertex3f(x1, y0, 0)
    glVertex3f(x1, y1, 0)
    glVertex3f(x0, y1, 0)


def draw_boundaries():
    wall_height = 100
    g = GRID_LENGTH
    glBegin(GL_QUADS)
    # front
    glColor3f(0.0, 1.0, 1.0)
    glVertex3f(-g, -g, 0)
    glVertex3f(g, -g, 0)
    glVertex3f(g, -g, wall_height)
    glVertex3f(-g, -g, wall_height)
    # right
    glColor3f(0, 0, 1)
    glVertex3f(g, -g, 0)
    glVertex3f(g, g, 0)
    glVertex3f(g, g, wall_height)
    glVertex3f(g, -g, wall_height)
    # back wall
    glColor3f(1, 1, 1)
    glVertex3f(-g, g, 0)
    glVertex3f(g, g, 0)
    glVertex3f(g, g, wall_height)
    glVertex3f(-g, g, wall_height)
    # left wall
    glColor3f(0, 1, 0)
    glVertex3f(-g, -g, 0)
    glVertex3f(-g, g, 0)
    glVertex3f(-g, g, wall_height)
    glVertex3f(-g, -g, wall_height)
    glEnd()


def draw_enemy(enemy):
    x = enemy["x"]
    y = enemy["y"]
    z = enemy["z"]
    scale = enemy["scale"]

    # Move zombie to correct floor height
    glPushMatrix()
    glTranslatef(0, 0, z)

    # Use your already made zombie models
    if enemy["type"] == "brute":
        draw_brute_zombie(x, y, scale)

    elif enemy["type"] == "runner":
        draw_runner_zombie(x, y, scale)

    else:
        draw_normal_zombie(x, y, scale)

    glPopMatrix()


def draw_bullets():
    for b in bullets:
        x, y, z = b["x"], b["y"], b["z"]
        glPushMatrix()
        glTranslatef(x, y, z)
        glColor3f(1.0, 0.0, 0.0)
        glutSolidCube(10)
        glPopMatrix()


def draw_floor():
    S = 2000
    TILE = 100
    cols = int((S * 2) / TILE)
    border = 6
    b = 2

    # solid dark base
    glColor3f(0.75, 0.75, 0.75)
    glBegin(GL_QUADS)
    glVertex3f(-S, -S, 0)
    glVertex3f(S, -S, 0)
    glVertex3f(S, S, 0)
    glVertex3f(-S, S, 0)
    glEnd()

    # tile borders
    for row in range(cols):
        for col in range(cols):
            x0 = -S + col * TILE + border
            y0 = -S + row * TILE + border
            x1 = x0 + TILE - border * 2
            y1 = y0 + TILE - border * 2

            glColor3f(1, 1, 1)
            glBegin(GL_QUADS)

            # bottom edge
            glVertex3f(x0, y0, 1)
            glVertex3f(x1, y0, 1)
            glVertex3f(x1, y0 + b, 1)
            glVertex3f(x0, y0 + b, 1)

            # top edge
            glVertex3f(x0, y1 - b, 1)
            glVertex3f(x1, y1 - b, 1)
            glVertex3f(x1, y1, 1)
            glVertex3f(x0, y1, 1)

            # left edge
            glVertex3f(x0, y0, 1)
            glVertex3f(x0 + b, y0, 1)
            glVertex3f(x0 + b, y1, 1)
            glVertex3f(x0, y1, 1)

            # right edge
            glVertex3f(x1 - b, y0, 1)
            glVertex3f(x1, y0, 1)
            glVertex3f(x1, y1, 1)
            glVertex3f(x1 - b, y1, 1)

            glEnd()

ESCALATOR_LENGTH = 600
ESCALATOR_RISE = 1400
ESCALATOR_WIDTH = 230
NUM_STEPS = 14
LANE_GAP = 260


def draw_single_escalator(x_center, y_start, y_end, z_bottom, z_top, num_steps=NUM_STEPS, direction=1):
    half_w = (ESCALATOR_WIDTH / 2)
    step_d = (y_end - y_start) / num_steps
    step_h = (z_top - z_bottom) / num_steps

    # --- Inclined base / underside --- (UNCHANGED)
    glColor3f(0.35, 0.35, 0.45)
    glBegin(GL_QUADS)
    glVertex3f(x_center - half_w, y_start, z_bottom)
    glVertex3f(x_center + half_w, y_start, z_bottom)
    glVertex3f(x_center + half_w, y_end, z_top)
    glVertex3f(x_center - half_w, y_end, z_top)
    glEnd()

    # --- Steps with looping offset ---
    for i in range(num_steps + 1):
        if direction == 1:
            t = (i - escalatorOffset) % num_steps
        else:
            t = (i + escalatorOffset) % num_steps

        y0 = y_start + t * step_d
        z0 = z_bottom + t * step_h

        # Tread
        glColor3f(0.75, 0.80, 0.90)
        glBegin(GL_QUADS)
        glVertex3f(x_center - half_w, y0, z0)
        glVertex3f(x_center + half_w, y0, z0)
        glVertex3f(x_center + half_w, y0 + step_d, z0)
        glVertex3f(x_center - half_w, y0 + step_d, z0)
        glEnd()

        # Riser
        glColor3f(0.50, 0.55, 0.65)
        glBegin(GL_QUADS)
        glVertex3f(x_center - half_w, y0, z0 - step_h)
        glVertex3f(x_center + half_w, y0, z0 - step_h)
        glVertex3f(x_center + half_w, y0, z0)
        glVertex3f(x_center - half_w, y0, z0)
        glEnd()

    # --- Rails (COMPLETELY UNCHANGED) ---
    rail_thickness = 8
    rail_lift = 0
    rail_outset = 30
    rail_height = 350

    for side_x in [x_center - half_w - rail_outset,
                   x_center + half_w + rail_outset]:
        glColor3f(0.20, 0.25, 0.35)
        glBegin(GL_QUADS)
        glVertex3f(side_x - rail_thickness, y_start, z_bottom + rail_lift + rail_height)
        glVertex3f(side_x + rail_thickness, y_start, z_bottom + rail_lift + rail_height)
        glVertex3f(side_x + rail_thickness, y_end, z_top + rail_lift + rail_height)
        glVertex3f(side_x - rail_thickness, y_end, z_top + rail_lift + rail_height)
        glEnd()

        glBegin(GL_QUADS)
        glVertex3f(side_x - rail_thickness, y_start, z_bottom + rail_lift)
        glVertex3f(side_x + rail_thickness, y_start, z_bottom + rail_lift)
        glVertex3f(side_x + rail_thickness, y_end, z_top + rail_lift)
        glVertex3f(side_x - rail_thickness, y_end, z_top + rail_lift)
        glEnd()

        glColor3f(0.15, 0.20, 0.30)
        glBegin(GL_QUADS)
        glVertex3f(side_x - rail_thickness, y_start, z_bottom + rail_lift)
        glVertex3f(side_x + rail_thickness, y_start, z_bottom + rail_lift)
        glVertex3f(side_x + rail_thickness, y_start, z_bottom + rail_lift + rail_height)
        glVertex3f(side_x - rail_thickness, y_start, z_bottom + rail_lift + rail_height)
        glEnd()

        glBegin(GL_QUADS)
        glVertex3f(side_x - rail_thickness, y_end, z_top + rail_lift)
        glVertex3f(side_x + rail_thickness, y_end, z_top + rail_lift)
        glVertex3f(side_x + rail_thickness, y_end, z_top + rail_lift + rail_height)
        glVertex3f(side_x - rail_thickness, y_end, z_top + rail_lift + rail_height)
        glEnd()

        glColor3f(0.18, 0.22, 0.32)
        glBegin(GL_QUADS)
        glVertex3f(side_x - rail_thickness, y_start, z_bottom + rail_lift)
        glVertex3f(side_x - rail_thickness, y_end, z_top + rail_lift)
        glVertex3f(side_x - rail_thickness, y_end, z_top + rail_lift + rail_height)
        glVertex3f(side_x - rail_thickness, y_start, z_bottom + rail_lift + rail_height)
        glEnd()

        glBegin(GL_QUADS)
        glVertex3f(side_x + rail_thickness, y_start, z_bottom + rail_lift)
        glVertex3f(side_x + rail_thickness, y_end, z_top + rail_lift)
        glVertex3f(side_x + rail_thickness, y_end, z_top + rail_lift + rail_height)
        glVertex3f(side_x + rail_thickness, y_start, z_bottom + rail_lift + rail_height)
        glEnd()


def draw_escalators():
    center_left = -LANE_GAP / 2
    center_right = LANE_GAP / 2

    y0 = -300
    y1 = 300

    glPushMatrix()
    glRotatef(90, 1, 0, 0)
    glTranslatef(0, 300, -350)

    draw_single_escalator(center_left, y0, y1, 0, ESCALATOR_RISE, direction=1)  # up
    draw_single_escalator(center_right, y0, y1, 0, ESCALATOR_RISE, direction=-1)  # down

    glPopMatrix()


def draw_second_floor():
    S_x = 4000  # <-- control X axis width here
    S_y = 2000  # Y axis depth
    floor_z = 625
    floor_y = -2000

    glPushMatrix()
    glTranslatef(0, floor_y, floor_z)

    # solid base floor
    glColor3f(0.5, 0.5, 0.5)
    glBegin(GL_QUADS)
    glVertex3f(-S_x / 2, -S_y / 2, 0)
    glVertex3f(S_x / 2, -S_y / 2, 0)
    glVertex3f(S_x / 2, S_y / 2, 0)
    glVertex3f(-S_x / 2, S_y / 2, 0)
    glEnd()

    # tiles — use S_x and S_y for col/row counts
    TILE = 100
    cols = int(S_x / TILE)
    rows = int(S_y / TILE)
    border = 6
    b = 5

    for row in range(rows):
        for col in range(cols):
            x0 = -S_x / 2 + col * TILE + border
            y0 = -S_y / 2 + row * TILE + border
            x1 = x0 + TILE - border * 2
            y1 = y0 + TILE - border * 2

            glColor3f(0.75, 0.75, 0.75)
            glBegin(GL_QUADS)

            glVertex3f(x0, y0, 1)  # bottom edge
            glVertex3f(x1, y0, 1)
            glVertex3f(x1, y0 + b, 1)
            glVertex3f(x0, y0 + b, 1)

            glVertex3f(x0, y1 - b, 1)  # top edge
            glVertex3f(x1, y1 - b, 1)
            glVertex3f(x1, y1, 1)
            glVertex3f(x0, y1, 1)

            glVertex3f(x0, y0, 1)  # left edge
            glVertex3f(x0 + b, y0, 1)
            glVertex3f(x0 + b, y1, 1)
            glVertex3f(x0, y1, 1)

            glVertex3f(x1 - b, y0, 1)  # right edge
            glVertex3f(x1, y0, 1)
            glVertex3f(x1, y1, 1)
            glVertex3f(x1 - b, y1, 1)

            glEnd()

    glPopMatrix()


def draw_floor_connector_walls():
    z_bottom = 0  # ground floor
    z_top = 625  # second floor level

    # Shaft boundaries in world space (adjust these to fit)
    x_left = -2000
    x_right = 2000
    y_front = -2000
    y_back = 2000

    # Front wall
    glColor3f(0.6, 0.6, 0.65)
    glBegin(GL_QUADS)
    glVertex3f(x_left, y_front, z_bottom)
    glVertex3f(x_right, y_front, z_bottom)
    glVertex3f(x_right, y_front, z_top)
    glVertex3f(x_left, y_front, z_top)
    glEnd()

    # Back wall
    glBegin(GL_QUADS)
    glVertex3f(x_left, y_back, z_bottom)
    glVertex3f(x_right, y_back, z_bottom)
    glVertex3f(x_right, y_back, z_top)
    glVertex3f(x_left, y_back, z_top)
    glEnd()

    # Left wall
    glColor3f(0.55, 0.55, 0.60)
    glBegin(GL_QUADS)
    glVertex3f(x_left, y_front, z_bottom)
    glVertex3f(x_left, y_back, z_bottom)
    glVertex3f(x_left, y_back, z_top)
    glVertex3f(x_left, y_front, z_top)
    glEnd()

    # Right wall
    glBegin(GL_QUADS)
    glVertex3f(x_right, y_front, z_bottom)
    glVertex3f(x_right, y_back, z_bottom)
    glVertex3f(x_right, y_back, z_top)
    glVertex3f(x_right, y_front, z_top)
    glEnd()


def draw_second_floor_railings():
    floor_z = 625
    floor_y = -2000
    S_x = 4000  # half width X — match your draw_second_floor
    S_y = 2000  # half width Y

    post_spacing = 80
    rail_height = 120
    pt = 8  # post thickness

    x_start = -S_x / 2
    x_end = S_x / 2
    y_start = floor_y - S_y / 2
    y_end = floor_y + S_y / 2
    z = floor_z

    def base_bar_x(y_pos):
        glColor3f(0.4, 0.4, 0.45)
        glBegin(GL_QUADS)
        glVertex3f(x_start, y_pos - pt, z + 8)
        glVertex3f(x_end, y_pos - pt, z + 8)
        glVertex3f(x_end, y_pos + pt, z + 8)
        glVertex3f(x_start, y_pos + pt, z + 8)
        glEnd()

    def top_rail_x(y_pos):
        glColor3f(0.35, 0.35, 0.40)
        glBegin(GL_QUADS)
        # top face
        glVertex3f(x_start, y_pos - pt - 4, z + rail_height)
        glVertex3f(x_end, y_pos - pt - 4, z + rail_height)
        glVertex3f(x_end, y_pos + pt + 4, z + rail_height)
        glVertex3f(x_start, y_pos + pt + 4, z + rail_height)
        # front face
        glVertex3f(x_start, y_pos - pt - 4, z + rail_height - 14)
        glVertex3f(x_end, y_pos - pt - 4, z + rail_height - 14)
        glVertex3f(x_end, y_pos - pt - 4, z + rail_height)
        glVertex3f(x_start, y_pos - pt - 4, z + rail_height)
        # back face
        glVertex3f(x_start, y_pos + pt + 4, z + rail_height - 14)
        glVertex3f(x_end, y_pos + pt + 4, z + rail_height - 14)
        glVertex3f(x_end, y_pos + pt + 4, z + rail_height)
        glVertex3f(x_start, y_pos + pt + 4, z + rail_height)
        glEnd()

    def posts_x(y_pos):
        num = int((x_end - x_start) / post_spacing)
        for i in range(num + 1):
            x = x_start + i * post_spacing
            glColor3f(0.38, 0.38, 0.43)
            glBegin(GL_QUADS)
            glVertex3f(x - pt / 2, y_pos - pt, z)
            glVertex3f(x + pt / 2, y_pos - pt, z)
            glVertex3f(x + pt / 2, y_pos - pt, z + rail_height)
            glVertex3f(x - pt / 2, y_pos - pt, z + rail_height)

            glVertex3f(x - pt / 2, y_pos + pt, z)
            glVertex3f(x + pt / 2, y_pos + pt, z)
            glVertex3f(x + pt / 2, y_pos + pt, z + rail_height)
            glVertex3f(x - pt / 2, y_pos + pt, z + rail_height)

            glVertex3f(x - pt / 2, y_pos - pt, z)
            glVertex3f(x - pt / 2, y_pos + pt, z)
            glVertex3f(x - pt / 2, y_pos + pt, z + rail_height)
            glVertex3f(x - pt / 2, y_pos - pt, z + rail_height)

            glVertex3f(x + pt / 2, y_pos - pt, z)
            glVertex3f(x + pt / 2, y_pos + pt, z)
            glVertex3f(x + pt / 2, y_pos + pt, z + rail_height)
            glVertex3f(x + pt / 2, y_pos - pt, z + rail_height)
            glEnd()

    def base_bar_y(x_pos):
        glColor3f(0.4, 0.4, 0.45)
        glBegin(GL_QUADS)
        glVertex3f(x_pos - pt, y_start, z + 8)
        glVertex3f(x_pos + pt, y_start, z + 8)
        glVertex3f(x_pos + pt, y_end, z + 8)
        glVertex3f(x_pos - pt, y_end, z + 8)
        glEnd()

    def top_rail_y(x_pos):
        glColor3f(0.35, 0.35, 0.40)
        glBegin(GL_QUADS)
        glVertex3f(x_pos - pt - 4, y_start, z + rail_height)
        glVertex3f(x_pos + pt + 4, y_start, z + rail_height)
        glVertex3f(x_pos + pt + 4, y_end, z + rail_height)
        glVertex3f(x_pos - pt - 4, y_end, z + rail_height)

        glVertex3f(x_pos - pt - 4, y_start, z + rail_height - 14)
        glVertex3f(x_pos + pt + 4, y_start, z + rail_height - 14)
        glVertex3f(x_pos + pt + 4, y_start, z + rail_height)
        glVertex3f(x_pos - pt - 4, y_start, z + rail_height)

        glVertex3f(x_pos - pt - 4, y_end, z + rail_height - 14)
        glVertex3f(x_pos + pt + 4, y_end, z + rail_height - 14)
        glVertex3f(x_pos + pt + 4, y_end, z + rail_height)
        glVertex3f(x_pos - pt - 4, y_end, z + rail_height)
        glEnd()

    def posts_y(x_pos):
        num = int((y_end - y_start) / post_spacing)
        for i in range(num + 1):
            y = y_start + i * post_spacing
            glColor3f(0.38, 0.38, 0.43)
            glBegin(GL_QUADS)
            glVertex3f(x_pos - pt, y, z)
            glVertex3f(x_pos + pt, y, z)
            glVertex3f(x_pos + pt, y, z + rail_height)
            glVertex3f(x_pos - pt, y, z + rail_height)
            glEnd()

    # --- Draw all 4 sides ---
    base_bar_x(y_start)
    top_rail_x(y_start)
    posts_x(y_start)

    # base_bar_x(y_end)
    # top_rail_x(y_end)
    # posts_x(y_end)

    base_bar_y(x_start)
    top_rail_y(x_start)
    posts_y(x_start)

    base_bar_y(x_end)
    top_rail_y(x_end)
    posts_y(x_end)


def draw_cross(cx, cy, cz, size, arm_w):
    """Draw a plus/cross shape using quads on a face"""
    # Horizontal bar
    glVertex3f(cx - size, cy + arm_w, cz)
    glVertex3f(cx + size, cy + arm_w, cz)
    glVertex3f(cx + size, cy - arm_w, cz)
    glVertex3f(cx - size, cy - arm_w, cz)
    # Vertical bar
    glVertex3f(cx - arm_w, cy + size, cz)
    glVertex3f(cx + arm_w, cy + size, cz)
    glVertex3f(cx + arm_w, cy - size, cz)
    glVertex3f(cx - arm_w, cy - size, cz)


def draw_life_cube(x, y, z, s=40):
    """White cube with red cross on each face"""

    # --- White cube body ---
    glColor3f(1.0, 1.0, 1.0)
    glBegin(GL_QUADS)
    # Front
    glVertex3f(x - s, y - s, z + s);
    glVertex3f(x + s, y - s, z + s)
    glVertex3f(x + s, y + s, z + s);
    glVertex3f(x - s, y + s, z + s)
    # Back
    glVertex3f(x - s, y - s, z - s);
    glVertex3f(x + s, y - s, z - s)
    glVertex3f(x + s, y + s, z - s);
    glVertex3f(x - s, y + s, z - s)
    # Left
    glVertex3f(x - s, y - s, z - s);
    glVertex3f(x - s, y - s, z + s)
    glVertex3f(x - s, y + s, z + s);
    glVertex3f(x - s, y + s, z - s)
    # Right
    glVertex3f(x + s, y - s, z - s);
    glVertex3f(x + s, y - s, z + s)
    glVertex3f(x + s, y + s, z + s);
    glVertex3f(x + s, y + s, z - s)
    # Top
    glVertex3f(x - s, y + s, z - s);
    glVertex3f(x + s, y + s, z - s)
    glVertex3f(x + s, y + s, z + s);
    glVertex3f(x - s, y + s, z + s)
    # Bottom
    glVertex3f(x - s, y - s, z - s);
    glVertex3f(x + s, y - s, z - s)
    glVertex3f(x + s, y - s, z + s);
    glVertex3f(x - s, y - s, z + s)
    glEnd()

    # --- Red cross on each face ---
    glColor3f(0.9, 0.1, 0.1)
    arm = s * 0.55
    arm_w = s * 0.18
    offset = s + 1.0  # slightly in front of face

    glBegin(GL_QUADS)
    # Front face cross
    draw_cross(x, y, z + offset, arm, arm_w)
    # Back face cross
    draw_cross(x, y, z - offset, arm, arm_w)
    # Top face cross (on XY plane at top)
    # horizontal
    glVertex3f(x - arm, y + offset, z + arm_w)
    glVertex3f(x + arm, y + offset, z + arm_w)
    glVertex3f(x + arm, y + offset, z - arm_w)
    glVertex3f(x - arm, y + offset, z - arm_w)
    # vertical
    glVertex3f(x - arm_w, y + offset, z + arm)
    glVertex3f(x + arm_w, y + offset, z + arm)
    glVertex3f(x + arm_w, y + offset, z - arm)
    glVertex3f(x - arm_w, y + offset, z - arm)
    glEnd()


def draw_bullet(cx, cy, cz, scale=1.0, angle=0):
    """Simple bullet shape using cylinder + cone approximation"""
    glPushMatrix()
    glTranslatef(cx, cy, cz)
    glRotatef(angle, 0, 0, 1)
    glScalef(scale, scale, scale)

    quad = gluNewQuadric()

    # Body — dark gold cylinder
    glColor3f(0.75, 0.60, 0.15)
    glPushMatrix()
    glRotatef(90, 0, 1, 0)
    gluCylinder(quad, 4, 4, 20, 10, 4)
    glPopMatrix()

    # Tip — pointed cone
    glColor3f(0.85, 0.70, 0.20)
    glPushMatrix()
    glTranslatef(20, 0, 0)
    glRotatef(90, 0, 1, 0)
    gluCylinder(quad, 4, 0, 10, 10, 4)
    glPopMatrix()

    # Base — flat cap
    glColor3f(0.60, 0.50, 0.10)
    glPushMatrix()
    glRotatef(-90, 0, 1, 0)
    gluDisk(quad, 0, 4, 10, 2)
    glPopMatrix()

    glPopMatrix()


def draw_ammo_cube(x, y, z, s=40):
    """Dark cube with gold bullet symbols on faces"""

    # --- Dark grey cube body ---
    glColor3f(0.25, 0.25, 0.28)
    glBegin(GL_QUADS)
    # Front
    glVertex3f(x - s, y - s, z + s);
    glVertex3f(x + s, y - s, z + s)
    glVertex3f(x + s, y + s, z + s);
    glVertex3f(x - s, y + s, z + s)
    # Back
    glVertex3f(x - s, y - s, z - s);
    glVertex3f(x + s, y - s, z - s)
    glVertex3f(x + s, y + s, z - s);
    glVertex3f(x - s, y + s, z - s)
    # Left
    glVertex3f(x - s, y - s, z - s);
    glVertex3f(x - s, y - s, z + s)
    glVertex3f(x - s, y + s, z + s);
    glVertex3f(x - s, y + s, z - s)
    # Right
    glVertex3f(x + s, y - s, z - s);
    glVertex3f(x + s, y - s, z + s)
    glVertex3f(x + s, y + s, z + s);
    glVertex3f(x + s, y + s, z - s)
    # Top
    glVertex3f(x - s, y + s, z - s);
    glVertex3f(x + s, y + s, z - s)
    glVertex3f(x + s, y + s, z + s);
    glVertex3f(x - s, y + s, z + s)
    # Bottom
    glVertex3f(x - s, y - s, z - s);
    glVertex3f(x + s, y - s, z - s)
    glVertex3f(x + s, y - s, z + s);
    glVertex3f(x - s, y - s, z + s)
    glEnd()

    # --- Bullets on front and side faces ---
    offset = s + 2.0
    draw_bullet(x, y, z + offset, scale=1.0, angle=0)  # front — horizontal
    draw_bullet(x - s - 2, y, z, scale=1.0, angle=45)  # left  — diagonal
    draw_bullet(x, y, z - offset, scale=1.0, angle=20)  # back


def draw_normal_zombie(x, y, scale=1.0):
    """Small, slow zombie - Health 1"""
    quad = gluNewQuadric()
    glPushMatrix()
    glTranslatef(x, y, 0)
    glScalef(scale * 0.6, scale * 0.6, scale * 0.6)
    glRotatef(90, 1, 0, 0)

    # body - cuboid (Y spans from 85 to 155)
    glColor3f(0.55, 0.65, 0.35)
    glPushMatrix()
    glTranslatef(0, 120, 0)
    glScalef(55, 70, 25)
    glutSolidCube(1)
    glPopMatrix()

    # neck (starts inside body top, extends to 168)
    glColor3f(0.55, 0.65, 0.35)
    glPushMatrix()
    glTranslatef(0, 150, 0)
    glRotatef(-90, 1, 0, 0)
    gluCylinder(quad, 7, 7, 18, 10, 4)
    glPopMatrix()

    # head (radius 30, base is at 160, overlapping neck perfectly)
    glColor3f(0.6, 0.75, 0.4)
    glPushMatrix()
    glTranslatef(0, 190, 0)
    gluSphere(quad, 30, 15, 15)
    glPopMatrix()

    # red eyes
    glColor3f(1.0, 0.0, 0.0)
    glPushMatrix()
    glTranslatef(-10, 195, -28)
    gluSphere(quad, 6, 8, 8)
    glPopMatrix()
    glPushMatrix()
    glTranslatef(10, 195, -28)
    gluSphere(quad, 6, 8, 8)
    glPopMatrix()

    # arm L (anchored to shoulder)
    glColor3f(0.55, 0.65, 0.35)
    glPushMatrix()
    glTranslatef(-32, 145, 0)
    glRotatef(180, 0, 1, 0)
    gluCylinder(quad, 9, 7, 55, 10, 4)
    glPopMatrix()

    # arm R (anchored to shoulder)
    glColor3f(0.55, 0.65, 0.35)
    glPushMatrix()
    glTranslatef(32, 145, 0)
    glRotatef(180, 0, 1, 0)
    gluCylinder(quad, 9, 7, 55, 10, 4)
    glPopMatrix()

    # leg L (anchored to hip, draws downward)
    glColor3f(0.45, 0.55, 0.28)
    glPushMatrix()
    glTranslatef(-16, 85, 0)
    glRotatef(90, 1, 0, 0)
    gluCylinder(quad, 14, 8, 80, 10, 6)
    glPopMatrix()

    # leg R (anchored to hip, draws downward)
    glColor3f(0.45, 0.55, 0.28)
    glPushMatrix()
    glTranslatef(16, 85, 0)
    glRotatef(90, 1, 0, 0)
    gluCylinder(quad, 14, 8, 80, 10, 6)
    glPopMatrix()

    glPopMatrix()


def draw_runner_zombie(x, y, scale=1.0):
    """Medium, fast zombie - Health 2 — leaning forward pose"""
    quad = gluNewQuadric()
    glPushMatrix()
    glTranslatef(x, y, 0)
    glScalef(scale * 0.85, scale * 0.85, scale * 0.85)
    glRotatef(90, 1, 0, 0)

    # body — leaning forward 15 degrees
    glColor3f(0.60, 0.72, 0.35)
    glPushMatrix()
    glTranslatef(0, 118, 0)
    glRotatef(15, 1, 0, 0)
    glScalef(60, 78, 28)
    glutSolidCube(1)
    glPopMatrix()

    # neck (shifted +Z and angled forward to align with leaned body)
    glColor3f(0.60, 0.72, 0.35)
    glPushMatrix()
    glTranslatef(0, 152, 8)
    glRotatef(-75, 1, 0, 0)
    gluCylinder(quad, 8, 8, 20, 10, 4)
    glPopMatrix()

    # head (tilted forward, intersects neck perfectly)
    glColor3f(0.65, 0.78, 0.38)
    glPushMatrix()
    glTranslatef(0, 188, 16)
    glRotatef(20, 1, 0, 0)
    gluSphere(quad, 32, 15, 15)
    glPopMatrix()

    # red eyes
    glColor3f(1.0, 0.0, 0.0)
    glPushMatrix()
    glTranslatef(-11, 192, -14)
    gluSphere(quad, 7, 8, 8)
    glPopMatrix()
    glPushMatrix()
    glTranslatef(11, 192, -14)
    gluSphere(quad, 7, 8, 8)
    glPopMatrix()

    # arm L — raised forward
    glColor3f(0.60, 0.72, 0.35)
    glPushMatrix()
    glTranslatef(-35, 145, 6)
    glRotatef(140, 1, 0, 0)
    gluCylinder(quad, 10, 7, 60, 10, 4)
    glPopMatrix()

    # arm R — pushed back
    glColor3f(0.60, 0.72, 0.35)
    glPushMatrix()
    glTranslatef(35, 145, 6)
    glRotatef(220, 1, 0, 0)
    gluCylinder(quad, 10, 7, 60, 10, 4)
    glPopMatrix()

    # leg L — stride forward (anchored to tilted hip)
    glColor3f(0.50, 0.62, 0.28)
    glPushMatrix()
    glTranslatef(-18, 82, -8)
    glRotatef(90, 1, 0, 0)  # Angled down and forward
    gluCylinder(quad, 15, 9, 85, 10, 6)
    glPopMatrix()

    # leg R — stride back (anchored to tilted hip)
    glColor3f(0.50, 0.62, 0.28)
    glPushMatrix()
    glTranslatef(18, 82, -8)
    glRotatef(90, 1, 0, 0)  # Angled down and backward
    gluCylinder(quad, 15, 9, 85, 10, 6)
    glPopMatrix()

    glPopMatrix()


def draw_brute_zombie(x, y, scale=1.0):
    """Large, slow zombie - Health 3 — massive build"""
    quad = gluNewQuadric()
    glPushMatrix()
    glTranslatef(x, y, 0)
    glScalef(scale * 1.4, scale * 1.4, scale * 1.4)
    glRotatef(90, 1, 0, 0)

    # body — massive wide cuboid (Y spans 65 to 155)
    glColor3f(0.40, 0.52, 0.22)
    glPushMatrix()
    glTranslatef(0, 110, 0)
    glScalef(100, 90, 45)
    glutSolidCube(1)
    glPopMatrix()

    # neck — thick, sunken into body
    glColor3f(0.38, 0.50, 0.20)
    glPushMatrix()
    glTranslatef(0, 150, 0)
    glRotatef(-90, 1, 0, 0)
    gluCylinder(quad, 15, 15, 25, 12, 4)
    glPopMatrix()

    # head — large and wide
    glColor3f(0.40, 0.52, 0.22)
    glPushMatrix()
    glTranslatef(0, 195, 0)
    glScalef(1.3, 1.1, 1.2)
    gluSphere(quad, 38, 15, 15)
    glPopMatrix()

    # red eyes — bigger and menacing
    glColor3f(1.0, 0.0, 0.0)
    glPushMatrix()
    glTranslatef(-15, 200, -35)
    gluSphere(quad, 10, 8, 8)
    glPopMatrix()
    glPushMatrix()
    glTranslatef(15, 200, -35)
    gluSphere(quad, 10, 8, 8)
    glPopMatrix()

    # Unified Left Arm (Shoulder + Arm + Fist)
    glPushMatrix()
    glTranslatef(-58, 140, 0)  # Anchored just outside body width
    # shoulder sphere
    glColor3f(0.38, 0.50, 0.20)
    gluSphere(quad, 22, 12, 12)
    # arm cylinder
    glColor3f(0.40, 0.52, 0.22)
    glRotatef(170, 0, 1, 0)
    gluCylinder(quad, 20, 14, 80, 12, 4)
    # fist sphere (translated exactly to the end of the arm cylinder)
    glColor3f(0.35, 0.45, 0.18)
    glTranslatef(0, 0, 80)
    gluSphere(quad, 16, 10, 10)
    glPopMatrix()

    # Unified Right Arm (Shoulder + Arm + Fist)
    glPushMatrix()
    glTranslatef(58, 140, 0)
    # shoulder sphere
    glColor3f(0.38, 0.50, 0.20)
    gluSphere(quad, 22, 12, 12)
    # arm cylinder
    glColor3f(0.40, 0.52, 0.22)
    glRotatef(170, 0, 1, 0)
    gluCylinder(quad, 20, 14, 80, 12, 4)
    # fist sphere
    glColor3f(0.35, 0.45, 0.18)
    glTranslatef(0, 0, 80)
    gluSphere(quad, 16, 10, 10)
    glPopMatrix()

    # leg L — anchored to hip, draws down
    glColor3f(0.32, 0.42, 0.18)
    glPushMatrix()
    glTranslatef(-28, 65, 0)
    glRotatef(90, 1, 0, 0)
    gluCylinder(quad, 24, 16, 85, 12, 6)
    glPopMatrix()

    # leg R — anchored to hip, draws down
    glColor3f(0.32, 0.42, 0.18)
    glPushMatrix()
    glTranslatef(28, 65, 0)
    glRotatef(90, 1, 0, 0)
    gluCylinder(quad, 24, 16, 85, 12, 6)
    glPopMatrix()

    glPopMatrix()


def drawPlayer():
    quad = gluNewQuadric()
    glPushMatrix()

    glTranslatef(position[0], position[1], playerZ)  # use actual position
    glRotatef(playerAngle - 90, 0, 0, 1)  # face movement direction
    glRotatef(90, 1, 0, 0)
    glScalef(0.8, 0.8, 0.8)

    # --- head ---
    glColor3f(0.90, 0.72, 0.55)
    glPushMatrix()
    glTranslatef(0, 215, 0)
    gluSphere(quad, 35, 20, 20)
    glPopMatrix()

    # --- neck ---
    glColor3f(0.90, 0.72, 0.55)
    glPushMatrix()
    glTranslatef(0, 160, 0)
    glRotatef(-90, 1, 0, 0)
    gluCylinder(quad, 8, 8, 22, 12, 4)
    glPopMatrix()

    # --- white undershirt ---
    glColor3f(0.95, 0.95, 0.95)
    glPushMatrix()
    glTranslatef(0, 120, 0)
    glScalef(72, 82, 28)
    glutSolidCube(1)
    glPopMatrix()

    # --- brown vest ---
    glColor3f(0.50, 0.35, 0.18)
    glPushMatrix()
    glTranslatef(0, 122, -2)
    glScalef(68, 75, 26)
    glutSolidCube(1)
    glPopMatrix()

    # --- vest pocket ---
    glColor3f(0.45, 0.30, 0.15)
    glPushMatrix()
    glTranslatef(-18, 130, -16)
    glScalef(14, 12, 4)
    glutSolidCube(1)
    glPopMatrix()

    # --- LEFT ARM ---
    glPushMatrix()
    glTranslatef(-35, 138, 0)
    glRotatef(180, 0, 1, 0)
    glColor3f(0.90, 0.72, 0.55)
    gluCylinder(quad, 12, 9, 70, 12, 4)
    glTranslatef(0, 0, 70)
    glColor3f(0.55, 0.38, 0.22)
    gluSphere(quad, 13, 10, 10)
    glTranslatef(0, 3, 5)
    glColor3f(0.30, 0.30, 0.30)
    gluCylinder(quad, 5, 4, 45, 12, 4)
    glColor3f(0.25, 0.18, 0.10)
    glPushMatrix()
    glTranslatef(0, -2, 5)
    glRotatef(100, 1, 0, 0)
    gluCylinder(quad, 4, 3, 20, 8, 4)
    glPopMatrix()
    glPopMatrix()

    # --- RIGHT ARM ---
    glColor3f(0.90, 0.72, 0.55)
    glPushMatrix()
    glTranslatef(35, 138, 0)
    glRotatef(180, 0, 1, 0)
    gluCylinder(quad, 12, 9, 70, 12, 4)
    glPopMatrix()

    # --- right hand ---
    glColor3f(0.90, 0.72, 0.55)
    glPushMatrix()
    glTranslatef(35, 138, -70)
    gluSphere(quad, 11, 10, 10)
    glPopMatrix()

    # --- pants leg L ---
    glColor3f(0.42, 0.28, 0.12)
    glPushMatrix()
    glTranslatef(-20, 80, 0)
    glScalef(26, 45, 24)
    glutSolidCube(1)
    glPopMatrix()

    # --- pants leg R ---
    glColor3f(0.42, 0.28, 0.12)
    glPushMatrix()
    glTranslatef(20, 80, 0)
    glScalef(26, 45, 24)
    glutSolidCube(1)
    glPopMatrix()

    # --- lower leg L ---
    glColor3f(0.38, 0.24, 0.10)
    glPushMatrix()
    glTranslatef(-20, 55, 0)
    glRotatef(90, 1, 0, 0)
    gluCylinder(quad, 13, 10, 55, 12, 6)
    glPopMatrix()

    # --- lower leg R ---
    glColor3f(0.38, 0.24, 0.10)
    glPushMatrix()
    glTranslatef(20, 55, 0)
    glRotatef(90, 1, 0, 0)
    gluCylinder(quad, 13, 10, 55, 12, 6)
    glPopMatrix()

    # --- boot L ---
    glColor3f(0.28, 0.16, 0.08)
    glPushMatrix()
    glTranslatef(-20, 0, 2)
    glScalef(1.2, 0.6, 1.4)
    gluSphere(quad, 16, 10, 10)
    glPopMatrix()

    # --- boot R ---
    glColor3f(0.28, 0.16, 0.08)
    glPushMatrix()
    glTranslatef(20, 0, 2)
    glScalef(1.2, 0.6, 1.4)
    gluSphere(quad, 16, 10, 10)
    glPopMatrix()

    glPopMatrix()

def useAltSkill():
    global score, enemies

    if score < ALT_COST:
        return

    score -= ALT_COST

    remaining = []

    for enemy in enemies:
        gap_xy = math.hypot(position[0] - enemy["x"], position[1] - enemy["y"])
        gap_z = abs(playerZ - enemy["z"])

        if gap_xy <= ALT_RADIUS and gap_z < 200:
            continue
        else:
            remaining.append(enemy)

    enemies = remaining


def showScreen():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    glViewport(0, 0, 1000, 800)

    setupCamera()
    drawPlayer()
    draw_floor()
    #draw_normal_zombie(200, 700, 1.0)
    #draw_runner_zombie(0, 700, 1.0)
    #draw_brute_zombie(-200, 700, 1.0)
    draw_life_cube(500, 100, 40)  # raised up on Z
    draw_ammo_cube(-500, 100, 40)  # raised up on Z
    draw_escalators()
    draw_floor_connector_walls()
    draw_second_floor()
    draw_second_floor_railings()

    # draw_grid()
    # draw_boundaries()

    for e in enemies:
      draw_enemy(e)

    draw_bullets()

    if showManual:
        draw_text(300, 600, "BULLET FRENZY")
        draw_text(250, 550, "Press ENTER to Start")

        draw_text(200, 480, "Controls:")
        draw_text(200, 450, "W/S - Move Forward/Backward")
        draw_text(200, 420, "A/D - Rotate Player")
        draw_text(200, 390, "Mouse Left - Shoot")
        draw_text(200, 360, "Mouse Right - Toggle FPS")

        draw_text(200, 310, "Camera Modes:")
        draw_text(200, 280, "1 - First Floor View")
        draw_text(200, 250, "2 - Second Floor View")
        draw_text(200, 220, "3 - Third Person View")
        draw_text(200, 190, "4 - First Person View")

        draw_text(200, 140, "C - Cheat Mode")
        draw_text(200, 110, "V - Auto Aim")

    hud_x = 15  # left margin
    hud_y = 770  # top position
    gap = 25  # vertical spacing

    draw_text(hud_x, hud_y, f"Life: {health}")
    draw_text(hud_x, hud_y - gap, f"Score: {score}")
    draw_text(hud_x, hud_y - gap * 2, f"Missed: {missed}")
    draw_text(hud_x, hud_y - gap * 3, f"Wave: {getCurrentWave()}")

    draw_text(hud_x, hud_y - gap * 4, "F: Blast (-5)")

    if cheatMode:
        draw_text(hud_x, hud_y - gap * 5, "Cheat: ON")

    if autoCam and fpMode:
        draw_text(hud_x, hud_y - gap * 6, "AutoCam: ON")

    if gameOver:
        draw_text(350, 400, "GAME OVER! Press R")

    glutSwapBuffers()


def keyboardListener(key, x, y):
    global position, playerAngle, cheatMode, autoCam, camMode, showManual

    if gameOver:
        if key == b'r':
            resetGame()
        return

    move_speed = 20.0

    if cheatMode:
        move_angle = gunAngle
    else:
        move_angle = playerAngle

    rad = math.radians(move_angle)

    # Move forward (W key)
    if key == b'w':
        position[0] += math.cos(rad) * move_speed
        position[1] += math.sin(rad) * move_speed

    # Move backward (S key)
    if key == b's':
        position[0] -= math.cos(rad) * move_speed
        position[1] -= math.sin(rad) * move_speed

    # Rotate left (A key)
    if key == b'a':
        playerAngle += 10

    # Rotate right (D key)
    if key == b'd':
        playerAngle -= 10

    # Toggle cheat mode (C key)
    if key == b'c':
        cheatMode = not cheatMode

    # Toggle cheat vision (V key)
    if key == b'v':
        autoCam = not autoCam

    #Alt skill activate
    if key == b'f':
        useAltSkill()

    # ---- CAMERA MODES ----
    if key == b'1':
        camMode = 1
    if key == b'2':
        camMode = 2
    if key == b'3':
        camMode = 3
    if key == b'4':
        camMode = 4

    # ---- START GAME (hide manual) ----
    if key == b'\r':
        showManual = False

    playerAngle %= 360
    playerBound()


def specialKeyListener(key, x, y):
    global camHeight, camAngle, camForward

    # ---- UP / DOWN ----
    if key == GLUT_KEY_UP:
        if camMode in [1, 2]:
            camForward += 50  # move forward
        else:
            camHeight += 20

    if key == GLUT_KEY_DOWN:
        if camMode in [1, 2]:
            camForward -= 50  # move backward
        else:
            camHeight -= 20

    # moving camera left (LEFT arrow key)
    if key == GLUT_KEY_LEFT:
        camAngle += 5  # Small angle decrement for smooth movement

    # moving camera right (RIGHT arrow key)
    if key == GLUT_KEY_RIGHT:
        camAngle -= 5  # Small angle increment for smooth movement

        # Keep camera height from going below the floor/viewing area
    camHeight = max(200, camHeight)

    # Keep angle clean between 0 and 359 degrees
    camAngle %= 360
def bulletSpawn(angle):
    rad = math.radians(angle)

    bx = position[0] + math.cos(rad) * gunFwd
    by = position[1] + math.sin(rad) * gunFwd
    bz = playerZ + gunH

    return bx, by, bz

def mouseListener(button, state, x, y):
    global fpMode

    if gameOver:
        return

    # Left mouse button fires a bullet
    if button == GLUT_LEFT_BUTTON and state == GLUT_DOWN:
        if cheatMode:
            shoot_angle = gunAngle
        else:
            shoot_angle = playerAngle

        rad = math.radians(shoot_angle)
        bx, by, bz = bulletSpawn(shoot_angle)
        bullets.append({
            "x": bx,
            "y": by,
            "z": bz,
            "dx": math.cos(rad) * speedBullet,
            "dy": math.sin(rad) * speedBullet
        })

    # Right mouse button toggles camera tracking mode
    if button == GLUT_RIGHT_BUTTON and state == GLUT_DOWN:
        fpMode = not fpMode
        if fpMode:
            camMode = 4
        else:
            camMode = 3


# Main function to set up OpenGL window and loop
def main():
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)  # Double buffering, RGB color, depth test
    glutInitWindowSize(1000, 800)  # Window size
    glutInitWindowPosition(0, 0)  # Window position
    wind = glutCreateWindow(b"Bracu Zombie Outbreak")  # Create the window

    enemy_initialize()

    glutDisplayFunc(showScreen)  # Register display function
    glutKeyboardFunc(keyboardListener)  # Register keyboard listener
    glutSpecialFunc(specialKeyListener)
    glutMouseFunc(mouseListener)
    glutIdleFunc(idle)
    glEnable(GL_DEPTH_TEST)
    glutMainLoop()  # Enter the GLUT main loop


if __name__ == "__main__":
    main()
