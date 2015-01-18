#Import Modules
import sys, os, pygame, random, time
import pygame.gfxdraw
import pygame.surface
import pygame.color
import pygame.mixer
from pygame.locals import *
from pygame.color import *

# images
_penguinImage=None
_orcaImage=None
_sealImage=None
_orcaKillImage=None
_fuelImage=None
_poopImage=None
_titleImage=None

# sounds
_heliSound=None
_missleSound=None
_enemySound=None
_enemyKillSound=None
_fuelSound=None
_fuelDownSound=None
_poopSound=None
_penguinKillSound=None

# screen dimensions
_backgroundWidth=800
_backgroundHeight=600


# High score
_highScore=0

time1 = time.clock()

# Cave BackgroundColor
cavebackground = (52, 73,94)

##############################################################
### Utility functions
##############################################################

# load image
def loadImage(name, colorkey=None):

    fullname = name
    try:
        image = pygame.image.load(fullname)
    except pygame.error, message:
        print 'Cannot load image:', fullname
        raise SystemExit(message)
    image = image.convert()
    if colorkey is not None:
        if colorkey is -1:
            colorkey = image.get_at((0,0))
        image.set_colorkey(colorkey, RLEACCEL)
    return image, image.get_rect()

# preload images
def loadImages():

    global _penguinImage
    global _orcaImage
    global _orcaKillImage
    global _sealImage
    global _fuelImage
    global _poopImage
    global _titleImage
    global _bgImage

    _penguinImage=loadImage('res/pennapps.png', (0,0,0))
    _orcaImage=loadImage('res/orca.png', (0,0,0))
    _sealImage=loadImage('res/seal.png', (0,0,0))
    _fuelImage=loadImage('res/nemo.png', (0,0,0))
    _poopImage=loadImage('res/emoji_poop.png', (0,0,0))
    _titleImage=loadImage('res/penguinlg.png',  (255,255,255))
    _bgImage = loadImage('res/bg.jpg', (0,0,0))

# load sound
def loadSound(name):

    class NoneSound:
        def play(self): pass
    if not pygame.mixer or not pygame.mixer.get_init():
        return NoneSound()
    fullname = name
    try:
        sound = pygame.mixer.Sound(fullname)
    except pygame.error, message:
        print 'Cannot load sound:', fullname
        raise SystemExit, message
    return sound

# preload sounds
def loadSounds():

    global _heliSound
    global _missleSound
    global _enemySound
    global _enemyKillSound
    global _fuelSound
    global _fuelDownSound
    global _poopSound
    global _penguinKillSound

    _heliSound=loadSound('res\\heli.wav')
    _missleSound=loadSound('res\\missle.wav')
    _enemySound=loadSound('res\\enemy.wav')
    _enemyKillSound=loadSound('res\\enemyKill.wav')
    _fuelSound=loadSound('res\\fuel.wav')
    _fuelDownSound=loadSound('res\\fuelDown.wav')
    _poopSound=loadSound('res\\poop.wav')
    _penguinKillSound=loadSound('res\\penguinKill.wav')

    _enemyKillSound.set_volume(0.5)
    _heliSound.set_volume(0.5)
    _fuelDownSound.set_volume(0.2)
    _fuelSound.set_volume(0.05)
    _poopSound.set_volume(0.1)
    _penguinKillSound.set_volume(0.5)

# Initialize the game window
def initWindow(width, height):

    pygame.init()
    screen = pygame.display.set_mode((width, height))
    pygame.display.set_caption('Penguin Muse')
    pygame.mouse.set_visible(1)
    return screen

# Create an empty background
def createEmptySurface(screen, rect):

    background = pygame.Surface(rect)
    background = background.convert()
    background.fill ((52, 73, 94))
    return background

# Carry out scroll operation of landscape on background by delta
def scrollLandscape(background, delta, tile, topspace):

    shiftDim=(delta, topspace, background.get_rect().width-delta, background.get_rect().height-topspace)
    shiftBackground=background.subsurface(shiftDim)

    shiftLandscape=tile.fetchTile()

    newBackground=pygame.Surface((background.get_rect().width, background.get_rect().height))
    newBackground.blit(shiftBackground, (0,topspace))
    newBackground.blit(shiftLandscape, (background.get_rect().width-delta,topspace))

    return newBackground

