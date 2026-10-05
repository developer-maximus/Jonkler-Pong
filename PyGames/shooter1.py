from pygame import *
from random import randint
import math as mathematics
window = display.set_mode((700,500)) # window size
display.set_caption("Catch!") # window title

font.init()
mixer.init()

all_objects = list()
all_renderObjects = list()

window_x = 700
window_y = 500

def nothing():
    pass

class Object(sprite.Sprite):
    def __init__(self,objimage,size:list,position=(0,0)):
        super().__init__()
        
        self.x = position[0]
        self.y = position[1]
        self.displayOffsetX = 0
        self.displayOffsetY = 0

        self.origImage = objimage
        self.origColor = objimage

        self.renderMethod = "Image"

        if isinstance(objimage,tuple):
            self.renderMethod = "Color"

        self.sizeX = size[0]
        self.sizeY = size[1]
        self.size = size

        self.collideable = True
        self.triggersCollisions = True
        self.collisionPromises = []
        self.tags = []

        self.objectsWeldedToMe = []


        self.image = self.get_surface()
        self.rect = self.image.get_rect()
        self.rect.x, self.rect.y = self.x, self.y
        self.rect.size = size
        self.position=position

        all_objects.append(self)
        all_renderObjects.append(self)

        self.currentAnimation = None
    
    def get_surface(self):
        returner = None
        if self.renderMethod == "Image":
            returner = transform.scale(image.load(self.origImage),self.size)
        if self.renderMethod == "Color":
            print("Color")
            color = Surface(size=self.size)
            color.fill(self.origColor)
            #color.fill
            returner = color
        self.image = returner
        return returner

    def changeSize(self,newSizeX,newSizeY):
        self.sizeX = newSizeX
        self.sizeY = newSizeY
        self.size = (newSizeX,newSizeY)
        self.image = self.get_surface()

    def isPositionViable(self, x,y):
        if not (y > 0 and y < window_y-self.sizeY):
            return False
        if not (x > 0 and x < window_x-self.sizeX):
            return False
        
        return True

        
    def changePosition(self, changeX, changeY):
        newX = self.x + changeX
        newY = self.y + changeY
        if self.isPositionViable(newX,newY):
            self.setPosition(newX,newY)
            for object in all_objects:
                if object != self:
                    if object.rect.colliderect(self.rect):
                        #print(f"{self.image} collided with {object.image} at {self.position}")
                        if object.collideable and self.collideable:
                            self.setPosition(self.x-changeX,self.y-changeY)
                        if object.triggersCollisions:
                            self.collided(object)
                        if self.triggersCollisions:
                            object.collided(self)

    def setPosition(self, x,y):
        dX = x - self.x
        dY = y - self.y
        for obj in self.objectsWeldedToMe:
            obj.changePosition(dX,dY)
        if not self.isPositionViable(x,y):
            return
        
        if x != None:
            self.x = x
        
        if y != None:
            self.y = y
        
        self.rect.x, self.rect.y = self.x, self.y
    
    def makeUncollideable(self):
        self.collideable = False
        self.triggersCollisions = False
    
    def makeCollideable(self):
        self.collideable = True
        self.triggersCollisions = True

    def ifCollisionHappens(self, funcToCall):
        self.collisionPromises.append(funcToCall)

    def collided(self, collidedObject):
        for p in self.collisionPromises:
            print(self,collidedObject)
            p(self, collidedObject) 
        
    def play_animation(self, animation:Animation):
        self.currentAnimation = animation
    
    def destroy(self):
        self.image = None
        try:
            all_objects.remove(self)
            all_renderObjects.remove(self)
        except ValueError:
            pass
        self.blit = nothing
        self.kill()
        self.remove()

    def blit(self):
        if self.currentAnimation:
            displayData = self.currentAnimation.update()
            
            self.image = displayData["frame"]

            dPos = displayData.get("positionChange")
                
            self.displayOffsetX += dPos[0]
            self.displayOffsetY += dPos[1]

        try:
            window.blit(self.image,(self.x + self.displayOffsetX, self.y + self.displayOffsetY))
        except TypeError:
            pass

