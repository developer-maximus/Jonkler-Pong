from pygame import *

window = display.set_mode((700,500)) # window size
display.set_caption("Catch!") # window title

font.init()
mixer.init()

all_objects = list()
all_renderObjects = list()

window_x = 700
window_y = 500

game = True

class Object(sprite.Sprite):
    def __init__(self,objimage,size:list,position=(0,0)):
        super().__init__()
        self.x = position[0]
        self.y = position[1]
        
        self.sizeX = size[0]
        self.sizeY = size[1]

        self.collideable = True
        self.triggersCollisions = True
        self.collisionPromises = []

        self.objectsWeldedToMe = []

        self.imageSource = objimage
        self.image = transform.scale(image.load(objimage),size)
        self.rect = self.image.get_rect()
        self.rect.x, self.rect.y = self.x, self.y
        self.position=position

        all_objects.append(self)
        all_renderObjects.append(self)

    def isPositionViable(self, x,y):
        #print(f"Data: X: {x}, Y: {y}, WinX: {window_x}, WinY: {window_y}, SizeY: {self.sizeY}")
        if not (y > 0 and y < window_y-self.sizeY):
            return False
        if not (x > 0 and x < window_x-self.sizeX):
            return False
        
        return True
    
        
    def changePosition(self, changeX, changeY, disregardSafety=False):
        newX = self.x + changeX
        newY = self.y + changeY
        if self.isPositionViable(newX,newY) or disregardSafety:
            self.setPosition(newX,newY)
            for object in all_objects:
                if object != self:
                    if object.rect.colliderect(self.rect) and object.collideable and self.collideable:
                        self.setPosition(self.x-changeX,self.y-changeY)
                        if object.triggersCollisions:
                            object.collided(self)
                        if self.triggersCollisions:
                            self.collided(object)

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
            p(collidedObject) 

    def blit(self):
        window.blit(self.image,(self.x, self.y))

class Player(Object):
    def __init__(self,objimage,size:list,position=(0,0)):
        super().__init__(objimage, size, position)
    
    def update(self):
        if not keys_pressed:
            return
        try:
            if keys_pressed[K_UP]:
                self.changePosition(0, -10)
            if keys_pressed[K_RIGHT]:
                self.changePosition(10,0)
            if keys_pressed[K_LEFT]:
                self.changePosition(-10,0)
            if keys_pressed[K_DOWN]:
                self.changePosition(0,10)
        finally:
            pass

class Enemy(Object):
    def __init__(self,objimage,size:list,position=(470,0)):
        super().__init__(objimage, size, position)
        self.xDir = 1
    
    def update(self):
        if self.rect.x <= 430:
            self.xDir = 3
        elif self.rect.x >= 580:
            self.xDir = -3

        self.changePosition(self.xDir,0)

        self.blit()
        

        

class Text(font.Font):
    def __init__(self, text="Label", position=[100,100], fontSize=24, textColor=(255,255,255)):
        super().__init__(None,fontSize)
        self.x = position[0] # X and Y are flipped... for whatever reason
        self.xOffset = 0
        self.y = position[1]
        self.weldedTo = None
        self.surface = self.render(text,True, textColor)
        self.rect = self.surface.get_rect(center=(self.x,self.y))
        all_renderObjects.append(self)
    def changePosition(self, dX, dY):
        self.setPosition(self.x+dX, self.y+dY)
    def setPosition(self, x, y):
        self.rect = self.surface.get_rect(center=(x+self.xOffset,y))
        self.x = x
        self.y = y

    def blit(self):
        window.blit(self.surface,self.rect)
    def weldToObject(self, object: Object):
        self.weldedTo = object
        self.xOffset = self.weldedTo.sizeX/2  # weird stuff
        self.setPosition(self.x,self.y)
        object.objectsWeldedToMe.append(self)


class Sound(mixer.Sound):
    def __init__(self, musicFile, isBackgroundMusic):
        super().__init__(musicFile)

        if isBackgroundMusic:
            self = mixer.music
            mixer.music.load(musicFile)
            mixer.music.set_volume(0.55)
            mixer.music.play()
    




background = Object("Tests\snail.png",(window_x,window_y), (0,0))
background.makeUncollideable()

enemy = Enemy("Tests\geniusses.png", (100,100), (500, 250))

freeze = False
def freezeGame():
    global freeze 
    freeze = True

def playerTouched(object:Object):
    global game
    if object.imageSource == r"Tests\snail.png":
        Text("You won!", (350,250),60,textColor=(0,255,0))
        freezeGame()
    if object.imageSource == r"Tests\blue_pong.png" or object.imageSource == "Tests\geniusses.png":
        Text("You lost!", (350,250),60,textColor=(255,0,0))
        freezeGame()
    

player = Player("Tests\jonkler.png", (100,100), (250, 250))
player.ifCollisionHappens(playerTouched)
treasure = Object(r"Tests\snail.png", (75,75), (625,425))
obstacle1 = Object(r"Tests\blue_pong.png", (20,300), (400,200))
obstacle2 = Object(r"Tests\blue_pong.png", (20,50), (400,0))
obstacle3 = Object(r"Tests\blue_pong.png", (150,20), (400,200))

clock = time.Clock()

bg_music = Sound("Tests\DroopyFace.mp3", True)
keys_pressed = None
while game:
    if not freeze:
    
        keys_pressed = key.get_pressed()

        for currObj in all_renderObjects:
            currObj.blit()
            try:
                currObj.update()
            except AttributeError:
                pass

    for e in event.get():
        if e.type == QUIT:
            game = False

    display.update()
    clock.tick(60)