# Check background collision of provided sprite
def checkBackgroundCollision(background, toCheck, toCheckGroup):

        try:
            # Carry out check
            result=True
            bgtile=BgTile(background, toCheck.rect)
            tiles = pygame.sprite.RenderPlain()
            tiles.add(bgtile)
            collgroup = pygame.sprite.spritecollide(bgtile, toCheckGroup, 0, pygame.sprite.collide_mask)

            # Communicate check result
            if len(collgroup) > 0: # collision
                collgroup[0].collidedBackground()
                collgroup.remove(toCheck)
                result=False

            # Cleanup
            tiles.remove(bgtile)
        except:
            result=True

        return result

# Checks UFO collisions with other objects
def checkOrcaCollisions(orcaGroup, killedGroup, state, background):

    # Avoid orca collisions with cave
    orcas=orcaGroup.sprites()
    for ndx in range(len(orcas)):
        orca=orcas[ndx]
        if orca.rect.left>=0:
            checkBackgroundCollision(background,orca,orcaGroup)

    # Handle killed UFOs
    handleKilledEnemies(killedGroup)

def checkSealCollisions(sealGroup, killedGroup, state, background):

    # Avoid orca collisions with cave
    seals=sealGroup.sprites()
    for ndx in range(len(seals)):
        seal=seals[ndx]
        if seal.rect.left>=0:
            checkBackgroundCollision(background,seal,sealGroup)

    # Handle killed UFOs
    handleKilledEnemies(killedGroup)

# Checks penguin collisions with other objects
def checkPenguinCollisions(penguin, orcaGroup, fuelGroup, sealGroup, \
                          poopGroup, state):
            # Check helipenguin collision with UFO
        collgroup=pygame.sprite.spritecollide(penguin, orcaGroup, sealGroup, pygame.sprite.collide_mask)
        if len(collgroup) > 0:
            _fuelDownSound.play()
            state.penguinFuel=state.penguinFuel-5
            if state.fuelCnt<0:
                state.fuelCnt=0

        # Check helipenguin collision with fuel tank
        collgroup=pygame.sprite.spritecollide(penguin, fuelGroup, 0)
        if len(collgroup) > 0:
            _fuelSound.play()
            collgroup[0].fuel=collgroup[0].fuel-1
            if collgroup[0].fuel<=0:
                fuelGroup.remove(collgroup[0])
                state.fuelCnt=0
                state.lastFuelCnt=0
            state.penguinFuel=state.penguinFuel+1

        # Check helipenguin collision with poop
        collgroup=pygame.sprite.spritecollide(penguin, poopGroup, 1)
        if len(collgroup) > 0:
            _fuelDownSound.play()
            state.poopCnt=state.poopCnt-1
            state.penguinFuel=state.penguinFuel-50

# Handles disappearence of killed enemies from screen
def handleKilledEnemies(killedGroup):

    # Check if there are exploded orcas to be removed
    toBeRemoved=[]
    for ndx in range(len(killedGroup.sprites())):
        killed=killedGroup.sprites()[ndx]
        killed.killCnt=killed.killCnt-1
        if killed.killCnt<=0:
            toBeRemoved.append(killed)

    for ndx in range(len(toBeRemoved)):
        killedGroup.remove(toBeRemoved[ndx])

# Adds randomly fuel tanks
def addFuel(tile, fuelGroup, state, topSpace):

    global _backgroundWidth
    global _backgroundHeight

    state.lastFuelCnt=state.lastFuelCnt+1
    doAdd=random.randint(1,100)
    if state.fuelCnt<state.fuelMax and state.lastFuelCnt>state.doFuelCnt:
        if doAdd==1:
            x=random.randint(1, 2)
            if x==1:
                position=tile.top_tileHeight+topSpace+random.randint(20, 40)
            else:
                position=_backgroundHeight-tile.btm_tileHeight-random.randint(30, 50)
            fuel=FuelTank(_backgroundWidth-50, position, fuelGroup, state)
            fuelGroup.add(fuel)
            state.fuelCnt=state.fuelCnt+1
            state.lastFuelCnt=0

