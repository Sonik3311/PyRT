from dataclasses import dataclass
from typing import ClassVar
from math import sqrt, acos, sin, cos
from typing import Iterable

class VectorN(tuple):
    def __new__(cls, values: Iterable[float]):
        return super(VectorN, cls).__new__(cls, values)

    def __add__(self, other: 'VectorN | float | int'):
        match other:
            case VectorN():
                assert len(self) == len(other)
                return VectorN((i + j for i, j in zip(self, other)))
            case float() | int():
                return VectorN((i + other for i in self))
            case _:
                raise ValueError

    def __sub__(self, other: 'VectorN | float | int'):
        match other:
            case VectorN():
                assert len(self) == len(other)
                return VectorN((i - j for i, j in zip(self, other)))
            case float() | int():
                return VectorN((i - other for i in self))
            case _:
                raise ValueError

    def __mul__(self, other: 'VectorN | float | int'):
        match other:
            case VectorN():
                assert len(self) == len(other)
                return VectorN((i * j for i, j in zip(self, other)))
            case float() | int():
                return VectorN((i * other for i in self))
            case _:
                raise ValueError

    def __truediv__(self, other: 'VectorN | float | int'):
        match other:
            case VectorN():
                assert len(self) == len(other)
                return VectorN((i / j for i, j in zip(self, other)))
            case float() | int():
                return VectorN((i / other for i in self))
            case _:
                raise ValueError

    def __neg__(self):
        return VectorN((-i for i in self))

@dataclass
class Vector3:
    ZERO: ClassVar['Vector3']
    FORWARD: ClassVar['Vector3']
    BACKWARD: ClassVar['Vector3']
    RIGHT: ClassVar['Vector3']
    LEFT: ClassVar['Vector3']
    UP: ClassVar['Vector3']
    DOWN: ClassVar['Vector3']

    x: float
    y: float
    z: float

    def __add__(self, other: 'Vector3 | float | int'):
        match other:
            case Vector3():
                return Vector3(self.x + other.x, self.y + other.y, self.z + other.z)
            case float() | int():
                return Vector3(self.x + other, self.y + other, self.z + other)
            case _:
                raise ValueError
    
    def __radd__(self, other):
        if other == 0:
            return self
        else:
            return self.__add__(other)

    def __sub__(self, other: 'Vector3 | float | int'):
        match other:
            case Vector3():
                return Vector3(self.x - other.x, self.y - other.y, self.z - other.z)
            case float() | int():
                return Vector3(self.x - other, self.y - other, self.z - other)
            case _:
                raise ValueError

    def __mul__(self, other: 'Quaternion | Vector3 | float | int'):
        match other:
            case Quaternion():
                u = Vector3(other.x, other.y, other.z)
                v = Vector3(self.x, self.y, self.z)
                s = other.w
                vprime = u * u.dot(v) * 2.0 + v * (s*s - u.dot(u)) + u.cross(v) * 2.0 * s
                return vprime
            case Vector3():
                return Vector3(self.x * other.x, self.y * other.y, self.z * other.z)
            case float() | int():
                return Vector3(self.x * other, self.y * other, self.z * other)
            case _:
                raise ValueError

    def __truediv__(self, other: 'Vector3 | float | int'):
        match other:
            case Vector3():
                return Vector3(self.x / other.x, self.y / other.y, self.z / other.z)
            case float() | int():
                return Vector3(self.x / other, self.y / other, self.z / other)
            case _:
                raise ValueError

    def __neg__(self):
        return Vector3(-self.x, -self.y, -self.z)

    def length2(self):
        return self.x ** 2 + self.y ** 2 + self.z ** 2

    def length(self):
        return sqrt(self.length2())

    def normalize(self):
        il = 1.0 / self.length()
        self.x *= il
        self.y *= il
        self.z *= il

    def normalized(self):
        return self / self.length()

    def dot(self, other: 'Vector3'):
        return self.x * other.x + self.y * other.y + self.z * other.z

    def cross(self, other: 'Vector3'):
        return Vector3(self.y * other.z - self.z * other.y, self.z * other.x - self.x * other.z, self.x * other.y - self.y * other.x)

    def rotate(self, axis: 'Vector3', angle: float):
        v = self.rotated(axis, angle)
        self.x = v.x
        self.y = v.y
        self.z = v.z

    def rotated(self, axis: 'Vector3', angle: float):
        c = cos(angle)
        s = sin(angle)

        return self * c + axis.cross(self) * s + axis * self.dot(axis) * (1 - c)
    
    def copy(self):
        return Vector3(self.x, self.y, self.z)


Vector3.ZERO = Vector3(0.0, 0.0, 0.0)
Vector3.FORWARD = Vector3(1.0, 0.0, 0.0)
Vector3.BACKWARD = Vector3(-1.0, 0.0, 0.0)
Vector3.RIGHT = Vector3(0.0, 0.0, 1.0)
Vector3.LEFT = Vector3(0.0, 0.0, -1.0)
Vector3.UP = Vector3(0.0, 1.0, 0.0)
Vector3.DOWN = Vector3(0.0, -1.0, 0.0)

