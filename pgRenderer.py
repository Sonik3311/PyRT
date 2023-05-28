import pygame as pg

class PygameRenderer():
    def __init__(self, resolution):
        self.resolution = resolution
        
        pg.init()
        self.surface = pg.Surface(self.resolution, pg.SRCALPHA)
    
    @staticmethod
    def invertColor(color):
        return (255-color[0], 255-color[1], 255-color[2], color[3]) 
    
    def drawRectangle(self, x,y,sizeX,sizeY, color):
        pg.draw.rect(self.surface, color, (x,y, sizeX,sizeY))
        pg.draw.rect(self.surface, self.invertColor(color), (x,y, sizeX,sizeY), 2)
    
    def render(self):
        self.surface.fill((0,0,0,0))
        self.drawRectangle(0, self.resolution[1]-25, self.resolution[0], 25, (60,50,50,255))
    