# Adds randomly enemy poops
def addPoop(orcaGroup, poopGroup, state):

    global _poopSound

    # Iterate over orcas and create poops randomly
    for ndx in range(len(orcaGroup.sprites())):
        orca=orcaGroup.sprites()[ndx]
        if state.poopCnt<state.poopMax:
            poopDeterminator=random.randint(1, state.poopRnd)
            if poopDeterminator<=state.doPoop:
                _poopSound.play()
                state.poopCnt=state.poopCnt+1
                poop=Poop(orca.rect.left+10, orca.rect.top+20, poopGroup, state)
                poopGroup.add(poop)

# Adds randomly enemy UFOs
def addOrca(tile, orcaGroup, state, topSpace):

    global _backgroundWidth
    global _backgroundHeight
    global _enemySound

    state.lastOrcaCnt=state.lastOrcaCnt+1
    doAdd=random.randint(1, 30)
    if state.orcaCnt<state.orcaMax and state.lastOrcaCnt>state.doOrcaCnt:
        if doAdd==1:
            x=random.randint(1, 2)
            if x==1:
                ymove=random.randint(1,state.maxYDelta)
                position=tile.top_tileHeight+topSpace+random.randint(20, 30)
            else:
                ymove=-random.randint(1,state.maxYDelta)
                position=_backgroundHeight-tile.btm_tileHeight-random.randint(20, 30)

            _enemySound.play()
            orca=Orca(_backgroundWidth-50, position-ymove, orcaGroup, state)
            orca.ymove=ymove
            orcaGroup.add(orca)
            state.orcaCnt=state.orcaCnt+1
            state.lastOrcaCnt=0


def addSeal(tile, sealGroup, state, topSpace):

    global _backgroundWidth
    global _backgroundHeight
    global _enemySound

    state.lastSealCnt=state.lastSealCnt+1
    doAdd=random.randint(1, 1000)
    if state.sealCnt<state.sealMax and state.lastSealCnt>state.doSealCnt:
        if doAdd==1:
            x=random.randint(1, 2)
            if x==1:
                ymove=random.randint(1,state.maxYDelta)
                position=tile.top_tileHeight+topSpace+random.randint(20, 30)
            else:
                ymove=-random.randint(1,state.maxYDelta)
                position=_backgroundHeight-tile.btm_tileHeight-random.randint(20, 30)

            _enemySound.play()
            seal=Seal(_backgroundWidth-50, position-ymove, sealGroup, state)
            seal.ymove=ymove
            sealGroup.add(seal)
            state.sealCnt=state.sealCnt+1
            state.lastSealCnt=0

# Add text to provided background
def addText(text, background, xpos, ypos, \
            color=(255,255,255), bgcolor=(0,0,0), size=22, center=False):

    font=pygame.font.SysFont("Arial", size, True)
    text=font.render(text, 4, color)
    textpos=text.get_rect()
    textpos.left=0
    textpos.top=0
    if center == True:
        xpos = background.get_width()/2 - textpos.width/2
    cleanrec=(xpos-1, ypos-1, textpos.width, textpos.height)
    if bgcolor!=None:
        background.fill(bgcolor, cleanrec);
    background.blit(text, (xpos, ypos));

# Update game information on top of the screen
def updatePenguinInfo(background, state):
    time2 = time.clock()
    addText("Health: " + str(state.penguinFuel), background, 15, 3, THECOLORS['lightgrey'], (0,0,0), 20)
    addText("Sector: " + str(state.sector), background, 210, 3, THECOLORS[state.sectorColor], (0,0,0), 20)
    addText("Score: " + str(int ((10 * (round (time2 - time1, 1)))/2)), background, 440, 3, THECOLORS['cyan'], (0,0,0), 20)