class Text(font.Font):
    def __init__(self, text="Label", position=[100,100], fontSize=24, textColor=(255,255,255)):
        super().__init__(None,fontSize)
        self.x = position[0] # X and Y are flipped... for whatever reason
        self.xOffset = 0
        self.yOffset = 0
        self.y = position[1]
        self.weldedTo = None
        self.text = text
        self.textColor = textColor
        self.surface = self.render(self.text,True, textColor)
        self.rect = self.surface.get_rect(center=(self.x,self.y))
        all_renderObjects.append(self)
    def changePosition(self, dX, dY):
        self.setPosition(self.x+dX, self.y+dY)
    def setPosition(self, x, y):
        self.rect = self.surface.get_rect(center=(x+self.xOffset,y+self.yOffset))
        self.x = x
        self.y = y

    def blit(self):
        self.surface = self.render(self.text,True, self.textColor)
        if self.weldedTo:
            self.yOffset = self.weldedTo.displayOffsetY
        self.rect = self.surface.get_rect(center=(self.x+self.xOffset,self.y+self.yOffset))
        window.blit(self.surface,self.rect)
    def weldToObject(self, object: Object):
        self.weldedTo = object 
        self.xOffset = self.weldedTo.sizeX/2  # weird stuff
        self.yOffset = self.weldedTo.displayOffsetY
        self.setPosition(self.x,self.y)
        object.objectsWeldedToMe.append(self)
    def destroy(self):
        self.text = ""
        self.blit = nothing


class Sound(mixer.Sound):
    def __init__(self, musicFile, isBackgroundMusic=False):
        super().__init__(musicFile)

        if isBackgroundMusic:
            self = mixer.music
            mixer.music.load(musicFile)
            mixer.music.set_volume(0.5)
            mixer.music.play()

class Animation():
    def __init__(self, animFrames, ticksPerChange=1, startingFrame = 0):
        self.speed = ticksPerChange
        self.animationFrames = list()
        self.ticksPerLastChange = self.speed
        self.paused = False
        self.totOffsetX = 0
        self.totOffsetY = 0
        if animFrames:
            self.animationFrames = animFrames
        
        self.currentFrame = startingFrame
        self.currentAnimFrame = None
        self.displayData = None
        try:
            self.currentAnimFrame = self.animationFrames[self.currentFrame-1]
        except IndexError:
            self.currentAnimFrame = self.animationFrames[0]
        

    def addAnimFrame(self, animFrame : AnimationFrame):
        self.animationFrames.append(animFrame)
    
    def getNextFrame(self):
        nextFrame = self.currentFrame + 1
        nextAnimFrame = None
        try:
            nextAnimFrame = self.animationFrames[nextFrame-1]
        except IndexError:
            nextFrame = 1
            nextAnimFrame = self.animationFrames[nextFrame-1]
        
        return nextFrame, nextAnimFrame

    def nextAnimFrame(self):
        currDisplayData = dict()
        oldAnimFrame : AnimationFrame = self.currentAnimFrame
        self.currentFrame, self.currentAnimFrame = self.getNextFrame()


        dPos = (0,0)
        if oldAnimFrame:

            oldSize = oldAnimFrame.frame.size
            newSize = self.currentAnimFrame.frame.size

            dX = oldSize[0] - newSize[0] + self.currentAnimFrame.positionChange[0]
            dY = oldSize[1] - newSize[1] + self.currentAnimFrame.positionChange[1]
            dPos = (dX/2,dY/2)

            currDisplayData["positionChange"] = dPos
        
        currDisplayData["frame"] = self.currentAnimFrame.frame
        
        return currDisplayData
    
    def pause(self):
        self.paused = True
    
    def continue_anim(self):
        self.paused = False

    def update(self):
        if not self.paused:
            self.ticksPerLastChange += 1


        oldDisplay : AnimationFrame= self.displayData

        if self.ticksPerLastChange >= self.speed:
            self.ticksPerLastChange = 0
            self.displayData = self.nextAnimFrame()
        

        if oldDisplay:
            if oldDisplay == self.displayData:
                self.displayData["positionChange"] = (0,0)
        

    
        

        return self.displayData
losDefVal = 3
class AnimationFrame():
    def __init__(self, frame, size=(100,100),positionChange=(0,0),smoothTransition=False):
        self.frame = transform.scale(image.load(frame),size)
        self.positionChange : list = positionChange
        self.smoothTransition = smoothTransition
        self.startingFrame = 0
        self.origImage = frame
        self.uniqueID = randint(0,255)

enemies = 0

