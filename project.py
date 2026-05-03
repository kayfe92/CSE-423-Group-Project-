from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import math
import random

playerZ=625.0
position=[0.0,-2000.0]
onEscalator=None
ESCALATOR_BOTTOM_Y=350
ESCALATOR_TOP_Y=-1050
ESCALATOR_BOTTOM_Z=0
ESCALATOR_TOP_Z=625
ESCALATOR_RIGHT_X=130
ESCALATOR_LEFT_X=-130
ESCALATOR_LANE_W=115
escalatorOffset=0.0
camForward=0.0
DEFAULT_FONT=GLUT_BITMAP_HELVETICA_18
camMode=3
showManual=True
camRadius=1000.0
camAngle=90.0
camHeight=1500.0
fpMode=False

fovY=122
WORLD_LIMIT=2000
GRID_LENGTH=600
TILE_SIZE=100

PLAYER_SCALE=0.8

enemies=[]
bullets=[]

MAX_ENEMIES=15
spawnTimer=0
spawnDelay=60

ALT_COST=5
ALT_RADIUS=350

speedBullet=120.0

gunFwd=265.0*PLAYER_SCALE
gunH=180.0*PLAYER_SCALE

playerAngle=90.0
gunAngle=90.0
health=5
ammo=30
score=0
missed=0
gameOver=False

frame=0
lastShot=0

cheatMode=False
autoCam=False

currentWaveNum=1
MAX_WAVES=3
wavePaused=False
waveCleared=False
gameWon=False

enemiesKilledThisWave=0
WAVE_KILL_TARGETS={1:10,2:20,3:30}

pickup=None
PICKUP_SPAWN_Z=625
PICKUP_RADIUS=80
PICKUP_INTERVAL=3
pickupTimer=0

def spawn_single_pickup():
    global pickup
    floor_x_min,floor_x_max=-1800,1800
    floor_y_min,floor_y_max=-2900,-1100
    ptype=random.choice(["health","ammo"])
    px=random.uniform(floor_x_min,floor_x_max)
    py=random.uniform(floor_y_min,floor_y_max)
    pickup={"type":ptype,"x":px,"y":py,"active":True}

def spawn_pickups():
    global pickup,pickupTimer
    pickup=None
    pickupTimer=0


def draw_text(x,y,text,font=None):
    if font is None:
        font=DEFAULT_FONT
    glColor3f(1,1,1)
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()

    gluOrtho2D(0,1000,0,800)

    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()

    glRasterPos2f(x,y)
    for ch in text:
        glutBitmapCharacter(font,ord(ch))

    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)


def enemy_initialize():
    global enemies
    enemies=[]

    for i in range(5):
        createEnemy()

def getMaxEnemiesForWave():
    if currentWaveNum==1:
        return 8
    if currentWaveNum==2:
        return 12
    return 20

def getCurrentWave():
    return currentWaveNum


def chooseZombieType():
    wave=getCurrentWave()
    r=random.random()

    if wave==1:
        return {
            "type":"brute",
            "scale":1.0,
            "speed":1.8,
        }

    if wave==2:
        if r<0.65:
            return {
                "type":"brute",
                "scale":1.0,
                "speed":1.8,
            }
        else:
            return {
                "type":"runner",
                "scale":1.0,
                "speed":3.2,
            }

    if r<0.40:
        return {
            "type":"brute",
            "scale":1.0,
            "speed":1.8,
        }
    elif r<0.70:
        return {
            "type":"runner",
            "scale":1.0,
            "speed":3.2,
        }
    else:
        return {
            "type":"normal",
            "scale":1.0,
            "speed":5.5,
        }


def createEnemy():
    zombie=chooseZombieType()

    x=random.uniform(-1800,1800)
    y=random.uniform(-1800,1800)

    while math.hypot(x-position[0],y-position[1])<500:
        x=random.uniform(-1800,1800)
        y=random.uniform(-1800,1800)

    enemies.append({
        "x":x,
        "y":y,
        "z":0,
        "type":zombie["type"],
        "scale":zombie["scale"],
        "baseScale":zombie["scale"],
        "speed":zombie["speed"],
        "phase":random.uniform(0,3.14)
    })

def updateEnemyFloor(enemy):
    enemy["z"]=ESCALATOR_BOTTOM_Z

def resetGame():
    global bullets,playerAngle,score,position
    global cheatMode,health,ammo,missed
    global gameOver,autoCam,gunAngle
    global currentWaveNum,wavePaused,waveCleared,gameWon
    global enemiesKilledThisWave

    health=5
    ammo=30
    position=[0.0,-1500.0]
    global playerZ
    playerZ=625.0
    cheatMode=autoCam=gameOver=False
    wavePaused=False
    waveCleared=False
    gameWon=False
    currentWaveNum=1
    enemiesKilledThisWave=0

    bullets=[]
    score=0
    gunAngle=90.0
    missed=0

    playerAngle=90.0

    enemy_initialize()
    spawn_pickups()


def playerBound():
    margin=50.0

    in_esc_y=ESCALATOR_TOP_Y<=position[1]<=ESCALATOR_BOTTOM_Y
    near_right=abs(position[0]-ESCALATOR_RIGHT_X)<ESCALATOR_LANE_W
    near_left=abs(position[0]-ESCALATOR_LEFT_X)<ESCALATOR_LANE_W
    on_escalator=in_esc_y and (near_right or near_left)

    if on_escalator:
        cx=ESCALATOR_RIGHT_X if near_right else ESCALATOR_LEFT_X
        if position[0]<cx-ESCALATOR_LANE_W+margin:
            position[0]=cx-ESCALATOR_LANE_W+margin
        elif position[0]>cx+ESCALATOR_LANE_W-margin:
            position[0]=cx+ESCALATOR_LANE_W-margin
        if position[1]<ESCALATOR_TOP_Y:
            position[1]=ESCALATOR_TOP_Y
        elif position[1]>ESCALATOR_BOTTOM_Y:
            position[1]=ESCALATOR_BOTTOM_Y
        return

    if playerZ>300:
        x_limit=2000
        y_min=-3000+margin
        y_max=-1000-margin

        if position[0]<-x_limit+margin:
            position[0]=-x_limit+margin
        elif position[0]>x_limit-margin:
            position[0]=x_limit-margin
        if position[1]<y_min:
            position[1]=y_min
        elif position[1]>y_max:
            position[1]=y_max
    else:
        x_limit=2000
        y_limit=2000

        if position[0]<-x_limit+margin:
            position[0]=-x_limit+margin
        elif position[0]>x_limit-margin:
            position[0]=x_limit-margin
        if position[1]<-y_limit+margin:
            position[1]=-y_limit+margin
        elif position[1]>y_limit-margin:
            position[1]=y_limit-margin


