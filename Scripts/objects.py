from dataclasses import dataclass, field
from typing import ClassVar

from util import Quaternion, Vector3


@dataclass
class Material:
    color         : tuple[float, float, float]
    specularColor : tuple[float, float, float]
    
    roughness  : float
    metalness  : float
    emissive   : float
    refractive : float

@dataclass
class Group:
    type         : ClassVar[str] = "Group"
    position     : Vector3
    rotation     : Quaternion
    parent       : 'Group | None'

    def __post_init__(self):
        p = self.parent
        self.parent = None
        self.assignParent(p)

    def assignParent(self, parent):
        #if self.parent != None: # convert to world space if in local space
        #    self.rotation = self.parent.rotation * self.rotation
        #    #for i in range(len(self.vertices)):
        #    self.position = (self.position - self.parent.position)
        #    rotated = self.parent.rotation.inverted() * Quaternion(self.position.x, self.position.y, self.position.z, 0) * self.parent.rotation
        #    self.position.x = rotated.x
        #    self.position.y = rotated.y
        #    self.position.z = rotated.z
                
        
        if parent != None:      # convert to local space of the new group if not world
            self.rotation = self.rotation * parent.rotation
            self.position = self.position + parent.position
            rotated = parent.rotation * Quaternion(x=self.position.x, y=self.position.y, z=self.position.z, w=0) * parent.rotation.inverted()
            self.position.x = rotated.x
            self.position.y = rotated.y
            self.position.z = rotated.z
        self.parent = parent

@dataclass
class Geometry:
    size     : float | int | Vector3
    type     : str
    material : Material
    vertices : list[Vector3]
    rotation : Quaternion
    group    : Group = None

    def __post_init__(self):
        match self.type.lower():
            case "sphere":
                assert len(self.vertices) == 1, "Sphere must have exactly 1 vertex."
                assert isinstance(self.size, float | int), "Size of a sphere must be a number"
            case "cube":
                assert len(self.vertices) == 1, "Cube must have exactly 1 vertex."
                assert isinstance(self.size, Vector3), "Size of a cube must be a Vector"
            case "cylinder":
                assert len(self.vertices) == 2, "Cylinder must have exactly 2 vertices."
                assert isinstance(self.size, float | int), "Size of a cylinder must be a number"
            case "quad":
                assert len(self.vertices) == 4, "Quad must have exactly 4 vertices."
                #assert not isinstance(self.size, float | int), "Size of a sphere must be a number"
        g = self.group
        self.group = None
        self.assignGroup(g)

    def assignGroup(self, group):
        #if self.group != None: # convert to world space if in local space
        #    #if self.type.lower() in ('cube', 'sphere'):
        #    #    self.rotation = self.group.rotation * self.rotation
        #    for i in range(len(self.vertices)):
        #        self.vertices[i] = (self.vertices[i] - self.group.position)
        #        rotated = self.group.rotation.inverted() * Quaternion(self.vertices[i].x, self.vertices[i].y, self.vertices[i].z, 0) * self.group.rotation
        #        self.vertices[i].x = rotated.x
        #        self.vertices[i].y = rotated.y
        #        self.vertices[i].z = rotated.z
                
        if group != None:      # convert to local space of the new group if not world
            medianVec = Vector3(0, 0, 0)
            for i in range(len(self.vertices)):
                # globat transform and compute local pivot
                rotated = group.rotation * Quaternion(x=self.vertices[i].x, y=self.vertices[i].y, z=self.vertices[i].z, w=0) * group.rotation.inverted()
                newPoint = Vector3(rotated.x, rotated.y, rotated.z) + group.position
                self.vertices[i] = newPoint
                medianVec += self.vertices[i]
            
            medianVec /= len(self.vertices)
            
            for i in range(len(self.vertices)):
                # apply local rotation
                rotated = self.rotation * Quaternion(self.vertices[i].x - medianVec.x, y=self.vertices[i].y - medianVec.y, z=self.vertices[i].z - medianVec.z, w=0) * self.rotation.inverted()
                newPoint = Vector3(rotated.x, rotated.y, rotated.z) + medianVec
                self.vertices[i] = newPoint
            
            
        self.group = group