# Explodes sprite into several fragments returned in a sprite group
def explodeSprite(toExplode=None, xtiles=0, ytiles=0):

    # Calculate number of tiles for explosion
    tileWidth=toExplode.image.get_rect().width/xtiles
    tileHeight=toExplode.image.get_rect().height/ytiles

    tileGroup = pygame.sprite.RenderPlain()
    tileTop=toExplode.rect.top
    for ycnt in range(ytiles):
        # Deterpoop y tile dimension
        tileTop=tileTop+tileHeight
        ypos=ycnt*tileHeight
        currentTileHeight=tileHeight
        if ypos+currentTileHeight>toExplode.rect.height:
            currentTileHeight=toExplode.rect.height-ypos

        tileLeft=toExplode.rect.left
        for xcnt in range(xtiles):
            # Deterpoop x tile dimension
            tileLeft=tileLeft+tileWidth
            xpos=xcnt*tileWidth
            currentTileWidth=tileWidth
            if xpos+currentTileWidth>toExplode.rect.width:
                currentTileWidth=toExplode.rect.width-xpos

            # Fetch tile
            tileDim=(xpos, ypos, currentTileWidth, currentTileHeight)
            tileImage=toExplode.image.subsurface(tileDim)

            # Create sprite and add it to sprite group
            tile=ExplodeTile(tileImage, tileLeft, tileTop)
            tileGroup.add(tile)

    return tileGroup




#############################################################
### Classes
#############################################################

# Vertical tile of cave
# The parts on the top and bottom of the screen
class CaveTile():

    # Create a cave tile
    def __init__(self, \
                 tileWidth=5, landHeight=600, topSpace=40, \
                 minSpace=350, color=THECOLORS['skyblue'], \
                 top_tileHeight=100, top_tileDiff=2, \
                 top_maxHeight=300, top_minHeight=50,
                 btm_tileHeight=100, btm_tileDiff=2, \
                 btm_maxHeight=300, btm_minHeight=50):

        self.tileWidth=tileWidth
        self.landHeight=landHeight
        self.color=color
        self.minSpace=minSpace
        self.topSpace=topSpace

        self.top_tileHeight=top_tileHeight
        self.top_maxHeight=top_maxHeight
        self.top_minHeight=top_minHeight
        self.top_tileDiff=top_tileDiff

        self.btm_tileHeight=btm_tileHeight
        self.btm_maxHeight=btm_maxHeight
        self.btm_minHeight=btm_minHeight
        self.btm_tileDiff=btm_tileDiff

    # Fetch a cave tile and set generate next one randomly
    def fetchTile(self):

        # Tile
        tile = pygame.Surface((self.tileWidth, self.landHeight))

        # Top tile
        pygame.gfxdraw.box(tile,(0,0,self.tileWidth,self.top_tileHeight), self.color)

        # Middle Opening
        pygame.gfxdraw.box(tile, (0,max(self.top_tileHeight, 0), self.tileWidth, self.landHeight - self.btm_tileHeight), cavebackground)

        # Bottom Tile
        pygame.gfxdraw.box(tile, (0,self.landHeight-self.btm_tileHeight, \
                           self.tileWidth,self.landHeight), self.color)

        # Adjust top tile height
        vec=random.randint(1, 10)
        if vec==1 or vec ==2:
            self.top_tileHeight=self.top_tileHeight+self.top_tileDiff
        elif vec==9 or vec==10:
            self.top_tileHeight=self.top_tileHeight-self.top_tileDiff
        if self.top_tileHeight<=self.top_minHeight:
            self.top_tileHeight=self.top_minHeight
        elif self.top_tileHeight>=self.top_maxHeight:
            self.top_tileHeight=self.top_maxHeight

        # Adjust top tile diff
        vec=random.randint(1, 3)
        if vec==1:
            self.top_tileDiff=self.top_tileDiff+1
            if self.top_tileDiff>5:
                self.top_tileDiff=5
        elif vec==2:
            self.top_tileDiff=self.top_tileDiff-1
            if self.top_tileDiff<1:
                self.top_tileDiff=1

        # Adjust bottom tile height
        vec=random.randint(1, 10)
        if vec==1 or vec ==2:
            self.btm_tileHeight=self.btm_tileHeight-self.btm_tileDiff
        elif vec==9 or vec==10:
            self.btm_tileHeight=self.btm_tileHeight+self.btm_tileDiff
        if self.btm_tileHeight<=self.btm_minHeight:
            self.btm_tileHeight=self.btm_minHeight
        elif self.btm_tileHeight>=self.btm_maxHeight:
            self.btm_tileHeight=self.btm_maxHeight

        # Adjust bottom tile diff
        vec=random.randint(1, 3)
        if vec==1:
            self.btm_tileDiff=self.btm_tileDiff+1
            if self.btm_tileDiff>5:
                self.btm_tileDiff=5
        elif vec==2:
            self.btm_tileDiff=self.btm_tileDiff-1
            if self.btm_tileDiff<1:
                self.btm_tileDiff=1

        # Leave enough space
        restSpace=self.landHeight-self.top_tileHeight-self.btm_tileHeight
        if restSpace<self.minSpace:
            self.top_tileHeight=self.top_tileHeight-(self.minSpace-restSpace)

        return tile

