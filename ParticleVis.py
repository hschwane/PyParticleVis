import numpy as np
import glm
import time

from vispy import app, gloo, util
from vispy.gloo import Program, VertexBuffer, IndexBuffer
from vispy.util.transforms import perspective, translate, rotate

from camera import Camera, CameraInputHandler

class Canvas(app.Canvas):
    def __init__(self):
        app.Canvas.__init__(self, size=(512, 512), title='Particle Renderer', keys='interactive')

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

        ######################################
        # settings

        # when changing near/far or fov you have to call resetProjection() for the changes to take effect
        # everything closer to the camera than near ot further away than far will not be drawn
        self.nearDistance = 0.1
        self.farDistance = 20
        self.fov = 45.0  # field of view in degree

        # // positions where spheres are rendered
        self.program['input_position'] = [(0, 0, 0), (1, 1, 1),
                                          (1,1,-1), (1,-1,1), (1,-1,-1),
                                          (-1,1,1), (-1,1,-1), (-1,-1,1),
                                          (-1,-1,-1)]


        # vector field for color
        # self.program['input_vector'] =
        # scalar field for color
        # self.program['input_scalar'] =

        self.program['input_radius'] = [[0.15], [0.1], [0.2], [0.1], [0.2], [0.05], [0.1], [0.15], [0.1]]

        # size
        self.program['enableSizePerParticle'] = False  # enable this and set a size for each particle above
        self.program['sphereRadius'] = 0.15  # radius of the spheres if "size per particle" is disabled

        # light settings
        self.program['lightPosition'] = (500, 500, 1000)  # position of the ligth
        self.program['lightDiffuse'] = (0.4, 0.4, 0.4)  # diffuse color of the light
        self.program['lightSpecular'] = (0.3, 0.3, 0.3)  # specular color of the light
        self.program['ambientLight'] = (0.1, 0.1, 0.1)  # ambient light color
        self.program['lightInViewSpace'] = True  # should the light move around with the camera?

        # sphere look
        self.program['defaultColor'] = (1, 1, 1)  # particle color in color mode 0
        self.program['brightness'] = 1  # additional brightness control
        self.program['colorMode'] = 0  # 1: color by vector field direction, 2: color by vector field magnitude, 3: color by scalar field, 0: constant color
        self.program['lowerBound'] = 0  # lowest value of scalar field / vector field magnitude
        self.program['upperBound'] = 1  # lowest value of scalar field / vector field magnitude
        self.program['materialAlpha'] = 1.0  # set lower than one to make spheres transparent
        self.program['materialShininess'] = 4.0  # material shininess

        # settings for flat shading
        self.program['renderFlatDisks'] = False  # render flat discs instead of spheres
        self.program['flatFalloff'] = False  # when using flat discs, enable this darken the edges

        # settings for additional depth cues
        self.program['enableEdgeHighlights'] = False  # add black edge around the particles for better depth perception

        self.program['spriteScale'] = 1.1  # increase this if spheres appear to have cut off edges

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
        self._lastTime = time.time()

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
        dt = newTime - self._lastTime
        self._lastTime = newTime

        # update camera and view matrix
        self.camInputHandler.on_draw(dt)
        self.cam.update(dt)
        self.program['view'] = self.cam.viewMatrix

        # draw
        self.program.draw('points')

        # update window content
        self.update()

    def on_resize(self, event):
        self.resetProjection()

    def resetProjection(self):
        gloo.set_viewport(0, 0, *self.physical_size)
        projection = perspective(self.fov, self.size[0] / float(self.size[1]), self.nearDistance, self.farDistance)
        self.program['projection'] = projection


if __name__ == '__main__':
    c = Canvas()
    app.run()