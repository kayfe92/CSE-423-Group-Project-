from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import math
import random

DEFAULT_FONT= GLUT_BITMAP_HELVETICA_18

camRadius= 500.0
camAngle= 90.0
camHeight= 500.0
fpMode= False

fovY= 120  
GRID_LENGTH= 600  
TILE_SIZE= 100

PLAYER_SCALE= 0.45

enemies= []
bullets= []
speedEnemy= 0.10
speedBullet= 10.0


gunFwd= 265.0*PLAYER_SCALE
gunH= 180.0*PLAYER_SCALE


position= [0.0,0.0]
playerAngle= 90.0
gunAngle= 90.0
health= 5
score=0
missed=0
gameOver= False



frame= 0
lastShot= 0

cheatMode= False
autoCam= False



def draw_text(x, y, text, font=None):
    if font is None:
        font = DEFAULT_FONT
    glColor3f(1,1,1)
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
    enemies=[]

    for i in range(5):

        createEnemy()


def createEnemy():
    x=random.uniform(-600,600)
    y=random.uniform(-600,600)
    phase=random.uniform(0,3.14)

    enemies.append({
        "x":x,
        "y":y,
        "scale":1.0,
        "phase":phase
    })

def resetGame():
    global bullets,playerAngle,score,position
    global cheatMode,health,missed
    global gameOver,autoCam,gunAngle

    health= 5
    position= [0.0,0.0]
    cheatMode=autoCam=gameOver=False
    
    bullets= []
    score= 0
    gunAngle= 90.0
    missed= 0
    
    playerAngle= 90.0
    
    enemy_initialize()

def playerBound():
    margin=50.0
    
    if(position[0]< -GRID_LENGTH+margin):
        position[0]= -GRID_LENGTH+margin

    elif(position[0]>GRID_LENGTH-margin):
        position[0]= GRID_LENGTH-margin

    if(position[1]< -GRID_LENGTH+margin):
        position[1]= -GRID_LENGTH+margin

    elif(position[1]>GRID_LENGTH-margin):
        position[1]= GRID_LENGTH-margin



def bulletSpawn(shoot_angle):
    rad=math.radians(shoot_angle)

    offset_x= math.cos(rad)*gunFwd
    offset_y= math.sin(rad)*gunFwd

    return (
        position[0]+ offset_x,
        position[1]+ offset_y,
        gunH
    )




def setupCamera():
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(fovY,1.25,0.1,3000)

    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

    if fpMode:
        look_ang=gunAngle if cheatMode and autoCam else playerAngle
        rad=math.radians(look_ang)

        dir_x=math.cos(rad)
        dir_y=math.sin(rad)

        cam_x=position[0]+dir_x*20
        cam_y=position[1]+dir_y*20
        cam_z=270.0*PLAYER_SCALE

        look_x=position[0]+dir_x*600
        look_y=position[1]+dir_y*600
        look_z=0

        gluLookAt(
            cam_x,cam_y,cam_z,
            look_x,look_y,look_z,
            0,0,1
        )

    else:
        rad=math.radians(camAngle)

        cx=math.cos(rad)*camRadius
        cy=math.sin(rad)*camRadius

        gluLookAt(
            cx,cy,camHeight,
            0,0,0,
            0,0,1
        )
def collisionCheacker():
    global health,score,missed,gameOver,bullets,enemies

    activeBullets=[]

    for bullet in bullets:
        x_out=abs(bullet["x"])>GRID_LENGTH
        y_out=abs(bullet["y"])>GRID_LENGTH

        if (x_out or y_out):
            missed+=1
            if missed>=10:
                gameOver=True
            continue

        hitEnemy=None
        for enemy in enemies:
            gap=math.hypot(bullet["x"]-enemy["x"],bullet["y"]-enemy["y"])
            if gap<40:
                hitEnemy=enemy
                break

        if hitEnemy:
            enemies.remove(hitEnemy)
            createEnemy()
            score+=1
        else:
            activeBullets.append(bullet)

    bullets=activeBullets

    for enemy in enemies[:]:
        gap=math.hypot(position[0]-enemy["x"],position[1]-enemy["y"])
        if gap<60:
            enemies.remove(enemy)
            createEnemy()
            health-=1
            if health<=0:
                gameOver=True
                return
