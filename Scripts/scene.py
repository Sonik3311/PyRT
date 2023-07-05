import struct
from dataclasses import dataclass

import numpy as np
from numpy.random import rand

from objects import *
from pyrt import PYRTManager
from util import *

class Scene:
    backup_material = Material(color=(1, 1, 1), specularColor=(1, 1, 1), roughness=0, metalness=0, emissive=0, refractive=0)
    backup_rotation = Quaternion(0, 0, 0, 1)
    backup_position = Vector3(0, 0, 0)

    groups = {}
    objects = {'spheres':[], 'cubes':[], 'cylinders':[], 'quads':[]}
    materials = {}

    def __init__(self):
        self.groups = {}
        self.objects = {'spheres':[], 'cubes':[], 'cylinders':[], 'quads':[]}
        self.materials = {}
        self.PYRTManager = PYRTManager(shape_handler=lambda *args, **kwargs: self.shapeCallback(*args, **kwargs),
                                       group_handler=lambda *args, **kwargs: self.groupCallback(*args, **kwargs),
                                       material_handler=lambda *args, **kwargs: self.materialCallback(*args, **kwargs)
        )
        

    def shapeCallback(self, line, parent, type, position=VectorN((0, 0, 0)), 
                      rotation=VectorN((0, 0, 0)), size=None, material=backup_material, **kwargs):

        rotation = Quaternion.from_euler(*rotation)
        parent = self.groups[parent[len(parent)-1]] if len(parent) > 0 else None
        position = Vector3(*position)
        vertices = []

        match type:
            case 'cube':
                size = Vector3(*size) if size else Vector3(1, 1, 1)
                vertices = [position]
            case 'sphere':
                size = size or 1.0
                vertices = [position]
            case 'cylinder':
                top_pos = kwargs['topPosition'] if 'topPosition' in kwargs else (0, 0, 1)
                btm_pos = kwargs['bottomPosition'] if 'bottomPosition' in kwargs else (0, 0, -1)
                vertices = [
                    Vector3(*top_pos),
                    Vector3(*btm_pos),
                ]
                size = size or 1.0
            case "quad":
                BLpos = kwargs['bottomLeft'] if 'bottomLeft' in kwargs else (0,-1,-1)
                BRpos = kwargs['bottomRight'] if 'bottomRight' in kwargs else (0,-1, 1)
                TRpos = kwargs['topRight'] if 'topRight' in kwargs else (0, 1, 1)
                TLpos = kwargs['topLeft'] if 'topLeft' in kwargs else (0, 1,-1)       
                vertices = [
                    Vector3(*BLpos),
                    Vector3(*BRpos),
                    Vector3(*TRpos),
                    Vector3(*TLpos),
                ]
                size = None
            case _:
                raise NotImplementedError
        
        geometry = Geometry(
            size=size,
            type=type,
            material=material,
            vertices=vertices,
            rotation=rotation,
            group=parent
        )
        self.objects[type+'s'].append(geometry)

    def groupCallback(self, line, parent, name, position=VectorN((0, 0, 0)), rotation=VectorN((0, 0, 0)), material=None):
        position = Vector3(position[0], position[1], position[2])
        rotation = Quaternion.from_euler(rotation[0], rotation[1], rotation[2])

        new_group = Group(position=position, rotation=rotation, parent=parent)
        print(rotation)
        self.groups[name] = new_group
        
        return new_group

    def materialCallback(self, line, parent, name, 
                         color=backup_material.color, 
                         specularColor=backup_material.specularColor, 
                         roughness=backup_material.roughness, 
                         metalness=backup_material.metalness, 
                         emissive=backup_material.emissive, 
                         refractive=backup_material.refractive):
        newMaterial = Material(color, specularColor, roughness, metalness, emissive, refractive)
        self.materials[name] = newMaterial
        return newMaterial

    def importFromFile(self, path):
        self.groups = {}
        self.objects = {'spheres':[], 'cubes':[], 'cylinders':[], 'quads':[]}
        self.materials = {}

        self.PYRTManager.readFile(path)

        self.pack_data()

    def get_object_count(self, count_category=None, in_pixels=False):
        lengths = {"spheres": 2, "cubes": 3, "cylinders": 3, "quads": 4}
        objects = self.objects if count_category is None else {count_category: self.objects[count_category]}

        return sum([len(objects[category]) * lengths[category] if in_pixels else len(objects[category]) for category in objects])
    
    def get_material_pixel_count(self):
         return sum([len(self.objects[category]) * 3 for category in self.objects])
    
    def pack_data(self):
        dataGeometry = b''
        dataMaterial = b''

        pixelDataMaterial = lambda object: (*object.material.color, 0,
                                            *object.material.specularColor, 0,
                                            object.material.roughness, object.material.metalness, object.material.emissive, object.material.refractive)

        pixelDataGeometry = {
            #                            RED                    GREEN                  BLUE                   ALPHA
            'spheres':   lambda object: (object.vertices[0].x,  object.vertices[0].y,  object.vertices[0].z,  object.size,          # 1
                                         object.rotation.x,     object.rotation.y,     object.rotation.z,     object.rotation.w),   # 2
             

            'cubes':     lambda object: (object.vertices[0].x,  object.vertices[0].y,  object.vertices[0].z,  0,                    # 1
                                         object.size.x,         object.size.y,         object.size.z,         0,                    # 2
                                         object.rotation.x,     object.rotation.y,     object.rotation.z,     object.rotation.w),   # 3
 

            'cylinders': lambda object: (object.vertices[0].x,  object.vertices[0].y,  object.vertices[0].z,  0,                    # 1
                                         object.vertices[1].x,  object.vertices[1].y,  object.vertices[1].z,  object.size,          # 2
                                         object.rotation.x,     object.rotation.y,     object.rotation.z,     object.rotation.w),   # 3
             

            'quads':     lambda object: (object.vertices[0].x,  object.vertices[0].y,  object.vertices[0].z,  object.vertices[3].x, # 1
                                         object.vertices[1].x,  object.vertices[1].y,  object.vertices[1].z,  object.vertices[3].y, # 2
                                         object.vertices[2].x,  object.vertices[2].y,  object.vertices[2].z,  object.vertices[3].z, # 3
                                         object.rotation.x,     object.rotation.y,     object.rotation.z,     object.rotation.w),   # 4
        }
        
        for objectType in self.objects:

            if objectType in pixelDataGeometry and len(self.objects[objectType]) > 0: 
                objects = self.objects[objectType]
                format_string = f"{len(pixelDataGeometry[objectType](objects[0]))}f"

                for obj in objects:
                    dataGeometry += struct.pack(format_string, *pixelDataGeometry[objectType](obj))
                    dataMaterial += struct.pack('12f', *pixelDataMaterial(obj))

        return dataGeometry, dataMaterial