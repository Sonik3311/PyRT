import struct

import numpy as np

from PYRTParser import PYRTParser


class Scene:
    objects = {
        "spheres": [],
        "cubes": [],
        "cylinders": [],
        "quads" : [],
    }

    PYRTParser = PYRTParser()

    def getObjectCount(self, countCategory=None, inPixels=False):
        lengths = {"spheres": 1, "cubes": 2, "cylinders": 2, "quads": 3}
        objects = self.objects if countCategory is None else {countCategory: self.objects[countCategory]}

        return sum([len(objects[category]) * lengths[category] if inPixels else len(objects[category]) for category in objects])
    
    def getMaterialPixelCount( self ):
         return sum([len(self.objects[category]) * 3 for category in self.objects])

    def addSphere( self, posr,  color,specColor,RMEG):
        self.objects["spheres"].append([posr[0:3], posr[3], color,specColor,RMEG])
    
    def addCube( self, pos,size, color,specColor,RMEG):
        self.objects["cubes"].append([pos,size, color,specColor,RMEG])
    
    def addCylinder( self, posA,posBradius, color,specColor,RMEG):
        self.objects["cylinders"].append([posA,posBradius[0:3],posBradius[3], color,specColor,RMEG])
    
    def addQuad( self, posBL,posBR,posTR,posTL, color,specColor,RMEG):
        self.objects["quads"].append([posBL,posBR,posTR,posTL, color,specColor,RMEG])


    def importFromFile(self,filePath):
        self.objects = {
            "spheres": [],
            "cubes": [],
            "cylinders": [],
            "quads" : [],
        }
        tokens = self.PYRTParser.tokenize(filePath)
        for token in tokens:
            func = eval(f"self.add{token[0].capitalize()}")
            func(*token[1])

    
    def packObjects( self ):
        dataGeometry = b''
        dataMaterial = b''
        shapes = {
            "spheres":   lambda object: (object[0][0], object[0][1], object[0][2], object[1]),

            "cubes":     lambda object: (object[0][0], object[0][1], object[0][2], 0, 
                                         object[1][0], object[1][1], object[1][2], 0),

            "cylinders": lambda object: (object[0][0], object[0][1], object[0][2], object[2], 
                                         object[1][0], object[1][1], object[1][2], 0),

            "quads":     lambda object: (object[0][0], object[0][1], object[0][2], object[3][0],
                                         object[1][0], object[1][1], object[1][2], object[3][1],
                                         object[2][0], object[2][1], object[2][2], object[3][2])
        }
        material = lambda material: (object[-3:-2][0][0], object[-3:-2][0][1], object[-3:-2][0][2], 0, # color
                                     object[-2:-1][0][0], object[-2:-1][0][1], object[-2:-1][0][2], 0, # specular color
                                     object[-1:][0][0],   object[-1:][0][1],   object[-1:][0][2]  , object[-1:][0][3], # roughness metalness emissive
        )
        for category in self.objects:
            if category in shapes and len(self.objects[category]) > 0:
                format_string = f"{len(shapes[category](self.objects[category][0]))}f"
                for object in self.objects[category]:
                    dataGeometry += struct.pack(format_string, *shapes[category](object))
                    dataMaterial += struct.pack("12f", *material(object))

        return dataGeometry, dataMaterial