def setupCamera():
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(fovY,1.25,0.1,3000)

    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

    if camMode==4:
        look_ang=gunAngle if cheatMode and autoCam else playerAngle
        rad=math.radians(look_ang)

        dir_x=math.cos(rad)
        dir_y=math.sin(rad)

        cam_x=position[0]+dir_x*20
        cam_y=position[1]+dir_y*20
        cam_z=playerZ+270.0*PLAYER_SCALE

        look_x=position[0]+dir_x*600
        look_y=position[1]+dir_y*600
        look_z=playerZ

        gluLookAt(cam_x,cam_y,cam_z,
                  look_x,look_y,look_z,
                  0,0,1)

    else:
        rad=math.radians(camAngle)
        base_x=math.cos(rad)*camRadius
        base_y=math.sin(rad)*camRadius

        forward_x=-math.cos(rad)*camForward
        forward_y=-math.sin(rad)*camForward

        cx=base_x+forward_x
        cy=base_y+forward_y

        if camMode==2:
            rad=math.radians(camAngle)

            dir_x=-math.cos(rad)
            dir_y=-math.sin(rad)

            cam_x=dir_x*camForward
            cam_y=-1100+dir_y*camForward
            cam_z=750

            look_x=cam_x+dir_x*600
            look_y=cam_y+dir_y*600

            gluLookAt(cam_x,cam_y,cam_z,
                      look_x,look_y,200,
                      0,0,1)

        else:
            if camMode==1:
                height=500
            else:
                height=camHeight

            dir_x=-math.cos(rad)
            dir_y=-math.sin(rad)

            look_distance=1200

            look_x=dir_x*look_distance
            look_y=dir_y*look_distance

            gluLookAt(cx,cy,height,
                      look_x,look_y,0,
                      0,0,1)


def collisionCheacker():
    global health,score,missed,gameOver,bullets,enemies
    global enemiesKilledThisWave,wavePaused,waveCleared,gameWon,currentWaveNum
    global ammo

    activeBullets=[]

    for bullet in bullets:
        x_out=abs(bullet["x"])>WORLD_LIMIT
        y_out=abs(bullet["y"])>WORLD_LIMIT

        if (x_out or y_out):
            if not cheatMode:
                missed+=1
                if missed>=12:
                    gameOver=True
            continue

        hitEnemy=None
        for enemy in enemies:
            if enemy["type"]=="brute":
                hit_radius=90
            elif enemy["type"]=="runner":
                hit_radius=55
            else:
                hit_radius=40
            gap=math.hypot(bullet["x"]-enemy["x"],bullet["y"]-enemy["y"])
            if gap<hit_radius:
                hitEnemy=enemy
                break

        if hitEnemy:
            enemies.remove(hitEnemy)
            score+=1
            enemiesKilledThisWave+=1

            target=WAVE_KILL_TARGETS.get(currentWaveNum,10)
            if enemiesKilledThisWave>=target:
                if currentWaveNum>=MAX_WAVES:
                    gameWon=True
                    gameOver=True
                else:
                    wavePaused=True
                    waveCleared=True
                    enemies.clear()
                    bullets.clear()
        else:
            activeBullets.append(bullet)

    bullets=activeBullets

    for enemy in enemies[:]:
        gap_xy=math.hypot(position[0]-enemy["x"],position[1]-enemy["y"])
        gap_z=abs(playerZ-enemy["z"])

        if gap_xy<70 and gap_z<120:
            enemies.remove(enemy)
            health-=1
            if health<=0:
                gameOver=True
                return

    if playerZ>300 and pickup is not None and pickup["active"]:
        gap=math.hypot(position[0]-pickup["x"],position[1]-pickup["y"])
        if gap<PICKUP_RADIUS:
            pickup["active"]=False
            if pickup["type"]=="health":
                health=min(health+5,20)
            elif pickup["type"]=="ammo":
                ammo=min(ammo+5,99)


def cheatShoot():
    global gunAngle,lastShot,frame

    canShoot=(frame-lastShot)>20

    best_enemy=None
    best_dist=float('inf')
    for enemy in enemies:
        gap_z=abs(playerZ-enemy["z"])
        if gap_z>200:
            continue
        dist=math.hypot(enemy["x"]-position[0],enemy["y"]-position[1])
        if dist<best_dist:
            best_dist=dist
            best_enemy=enemy

    if best_enemy is not None:
        dx=best_enemy["x"]-position[0]
        dy=best_enemy["y"]-position[1]
        target_angle=math.degrees(math.atan2(dy,dx))

        diff=(target_angle-gunAngle+180)%360-180
        rotate_speed=8.0
        if abs(diff)<rotate_speed:
            gunAngle=target_angle
        else:
            gunAngle+=rotate_speed if diff>0 else -rotate_speed
        gunAngle%=360

        if abs(diff)<5.0 and canShoot:
            dist=math.hypot(dx,dy)
            dirX=dx/dist
            dirY=dy/dist
            bx,by,bz=bulletSpawn(gunAngle)
            bullets.append({
                "x":bx,
                "y":by,
                "z":bz,
                "dx":dirX*speedBullet,
                "dy":dirY*speedBullet
            })
            lastShot=frame
    else:
        gunAngle=(gunAngle+4.0)%360.0


def idle():
    global frame,gunAngle,bullets,lastShot,escalatorOffset
    global playerZ,onEscalator,spawnTimer,playerAngle
    global pickup,pickupTimer

    if gameOver or wavePaused:
        glutPostRedisplay()
        return

    frame+=1
    escalatorOffset=(escalatorOffset+0.75)%NUM_STEPS

    px,py=position[0],position[1]

    in_esc_y=ESCALATOR_TOP_Y<=py<=ESCALATOR_BOTTOM_Y

    on_right=in_esc_y and abs(px-ESCALATOR_RIGHT_X)<ESCALATOR_LANE_W
    on_left=in_esc_y and abs(px-ESCALATOR_LEFT_X)<ESCALATOR_LANE_W

    if on_right:
        onEscalator='up'
    elif on_left:
        onEscalator='down'
    else:
        onEscalator=None

    if onEscalator=='up':
        position[1]+=6.0
    elif onEscalator=='down':
        position[1]-=6.0

    if onEscalator=='up':
        t=(ESCALATOR_BOTTOM_Y-py)/(ESCALATOR_BOTTOM_Y-ESCALATOR_TOP_Y)
        t=max(0.0,min(1.0,t))
        playerZ=ESCALATOR_BOTTOM_Z+t*(ESCALATOR_TOP_Z-ESCALATOR_BOTTOM_Z)

    elif onEscalator=='down':
        t=(ESCALATOR_BOTTOM_Y-py)/(ESCALATOR_BOTTOM_Y-ESCALATOR_TOP_Y)
        t=max(0.0,min(1.0,t))
        playerZ=ESCALATOR_BOTTOM_Z+t*(ESCALATOR_TOP_Z-ESCALATOR_BOTTOM_Z)

    else:
        if playerZ>300:
            playerZ=ESCALATOR_TOP_Z
        else:
            playerZ=ESCALATOR_BOTTOM_Z

    for bullet in bullets:
        bullet["x"]+=bullet["dx"]
        bullet["y"]+=bullet["dy"]

    for enemy in enemies:
        dx=position[0]-enemy["x"]
        dy=position[1]-enemy["y"]
        dist=math.hypot(dx,dy)

        if dist>0:
            enemy["x"]+=(dx/dist)*enemy["speed"]
            enemy["y"]+=(dy/dist)*enemy["speed"]

        updateEnemyFloor(enemy)

        enemy["scale"]=enemy["baseScale"]+0.08*math.sin(frame*0.04+enemy["phase"])

    if cheatMode:
        cheatShoot()
        if autoCam:
            playerAngle=gunAngle
    else:
        if autoCam:
            best_enemy=None
            best_dist=float('inf')
            for enemy in enemies:
                gap_z=abs(playerZ-enemy["z"])
                if gap_z>200:
                    continue
                dist=math.hypot(enemy["x"]-position[0],enemy["y"]-position[1])
                if dist<best_dist:
                    best_dist=dist
                    best_enemy=enemy
            if best_enemy is not None:
                dx=best_enemy["x"]-position[0]
                dy=best_enemy["y"]-position[1]
                target_angle=math.degrees(math.atan2(dy,dx))
                diff=(target_angle-playerAngle+180)%360-180
                rotate_speed=6.0
                if abs(diff)<rotate_speed:
                    playerAngle=target_angle
                else:
                    playerAngle+=rotate_speed if diff>0 else -rotate_speed
                playerAngle%=360
            gunAngle=playerAngle
        else:
            gunAngle=playerAngle

    spawnTimer+=1

    currentSpawnDelay=max(20,spawnDelay-score*2)

    if spawnTimer>=currentSpawnDelay and len(enemies)<getMaxEnemiesForWave():
        createEnemy()
        spawnTimer=0

    if pickup is None or not pickup["active"]:
        pickupTimer+=1
        if pickupTimer>=PICKUP_INTERVAL:
            spawn_single_pickup()
            pickupTimer=0

    collisionCheacker()
    glutPostRedisplay()


