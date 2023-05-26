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

    def addSphere( self, pos, radius ):
        self.objects["spheres"].append([pos,radius])
    
    def addCube( self, pos, size ):
        self.objects["cubes"].append([pos,size])
    
    def addCylinder( self, posA, posB, radius ):
        self.objects["cylinders"].append([posA,posB,radius])
    
    def packObjects( self ):
        dataGeometry = b''
        for category in self.objects:
            for object in self.objects[category]:
                match category:
                    case "spheres":
                        #print(object)
                        posx,posy,posz = object[0]
                        radius         = object[1]
                        dataGeometry += (               # Pixel
                              struct.pack("f", posx)    # R
                            + struct.pack("f", posy)    # G
                            + struct.pack("f", posz)    # B
                            + struct.pack("f", radius)  # A
                        )
                    case "cubes":
                        posx,posy,posz    = object[0]
                        sizex,sizey,sizez = object[1]
                        dataGeometry += (               # Pixel
                              struct.pack("f", posx)    # R
                            + struct.pack("f", posy)    # G
                            + struct.pack("f", posz)    # B
                            + struct.pack("f", 0)       # A (filler)
                            + struct.pack("f", sizex)   # R
                            + struct.pack("f", sizey)   # G
                            + struct.pack("f", sizez)   # B
                            + struct.pack("f", 0)       # A (filler)
                        )

                    case "cylinders":
                        posAx,posAy,posAz = object[0]
                        posBx,posBy,posBz = object[1]
                        radius            = object[2]
                        dataGeometry += (               # Pixel
                              struct.pack("f", posAx)    # R
                            + struct.pack("f", posAy)    # G
                            + struct.pack("f", posAz)    # B
                            + struct.pack("f", radius)       # A (filler)
                            + struct.pack("f", posBx)   # R
                            + struct.pack("f", posBy)   # G
                            + struct.pack("f", posBz)   # B
                            + struct.pack("f", 0)       # A (filler)
                        )

        
        return dataGeometry