def idle():
    global frame,gunAngle,bullets,lastShot

    if gameOver:
        glutPostRedisplay()
        return

    frame+=1

    for bullet in bullets:
        bullet["x"]+=bullet["dx"]
        bullet["y"]+=bullet["dy"]

    for enemy in enemies:
        dx=position[0]-enemy["x"]
        dy=position[1]-enemy["y"]
        dist=math.hypot(dx,dy)

        if dist>0:
            enemy["x"]+=(dx/dist)*speedEnemy
            enemy["y"]+=(dy/dist)*speedEnemy

        enemy["scale"]=1.0+0.1*math.sin(frame*0.02+enemy["phase"])

    if cheatMode:
        cheatShoot()
    else:
        gunAngle=playerAngle

    collisionCheacker()
    glutPostRedisplay()


def cheatShoot():
    global gunAngle,lastShot

    gunAngle=(gunAngle+2.0)%360.0

    rad=math.radians(gunAngle)
    gunDirX=math.cos(rad)
    gunDirY=math.sin(rad)

    canShoot=(frame-lastShot)>20

    for enemy in enemies:
        dx=enemy["x"]-position[0]
        dy=enemy["y"]-position[1]
        dist=math.hypot(dx,dy)

        if dist==0:
            continue

        dirX=dx/dist
        dirY=dy/dist

        isAligned=(gunDirX*dirX+gunDirY*dirY)>0.95

        if isAligned and canShoot:
            bx,by,bz=bulletSpawn(gunAngle)
            bullets.append({
                "x":bx,"y":by,"z":bz,
                "dx":dirX*speedBullet,
                "dy":dirY*speedBullet
            })
            lastShot=frame
            break

def draw_grid():
    cols=int((2*GRID_LENGTH)/TILE_SIZE)
    rows=cols
    start=-GRID_LENGTH

    glBegin(GL_QUADS)

    for row in range(rows):
        for col in range(cols):
            x=start+col*TILE_SIZE
            y=start+row*TILE_SIZE

            if (row+col)%2==0:
                draw_tile(x,y,TILE_SIZE,(1.0,1.0,1.0))
            else:
                draw_tile(x,y,TILE_SIZE,(0.7,0.5,0.95))

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
    wall_height=100
    g=GRID_LENGTH
    glBegin(GL_QUADS)
    # front 
    glColor3f(0.0,1.0,1.0)
    glVertex3f(-g,-g,0)
    glVertex3f(g,-g,0)
    glVertex3f(g,-g,wall_height)
    glVertex3f(-g,-g,wall_height)
    # right 
    glColor3f(0,0,1)
    glVertex3f(g,-g,0)
    glVertex3f(g,g,0)
    glVertex3f(g,g,wall_height)
    glVertex3f(g,-g,wall_height)
    # back wall
    glColor3f(1,1,1)
    glVertex3f(-g,g,0)
    glVertex3f(g,g,0)
    glVertex3f(g,g,wall_height)
    glVertex3f(-g,g,wall_height)
     # left wall
    glColor3f(0,1,0)
    glVertex3f(-g,-g,0)
    glVertex3f(-g,g,0)
    glVertex3f(-g,g,wall_height)
    glVertex3f(-g,-g,wall_height)
    glEnd()

def draw_enemy(x,y,scale):
    glPushMatrix()
    glTranslatef(x,y,0)
    glScalef(scale,scale,scale)

    quadric=gluNewQuadric()
#body
    glColor3f(1,0,0)
    glPushMatrix()
    glTranslatef(0,0,40)
    gluSphere(quadric,40,15,15)
    glPopMatrix()