def draw_enemy(enemy):
    x=enemy["x"]
    y=enemy["y"]
    z=enemy["z"]
    scale=enemy["scale"]

    glPushMatrix()
    glTranslatef(0,0,z)

    if enemy["type"]=="brute":
        draw_brute_zombie(x,y,scale)

    elif enemy["type"]=="runner":
        draw_runner_zombie(x,y,scale)

    else:
        draw_normal_zombie(x,y,scale)

    glPopMatrix()


def draw_bullets():
    for b in bullets:
        x,y,z=b["x"],b["y"],b["z"]
        glPushMatrix()
        glTranslatef(x,y,z)
        glColor3f(1.0,0.0,0.0)
        glutSolidCube(10)
        glPopMatrix()


def draw_floor():
    S=2000
    TILE=100
    cols=int((S*2)/TILE)
    border=6
    b=2

    glColor3f(0.75,0.75,0.75)
    glBegin(GL_QUADS)
    glVertex3f(-S,-S,0)
    glVertex3f(S,-S,0)
    glVertex3f(S,S,0)
    glVertex3f(-S,S,0)
    glEnd()

    for row in range(cols):
        for col in range(cols):
            x0=-S+col*TILE+border
            y0=-S+row*TILE+border
            x1=x0+TILE-border*2
            y1=y0+TILE-border*2

            glColor3f(1,1,1)
            glBegin(GL_QUADS)

            glVertex3f(x0,y0,1)
            glVertex3f(x1,y0,1)
            glVertex3f(x1,y0+b,1)
            glVertex3f(x0,y0+b,1)

            glVertex3f(x0,y1-b,1)
            glVertex3f(x1,y1-b,1)
            glVertex3f(x1,y1,1)
            glVertex3f(x0,y1,1)

            glVertex3f(x0,y0,1)
            glVertex3f(x0+b,y0,1)
            glVertex3f(x0+b,y1,1)
            glVertex3f(x0,y1,1)

            glVertex3f(x1-b,y0,1)
            glVertex3f(x1,y0,1)
            glVertex3f(x1,y1,1)
            glVertex3f(x1-b,y1,1)

            glEnd()

ESCALATOR_LENGTH=600
ESCALATOR_RISE=1400
ESCALATOR_WIDTH=230
NUM_STEPS=14
LANE_GAP=260


def draw_single_escalator(x_center,y_start,y_end,z_bottom,z_top,num_steps=NUM_STEPS,direction=1):
    half_w=(ESCALATOR_WIDTH/2)
    step_d=(y_end-y_start)/num_steps
    step_h=(z_top-z_bottom)/num_steps

    glColor3f(0.35,0.35,0.45)
    glBegin(GL_QUADS)
    glVertex3f(x_center-half_w,y_start,z_bottom)
    glVertex3f(x_center+half_w,y_start,z_bottom)
    glVertex3f(x_center+half_w,y_end,z_top)
    glVertex3f(x_center-half_w,y_end,z_top)
    glEnd()

    for i in range(num_steps+1):
        if direction==1:
            t=(i-escalatorOffset)%num_steps
        else:
            t=(i+escalatorOffset)%num_steps

        y0=y_start+t*step_d
        z0=z_bottom+t*step_h

        glColor3f(0.75,0.80,0.90)
        glBegin(GL_QUADS)
        glVertex3f(x_center-half_w,y0,z0)
        glVertex3f(x_center+half_w,y0,z0)
        glVertex3f(x_center+half_w,y0+step_d,z0)
        glVertex3f(x_center-half_w,y0+step_d,z0)
        glEnd()

        glColor3f(0.50,0.55,0.65)
        glBegin(GL_QUADS)
        glVertex3f(x_center-half_w,y0,z0-step_h)
        glVertex3f(x_center+half_w,y0,z0-step_h)
        glVertex3f(x_center+half_w,y0,z0)
        glVertex3f(x_center-half_w,y0,z0)
        glEnd()

    rail_thickness=8
    rail_lift=0
    rail_outset=30
    rail_height=350

    for side_x in [x_center-half_w-rail_outset,
                   x_center+half_w+rail_outset]:
        glColor3f(0.20,0.25,0.35)
        glBegin(GL_QUADS)
        glVertex3f(side_x-rail_thickness,y_start,z_bottom+rail_lift+rail_height)
        glVertex3f(side_x+rail_thickness,y_start,z_bottom+rail_lift+rail_height)
        glVertex3f(side_x+rail_thickness,y_end,z_top+rail_lift+rail_height)
        glVertex3f(side_x-rail_thickness,y_end,z_top+rail_lift+rail_height)
        glEnd()

        glBegin(GL_QUADS)
        glVertex3f(side_x-rail_thickness,y_start,z_bottom+rail_lift)
        glVertex3f(side_x+rail_thickness,y_start,z_bottom+rail_lift)
        glVertex3f(side_x+rail_thickness,y_end,z_top+rail_lift)
        glVertex3f(side_x-rail_thickness,y_end,z_top+rail_lift)
        glEnd()

        glColor3f(0.15,0.20,0.30)
        glBegin(GL_QUADS)
        glVertex3f(side_x-rail_thickness,y_start,z_bottom+rail_lift)
        glVertex3f(side_x+rail_thickness,y_start,z_bottom+rail_lift)
        glVertex3f(side_x+rail_thickness,y_start,z_bottom+rail_lift+rail_height)
        glVertex3f(side_x-rail_thickness,y_start,z_bottom+rail_lift+rail_height)
        glEnd()

        glBegin(GL_QUADS)
        glVertex3f(side_x-rail_thickness,y_end,z_top+rail_lift)
        glVertex3f(side_x+rail_thickness,y_end,z_top+rail_lift)
        glVertex3f(side_x+rail_thickness,y_end,z_top+rail_lift+rail_height)
        glVertex3f(side_x-rail_thickness,y_end,z_top+rail_lift+rail_height)
        glEnd()

        glColor3f(0.18,0.22,0.32)
        glBegin(GL_QUADS)
        glVertex3f(side_x-rail_thickness,y_start,z_bottom+rail_lift)
        glVertex3f(side_x-rail_thickness,y_end,z_top+rail_lift)
        glVertex3f(side_x-rail_thickness,y_end,z_top+rail_lift+rail_height)
        glVertex3f(side_x-rail_thickness,y_start,z_bottom+rail_lift+rail_height)
        glEnd()

        glBegin(GL_QUADS)
        glVertex3f(side_x+rail_thickness,y_start,z_bottom+rail_lift)
        glVertex3f(side_x+rail_thickness,y_end,z_top+rail_lift)
        glVertex3f(side_x+rail_thickness,y_end,z_top+rail_lift+rail_height)
        glVertex3f(side_x+rail_thickness,y_start,z_bottom+rail_lift+rail_height)
        glEnd()


