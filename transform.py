import glm

class Transform:
    """Class represents a full 3d transformation including scale,
    translation and rotation."""

    position = glm.vec3(0, 0, 0)    # position as vec3
    scale = glm.vec3(1, 1, 1)   # scale as vec3
    orientation = glm.angleAxis(0, glm.vec3(0))  # orientation as a quaternion

    def __init__(self, position=glm.vec3(0, 0, 0), orientation = glm.angleAxis(0, glm.vec3(0)), scale =glm.vec3(1, 1, 1)):
        """construct transform from an 4x4 transformation matrix"""
        self.position = position
        self.orientation = orientation
        self.scale = scale

    def __eq__(self, other):
        return self.position == other.position \
               and self.scale == other.scale \
               and self.orientation == other.orientation

    def __ne__(self, other):
        return self.position != other.position \
            or self.scale != other.scale \
            or self.orientation != other.orientation

    def mat4(self):
        return glm.translate(glm.mat4(1.0), self.position) * glm.scale(glm.mat4(1.0), self.scale) * glm.mat4_cast(self.orientation)

    def lookAt(self, target, up):
        """set orientation to look at the target, target and up are expected to be glm.vec3"""
        self.orientation = glm.quatLookAt(glm.normalize(target-self.position), up)