@dataclass
class Transform:
    x: Vector3
    y: Vector3
    z: Vector3
    origin: Vector3

    def copy(self):
        return Transform(self.x.copy(), self.y.copy(), self.z.copy(), self.origin.copy())
    def scale(self, v: float):
        self.scale_basis(v)
        self.origin *= v

    def scaled(self, v: float):
        t = self.copy()
        t.scale(v)
        return t

    def scale_basis(self, v: float):
        self.x *= v
        self.y *= v
        self.z *= v

    def scaled_basis(self, v: float):
        t = self.copy()
        t.scale_basis(v)
        return t

    def translate(self, v: Vector3):
        self.origin += self._basis_xform(v)

    def translated(self, v: Vector3):
        t = self.copy()
        t.translate(v)
        return t

    def orthonormalize(self):
        x = self.x
        y = self.y
        z = self.z

        x.normalize()
        y = y - x * x.dot(y)
        y.normalize()
        z = z - x * x.dot(z) - y * y.dot(z)
        z.normalize()

    def orthonormalized(self):
        t = self.copy()
        t.orthonormalize()
        return t

    def orthogonalize(self):
        s = self.x.length()
        self.orthonormalize()
        self.scale_basis(s)

    def orthogonalized(self):
        t = self.copy()
        t.orthogonalize()
        return t

    def invert(self):
        x = self.x
        y = self.y
        z = self.z

        co0 = y.y * z.z - y.z * z.y
        co1 = y.z * z.x - y.x * z.z
        co2 = y.z * z.y - y.y * z.x

        s = 1.0 / (x.x * co0 + x.y * co1 + x.z * co2)

        self.x.x = co0 * s
        self.x.y = (x.z * z.y - x.y * z.z) * s
        self.x.z = (x.y * y.z - x.z * y.y) * s

        self.y.x = co1 * s
        self.y.y = (x.x * z.z - x.z * z.x) * s
        self.y.z = (x.z * y.z - x.x * y.z) * s

        self.z.x = co2 * s
        self.z.y = (x.y * z.x - x.x * z.y) * s
        self.z.z = (x.x * y.y - x.y * y.x) * s

    def inverted(self):
        t = self.copy()
        t.invert()
        return t

    def _get_basis_determinant(self):
        return self.x.x * (self.y.y * self.z.z - self.y.z * self.z.y) - \
                self.x.y * (self.y.x * self.z.z - self.y.z * self.z.x) + \
                self.x.z * (self.y.x * self.z.y - self.y.y * self.z.x)

    def _basis_xform(self, v: Vector3):
        return Vector3(
            self.x.dot(v),
            self.y.dot(v),
            self.z.dot(v)
        )

    #def _basis_xform_inv(self, v: Vector3):
    #    return Vector3(
    #        self.x.x * v.x + self.y.x * v.y + self.z.x * v.z,
    #        self.x.y * v.x + self.y.y * v.y + self.z.y * v.z,
    #        self.x.z * v.x + self.y.z * v.y + self.z.z * v.z
    #    )

    def xform(self, v: 'Vector3 | Transform'):
        match v:
            case Transform():
                return Transform(
                    self._basis_xform(v.x),
                    self._basis_xform(v.y),
                    self._basis_xform(v.z),
                    self.xform(v.origin)
                )
            case Vector3():
                return self.origin + self._basis_xform(v)
            case _:
                raise ValueError

    def __mul__(self, other):
        return self.xform(other)

    def __invert__(self):
        return self.inverted()

    def xform_inv(self, v: 'Vector3 | Transform'):
        return self.inverted().xform(v)