#head
    glColor3f(0,0,0)
    glPushMatrix()
    glTranslatef(0,0,100)
    gluSphere(quadric,20,15,15)
    glPopMatrix()

    glPopMatrix()



def draw_bullets():
    for b in bullets:
        x, y, z = b["x"], b["y"], b["z"]
        glPushMatrix()
        glTranslatef(x, y, z)
        glColor3f(1.0, 0.0, 0.0)
        glutSolidCube(20)  # fix this
        glPopMatrix()




def drawPlayer():
    quad=gluNewQuadric()
    glPushMatrix()

    glTranslatef(position[0],position[1],0)

    if cheatMode:
        current_rot = gunAngle
    else:
        current_rot = playerAngle

    glRotatef(current_rot-90,0,0,1)

    glScalef(PLAYER_SCALE*1.6,PLAYER_SCALE*1.6,PLAYER_SCALE*1.6)
    if gameOver:
        glTranslatef(0,80,50)
        glRotatef(90,1,0,0)
    glRotatef(90,1,0,0)

    # head
    glColor3f(0.0,0.0,0.0)
    glPushMatrix()
    glTranslatef(0,215,0)
    gluSphere(quad,35,20,20)
    glPopMatrix()

    # neck
    glColor3f(0.9,0.7,0.6)
    glPushMatrix()
    glTranslatef(0,160,0)
    glRotatef(-90,1,0,0)
    gluCylinder(quad,8,8,20,12,4)
    glPopMatrix()

    # body 
    glColor3f(0.35, 0.45, 0.20)
    glPushMatrix()
    glTranslatef(0, 120, 0)
    glScalef(70, 80, 30)
    glutSolidCube(1)
    glPopMatrix()

    # armL
    glColor3f(0.9,0.7,0.6)
    glPushMatrix()
    glTranslatef(-35,120,10)
    glRotatef(180,0,1,0)
    gluCylinder(quad,12,9,60,12,4)
    glPopMatrix()

    # armR
    glColor3f(0.9,0.7,0.6)
    glPushMatrix()
    glTranslatef(35,120,10)
    glRotatef(180,0,1,0)
    gluCylinder(quad,12,9,60,12,4)
    glPopMatrix()

    # legL 
    glColor3f(0.1, 0.1, 0.8)
    glPushMatrix()
    glTranslatef(-20, 0, 0)
    glRotatef(-90, 1, 0, 0)
    gluCylinder(quad, 18, 10, 90, 12, 8)
    glPopMatrix()

    # legR 
    glColor3f(0.1, 0.1, 0.8)
    glPushMatrix()
    glTranslatef(20, 0, 0)
    glRotatef(-90, 1, 0, 0)
    gluCylinder(quad, 18, 10, 90, 12, 8)
    glPopMatrix()

    # gun
    glColor3f(0.7,0.7,0.7)
    glPushMatrix()
    glTranslatef(0,120,-5)
    glRotatef(180,0,1,0)
    gluCylinder(quad,10,7,120,16,8)
    glPopMatrix()

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
    glVertex3f( S, -S, 0)
    glVertex3f( S,  S, 0)
    glVertex3f(-S,  S, 0)
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
            glVertex3f(x0,     y0,     1)
            glVertex3f(x1,     y0,     1)
            glVertex3f(x1,     y0 + b, 1)
            glVertex3f(x0,     y0 + b, 1)

            # top edge
            glVertex3f(x0,     y1 - b, 1)
            glVertex3f(x1,     y1 - b, 1)
            glVertex3f(x1,     y1,     1)
            glVertex3f(x0,     y1,     1)

            # left edge
            glVertex3f(x0,     y0,     1)
            glVertex3f(x0 + b, y0,     1)
            glVertex3f(x0 + b, y1,     1)
            glVertex3f(x0,     y1,     1)

            # right edge
            glVertex3f(x1 - b, y0,     1)
            glVertex3f(x1,     y0,     1)
            glVertex3f(x1,     y1,     1)
            glVertex3f(x1 - b, y1,     1)

            glEnd()