def draw_escalators():
    center_left=-LANE_GAP/2
    center_right=LANE_GAP/2

    y0=-300
    y1=300

    glPushMatrix()
    glRotatef(90,1,0,0)
    glTranslatef(0,300,-350)

    draw_single_escalator(center_left,y0,y1,0,ESCALATOR_RISE,direction=1)
    draw_single_escalator(center_right,y0,y1,0,ESCALATOR_RISE,direction=-1)

    glPopMatrix()


def draw_second_floor():
    S_x=4000
    S_y=2000
    floor_z=625
    floor_y=-2000

    glPushMatrix()
    glTranslatef(0,floor_y,floor_z)

    glColor3f(0.5,0.5,0.5)
    glBegin(GL_QUADS)
    glVertex3f(-S_x/2,-S_y/2,0)
    glVertex3f(S_x/2,-S_y/2,0)
    glVertex3f(S_x/2,S_y/2,0)
    glVertex3f(-S_x/2,S_y/2,0)
    glEnd()

    TILE=100
    cols=int(S_x/TILE)
    rows=int(S_y/TILE)
    border=6
    b=5

    for row in range(rows):
        for col in range(cols):
            x0=-S_x/2+col*TILE+border
            y0=-S_y/2+row*TILE+border
            x1=x0+TILE-border*2
            y1=y0+TILE-border*2

            glColor3f(0.75,0.75,0.75)
            glBegin(GL_QUADS)

            glVertex3f(x0,y0,1)
            glVertex3f(x1,y0,1)
            glVertex3f(x1,y0+b,1)
            glVertex3f(x0,y0+b,1)

            glVertex3f(x0,y1-b,1)
            glVertex3f(x1,y1-b,1)
            glVertex3f(x1,y1,1)
            glVertex3f(x0,y1,1)

            glVertex3f(x0,y0,1)
            glVertex3f(x0+b,y0,1)
            glVertex3f(x0+b,y1,1)
            glVertex3f(x0,y1,1)

            glVertex3f(x1-b,y0,1)
            glVertex3f(x1,y0,1)
            glVertex3f(x1,y1,1)
            glVertex3f(x1-b,y1,1)

            glEnd()

    glPopMatrix()


def draw_floor_connector_walls():
    z_bottom=0
    z_top=625

    x_left=-2000
    x_right=2000
    y_front=-2000
    y_back=2000

    glColor3f(0.6,0.6,0.65)
    glBegin(GL_QUADS)
    glVertex3f(x_left,y_front,z_bottom)
    glVertex3f(x_right,y_front,z_bottom)
    glVertex3f(x_right,y_front,z_top)
    glVertex3f(x_left,y_front,z_top)
    glEnd()

    glBegin(GL_QUADS)
    glVertex3f(x_left,y_back,z_bottom)
    glVertex3f(x_right,y_back,z_bottom)
    glVertex3f(x_right,y_back,z_top)
    glVertex3f(x_left,y_back,z_top)
    glEnd()

    glColor3f(0.55,0.55,0.60)
    glBegin(GL_QUADS)
    glVertex3f(x_left,y_front,z_bottom)
    glVertex3f(x_left,y_back,z_bottom)
    glVertex3f(x_left,y_back,z_top)
    glVertex3f(x_left,y_front,z_top)
    glEnd()

    glBegin(GL_QUADS)
    glVertex3f(x_right,y_front,z_bottom)
    glVertex3f(x_right,y_back,z_bottom)
    glVertex3f(x_right,y_back,z_top)
    glVertex3f(x_right,y_front,z_top)
    glEnd()