# Sprite to detect background collision
# Character collider
class BgTile(pygame.sprite.Sprite):

    # Initialize background tile
    def __init__(self, background, tiledim):

        pygame.sprite.Sprite.__init__(self)
        self.image=background.subsurface(tiledim)
        self.image.set_colorkey(cavebackground)
        self.rect=tiledim

# Sprite to detect background collision
class ExplodeTile(pygame.sprite.Sprite):

    # Initialize explode tile
    def __init__(self, image, xpos, ypos):

        pygame.sprite.Sprite.__init__(self)
        self.image=image
        self.rect=image.get_rect()
        self.rect.left=xpos
        self.rect.top=ypos
        self.xpos=xpos
        self.ypos=ypos
        self.xdelta=random.uniform(-1, 1)
        self.ydelta=random.uniform(-1, 1)
        self.rotation=random.randint(-3,3)

    # Update explode tile settings
    def update(self):
        self.xpos=self.xpos+self.xdelta
        self.ypos=self.ypos+self.ydelta
        self.rect.left=int(self.xpos)
        self.rect.top=int(self.ypos)

# Fuel tank
class FuelTank(pygame.sprite.Sprite):

    # Init fuel tankeinstance
    def __init__(self, xpos=800, ypos=300, fuelGroup=None, gameState=None):

        global _fuelImage
        pygame.sprite.Sprite.__init__(self) #call Sprite initializer
        self.image, self.rect=_fuelImage
        self.rect.top=ypos
        self.rect.left=xpos
        self.xmove=-1
        self.ymove=0
        self.fuelGroup=fuelGroup
        self.gameState=gameState
        self.fuel=1

    # Update fuel tank settings
    def update(self):

        # Adjust fuel tank position
        newpos = self.rect.move((self.xmove, self.ymove))
        self.rect=newpos

        # Remove fuel tank leaving screen
        if self.rect.left==-30:
            self.gameState.fuelCnt=self.gameState.fuelCnt-1
            self.fuelGroup.remove(self)



# Poops are dropped by Orcas
class Poop(pygame.sprite.Sprite):

    # Init fuel tankeinstance
    def __init__(self, xpos=800, ypos=300, poopGroup=None, gameState=None):

        global _rocketImage
        pygame.sprite.Sprite.__init__(self) #call Sprite initializer
        self.image, self.rect=_poopImage
        self.rect.top=ypos
        self.rect.left=xpos
        self.xmove=-1
        self.ymove=0
        self.gameState=gameState
        self.poopGroup=poopGroup

    # Update fuel tank settings
    def update(self):
        global _backgroundWidth

        # Adjust rocket position
        newpos = self.rect.move((self.xmove, self.ymove))
        self.rect=newpos

        # Remove poop leaving screen
        if self.rect.left<=0:
            self.gameState.poopCnt=self.gameState.poopCnt-1
            self.poopGroup.remove(self)