ESCALATOR_LENGTH = 600   # how long the escalator runs (Y axis)
ESCALATOR_RISE   = 1400   # how high it goes (Z axis)
ESCALATOR_WIDTH  = 230   # width of one lane
NUM_STEPS        = 14
LANE_GAP         = 260   # center-to-center distance between the two lanes

def draw_single_escalator(x_center, y_start, y_end, z_bottom, z_top, num_steps=NUM_STEPS):
    half_w   = (ESCALATOR_WIDTH / 2)
    step_d   = (y_end   - y_start)  / num_steps   # depth per step  (Y)
    step_h   = (z_top   - z_bottom) / num_steps   # height per step (Z)

    # --- Inclined base / underside ---
    glColor3f(0.35, 0.35, 0.45)
    glBegin(GL_QUADS)
    glVertex3f(x_center - half_w, y_start, z_bottom)
    glVertex3f(x_center + half_w, y_start, z_bottom)
    glVertex3f(x_center + half_w, y_end,   z_top)
    glVertex3f(x_center - half_w, y_end,   z_top)
    glEnd()

    # --- Steps (tread + riser) ---
    for i in range(num_steps):
        y0 = y_start + i * step_d
        y1 = y0 + step_d
        z0 = z_bottom + i * step_h

        # Tread — flat horizontal surface
        glColor3f(0.75, 0.80, 0.90)
        glBegin(GL_QUADS)
        glVertex3f(x_center - half_w, y0, z0)
        glVertex3f(x_center + half_w, y0, z0)
        glVertex3f(x_center + half_w, y1, z0)
        glVertex3f(x_center - half_w, y1, z0)
        glEnd()

        # Riser — vertical front face of step
        glColor3f(0.50, 0.55, 0.65)
        glBegin(GL_QUADS)
        glVertex3f(x_center - half_w, y0, z0 - step_h)
        glVertex3f(x_center + half_w, y0, z0 - step_h)
        glVertex3f(x_center + half_w, y0, z0)
        glVertex3f(x_center - half_w, y0, z0)
        glEnd()

    rail_thickness = 8
    rail_lift      = -150
    rail_outset    = 30
    rail_height    = 350      # <-- add this, controls how tall the rail is

    for side_x in [x_center - half_w - rail_outset,
                   x_center + half_w + rail_outset]:

        glColor3f(0.20, 0.25, 0.35)

        # top face
        glColor3f(0.20, 0.25, 0.35)
        glBegin(GL_QUADS)
        glVertex3f(side_x - rail_thickness, y_start, z_bottom + rail_lift + rail_height)
        glVertex3f(side_x + rail_thickness, y_start, z_bottom + rail_lift + rail_height)
        glVertex3f(side_x + rail_thickness, y_end,   z_top    + rail_lift + rail_height)
        glVertex3f(side_x - rail_thickness, y_end,   z_top    + rail_lift + rail_height)
        glEnd()

        # bottom face
        glBegin(GL_QUADS)
        glVertex3f(side_x - rail_thickness, y_start, z_bottom + rail_lift)
        glVertex3f(side_x + rail_thickness, y_start, z_bottom + rail_lift)
        glVertex3f(side_x + rail_thickness, y_end,   z_top    + rail_lift)
        glVertex3f(side_x - rail_thickness, y_end,   z_top    + rail_lift)
        glEnd()

        # front face
        glColor3f(0.15, 0.20, 0.30)
        glBegin(GL_QUADS)
        glVertex3f(side_x - rail_thickness, y_start, z_bottom + rail_lift)
        glVertex3f(side_x + rail_thickness, y_start, z_bottom + rail_lift)
        glVertex3f(side_x + rail_thickness, y_start, z_bottom + rail_lift + rail_height)
        glVertex3f(side_x - rail_thickness, y_start, z_bottom + rail_lift + rail_height)
        glEnd()

        # back face
        glBegin(GL_QUADS)
        glVertex3f(side_x - rail_thickness, y_end, z_top + rail_lift)
        glVertex3f(side_x + rail_thickness, y_end, z_top + rail_lift)
        glVertex3f(side_x + rail_thickness, y_end, z_top + rail_lift + rail_height)
        glVertex3f(side_x - rail_thickness, y_end, z_top + rail_lift + rail_height)
        glEnd()

        # left end cap
        glColor3f(0.18, 0.22, 0.32)
        glBegin(GL_QUADS)
        glVertex3f(side_x - rail_thickness, y_start, z_bottom + rail_lift)
        glVertex3f(side_x - rail_thickness, y_end,   z_top    + rail_lift)
        glVertex3f(side_x - rail_thickness, y_end,   z_top    + rail_lift + rail_height)
        glVertex3f(side_x - rail_thickness, y_start, z_bottom + rail_lift + rail_height)
        glEnd()

        # right end cap
        glBegin(GL_QUADS)
        glVertex3f(side_x + rail_thickness, y_start, z_bottom + rail_lift)
        glVertex3f(side_x + rail_thickness, y_end,   z_top    + rail_lift)
        glVertex3f(side_x + rail_thickness, y_end,   z_top    + rail_lift + rail_height)
        glVertex3f(side_x + rail_thickness, y_start, z_bottom + rail_lift + rail_height)
        glEnd()