def draw_second_floor_railings():
    floor_z=625
    floor_y=-2000
    S_x=4000
    S_y=2000

    post_spacing=80
    rail_height=120
    pt=8

    x_start=-S_x/2
    x_end=S_x/2
    y_start=floor_y-S_y/2
    y_end=floor_y+S_y/2
    z=floor_z

    def base_bar_x(y_pos):
        glColor3f(0.4,0.4,0.45)
        glBegin(GL_QUADS)
        glVertex3f(x_start,y_pos-pt,z+8)
        glVertex3f(x_end,y_pos-pt,z+8)
        glVertex3f(x_end,y_pos+pt,z+8)
        glVertex3f(x_start,y_pos+pt,z+8)
        glEnd()

    def top_rail_x(y_pos):
        glColor3f(0.35,0.35,0.40)
        glBegin(GL_QUADS)
        glVertex3f(x_start,y_pos-pt-4,z+rail_height)
        glVertex3f(x_end,y_pos-pt-4,z+rail_height)
        glVertex3f(x_end,y_pos+pt+4,z+rail_height)
        glVertex3f(x_start,y_pos+pt+4,z+rail_height)
        glVertex3f(x_start,y_pos-pt-4,z+rail_height-14)
        glVertex3f(x_end,y_pos-pt-4,z+rail_height-14)
        glVertex3f(x_end,y_pos-pt-4,z+rail_height)
        glVertex3f(x_start,y_pos-pt-4,z+rail_height)
        glVertex3f(x_start,y_pos+pt+4,z+rail_height-14)
        glVertex3f(x_end,y_pos+pt+4,z+rail_height-14)
        glVertex3f(x_end,y_pos+pt+4,z+rail_height)
        glVertex3f(x_start,y_pos+pt+4,z+rail_height)
        glEnd()

    def posts_x(y_pos):
        num=int((x_end-x_start)/post_spacing)
        for i in range(num+1):
            x=x_start+i*post_spacing
            glColor3f(0.38,0.38,0.43)
            glBegin(GL_QUADS)
            glVertex3f(x-pt/2,y_pos-pt,z)
            glVertex3f(x+pt/2,y_pos-pt,z)
            glVertex3f(x+pt/2,y_pos-pt,z+rail_height)
            glVertex3f(x-pt/2,y_pos-pt,z+rail_height)

            glVertex3f(x-pt/2,y_pos+pt,z)
            glVertex3f(x+pt/2,y_pos+pt,z)
            glVertex3f(x+pt/2,y_pos+pt,z+rail_height)
            glVertex3f(x-pt/2,y_pos+pt,z+rail_height)

            glVertex3f(x-pt/2,y_pos-pt,z)
            glVertex3f(x-pt/2,y_pos+pt,z)
            glVertex3f(x-pt/2,y_pos+pt,z+rail_height)
            glVertex3f(x-pt/2,y_pos-pt,z+rail_height)

            glVertex3f(x+pt/2,y_pos-pt,z)
            glVertex3f(x+pt/2,y_pos+pt,z)
            glVertex3f(x+pt/2,y_pos+pt,z+rail_height)
            glVertex3f(x+pt/2,y_pos-pt,z+rail_height)
            glEnd()

    def base_bar_y(x_pos):
        glColor3f(0.4,0.4,0.45)
        glBegin(GL_QUADS)
        glVertex3f(x_pos-pt,y_start,z+8)
        glVertex3f(x_pos+pt,y_start,z+8)
        glVertex3f(x_pos+pt,y_end,z+8)
        glVertex3f(x_pos-pt,y_end,z+8)
        glEnd()

    def top_rail_y(x_pos):
        glColor3f(0.35,0.35,0.40)
        glBegin(GL_QUADS)
        glVertex3f(x_pos-pt-4,y_start,z+rail_height)
        glVertex3f(x_pos+pt+4,y_start,z+rail_height)
        glVertex3f(x_pos+pt+4,y_end,z+rail_height)
        glVertex3f(x_pos-pt-4,y_end,z+rail_height)

        glVertex3f(x_pos-pt-4,y_start,z+rail_height-14)
        glVertex3f(x_pos+pt+4,y_start,z+rail_height-14)
        glVertex3f(x_pos+pt+4,y_start,z+rail_height)
        glVertex3f(x_pos-pt-4,y_start,z+rail_height)

        glVertex3f(x_pos-pt-4,y_end,z+rail_height-14)
        glVertex3f(x_pos+pt+4,y_end,z+rail_height-14)
        glVertex3f(x_pos+pt+4,y_end,z+rail_height)
        glVertex3f(x_pos-pt-4,y_end,z+rail_height)
        glEnd()

    def posts_y(x_pos):
        num=int((y_end-y_start)/post_spacing)
        for i in range(num+1):
            y=y_start+i*post_spacing
            glColor3f(0.38,0.38,0.43)
            glBegin(GL_QUADS)
            glVertex3f(x_pos-pt,y,z)
            glVertex3f(x_pos+pt,y,z)
            glVertex3f(x_pos+pt,y,z+rail_height)
            glVertex3f(x_pos-pt,y,z+rail_height)
            glEnd()

    base_bar_x(y_start)
    top_rail_x(y_start)
    posts_x(y_start)

    base_bar_y(x_start)
    top_rail_y(x_start)
    posts_y(x_start)

    base_bar_y(x_end)
    top_rail_y(x_end)
    posts_y(x_end)


def draw_cross(cx,cy,cz,size,arm_w):
    glVertex3f(cx-size,cy+arm_w,cz)
    glVertex3f(cx+size,cy+arm_w,cz)
    glVertex3f(cx+size,cy-arm_w,cz)
    glVertex3f(cx-size,cy-arm_w,cz)
    glVertex3f(cx-arm_w,cy+size,cz)
    glVertex3f(cx+arm_w,cy+size,cz)
    glVertex3f(cx+arm_w,cy-size,cz)
    glVertex3f(cx-arm_w,cy-size,cz)


def draw_life_cube(x,y,z,s=40):
    glColor3f(1.0,1.0,1.0)
    glBegin(GL_QUADS)
    glVertex3f(x-s,y-s,z+s);glVertex3f(x+s,y-s,z+s)
    glVertex3f(x+s,y+s,z+s);glVertex3f(x-s,y+s,z+s)
    glVertex3f(x-s,y-s,z-s);glVertex3f(x+s,y-s,z-s)
    glVertex3f(x+s,y+s,z-s);glVertex3f(x-s,y+s,z-s)
    glVertex3f(x-s,y-s,z-s);glVertex3f(x-s,y-s,z+s)
    glVertex3f(x-s,y+s,z+s);glVertex3f(x-s,y+s,z-s)
    glVertex3f(x+s,y-s,z-s);glVertex3f(x+s,y-s,z+s)
    glVertex3f(x+s,y+s,z+s);glVertex3f(x+s,y+s,z-s)
    glVertex3f(x-s,y+s,z-s);glVertex3f(x+s,y+s,z-s)
    glVertex3f(x+s,y+s,z+s);glVertex3f(x-s,y+s,z+s)
    glVertex3f(x-s,y-s,z-s);glVertex3f(x+s,y-s,z-s)
    glVertex3f(x+s,y-s,z+s);glVertex3f(x-s,y-s,z+s)
    glEnd()

    glColor3f(0.9,0.1,0.1)
    arm=s*0.55
    arm_w=s*0.18
    offset=s+1.0

    glBegin(GL_QUADS)
    draw_cross(x,y,z+offset,arm,arm_w)
    draw_cross(x,y,z-offset,arm,arm_w)
    glVertex3f(x-arm,y+offset,z+arm_w)
    glVertex3f(x+arm,y+offset,z+arm_w)
    glVertex3f(x+arm,y+offset,z-arm_w)
    glVertex3f(x-arm,y+offset,z-arm_w)
    glVertex3f(x-arm_w,y+offset,z+arm)
    glVertex3f(x+arm_w,y+offset,z+arm)
    glVertex3f(x+arm_w,y+offset,z-arm)
    glVertex3f(x-arm_w,y+offset,z-arm)
    glEnd()


def draw_bullet(cx,cy,cz,scale=1.0,angle=0):
    glPushMatrix()
    glTranslatef(cx,cy,cz)
    glRotatef(angle,0,0,1)
    glScalef(scale,scale,scale)

    quad=gluNewQuadric()

    glColor3f(0.75,0.60,0.15)
    glPushMatrix()
    glRotatef(90,0,1,0)
    gluCylinder(quad,4,4,20,10,4)
    glPopMatrix()

    glColor3f(0.85,0.70,0.20)
    glPushMatrix()
    glTranslatef(20,0,0)
    glRotatef(90,0,1,0)
    gluCylinder(quad,4,0,10,10,4)
    glPopMatrix()

    glColor3f(0.60,0.50,0.10)
    glPushMatrix()
    glTranslatef(-2,0,0)
    glScalef(1,4,4)
    glutSolidCube(2)
    glPopMatrix()

    glPopMatrix()