# Enemy UFO
class Orca(pygame.sprite.Sprite):

    # Init UFO instance
    def __init__(self, xpos=800, ypos=300, orcaGroup=None, gameState=None):

        global _orcaImage
        pygame.sprite.Sprite.__init__(self) #call Sprite initializer
        self.image, self.rect=_orcaImage
        self.rect.top=ypos
        self.rect.left=xpos
        self.xmove=-2
        self.ymove=0
        self.orcaGroup=orcaGroup
        self.gameState=gameState
        self.lastReverseCnt=0
        self.killCnt=25

    # Update UFO settings
    def update(self):

        # Adjust UFO position
        newpos = self.rect.move((self.xmove, self.ymove))
        self.rect=newpos

        # Remove UFO leaving screen
        if self.rect.left==-30:
            self.gameState.orcaCnt=self.gameState.orcaCnt-1
            self.orcaGroup.remove(self)

        # Increase last reverse counter
        self.lastReverseCnt=self.lastReverseCnt+1

    # Orca has collided with background
    def collidedBackground(self):

        # Revert movement direction
        if self.lastReverseCnt > 30:
            self.ymove=-self.ymove
            self.lastReverseCnt=0


# Enemy Seal
class Seal(pygame.sprite.Sprite):

    # Init Seal instance
    def __init__(self, xpos=800, ypos=400, sealGroup=None, gameState=None):

        global _sealImage
        pygame.sprite.Sprite.__init__(self) #call Sprite initializer
        self.image, self.rect=_sealImage
        self.rect.top=ypos
        self.rect.left=xpos
        self.xmove=-2
        self.ymove=0
        self.sealGroup=sealGroup
        self.gameState=gameState
        self.lastReverseCnt=0
        self.killCnt=25

    # Update UFO settings
    def update(self):

        # Adjust UFO position
        newpos = self.rect.move((self.xmove, self.ymove))
        self.rect=newpos

        # Remove UFO leaving screen
        if self.rect.left==-30:
            self.gameState.sealCnt=self.gameState.sealCnt-1
            self.sealGroup.remove(self)

        # Increase last reverse counter
        self.lastReverseCnt=self.lastReverseCnt+1

    # Orca has collided with background
    def collidedBackground(self):

        # Revert movement direction
        if self.lastReverseCnt > 30:
            self.ymove=-self.ymove
            self.lastReverseCnt=0
            

# Manages a sprite explosion
class SpriteExplosion():

    # Init sprite explosion
    def __init__(self, background=None, toExplode=None, xtiles=0, ytiles=0):

        # Set input parameter
        self.imageToExplode=toExplode.image
        self.xtiles=xtiles
        self.ytiles=ytiles

        # Calculate number of tiles for explosion
        self.tileWidth=toExplode.get_rect().width/self.xtiles
        self.tileHeigh=toExplode.get_rect().height/self.ytiles

# Player's helipenguin
class Penguin(pygame.sprite.Sprite):

    # Init helipenguin instance
    def __init__(self, xpos=50, ypos=280, state=None):

        global _penguinImage
        pygame.sprite.Sprite.__init__(self) #call Sprite initializer
        self.image, self.rect=_penguinImage
        self.imageNormal=self.image
        self.image=pygame.transform.rotate(self.image, 20)
        # self.imageForward=pygame.transform.rotate(self.image, -10)
        self.rect.top=ypos
        self.rect.left=xpos
        self.xmove=0
        self.ymove=0
        self.xdelta=2
        self.ydelta=2
        self.xpos=xpos
        self.ypos=ypos
        self.state=state
        self.area = pygame.display.get_surface().get_rect()

    # Update helipenguin settings
    def update(self):

        # Drop penguin if no fuel left
        if self.state.penguinFuel<=0:
            self.ymove=2
        

        # Adjust helipenguin position
        newpos = self.rect.move((self.xmove, self.ymove))
        if newpos.left<=0:
            newpos.left=0
        elif newpos.left+newpos.width>=800:
            newpos.left=newpos.left-self.xdelta

        self.rect = newpos

    # Helipenguin has collided with background
    def collidedBackground(self):

        self.kill()
        print ">>>> collided"

