import numpy as np
import struct

class Scene:
    objects = {
        "spheres": [],
        "cubes": [],
        "cylinders": [],
    }

    def getObjectCount(self, countCategory=None, inPixels=False):
        lengths = {"spheres": 1, "cubes": 2, "cylinders": 2}
        objects = self.objects if countCategory is None else {countCategory: self.objects[countCategory]}

        return sum([len(objects[category]) * lengths[category] if inPixels else len(objects[category]) for category in objects])
    
    def getMaterialPixelCount( self ):
         return sum([len(self.objects[category]) * 3 for category in self.objects])

    def addSphere( self, pos,radius,  color,specColor,RME):
        self.objects["spheres"].append([pos,radius, color,specColor,RME])
    
    def addCube( self, pos,size, color,specColor,RME):
        self.objects["cubes"].append([pos,size, color,specColor,RME])
    
    def addCylinder( self, posA,posB,radius, color,specColor,RME):
        self.objects["cylinders"].append([posA,posB,radius, color,specColor,RME])
    
    def packObjects( self ):
        dataGeometry = b''
        dataMaterial = b''
        shapes = {
            "spheres":   lambda object: (object[0][0], object[0][1], object[0][2], object[1]),

            "cubes":     lambda object: (object[0][0], object[0][1], object[0][2], 0, 
                                         object[1][0], object[1][1], object[1][2], 0),

            "cylinders": lambda object: (object[0][0], object[0][1], object[0][2], object[2], 
                                         object[1][0], object[1][1], object[1][2], 0)
        }
        material = lambda material: (object[-3:-2][0][0], object[-3:-2][0][1], object[-3:-2][0][2], 0, # color
                                     object[-2:-1][0][0], object[-2:-1][0][1], object[-2:-1][0][2], 0, # specular color
                                     object[-1:][0][0],   object[-1:][0][1],   object[-1:][0][2]  , 0, # roughness metalness emissive
        )
        for category in self.objects:
            if category in shapes:
                format_string = f"{len(shapes[category](self.objects[category][0]))}f"
                for object in self.objects[category]:
                    dataGeometry += struct.pack(format_string, *shapes[category](object))
                    dataMaterial += struct.pack("12f", *material(object))

        return dataGeometry, dataMaterial