def draw_ammo_cube(x,y,z,s=40):
    glColor3f(0.25,0.25,0.28)
    glBegin(GL_QUADS)
    glVertex3f(x-s,y-s,z+s);glVertex3f(x+s,y-s,z+s)
    glVertex3f(x+s,y+s,z+s);glVertex3f(x-s,y+s,z+s)
    glVertex3f(x-s,y-s,z-s);glVertex3f(x+s,y-s,z-s)
    glVertex3f(x+s,y+s,z-s);glVertex3f(x-s,y+s,z-s)
    glVertex3f(x-s,y-s,z-s);glVertex3f(x-s,y-s,z+s)
    glVertex3f(x-s,y+s,z+s);glVertex3f(x-s,y+s,z-s)
    glVertex3f(x+s,y-s,z-s);glVertex3f(x+s,y-s,z+s)
    glVertex3f(x+s,y+s,z+s);glVertex3f(x+s,y+s,z-s)
    glVertex3f(x-s,y+s,z-s);glVertex3f(x+s,y+s,z-s)
    glVertex3f(x+s,y+s,z+s);glVertex3f(x-s,y+s,z+s)
    glVertex3f(x-s,y-s,z-s);glVertex3f(x+s,y-s,z-s)
    glVertex3f(x+s,y-s,z+s);glVertex3f(x-s,y-s,z+s)
    glEnd()

    offset=s+2.0
    draw_bullet(x,y,z+offset,scale=1.0,angle=0)
    draw_bullet(x-s-2,y,z,scale=1.0,angle=45)
    draw_bullet(x,y,z-offset,scale=1.0,angle=20)


def draw_pickups():
    if pickup is None or not pickup["active"]:
        return
    px=pickup["x"]
    py=pickup["y"]
    pz=PICKUP_SPAWN_Z+40

    bob=15.0*math.sin(frame*0.05+px*0.01)
    pz+=bob

    if pickup["type"]=="health":
        draw_life_cube(px,py,pz,s=35)
    else:
        draw_ammo_cube(px,py,pz,s=35)


def draw_normal_zombie(x,y,scale=1.0):
    quad=gluNewQuadric()
    glPushMatrix()
    glTranslatef(x,y,0)
    glScalef(scale*0.6,scale*0.6,scale*0.6)
    glRotatef(90,1,0,0)

    glColor3f(0.55,0.65,0.35)
    glPushMatrix()
    glTranslatef(0,120,0)
    glScalef(55,70,25)
    glutSolidCube(1)
    glPopMatrix()

    glColor3f(0.55,0.65,0.35)
    glPushMatrix()
    glTranslatef(0,150,0)
    glRotatef(-90,1,0,0)
    gluCylinder(quad,7,7,18,10,4)
    glPopMatrix()

    glColor3f(0.6,0.75,0.4)
    glPushMatrix()
    glTranslatef(0,190,0)
    gluSphere(quad,30,15,15)
    glPopMatrix()

    glColor3f(1.0,0.0,0.0)
    glPushMatrix()
    glTranslatef(-10,195,-28)
    gluSphere(quad,6,8,8)
    glPopMatrix()
    glPushMatrix()
    glTranslatef(10,195,-28)
    gluSphere(quad,6,8,8)
    glPopMatrix()

    glColor3f(0.55,0.65,0.35)
    glPushMatrix()
    glTranslatef(-32,145,0)
    glRotatef(180,0,1,0)
    gluCylinder(quad,9,7,55,10,4)
    glPopMatrix()

    glColor3f(0.55,0.65,0.35)
    glPushMatrix()
    glTranslatef(32,145,0)
    glRotatef(180,0,1,0)
    gluCylinder(quad,9,7,55,10,4)
    glPopMatrix()

    glColor3f(0.45,0.55,0.28)
    glPushMatrix()
    glTranslatef(-16,85,0)
    glRotatef(90,1,0,0)
    gluCylinder(quad,14,8,80,10,6)
    glPopMatrix()

    glColor3f(0.45,0.55,0.28)
    glPushMatrix()
    glTranslatef(16,85,0)
    glRotatef(90,1,0,0)
    gluCylinder(quad,14,8,80,10,6)
    glPopMatrix()

    glPopMatrix()


def draw_runner_zombie(x,y,scale=1.0):
    quad=gluNewQuadric()
    glPushMatrix()
    glTranslatef(x,y,0)
    glScalef(scale*0.85,scale*0.85,scale*0.85)
    glRotatef(90,1,0,0)

    glColor3f(0.60,0.72,0.35)
    glPushMatrix()
    glTranslatef(0,118,0)
    glRotatef(15,1,0,0)
    glScalef(60,78,28)
    glutSolidCube(1)
    glPopMatrix()

    glColor3f(0.60,0.72,0.35)
    glPushMatrix()
    glTranslatef(0,152,8)
    glRotatef(-75,1,0,0)
    gluCylinder(quad,8,8,20,10,4)
    glPopMatrix()

    glColor3f(0.65,0.78,0.38)
    glPushMatrix()
    glTranslatef(0,188,16)
    glRotatef(20,1,0,0)
    gluSphere(quad,32,15,15)
    glPopMatrix()

    glColor3f(1.0,0.0,0.0)
    glPushMatrix()
    glTranslatef(-11,192,-14)
    gluSphere(quad,7,8,8)
    glPopMatrix()
    glPushMatrix()
    glTranslatef(11,192,-14)
    gluSphere(quad,7,8,8)
    glPopMatrix()

    glColor3f(0.60,0.72,0.35)
    glPushMatrix()
    glTranslatef(-35,145,6)
    glRotatef(140,1,0,0)
    gluCylinder(quad,10,7,60,10,4)
    glPopMatrix()

    glColor3f(0.60,0.72,0.35)
    glPushMatrix()
    glTranslatef(35,145,6)
    glRotatef(220,1,0,0)
    gluCylinder(quad,10,7,60,10,4)
    glPopMatrix()

    glColor3f(0.50,0.62,0.28)
    glPushMatrix()
    glTranslatef(-18,82,-8)
    glRotatef(90,1,0,0)
    gluCylinder(quad,15,9,85,10,6)
    glPopMatrix()

    glColor3f(0.50,0.62,0.28)
    glPushMatrix()
    glTranslatef(18,82,-8)
    glRotatef(90,1,0,0)
    gluCylinder(quad,15,9,85,10,6)
    glPopMatrix()

    glPopMatrix()