# Player's helipenguin
class StateData():

    # Initialize state data instance
    def __init__(self):

        # Orca create parameter
        self.orcaMax=1
        self.orcaCnt=0
        self.lastOrcaCnt=-200
        self.doOrcaCnt=50
        self.maxYDelta=1

        # Seal create parameter
        self.sealMax=1
        self.sealCnt=0
        self.lastSealCnt=-200
        self.doSealCnt=50
        self.maxYDelta=1

        # Poop create parameter
        self.poopMax=3
        self.poopCnt=0
        self.poopRnd=1000
        self.lastPoopCnt=0
        self.doPoop=25

        # Fuel create parameter
        self.fuelMax=1
        self.fuelCnt=0
        self.lastFuelCnt=-600
        self.doFuelCnt=500


        # Penguin state
        self.penguinFuel=5000
        self.penguinScore=0


        # Level parameter
        self.sectorColors=['skyblue', 'skyblue', 'lightblue', 'lightblue',
                          'skyblue', 'skyblue', 'lightblue', 'lightblue']
        self.sectorColorCnt=0
        self.sectorColor=self.sectorColors[self.sectorColorCnt]
        self.sector=1
        self.sectorCnt=0
        self.nextSectorCnt=2500

    # Adjusts state data to next sector
    def nextSector(self, tile):

        # Check if new sector reached
        self.sectorCnt=self.sectorCnt+1
        if self.sectorCnt >= self.nextSectorCnt:
            self.sector=self.sector+1
            self.sectorCnt=0

            # Set new cave color for sector
            self.sectorColorCnt=self.sectorColorCnt+1
            if self.sectorColorCnt >= len(self.sectorColors):
                self.sectorColorCnt=0
            self.sectorColor=self.sectorColors[self.sectorColorCnt]

            # Increase game difficulty
            if self.sector%4 == 0:
                self.poopMax=self.poopMax+1
            elif self.sector%3 == 0:
                self.orcaMax=self.orcaMax+1

            if tile.minSpace>100:
                tile.minSpace=tile.minSpace-25

            if self.sector == 3 or self.sector == 5:
                self.maxYDelta=self.maxYDelta+1


#############################################################
### Main functions
#############################################################

# Process game entry loop
def doEntryLoop(screen,background):

    global _backgroundWidth
    global _titleImage
    global _highScore
    global _bgImage


    # Draw static background
    tile=CaveTile()
    tile.topSpace=0
    for x in range(_backgroundWidth):
        cave=tile.fetchTile()
        background.blit(cave, (x,tile.topSpace))
    addText("Highscore: " + str(_highScore), background, 310, 300, \
            THECOLORS['lightgreen'], THECOLORS['black'], 20, True)
    addText("[SPACE] to continue", background, 310, 560, \
            THECOLORS['black'], THECOLORS['skyblue'], 20, True)

    background.blit(_titleImage[0], (130,50))
    screen.blit(background, (0,0))
    pygame.display.flip()

    doLoop=True
    clock=pygame.time.Clock()
    while doLoop:
        clock.tick(100) # fps

        # Catch input event
        for event in pygame.event.get():
            if event.type == QUIT:
                sys.exit(0)
            elif event.type == KEYDOWN:
                if event.key == 32:
                    doLoop=False


    tile.topSpace=40
    for x in range(_backgroundWidth):
        cave=tile.fetchTile()
        background.blit(cave, (x,tile.topSpace))
    screen.blit(background, (0,0))
    pygame.display.flip()

    return tile