def draw_escalators():
    center_left  = -LANE_GAP / 2
    center_right =  LANE_GAP / 2

    y0 = -300
    y1 =  300

    glPushMatrix()                    # <-- add this
    glRotatef(90, 1, 0, 0)           # <-- rotation goes here
    glTranslatef(0, 320, -300)            # <-- optional: move position

    draw_single_escalator(center_left,  y0, y1, 0, ESCALATOR_RISE)
    draw_single_escalator(center_right, y0, y1, 0, ESCALATOR_RISE)

    glPopMatrix()                     # <-- add this


def draw_second_floor():
    S = 2000
    floor_z = 625
    floor_y = -2000

    glPushMatrix()
    glTranslatef(0, floor_y, floor_z)

    TILE = 100
    cols = int(S / TILE)

    # solid base floor first
    glColor3f(0.5, 0.5, 0.5)   # dark background color
    glBegin(GL_QUADS)
    glVertex3f(-S/2, -S/2, 0)
    glVertex3f( S/2, -S/2, 0)
    glVertex3f( S/2,  S/2, 0)
    glVertex3f(-S/2,  S/2, 0)
    glEnd()

    border = 6
    b = 5   # thickness of the border quad

    for row in range(cols):
        for col in range(cols):
            x0 = -S/2 + col * TILE + border
            y0 = -S/2 + row * TILE + border
            x1 = x0 + TILE - border * 2
            y1 = y0 + TILE - border * 2

            glColor3f(0.75, 0.75, 0.75)
            glBegin(GL_QUADS)

            # bottom edge
            glVertex3f(x0,     y0,     1)
            glVertex3f(x1,     y0,     1)
            glVertex3f(x1,     y0 + b, 1)
            glVertex3f(x0,     y0 + b, 1)

            # top edge
            glVertex3f(x0,     y1 - b, 1)
            glVertex3f(x1,     y1 - b, 1)
            glVertex3f(x1,     y1,     1)
            glVertex3f(x0,     y1,     1)

            # left edge
            glVertex3f(x0,     y0,     1)
            glVertex3f(x0 + b, y0,     1)
            glVertex3f(x0 + b, y1,     1)
            glVertex3f(x0,     y1,     1)

            # right edge
            glVertex3f(x1 - b, y0,     1)
            glVertex3f(x1,     y0,     1)
            glVertex3f(x1,     y1,     1)
            glVertex3f(x1 - b, y1,     1)

            glEnd()

    glPopMatrix()



