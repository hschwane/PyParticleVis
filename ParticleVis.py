import numpy as np
import glm
import time

from vispy import app, gloo, util
from vispy.gloo import Program, VertexBuffer, IndexBuffer
from vispy.util.transforms import perspective, translate, rotate
from vispy.geometry import create_cube

from camera import Camera, CameraInputHandler

class Canvas(app.Canvas):
    def __init__(self):
        app.Canvas.__init__(self, size=(512, 512), title='Particle Renderer', keys='interactive')

        # settings
        self.nearDistance = 0.1
        self.farDistance = 20
        self.fov = 45.0 # field of view in degree

        # enable geometry shader
        gloo.gl.use_gl('gl+')

        # load and compile shader
        with open('shader/particleRenderer.frag', 'r') as file:
            fragmentString = file.read()

        with open('shader/particleRenderer.geom', 'r') as file:
            geomString = file.read()

        with open('shader/particleRenderer.vert', 'r') as file:
            vertexString = file.read()

        self.program = Program()
        self.program.set_shaders(vertexString, fragmentString, geomString, True)

        # upload some point data
        self.program['input_position'] = [(0,0,0),(1,1,1),
                                          (1,1,-1),(1,-1,1),(1,-1,-1),
                                          (-1,1,1),(-1,1,-1),(-1,-1,1),
                                          (-1,-1,-1)]

        ######################################
        # settings

        # light settings
        self.program['lightPosition'] = (500, 500, 1000)
        self.program['lightDiffuse'] = (0.4, 0.4, 0.4)
        self.program['lightSpecular'] = (0.3, 0.3, 0.3)
        self.program['ambientLight'] = (0.1, 0.1, 0.1)
        self.program['lightInViewSpace'] = True

        # sphere look
        self.program['sphereRadius'] = 0.15
        self.program['defaultColor'] = (1, 1, 1)
        self.program['brightness'] = 1
        self.program['colorMode'] = 0
        self.program['lowerBound'] = 0
        self.program['upperBound'] = 1
        self.program['materialAlpha'] = 1.0
        self.program['materialShininess'] = 4.0

        # settings for flat shading
        self.program['renderFlatDisks'] = False
        self.program['flatFalloff'] = False

        # settings for additional depth cues
        self.program['enableEdgeHighlights'] = False

        # increase this if spheres appear to have cut away edges
        self.program['spriteScale'] = 1.1

        ############################################

        # model matrix
        model = np.eye(4, dtype=np.float32)
        self.program['model'] = model

        # camera and view matrix
        self.cam = Camera(1, glm.vec3(3, 3, 3))
        self.program['view'] = self.cam.viewMatrix
        self.camInputHandler = CameraInputHandler(self.cam)

        # projection matrix
        self.reset_projection()

        # timing
        self.lastTime = time.time()

        # set opengl settings and show
        gloo.set_state(clear_color=(0.30, 0.30, 0.35, 1.00), depth_test=True)
        self.show()

    def on_mouse_move(self, event):
        self.camInputHandler.on_mouse_move(event)

    def on_key_press(self, event):
        self.camInputHandler.on_key_pressed(event)

    def on_key_release(self, event):
        self.camInputHandler.on_key_released(event)

    def on_mouse_wheel(self, event):
        self.camInputHandler.on_mouse_wheel(event)

    def on_draw(self, event):
        # clear window content
        gloo.clear(color=True, depth=True)

        # calculate dt (time since last frame)
        newTime = time.time()
        dt = newTime - self.lastTime
        self.lastTime = newTime

        # update camera and view matrix
        self.camInputHandler.on_draw(dt)
        self.cam.update(dt)
        self.program['view'] = self.cam.viewMatrix

        # draw
        self.program.draw('points')

        # update window content
        self.update()

    def on_resize(self, event):
        self.reset_projection()

    def reset_projection(self):
        gloo.set_viewport(0, 0, *self.physical_size)
        projection = perspective(self.fov, self.size[0] / float(self.size[1]), self.nearDistance, self.farDistance)
        self.program['projection'] = projection


if __name__ == '__main__':
    c = Canvas()
    app.run()