# Process main game loop
def doMainLoop(screen,background, tile):

    global _heliSound
    global _fuelSound
    global _fuelDownSound
    global _enemyKillSound
    global _orcaKillImage
    global _bgImage

    _heliSound.play()


    # Game state data
    state=StateData()

    # Create helipenguin
    penguin=Penguin(275, 280, state)
    

    # Create sprite groups
    penguinGroup = pygame.sprite.RenderPlain((penguin))
    orcaGroup = pygame.sprite.RenderPlain()
    sealGroup = pygame.sprite.RenderPlain()
    killedGroup = pygame.sprite.RenderPlain()
    fuelGroup = pygame.sprite.RenderPlain()
    poopGroup = pygame.sprite.RenderPlain()

    # Main Loop
    clock=pygame.time.Clock()
    delta=1
    doContinue=True
    topSpace=40
    fuelReductionCnt=0
    while doContinue:
        clock.tick(100) # fps
        
        # Catch input event
        for event in pygame.event.get():
            if event.type == QUIT:
                return
            elif event.type == KEYDOWN:
                if event.key == 273: # up
                    penguin.ymove=-penguin.ydelta
                if event.key == 274: # down
                    penguin.ymove=penguin.ydelta
                if event.key == K_ESCAPE: # esc
                    quit();
            elif event.type == KEYUP:
                penguin.xmove=0
                penguin.ymove=0
                
                

        # Scroll landsape
        tile.color=THECOLORS[state.sectorColor]
        newBackground=scrollLandscape(background, delta, tile, topSpace)
        background.blit(_bgImage[0], (0,0))
        background.blit(newBackground, (0,0))

        # Add objects to sprite groups
        addOrca(tile, orcaGroup, state, topSpace)
        addSeal(tile, orcaGroup, state, topSpace)
        addPoop(orcaGroup, poopGroup, state)
        addFuel(tile, fuelGroup, state, topSpace)

        # Check object collisions
        checkOrcaCollisions(orcaGroup, killedGroup, state, background)
        checkSealCollisions(orcaGroup, killedGroup, state, background)
        doContinue=checkBackgroundCollision(background, penguin, penguinGroup)
        checkPenguinCollisions(penguin, orcaGroup, fuelGroup, sealGroup, \
                              poopGroup, state)

        # Update game state data
        if state.penguinFuel<0:
            state.penguin=0
        updatePenguinInfo(background, state)

        # Reduce penguin fuel
        if fuelReductionCnt>10 and state.penguinFuel>0:
            state.penguinFuel=state.penguinFuel-1
            fuelReductionCnt=0
            state.penguinScore=state.penguinScore+1

        

        # Update sprites
        penguinGroup.update()
        poopGroup.update()
        orcaGroup.update()
        sealGroup.update()
        killedGroup.update()
        fuelGroup.update()

        # Update screen
        screen.blit(background, (0,0))
        fuelGroup.draw(screen)
        penguinGroup.draw(screen)
        poopGroup.draw(screen)
        orcaGroup.draw(screen)
        sealGroup.draw(screen)
        killedGroup.draw(screen)
        pygame.display.flip()

        # Change to next sectory
        state.nextSector(tile)

    # Penguin explodes
    explodeGroup=explodeSprite(penguin,10, 4)
    penguinGroup.remove(penguin)

    global _penguinKillSound
    cnt=0
    _penguinKillSound.play()
    while cnt<100:

        clock.tick(100) # fps
        cnt=cnt+1

        # Update explosion sprites
        explodeGroup.update()

        # Update screen
        screen.blit(background, (0,0))
        fuelGroup.draw(screen)
        explodeGroup.draw(screen)
        poopGroup.draw(screen)
        sealGroup.draw(screen)
        orcaGroup.draw(screen)
        killedGroup.draw(screen)
        pygame.display.flip()
        pygame.time.wait(25)

    # New highscore?
    global _highScore
    if state.penguinScore > _highScore:
        _highScore=state.penguinScore
        addText("New Highscore!", background, 270, 330, \
                THECOLORS['lightgreen'], (0,0,0), 30, True)
    # Show GAME OVER
    addText("GAME OVER", background, 270, 270, \
            THECOLORS['lightgreen'], cavebackground, 50, True)
    addText("[SPACE] to continue", background, 310, 560, \
            (0,0,0), THECOLORS[state.sectorColor], 20, True)
    screen.fill ((52, 73, 94))
    screen.blit(background, (0,0))
    pygame.display.flip()
    doLoop=True
    while doLoop:
        clock.tick(100) # fps

        # Catch input event
        for event in pygame.event.get():
            if event.type == QUIT:
                sys.exit(0)
            elif event.type == KEYDOWN:
                if event.key == 32:
                    doLoop=False


# Entrypoint
def main():

    
    # Main window dimension
    global backgroundWidth
    mainWindowWidth=_backgroundWidth
    mainWindowHeight=_backgroundHeight

    # Initialize window
    screen=initWindow(mainWindowWidth, mainWindowHeight)

    # Load images for sprites
    loadImages()

    # Load sounds
    loadSounds()

    # Create empty background
    background=createEmptySurface(screen, screen.get_size())

    while True:
        # Enter entry loop
        caveTile=doEntryLoop(screen, background)

        # Enter main loop
        doMainLoop(screen, background, caveTile)

#this calls the 'main' function when this script is executed
if __name__ == '__main__': main()
