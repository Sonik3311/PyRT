from dataclasses import dataclass, field
from typing import ClassVar

from util import Quaternion, Vector3, Transform


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

        if parent != None:
            self.rotation = self.rotation * parent.rotation

            #rotate
            v = Quaternion(x=self.position.x, y=self.position.y, z=self.position.z, w=0)
            pointQ = (parent.rotation.hamilton(v)).hamilton(parent.rotation.inverted())
            point = Vector3(pointQ.x, pointQ.y, pointQ.z)
            #translate
            point += parent.position
            self.position = point
            

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
    
        g = self.group
        self.group = None
        self.assignGroup(g)

    def assignGroup(self, group):
        # for in-app editing
        """
        if self.group != None: # convert to world space if in local space
            #if self.type.lower() in ('cube', 'sphere'):
            #    self.rotation = self.group.rotation * self.rotation
            for i in range(len(self.vertices)):
                self.vertices[i] = (self.vertices[i] - self.group.position)
                rotated = self.group.rotation.inverted() * Quaternion(self.vertices[i].x, self.vertices[i].y, self.vertices[i].z, 0) * self.group.rotation
                self.vertices[i].x = rotated.x
                self.vertices[i].y = rotated.y
                self.vertices[i].z = rotated.z
        """

        # convert to local space of the new group if not world 
        if group != None: 
            medianVecGeometry = sum(self.vertices) / len(self.vertices)
            for i,vertex in enumerate(self.vertices):
                #local
                pivot = vertex-medianVecGeometry
                v = Quaternion(pivot.x, pivot.y, pivot.z, w=0)
                pointQ = (self.rotation.hamilton(v)).hamilton(self.rotation.inverted())
                point = Vector3(pointQ.x, pointQ.y, pointQ.z) + medianVecGeometry
                #global
                v = Quaternion(point.x, point.y, point.z, w=0)
                pointQ = (group.rotation.hamilton(v)).hamilton(group.rotation.inverted())
                point = Vector3(pointQ.x, pointQ.y, pointQ.z) 
                #translate
                point += group.position
                self.vertices[i] = point

            self.rotation = self.rotation.hamilton(group.rotation)

            
        self.group = group