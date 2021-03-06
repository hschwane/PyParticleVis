import glm
import sys
from enum import Enum
from transform import Transform

class Camera:
    """class controlling a 3d camera for use with opengl"""

    def __init__(self, mode=1, position=glm.vec3(1,0,0), target=glm.vec3(0), worldUp=glm.vec3(0,1,0)):

        # settings
        self.fpsRotationSpeed = 0.005  # speed with which the camera rotates in fps mode
        self.moveSpeed = 0.125  # speed with which the camera moves in fps mode
        self.tbRotationSpeed = 0.015  # speed with which the camera rotates in trackball mode
        self.panSpeed = 0.006  # speed with which the camera pans in trackball mode
        self.zoomSpeed = 0.25  # speed with which the camera zooms (used for Z axis in trackball mode)
        self.enableAllControls = False  # enable movement while in trackball mode and pan/zoom while in fps mode
        self.movementSmoothing = 0.25  # higher numbers result in stronger smoothing and delayed movement
        self.rotationSmoothing = 0.3  # higher numbers result in stronger smoothing and delayed rotation
        self.worldUp = worldUp  # worlds up vector
        self.mode = mode  # 0 = trackball, 1 = first person
        self.movementSpeedMod = 1.0  # temporary modified movement speed, will be reset every frame

        # cameras internal state (DO NOT WRITE)
        self._movementInput = glm.vec3(0)
        self._rotationInput = glm.vec2(0)
        self._desiredTransform = Transform() # Transform(position)  # desired transform based on inputs
        self._desiredTargetDistance = 0  # desired distance along the front vector where the center for trackball mode lives
        self._currentTransform = Transform() #Transform(position)  # transform object describing orientation and position of camera
        self._currentTargetDistance = 0  # distance along the front vector where the center for trackball mode lives
        self.setPosition(position)
        self.setTarget(target)

        # variables depending on state, they are automatically updated when calling the Camera.update() (DO NOT WRITE, only read)
        self.modelMatrix = self._currentTransform.mat4()
        self.viewMatrix = glm.inverse(self.modelMatrix)

    def setTarget(self, target, interpolate=False):
        """Use to set a point where the camera should look. Target is expected to be a glm.vec3,
        interpolate is a bool. Set interpolate to true produces an animated camera movement"""
        self._desiredTransform.lookAt(target, self.worldUp)
        self._desiredTargetDistance = glm.length(target - self._desiredTransform.position)

        if not interpolate:
            self._currentTransform.orientation = self._desiredTransform.orientation
            self._currentTargetDistance = self._desiredTargetDistance

    def setPosition(self,position, interpolate=False):
        """Use to set the position of the camera. Position is expected to be a glm.vec3,
        interpolate is a bool. Set interpolate to true produces an animated camera movement"""
        newPos = glm.vec3(position.x,position.y,position.z) # avoid python binding a reference to the position
        self._desiredTransform.position = newPos
        if not interpolate:
            self._currentTransform.position = newPos

    def rotateH(self, dPhi):
        self._rotationInput.x += dPhi * (self.fpsRotationSpeed if self.mode == 1 else self.tbRotationSpeed)

    def rotateV(self, dTheta):
        self._rotationInput.y += dTheta * (self.fpsRotationSpeed if self.mode == 1 else self.tbRotationSpeed)

    def moveX(self, dx):
        if self.mode == 1 or self.enableAllControls:
            self._movementInput.x += dx * self.moveSpeed

    def moveY(self, dy):
        if self.mode == 1 or self.enableAllControls:
            self._movementInput.y += dy * self.moveSpeed

    def moveZ(self, dz):
        if self.mode == 1 or self.enableAllControls:
            self._movementInput.z += dz * self.moveSpeed

    def panH(self, dx):
        if self.mode == 0 or self.enableAllControls:
            self._movementInput.x += dx * self.panSpeed

    def panV(self, dy):
        if self.mode == 0 or self.enableAllControls:
            self._movementInput.y += dy * self.panSpeed

    def zoom(self, dz):
        if self.mode == 0 or self.enableAllControls:
            self._movementInput.z -= dz * self.zoomSpeed

    def update(self, deltaTime):
        # movement in camera coordinates
        movement = self._currentTransform.orientation * (self._movementInput * self.movementSpeedMod)

        if self.mode == 0:
            # rotate position around target
            # figure out where the old target is
            oldTarget = self._desiredTransform.position \
                        + self._desiredTransform.orientation * glm.vec3(0, 0, -1) * self._desiredTargetDistance

            # rotate the camera
            self._desiredTransform.orientation = glm.normalize(glm.angleAxis(self._rotationInput.x, self.worldUp)
                                                               * self._desiredTransform.orientation
                                                               * glm.angleAxis(self._rotationInput.y, glm.vec3(1, 0, 0)))

            # move so old target matches new target
            newTarget = self._desiredTransform.position \
                        + self._desiredTransform.orientation * glm.vec3(0, 0, -1) * self._desiredTargetDistance
            self._desiredTransform.position += oldTarget - newTarget

            # pan
            # zooming, make sure distance to the target does not become negative
            if self._desiredTargetDistance + self._movementInput.z > 0.01 * self.zoomSpeed:
                self._desiredTargetDistance += self._movementInput.z

            # now just apply  movement
            self._desiredTransform.position += movement

            # interpolate
            # interpolate distance to target
            self._currentTargetDistance = glm.mix(self._currentTargetDistance, self._desiredTargetDistance, glm.pow(deltaTime, self.movementSmoothing))

            # interpolate current target position
            desiredTarget = self._desiredTransform.position + self._desiredTransform.orientation * glm.vec3(0, 0, -1) * self._desiredTargetDistance
            oldActualTarget = self._currentTransform.position + self._currentTransform.orientation * glm.vec3(0, 0, -1) * self._currentTargetDistance
            oldActualTarget = glm.mix(oldActualTarget, desiredTarget, glm.pow(deltaTime, self.movementSmoothing))

            # interpolate orientation
            self._currentTransform.orientation = glm.slerp(self._currentTransform.orientation, self._desiredTransform.orientation, glm.pow(deltaTime, self.rotationSmoothing))

            # calculate proper position using difference that was created by rotation and moving the target
            newActualTarget = self._currentTransform.position + self._currentTransform.orientation * glm.vec3(0, 0, -1) * self._currentTargetDistance
            self._currentTransform.position += oldActualTarget - newActualTarget

        elif self.mode == 1:

            # movement
            self._desiredTransform.position += movement

            # rotation
            self._desiredTransform.orientation = glm.normalize(glm.angleAxis(self._rotationInput.x, self.worldUp)
                                                               * self._desiredTransform.orientation
                                                               * glm.angleAxis(self._rotationInput.y, glm.vec3(1, 0, 0)))

            # interpolate between transform and desired transform
            self._currentTransform.position = glm.mix(self._currentTransform.position, self._desiredTransform.position,
                                                      glm.pow(deltaTime, self.movementSmoothing))
            self._currentTransform.orientation = glm.slerp(self._currentTransform.orientation, self._desiredTransform.orientation,
                                                           glm.pow(deltaTime, self.rotationSmoothing))

        self.modelMatrix = self._currentTransform.mat4()
        self.viewMatrix = glm.inverse(self.modelMatrix)
        self._rotationInput.x = 0
        self._rotationInput.y = 0
        self._movementInput.x = 0
        self._movementInput.y = 0
        self._movementInput.z = 0
        self.movementSpeedMod = 1.0


