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
            self.rotation = parent.rotation.hamilton(self.rotation)

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
    
    def rotatePointAround(self, point, pivot, quat):
        local_v = point - pivot
        v_q = Quaternion(x = local_v.x, y = local_v.y, z = local_v.z, w = 0)
        rotated_v_q = (quat.hamilton(v_q)).hamilton(quat.inverted())
        rotated_local_v = Vector3(x = rotated_v_q.x, y = rotated_v_q.y, z = rotated_v_q.z)
        rotated_v = rotated_local_v + pivot
        return rotated_v
            

    def assignGroup(self, group):
        if group != None: 
            medianVecGeometry = sum(self.vertices) / len(self.vertices)
            for i,vertex in enumerate(self.vertices):
                rotated_v = self.rotatePointAround(vertex, medianVecGeometry, self.rotation)
                rotated_local_v = self.rotatePointAround(Vector3(rotated_v.x, rotated_v.y, rotated_v.z), Vector3(0,0,0), group.rotation)
                
                v = Vector3(rotated_local_v.x, rotated_local_v.y, rotated_local_v.z)
                point = v + group.position
                self.vertices[i] = point
            self.rotation = group.rotation.hamilton(self.rotation)  
        self.group = group