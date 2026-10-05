from pygame import *
from random import randint
window = display.set_mode((700,500)) # window size
display.set_caption("Catch!") # window title

font.init()
mixer.init()

all_objects = list()
all_renderObjects = list()

window_x = 700
window_y = 500

class Object(sprite.Sprite):
    def __init__(self,objimage,size:list,position=(0,0)):
        super().__init__()
        self.x = position[0]
        self.y = position[1]
        self.displayOffsetX = 0
        self.displayOffsetY = 0
        
        self.sizeX = size[0]
        self.sizeY = size[1]

        self.collideable = True
        self.triggersCollisions = True
        self.collisionPromises = []

        self.objectsWeldedToMe = []
        
        self.image = transform.scale(image.load(objimage),size)
        self.rect = self.image.get_rect()
        self.rect.x, self.rect.y = self.x, self.y
        self.rect.size = size
        self.position=position

        all_objects.append(self)
        all_renderObjects.append(self)

        self.currentAnimation = None

    def isPositionViable(self, x,y):
        if not (y > 0 and y < window_y-self.sizeY):
            return False
        if not (x > 0 and x < window_x-self.sizeX):
            return False
        
        return True
    
        
    def changePosition(self, changeX, changeY):
        coll = False
        newX = self.x + changeX
        newY = self.y + changeY
        if self.isPositionViable(newX,newY):
            self.setPosition(newX,newY)
            for object in all_objects:
                if object != self:
                    if object.rect.colliderect(self.rect):
                        #print(f"{self.image} collided with {object.image} at {self.position}")
                        if object.collideable and self.collideable:
                            coll = True
                            self.setPosition(self.x-changeX,self.y-changeY)
                        if object.triggersCollisions:
                            self.collided(object)
                        if self.triggersCollisions:
                            object.collided(self)
        else:
            coll = True
        return coll

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
        self.blit = print
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


class Sound(mixer.Sound):
    def __init__(self, musicFile, isBackgroundMusic):
        super().__init__(musicFile)
        

        if isBackgroundMusic:
            self = mixer.music
            mixer.music.load(musicFile)
            mixer.music.set_volume(0.2)
            mixer.music.play()
        else:
            self.set_volume(0.3)
            self.play()

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

class AnimationFrame():
    def __init__(self, frame, size=(100,100),positionChange=(0,0),smoothTransition=False):
        self.frame = transform.scale(image.load(frame),size)
        self.positionChange : list = positionChange
        self.smoothTransition = smoothTransition
        self.startingFrame = 0
        self.origImage = frame
        self.uniqueID = randint(0,255)


background = Object(r"Tests\blue_pong.png",(window_x,window_y), (0,0))
background.makeUncollideable()

sprite1 = Object("Tests\geniusses.png", (50,200), (600, 250))

sprite2 = Object("Tests\jonkler.png", (50,200), (50, 250))

pong = Object(r"Tests\red_pong.png", (40,40), (350,250))

firstPointText = Text("0", [30,30], 24, (0,0,0))
secondPointText = Text("0", [560,30], 24, (0,0,0))

firstPoints = 0
secondPoints = 0

clock = time.Clock()
game = True
bg_music = Sound("Tests\DroopyFace.mp3", True)

PONG_SPEED = 0
PONG_MAX_VEL = [12,7]
PONG_VEL = [1,1]
pong_buildup = 0



def resetPong():
    global pong_buildup,PONG_VEL,PONG_SPEED
    firstPointText.text = str(secondPoints)
    secondPointText.text = str(firstPoints)

    pong.setPosition(350,250)
    pong_buildup = 0
    PONG_SPEED = 5
    x = 1
    y = 1
    if PONG_VEL[0] > 0:
        x = -1
    if PONG_VEL[1] > 0:
        y = -1

    PONG_VEL = [x,y]
    Sound("popsfx.mp3", False)

def game_loop():
    global game, pong_buildup, firstPoints, secondPoints, clock, bg_music, PONG_SPEED, PONG_MAX_VEL, PONG_VEL
    
    PONG_SPEED += 0.01

    if PONG_VEL[0] > 0:
        PONG_VEL[0] = PONG_MAX_VEL[0] * PONG_SPEED/10
    else:
        PONG_VEL[0] = -PONG_MAX_VEL[0]* PONG_SPEED/10
        
    if PONG_VEL[1] > 0:
        PONG_VEL[1] = PONG_MAX_VEL[1]* PONG_SPEED/10
    else:
        PONG_VEL[1] = -PONG_MAX_VEL[1]* PONG_SPEED/10
    


    y_hit = pong.changePosition(-PONG_VEL[0], PONG_VEL[1])
    
    if y_hit:
        Sound("collide.mp3", False)
        PONG_VEL[1] *= -1
    x_hit = pong.changePosition(PONG_VEL[0],0)
    if x_hit:
        Sound("collide.mp3", False)
        PONG_VEL[0] *= -1
        
        
    corner_hit = pong.changePosition(PONG_VEL[0], 0)
    
    if corner_hit:
        PONG_VEL[0] *= -1
        PONG_VEL[1] *= -1
        
    if pong.x <= 50:
        firstPoints += 1
        resetPong()
    if pong.x >= 600:
        secondPoints += 1
        resetPong()
        
    keys_pressed = key.get_pressed()
    
    if keys_pressed[K_BACKSPACE]:
        sprite1.changePosition(0, -10)
    if keys_pressed[K_RSHIFT]:
        sprite1.changePosition(0,10)
    
    if keys_pressed[K_BACKQUOTE]:
        sprite2.changePosition(0, -10)
    if keys_pressed[K_LSHIFT]:
        sprite2.changePosition(0,10)
        
starting_screen = Object(r"Tests\background_pong.png", (700,500), (0,0))
start_game = False
while game:
    if start_game:
        game_loop()
    for currObj in all_renderObjects:
            currObj.blit()
    for e in event.get():
        if e.type == QUIT:
            game = False
        if e.type == MOUSEBUTTONDOWN:
            start_game = True
            starting_screen.destroy()
    display.update()
    clock.tick(60)