class Bullet(Object):
    def __init__(self):
        targPos = (Player.x,Player.y-70)
        super().__init__(r"Tests\jonkler.png", (30,60), targPos)
    def blit(self):
        self.changePosition(0,-10)
        if self.y <= 10:
            self.destroy()
        try:
            window.blit(self.image,(self.x,self.y))
        except TypeError: 
            pass
    def collided(self, obj):
        global enemies,enDafVal,enDef
        self.destroy()
        try:
            x = obj.attackable
        except AttributeError:
            return
        try:
            obj.HP -= 1
            if obj.HP <= 0:
                obj.destroy()
                enemies -= 1
                enDafVal += 1
        except AttributeError:
            obj.destroy()
            enemies -= 1
            enDafVal += 1
        enDef.text = f"Enemies defeated: {enDafVal}"

class Enemy(Object):
    def __init__(self,size=(100,100),type="Snail"):
        self.HP = 1
        self.speed = 2
        # temporary:
        random = randint(0,10)
        if random <= 7: #type == "Snail":
            super().__init__(r"Tests\snail.png", size, (randint(0,window_x-100), 0))
        elif random >= 3: #type == "WhiteBall":
            self.HP = 1
            self.speed = 3
            super().__init__(r"Tests\white_ball.png", (60,60), (randint(0,window_x-100), 0))
        self.collideable = False
        self.attackable = True
        self.tags.append("Enemy")
    
    def update(self):
        global losDef,losDefVal
        self.changePosition(0,self.speed)
        if self.y >= window_y-110:
            losDefVal -= 1
            losDef.text = f"Lives left: {losDefVal}"
            self.destroy()

class Boss(Object):
    def __init__(self):
        super().__init__(r"Tests\boss.jpg", (200,200), (250,10))
        self.changeSize(200,200)
        self.attack_db = Debounce(120, self.attack)
        self.temp_db = None
        self.state = "Idle"
        self.laser = None
        self.attackable = True
        self.xVel = 3   
        self.mHP = 20
        self.HP = self.mHP
        self.oHP = self.HP
        self.laserAttack = False

        self.BossTxt = Text("Boss health:", (600,50),40,(0,10,200))
        #self.Rect1 = Object(r"Tests\blue_pong.png", (200,40),(500,90))
        #self.Rect2 = Object(r"Tests\red_pong.png", (200,40),(500,90))
   
        self.HPDisplay = ProgressBar((200,40),(500,90),(0,0,0),(255,0,0))

        for en in all_objects:
            if "Enemy" in en.tags:
                en.destroy()

        self.lastAttacked = currentTick
    def attack(self):
        rng = randint(0,10)
        if rng >= 5:
            self.attack_1()
        else:
            self.attack_2()
    def attack_1(self):
        if self.state == "Idle" and currentTick >= self.lastAttacked+180:
            self.state = "Attacking"
            self.laserAttack = True
            self.lastAttacked = currentTick
        
            self.laser = Object(r"Tests\red_pong.png",(50,300),(self.x+100,200))
            self.laser.ifCollisionHappens(self.__laserCollided__)
            #self.laser.collideable = False
            
        elif self.state == "Attacking" and currentTick >= self.lastAttacked+180:
            self.state = "Idle"
        elif self.state == "Attacking" and currentTick >= self.lastAttacked+30:
            self.laserAttack = False
            self.attack_stop()
    def attack_2(self):
        if self.state == "Idle" and currentTick >= self.lastAttacked+180:
            self.state = "Attacking"
            self.lastAttacked = currentTick
        
            en_1 = Enemy()
            en_1.setPosition(self.x,self.y-200)
            en_2 = Enemy()
            en_2.setPosition(self.x-200,self.y-200)
            en_3 = Enemy()
            en_3.setPosition(self.x+200,self.y-200)
            
        elif self.state == "Attacking" and currentTick >= self.lastAttacked+180:
            self.state = "Idle"
    def __laserCollided__(self, me, obj:Object):
        global fake_paused
        print("coll")
        tagsObj = obj.tags
        if not "Player" in tagsObj:
            return
        print(tagsObj)
        Text("YOU LOST", (350,250), 60, (255,0,0))
        fake_paused = True
        paused = 0
    def update(self):
        if self.x <= 50:
            self.xVel = 3
        if self.x >= 500:
            self.xVel = -3
        self.x += self.xVel
        self.rect.x += self.xVel

        if self.oHP != self.HP:
            self.oHP = self.HP
            print("Changing size")
            #self.Rect2.changeSize(self.HP/self.mHP*200,self.Rect2.sizeY)
            self.HPDisplay.changePercentBar(self.HP/self.mHP*100)

    def attack_stop(self):
        self.attack_1_stop()
    def attack_1_stop(self):
        try:
            self.laser.destroy()
            self.laser = None
            self.state = "Idle"
        except AttributeError:
            pass
    def destroy(self):
        global Boss_1
        super().destroy()
        self.attack = nothing
        self.update = nothing
        self.HPDisplay.destroy()
        self.attack_1_stop()
        self.BossTxt.text = ""
        self = None
        Boss_1 = None
        del self