def draw_brute_zombie(x,y,scale=1.0):
    quad=gluNewQuadric()
    glPushMatrix()
    glTranslatef(x,y,0)
    glScalef(scale*1.4,scale*1.4,scale*1.4)
    glRotatef(90,1,0,0)

    glColor3f(0.40,0.52,0.22)
    glPushMatrix()
    glTranslatef(0,110,0)
    glScalef(100,90,45)
    glutSolidCube(1)
    glPopMatrix()

    glColor3f(0.38,0.50,0.20)
    glPushMatrix()
    glTranslatef(0,150,0)
    glRotatef(-90,1,0,0)
    gluCylinder(quad,15,15,25,12,4)
    glPopMatrix()

    glColor3f(0.40,0.52,0.22)
    glPushMatrix()
    glTranslatef(0,195,0)
    glScalef(1.3,1.1,1.2)
    gluSphere(quad,38,15,15)
    glPopMatrix()

    glColor3f(1.0,0.0,0.0)
    glPushMatrix()
    glTranslatef(-15,200,-35)
    gluSphere(quad,10,8,8)
    glPopMatrix()
    glPushMatrix()
    glTranslatef(15,200,-35)
    gluSphere(quad,10,8,8)
    glPopMatrix()

    glPushMatrix()
    glTranslatef(-58,140,0)
    glColor3f(0.38,0.50,0.20)
    gluSphere(quad,22,12,12)
    glColor3f(0.40,0.52,0.22)
    glRotatef(170,0,1,0)
    gluCylinder(quad,20,14,80,12,4)
    glColor3f(0.35,0.45,0.18)
    glTranslatef(0,0,80)
    gluSphere(quad,16,10,10)
    glPopMatrix()

    glPushMatrix()
    glTranslatef(58,140,0)
    glColor3f(0.38,0.50,0.20)
    gluSphere(quad,22,12,12)
    glColor3f(0.40,0.52,0.22)
    glRotatef(170,0,1,0)
    gluCylinder(quad,20,14,80,12,4)
    glColor3f(0.35,0.45,0.18)
    glTranslatef(0,0,80)
    gluSphere(quad,16,10,10)
    glPopMatrix()

    glColor3f(0.32,0.42,0.18)
    glPushMatrix()
    glTranslatef(-28,65,0)
    glRotatef(90,1,0,0)
    gluCylinder(quad,24,16,85,12,6)
    glPopMatrix()

    glColor3f(0.32,0.42,0.18)
    glPushMatrix()
    glTranslatef(28,65,0)
    glRotatef(90,1,0,0)
    gluCylinder(quad,24,16,85,12,6)
    glPopMatrix()

    glPopMatrix()


def drawPlayer():
    quad=gluNewQuadric()
    glPushMatrix()

    glTranslatef(position[0],position[1],playerZ)
    glRotatef(playerAngle-90,0,0,1)
    glRotatef(90,1,0,0)
    glScalef(1.2,1.2,1.2)

    glColor3f(0.90,0.72,0.55)
    glPushMatrix()
    glTranslatef(0,215,0)
    gluSphere(quad,35,20,20)
    glPopMatrix()

    glColor3f(0.90,0.72,0.55)
    glPushMatrix()
    glTranslatef(0,160,0)
    glRotatef(-90,1,0,0)
    gluCylinder(quad,8,8,22,12,4)
    glPopMatrix()

    glColor3f(0.95,0.95,0.95)
    glPushMatrix()
    glTranslatef(0,120,0)
    glScalef(72,82,28)
    glutSolidCube(1)
    glPopMatrix()

    glColor3f(0.50,0.35,0.18)
    glPushMatrix()
    glTranslatef(0,122,-2)
    glScalef(68,75,26)
    glutSolidCube(1)
    glPopMatrix()

    glColor3f(0.45,0.30,0.15)
    glPushMatrix()
    glTranslatef(-18,130,-16)
    glScalef(14,12,4)
    glutSolidCube(1)
    glPopMatrix()

    glPushMatrix()
    glTranslatef(-35,138,0)
    glRotatef(180,0,1,0)
    glColor3f(0.90,0.72,0.55)
    gluCylinder(quad,12,9,70,12,4)
    glTranslatef(0,0,70)
    glColor3f(0.55,0.38,0.22)
    gluSphere(quad,13,10,10)
    glTranslatef(0,3,5)
    glColor3f(0.30,0.30,0.30)
    gluCylinder(quad,5,4,45,12,4)
    glColor3f(0.25,0.18,0.10)
    glPushMatrix()
    glTranslatef(0,-2,5)
    glRotatef(100,1,0,0)
    gluCylinder(quad,4,3,20,8,4)
    glPopMatrix()
    glPopMatrix()

    glColor3f(0.90,0.72,0.55)
    glPushMatrix()
    glTranslatef(35,138,0)
    glRotatef(180,0,1,0)
    gluCylinder(quad,12,9,70,12,4)
    glPopMatrix()

    glColor3f(0.90,0.72,0.55)
    glPushMatrix()
    glTranslatef(35,138,-70)
    gluSphere(quad,11,10,10)
    glPopMatrix()

    glColor3f(0.42,0.28,0.12)
    glPushMatrix()
    glTranslatef(-20,80,0)
    glScalef(26,45,24)
    glutSolidCube(1)
    glPopMatrix()

    glColor3f(0.42,0.28,0.12)
    glPushMatrix()
    glTranslatef(20,80,0)
    glScalef(26,45,24)
    glutSolidCube(1)
    glPopMatrix()

    glColor3f(0.38,0.24,0.10)
    glPushMatrix()
    glTranslatef(-20,55,0)
    glRotatef(90,1,0,0)
    gluCylinder(quad,13,10,55,12,6)
    glPopMatrix()

    glColor3f(0.38,0.24,0.10)
    glPushMatrix()
    glTranslatef(20,55,0)
    glRotatef(90,1,0,0)
    gluCylinder(quad,13,10,55,12,6)
    glPopMatrix()

    glColor3f(0.28,0.16,0.08)
    glPushMatrix()
    glTranslatef(-20,0,2)
    glScalef(1.2,0.6,1.4)
    gluSphere(quad,16,10,10)
    glPopMatrix()

    glColor3f(0.28,0.16,0.08)
    glPushMatrix()
    glTranslatef(20,0,2)
    glScalef(1.2,0.6,1.4)
    gluSphere(quad,16,10,10)
    glPopMatrix()

    glPopMatrix()


def draw_centered_text(y,text,font=None):
    if font is None:
        font=DEFAULT_FONT
    char_w=11
    text_w=len(text)*char_w
    x=(1000-text_w)/2
    draw_text(x,y,text,font)

def draw_sky():
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0,1,0,1)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()

    glDisable(GL_DEPTH_TEST)
    glColor3f(0.53,0.81,0.98)
    glBegin(GL_QUADS)
    glVertex2f(0,0)
    glVertex2f(1,0)
    glVertex2f(1,1)
    glVertex2f(0,1)
    glEnd()
    glEnable(GL_DEPTH_TEST)

    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