CMP_EPSILON = 0.0001
@dataclass
class Quaternion:
    x: float
    y: float
    z: float
    w: float

    @staticmethod
    def shortest_arc(v0: Vector3, v1: Vector3):
        c = v0.cross(v1)
        d = v0.dot(v1)

        if d < -1.0 + CMP_EPSILON:
            return Quaternion(
                0, 1, 0, 0
            )

        s = sqrt((d + 1.0) * 2.0)
        rs = 1.0 / s
        return Quaternion(
            c.x * rs,
            c.y * rs,
            c.z * rs,
            s * 0.5
        )

    @staticmethod
    def from_axis_angle(axis: Vector3, angle: float):
        d = axis.length()
        if d == 0:
            return Quaternion(0.0, 0.0, 0.0, 0.0)

        sin_angle = sin(angle * 0.5)
        cos_angle = cos(angle * 0.5)
        s = sin_angle / d

        return Quaternion(axis.x * s, axis.y * s, axis.z * s, cos_angle)

    @staticmethod
    def from_euler(x: float, y: float, z: float):
        half_a1 = y * 0.5
        half_a2 = x * 0.5
        half_a3 = z * 0.5

        cos_a1 = cos(half_a1)
        sin_a1 = sin(half_a1)
        cos_a2 = cos(half_a2)
        sin_a2 = sin(half_a2)
        cos_a3 = cos(half_a3)
        sin_a3 = sin(half_a3)

        return Quaternion(
            sin_a1 * cos_a2 * sin_a3 + cos_a1 * sin_a2 * cos_a3,
            sin_a1 * cos_a2 * cos_a3 - cos_a1 * sin_a2 * sin_a3,
            -sin_a1 * sin_a2 * cos_a3 + cos_a1 * cos_a2 * sin_a3,
            sin_a1 * sin_a2 * sin_a3 + cos_a1 * cos_a2 * cos_a3
        )

    def dot(self, other: 'Quaternion'):
        return self.x * other.x + self.y * other.y + self.z * other.z + self.w * other.w

    def length2(self):
        return self.x ** 2 + self.y ** 2 + self.z ** 2 + self.w ** 2

    def length(self):
        return sqrt(self.length2())

    def normalize(self):
        il = 1.0 / self.length()
        self.x *= il
        self.y *= il
        self.z *= il
        self.w *= il

    def normalized(self):
        return self / self.length()

    def invert(self):
        self.x = -self.x
        self.y = -self.y
        self.z = -self.z

    def inverted(self):
        return Quaternion(-self.x, -self.y, -self.z, self.w)

    def xform(self, v: Vector3 | Transform):
        if isinstance(v, Vector3):
            u = Vector3(self.x, self.y, self.z)
            uv = u.cross(v)

            return v + ((uv * self.w) + u.cross(uv)) * 2.0
        else:
            return Transform(
                self.xform(v.x),
                self.xform(v.y),
                self.xform(v.z),
                self.xform(v.origin)
            )

    def xform_basis(self, t: Transform):
        return Transform(
            self.xform(t.x),
            self.xform(t.y),
            self.xform(t.z),
            t.origin
        )

    def xform_basis_inv(self, t: Transform):
        return self.inverted().xform_basis(t)

    def xform_inv(self, v: Vector3):
        return self.inverted().xform(v)

    def get_axis(self):
        if abs(self.w) > 1.0 - CMP_EPSILON:
            return Vector3(self.x, self.y, self.z)

        r = 1.0 / sqrt(1 - self.w ** 2)
        return Vector3(self.x * r, self.y * r, self.z * r)

    def get_angle(self):
        return acos(self.w) * 2.0

    def __add__(self, other: 'Quaternion'):
        return Quaternion(
            self.x + other.x,
            self.y + other.y,
            self.z + other.z,
            self.w + other.w
        )

    def __sub__(self, other: 'Quaternion'):
        return Quaternion(
            self.x - other.x,
            self.y - other.y,
            self.z - other.z,
            self.w - other.w
        )

    def __mul__(self, other: 'float | Vector3 | Transform | Quaternion'):
        match other:
            case float():
                return Quaternion(
                    self.x * other,
                    self.y * other,
                    self.z * other,
                    self.w * other
                )
            case Quaternion():
                return Quaternion(
                    x = self.w * other.x + self.x * other.w + self.y * other.z - self.z * other.y,
                    y = self.w * other.y - self.x * other.z + self.y * other.w + self.z * other.x,
                    z = self.w * other.z + self.x * other.y - self.y * other.x + self.z * other.w,
                    w = self.w * other.w - self.x * other.x - self.y * other.y - self.z * other.z
                )
                
                # x = w0 * x1 + x0 * w1 + y0 * z1 - z0 * y1
                # y = w0 * y1 - x0 * z1 + y0 * w1 + z0 * x1
                # z = w0 * z1 + x0 * y1 - y0 * x1 + z0 * w1
                # w = w0 * w1 - x0 * x1 - y0 * y1 - z0 * z1
            
            case Vector3() | Transform():
                q = self * Quaternion(other.x, other.y, other.z, w=0)
                return Vector3(x=q.x, y=q.y, z=q.z)
            case _:
                raise ValueError
    def hamilton(self, other): # for multiple multiplications in one line
        return Quaternion(
                    x = self.w * other.x + self.x * other.w + self.y * other.z - self.z * other.y,
                    y = self.w * other.y - self.x * other.z + self.y * other.w + self.z * other.x,
                    z = self.w * other.z + self.x * other.y - self.y * other.x + self.z * other.w,
                    w = self.w * other.w - self.x * other.x - self.y * other.y - self.z * other.z
                )

    def __truediv__(self, other: float):
        s = 1.0 / other
        return Quaternion(
            self.x * s,
            self.y * s,
            self.z * s,
            self.w * s
        )

    def __neg__(self):
        return Quaternion(-self.x, -self.y, -self.z, -self.w)


if __name__ == "__main__":
    v = Vector3.UP
    print(v)
    q1 = Quaternion.from_euler(3.14159 / 2, 0, 0)
    q2 = Quaternion.from_euler(-3.14159 / 2, 0, 0)
    q = q1 * q2
    q.normalize()
    axis, angle = q.get_axis(), q.get_angle()
    print(q * v)
    print(v.rotated(axis, angle))