class Debounce():
    def __init__(self, cooldown, action=nothing, oneTime=False):
        self.lastUsed = currentTick+cooldown
        self.cooldown = cooldown
        self.action = action
        self.oneTime = oneTime
    def use(self):
        if self.oneTime == "Done":
            return
        
        if currentTick >= self.lastUsed:
            self.lastUsed = currentTick + self.cooldown
            self.action()
            if self.oneTime == True:
                self.oneTime = "Done"
            return True
class ProgressBar():
    def __init__(self, size=(100,30), position=(0,0,0),bgColor=(0,0,0), fillColor=(255,255,255)):
        bgBar = Object(bgColor, size, position)
        progSize = (size[0]-10,size[1]-10)
        progPos = (position[0]+5,position[1]+5)
        progBar = Object(fillColor,progSize,progPos)
        self.bgBar = bgBar
        self.progBar = progBar
        self.size = size
        self.position = position
        self.fillColor = fillColor
        self.progSize = progSize
        self.progPos = progPos
    def changePercentBar(self,percent):
        self.progBar.changeSize(self.progSize[0]*percent/100, self.progSize[1])
    def destroy(self):
        self.bgBar.destroy()
        self.progBar.destroy()





# MAIN WRITING  
background = Object("Tests\snail.png",(window_x,window_y), (0,0))
background.makeUncollideable()

Player = Object("Tests\geniusses.png", (100,100), (500, 399))
Player.tags.append("Player")

enDafVal = 0
enDef = Text("Enemies defeated: 0", [80,24], 24, (0,0,0))

losDef = Text("Lives left: 3", [48, 48], 24, (0,0,0))
clock = time.Clock()
currentTick = 0
game = True
#bg_music = Sound("Tests\DroopyFace.mp3", True)
fire_db = Debounce(25)
enemy_db = Debounce(55)
dash_db = Debounce(1)

dashAnnounc = None
dashAnnDB = None

fake_paused = False

tut_txt = Text("Press ARROW KEYS and SPACE to SHOOT at SNAILS",  (350,450),35,(0,10,10))

Boss_1 = None

Shoot = Sound("Tests\shock.mp3")

paused=2
while game:
    if currentTick >= 240 and tut_txt:
        tut_txt.destroy()
    currentTick += 1
    if fake_paused and paused > 0:
        paused -= 1
    elif not fake_paused:
        paused = 2

    if dashAnnDB:
        dashAnnDB.use()
    if not Boss_1 and enemy_db.use():
        Enemy()

        if enemies <= 4:
            enemy_db.cooldown = randint(25,65)
        else:
            enemy_db.cooldown = randint(65,130)

    if losDefVal <= 0 :
        Text("YOU LOST", (350,250), 60, (255,0,0))
        fake_paused = True
    if paused > 0:
        for currObj in all_renderObjects:
            currObj.blit()
        for enemy in all_objects:
            try:
                enemy.update()
            except AttributeError:
                pass

    if enDafVal == 10 and Boss_1 == None:
        dashAnnounc = Text("Press SHIFT and move 2 Dash: KILL the BOSS & SNAILS", (350,450),35,(0,0,100))
        def d():
            dashAnnounc.destroy()
        dashAnnDB = Debounce(300, d, True)
        Boss_1 = Boss()
    elif Boss_1:
        Boss_1.attack()

    for e in event.get():
        if e.type == QUIT:
            game = False

    keys_pressed = key.get_pressed()

    if keys_pressed[K_SPACE] and fire_db.use():
        Bullet()

    if keys_pressed[K_RIGHT]:
        Player.changePosition(10,0)
        if dash_db.use() and keys_pressed[K_LSHIFT] and dashAnnDB:
            if not dashAnnDB.use():
            
                Player.changePosition(100,0)

    if keys_pressed[K_LEFT]:
        Player.changePosition(-10,0)
        if dash_db.use() and keys_pressed[K_LSHIFT] and dashAnnDB:
            if not dashAnnDB.use():
                Player.changePosition(-100,0)
    
    display.update()
    clock.tick(60)