def showScreen():
    glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    glViewport(0,0,1000,800)
    draw_sky()
    setupCamera()
    drawPlayer()
    draw_floor()
    draw_escalators()
    draw_floor_connector_walls()
    draw_second_floor()
    draw_second_floor_railings()
    draw_pickups()

    for e in enemies:
        draw_enemy(e)

    draw_bullets()

    if showManual:
        draw_text(200,600,"BRACU Escalator Zombie Outbreak")
        draw_text(250,550,"Press ENTER to Start")

        draw_text(200,480,"Controls:")
        draw_text(200,450,"W/S - Move Forward/Backward")
        draw_text(200,420,"A/D - Rotate Player")
        draw_text(200,390,"Mouse Left - Shoot")

        draw_text(200,310,"Camera Modes:")
        draw_text(200,280,"1 - First Floor View")
        draw_text(200,250,"2 - Second Floor View")
        draw_text(200,220,"3 - Third Person View")
        draw_text(200,190,"4 - First Person View")

        draw_text(200,140,"C - Cheat Mode")
        draw_text(200,110,"V - Auto Aim")

    hud_x=15
    hud_y=770
    gap=25

    draw_text(hud_x,hud_y,f"Life: {health}")
    draw_text(hud_x,hud_y-gap,f"Ammo: {ammo}")
    draw_text(hud_x,hud_y-gap*2,f"Score: {score}")
    draw_text(hud_x,hud_y-gap*3,f"Missed: {missed}")
    draw_text(hud_x,hud_y-gap*4,f"Wave: {getCurrentWave()}")

    target=WAVE_KILL_TARGETS.get(currentWaveNum,10)
    draw_text(hud_x,hud_y-gap*5,f"Kills: {enemiesKilledThisWave}/{target}")

    if cheatMode:
        draw_text(hud_x,hud_y-gap*7,"Cheat: ON")

    if autoCam and fpMode:
        draw_text(hud_x,hud_y-gap*8,"AutoCam: ON")

    if playerZ>300:
        if pickup is not None and pickup["active"]:
            ptype=pickup["type"].upper()
            draw_text(680,30,f"2nd Floor: {ptype} pickup here!")
        else:
            secs_left=max(0,(PICKUP_INTERVAL-pickupTimer)//60)
            draw_text(680,30,f"Next pickup in: {secs_left}s")

    if wavePaused and not gameOver:
        draw_centered_text(480,f"WAVE {currentWaveNum} CLEARED!",GLUT_BITMAP_TIMES_ROMAN_24)
        draw_centered_text(430,f"Score: {score}   Health: {health}   Ammo: {ammo}")
        draw_centered_text(380,"Head to the 2nd floor for health & ammo pickups!")
        draw_centered_text(330,f"Next: Wave {currentWaveNum+1} of {MAX_WAVES}")
        draw_centered_text(280,"Press ENTER to continue to next wave")

    if gameOver:
        if gameWon:
            draw_centered_text(500,"CONGRATULATIONS!",GLUT_BITMAP_TIMES_ROMAN_24)
            draw_centered_text(450,"You survived all 3 waves!")
            draw_centered_text(400,f"Final Score: {score}")
            draw_centered_text(350,"Press R to play again")
        else:
            draw_centered_text(430,"GAME OVER!",GLUT_BITMAP_TIMES_ROMAN_24)
            draw_centered_text(380,f"Final Score: {score}   Wave: {currentWaveNum}")
            draw_centered_text(330,"Press R to restart")

    glutSwapBuffers()


def advance_to_next_wave():
    global currentWaveNum,wavePaused,waveCleared,enemiesKilledThisWave
    global spawnTimer,bullets

    currentWaveNum+=1
    wavePaused=False
    waveCleared=False
    enemiesKilledThisWave=0
    spawnTimer=0
    bullets=[]

    spawn_pickups()

    enemy_initialize()


def keyboardListener(key,x,y):
    global position,playerAngle,cheatMode,autoCam,camMode,showManual

    if wavePaused and not gameOver:
        if key==b'\r':
            advance_to_next_wave()
        return

    if gameOver:
        if key==b'r':
            resetGame()
        return

    move_speed=20.0

    if cheatMode:
        move_angle=gunAngle
    else:
        move_angle=playerAngle

    rad=math.radians(move_angle)

    if key==b'w':
        position[0]+=math.cos(rad)*move_speed
        position[1]+=math.sin(rad)*move_speed

    if key==b's':
        position[0]-=math.cos(rad)*move_speed
        position[1]-=math.sin(rad)*move_speed

    if key==b'a':
        playerAngle+=10

    if key==b'd':
        playerAngle-=10

    if key==b'c':
        cheatMode=not cheatMode

    if key==b'v':
        autoCam=not autoCam

    if key==b'1':
        camMode=1
    if key==b'2':
        camMode=2
    if key==b'3':
        camMode=3
    if key==b'4':
        camMode=4

    if key==b'\r':
        showManual=False

    playerAngle%=360
    playerBound()


def specialKeyListener(key,x,y):
    global camHeight,camAngle,camForward,camMode

    if key==GLUT_KEY_UP:
        if camMode in [1,2]:
            camForward+=50
        else:
            camHeight+=20

    if key==GLUT_KEY_DOWN:
        if camMode in [1,2]:
            camForward-=50
        else:
            camHeight-=20

    if key==GLUT_KEY_LEFT:
        camAngle+=5

    if key==GLUT_KEY_RIGHT:
        camAngle-=5

    camHeight=max(200,camHeight)

    camAngle%=360

def bulletSpawn(angle):
    rad=math.radians(angle)

    bx=position[0]+math.cos(rad)*gunFwd
    by=position[1]+math.sin(rad)*gunFwd
    bz=playerZ+gunH

    return bx,by,bz

def mouseListener(button,state,x,y):
    global fpMode,ammo

    if gameOver or wavePaused:
        return

    if button==GLUT_LEFT_BUTTON and state==GLUT_DOWN:
        if ammo<=0:
            return

        if cheatMode:
            shoot_angle=gunAngle
        else:
            shoot_angle=playerAngle

        rad=math.radians(shoot_angle)
        bx,by,bz=bulletSpawn(shoot_angle)
        bullets.append({
            "x":bx,
            "y":by,
            "z":bz,
            "dx":math.cos(rad)*speedBullet,
            "dy":math.sin(rad)*speedBullet
        })
        ammo-=1

    if button==GLUT_RIGHT_BUTTON and state==GLUT_DOWN:
        fpMode=not fpMode
        if fpMode:
            camMode=4
        else:
            camMode=3


def main():
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE|GLUT_RGB|GLUT_DEPTH)
    glutInitWindowSize(1000,800)
    glutInitWindowPosition(0,0)
    wind=glutCreateWindow(b"Bracu Zombie Outbreak")

    enemy_initialize()
    spawn_pickups()

    glutDisplayFunc(showScreen)
    glutKeyboardFunc(keyboardListener)
    glutSpecialFunc(specialKeyListener)
    glutMouseFunc(mouseListener)
    glutIdleFunc(idle)
    glEnable(GL_DEPTH_TEST)

    glutMainLoop()


if __name__=="__main__":
    main()