class CameraKeyInputs(Enum):
    """different camera functions that can be mapped to keys using the camera input handler"""
    MOVE_FORWARD = 0
    MOVE_BACKWARD = 1
    MOVE_RIGHT = 2
    MOVE_LEFT = 3
    MOVE_UP = 4
    MOVE_DOWN = 5
    ENABLE_MOUSE_ROTATION = 6
    ENABLE_MOUSE_PAN = 7
    SWITCH_INPUT_MODE = 8
    MOVE_FAST = 9
    MOVE_SLOW = 10
    INCREASE_SPEED = 11
    DECREASE_SPEED = 12
    ROTATE_UP = 13
    ROTATE_DOWN = 14
    ROTATE_RIGHT = 15
    ROTATE_LEFT = 16
    PAN_UP = 17
    PAN_DOWN = 18
    PAN_RIGHT = 20
    PAN_LEFT = 19
    ZOOM_IN = 20
    ZOOM_OUT = 21


class CameraInputHandler:
    """Moves the camera depending on mouse and keyboard input."""
    def __init__(self, camera, keyMap=None, enableMouseRotation=True, enableMousePan=True, enableMouseZoom=True, rotateMouseButton=1, panMouseButton=3):
        self.camera = camera

        self._keyMap = {}
        self._keyDown = {}
        if keyMap:
            self.setKeyMap(keyMap)
        else:
            self.setKeyMap( {'W': CameraKeyInputs.MOVE_FORWARD, 'S': CameraKeyInputs.MOVE_BACKWARD,
                           'D': CameraKeyInputs.MOVE_RIGHT, 'A': CameraKeyInputs.MOVE_LEFT,
                           'Q': CameraKeyInputs.MOVE_DOWN, 'E': CameraKeyInputs.MOVE_UP,
                           'Control': CameraKeyInputs.ENABLE_MOUSE_ROTATION, 'Alt': CameraKeyInputs.ENABLE_MOUSE_PAN,
                           'Shift': CameraKeyInputs.MOVE_SLOW, ' ': CameraKeyInputs.MOVE_FAST,
                           'X': CameraKeyInputs.SWITCH_INPUT_MODE,
                           'F': CameraKeyInputs.INCREASE_SPEED, 'C': CameraKeyInputs.DECREASE_SPEED,
                           'Up': CameraKeyInputs.ROTATE_UP, 'Down': CameraKeyInputs.ROTATE_DOWN,
                           'Left': CameraKeyInputs.ROTATE_LEFT, 'Right' : CameraKeyInputs.ROTATE_RIGHT
                            } )

        self.enableMouseRotation = enableMouseRotation
        self.enableMousePan = enableMousePan
        self.enableMouseZoom = enableMouseZoom
        self.rotateMouseButton = rotateMouseButton
        self.panMouseButton = panMouseButton
        self.prevMousePos = (0, 0)

    def setKeyMap(self, keyMap):
        self._keyMap = keyMap
        self._keyDown = {}
        for function in CameraKeyInputs:
            self._keyDown[function] = False

    def on_key_pressed(self, event):
        if not event.handled and event.key in self._keyMap:
            if self._keyMap[event.key] == CameraKeyInputs.SWITCH_INPUT_MODE:
                self.camera.mode = (self.camera.mode + 1) % 2
            else:
                self._keyDown[self._keyMap[event.key]] = True
            event.handled = True

    def on_key_released(self, event):
        if not event.handled and event.key in self._keyMap:
            self._keyDown[self._keyMap[event.key]] = False
            event.handled = True

    def on_mouse_move(self, event):
        if not event.handled:
            mouseDelta = event.pos - self.prevMousePos
            self.prevMousePos = event.pos
            if self.enableMouseRotation and (self.rotateMouseButton in event.buttons or self._keyDown[CameraKeyInputs.ENABLE_MOUSE_ROTATION]):
                self.camera.rotateH(-mouseDelta[0])
                self.camera.rotateV(-mouseDelta[1])
                event.handled = True
            elif self.enableMousePan and (self.panMouseButton in event.buttons or self._keyDown[CameraKeyInputs.ENABLE_MOUSE_PAN]):
                self.camera.panH(-mouseDelta[0])
                self.camera.panV(mouseDelta[1])
                event.handled = True

    def on_mouse_wheel(self, event):
        if not event.handled and self.enableMouseZoom:
            self.camera.zoom(event.delta[1]*10)
            event.handled = True

    def changeMovementSpeed(self, change):
        self.camera.moveSpeed = self.camera.moveSpeed + change * 0.025 * (self.camera.moveSpeed + sys.float_info.min)
        self.camera.panSpeed = self.camera.panSpeed + change * 0.025 * (self.camera.panSpeed + sys.float_info.min)
        self.camera.zoomSpeed = self.camera.zoomSpeed + change * 0.025 * (self.camera.zoomSpeed + sys.float_info.min)

    def on_draw(self, deltaTime):
        """call once per frame to update camera movement"""
        if self._keyDown[CameraKeyInputs.INCREASE_SPEED]:
            self.changeMovementSpeed(20*deltaTime)
        if self._keyDown[CameraKeyInputs.DECREASE_SPEED]:
            self.changeMovementSpeed(-20*deltaTime)
        if self._keyDown[CameraKeyInputs.MOVE_BACKWARD]:
            self.camera.moveZ(20*deltaTime)
        if self._keyDown[CameraKeyInputs.MOVE_FORWARD]:
            self.camera.moveZ(-20*deltaTime)
        if self._keyDown[CameraKeyInputs.MOVE_RIGHT]:
            self.camera.moveX(20*deltaTime)
        if self._keyDown[CameraKeyInputs.MOVE_LEFT]:
            self.camera.moveX(-20*deltaTime)
        if self._keyDown[CameraKeyInputs.MOVE_UP]:
            self.camera.moveY(20*deltaTime)
        if self._keyDown[CameraKeyInputs.MOVE_DOWN]:
            self.camera.moveY(-20*deltaTime)
        if self._keyDown[CameraKeyInputs.MOVE_FAST]:
            self.camera.movementSpeedMod *= 2.0
        if self._keyDown[CameraKeyInputs.MOVE_SLOW]:
            self.camera.movementSpeedMod *= 0.5
        if self._keyDown[CameraKeyInputs.ROTATE_UP]:
            self.camera.rotateV(60*deltaTime)
        if self._keyDown[CameraKeyInputs.ROTATE_DOWN]:
            self.camera.rotateV(-60 * deltaTime)
        if self._keyDown[CameraKeyInputs.ROTATE_RIGHT]:
            self.camera.rotateH(-60*deltaTime)
        if self._keyDown[CameraKeyInputs.ROTATE_LEFT]:
            self.camera.rotateH(60 * deltaTime)
        if self._keyDown[CameraKeyInputs.PAN_UP]:
            self.camera.panV(60*deltaTime)
        if self._keyDown[CameraKeyInputs.PAN_DOWN]:
            self.camera.panV(-60 * deltaTime)
        if self._keyDown[CameraKeyInputs.PAN_RIGHT]:
            self.camera.panH(60*deltaTime)
        if self._keyDown[CameraKeyInputs.PAN_LEFT]:
            self.camera.panH(-60 * deltaTime)
        if self._keyDown[CameraKeyInputs.ZOOM_IN]:
            self.camera.panH(1 * deltaTime)
        if self._keyDown[CameraKeyInputs.ZOOM_OUT]:
            self.camera.panH(-1 * deltaTime)