def showScreen():
   
   
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity() 
    glViewport(0, 0, 1000, 800)  

    setupCamera()  

    draw_floor()
    draw_escalators()
    draw_second_floor()
    #draw_grid()
    #draw_boundaries()

    #drawPlayer()

    #for e in enemies:
     #   draw_enemy(e["x"], e["y"], e["scale"])

    #draw_bullets()

  
    draw_text(10, 770, f"Player Life Remaining: {health}")
    draw_text(10, 740, f"Game Score: {score}")
    draw_text(10, 710, f"Player Bullet Missed: {missed}")

    if cheatMode:
        draw_text(10, 680, "CHEAT MODE is ON")
    if autoCam and fpMode:
        draw_text(10, 650, "AUTO-CAM is ON")

    if gameOver:
        draw_text(400, 600, "GAME OVER! Press 'R' to Restart")


    glutSwapBuffers()


def keyboardListener(key, x, y):
  
    global position, playerAngle, cheatMode, autoCam

  
    if gameOver:
        if key== b'r':
            resetGame()
        return

    move_speed=20.0

    if cheatMode:
        move_angle=gunAngle
    else:
        move_angle=playerAngle

    rad=math.radians(move_angle)

    # Move forward (W key)
    if key == b'w':
        position[0]+=math.cos(rad)*move_speed
        position[1]+=math.sin(rad)*move_speed

    # Move backward (S key)
    if key == b's':
        position[0] -=math.cos(rad)*move_speed
        position[1] -=math.sin(rad)* move_speed

    # Rotate gun left (A key)
    if key == b'a':
        playerAngle +=10

    # Rotate gun right (D key)
    if key == b'd':
        playerAngle -=10

    # Toggle cheat mode (C key)
    if key == b'c':
        cheatMode=not cheatMode

    # Toggle cheat vision (V key)
    if key == b'v':
        autoCam=not autoCam

    # Reset the game if R key is pressed
    if key == b'r':
        resetGame()

    playerBound()


def specialKeyListener(key, x, y):
    
    global camHeight, camAngle

    # Move camera up (UP arrow key)
    if key == GLUT_KEY_UP:
        camHeight+=20

    # Move camera down (DOWN arrow key)
    if key == GLUT_KEY_DOWN:
        camHeight-=20

    # moving camera left (LEFT arrow key)
    if key == GLUT_KEY_LEFT:
        camAngle += 5  # Small angle decrement for smooth movement

    # moving camera right (RIGHT arrow key)
    if key == GLUT_KEY_RIGHT:
        camAngle -= 5  # Small angle increment for smooth movement


def mouseListener(button, state, x, y):
  
    global fpMode

    if gameOver:
        return

    # Left mouse button fires a bullet
    if button == GLUT_LEFT_BUTTON and state == GLUT_DOWN:
        if cheatMode:
            shoot_angle= gunAngle
        else:
            shoot_angle= playerAngle

        rad= math.radians(shoot_angle)
        bx,by,bz= bulletSpawn(shoot_angle)
        bullets.append({
            "x":bx,
            "y":by,
            "z":bz,
            "dx":math.cos(rad)*speedBullet,
            "dy":math.sin(rad)*speedBullet
        })

    # Right mouse button toggles camera tracking mode
    if button == GLUT_RIGHT_BUTTON and state == GLUT_DOWN:
        fpMode = not fpMode

# Main function to set up OpenGL window and loop
def main():
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)  # Double buffering, RGB color, depth test
    glutInitWindowSize(1000, 800)  # Window size
    glutInitWindowPosition(0, 0)  # Window position
    wind = glutCreateWindow(b"Bullet Frenzy")  # Create the window

    enemy_initialize()

    glutDisplayFunc(showScreen)  # Register display function
    glutKeyboardFunc(keyboardListener)  # Register keyboard listener
    glutSpecialFunc(specialKeyListener)
    glutMouseFunc(mouseListener)
    glutIdleFunc(idle)  # Register the idle function to move the bullet automatically
    glEnable(GL_DEPTH_TEST)
    
    glutMainLoop()  # Enter the GLUT main loop

if __name__ == "__main__":
    main()