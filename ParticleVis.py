import numpy as np
import glm
import time

from vispy import app, gloo, util
from vispy.gloo import Program
from vispy.util.transforms import perspective

from camera import Camera, CameraInputHandler

def _checkerboard(size=64,tiles=4):
    return np.reshape(
                np.kron(
                    np.kron([[1, 0] * tiles, [0, 1] * tiles] * tiles, np.ones((size, size))),
                    [1,1,1]),
            (2*tiles*size,2*tiles*size,3) )

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
        # scalar field, used for color in color mode 3
        self.program['input_scalar'] = np.array([0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9], dtype=np.float32)
        # radius per particle, set self.program['enableSizePerParticle']  = True to enable
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

        # transfer function / color
        self.program['colorMode'] = 0  # 1: color by vector field direction, 2: color by vector field magnitude, 3: color by scalar field, 0: constant color
        self.program['defaultColor'] = (1, 1, 1)  # particle color in color mode 0
        self.program['lowerBound'] = 0.0  # lowest value of scalar field / vector field magnitude
        self.program['upperBound'] = 1.0  # lowest value of scalar field / vector field magnitude
        self.program['customTransferFunc'] = False  # set to true to use a custom transfer function
        # Transfer function uses a 1D Texture.
        # Provide 1D list of colors (r,g,b) as the textures data attribute, colors will be evenly spread over
        # the range [lowerBound,upperBound]. Meaning particles where the scalar is equal to lowerBound will
        # have the first specified color, the one with a scalar equal to lowerBound will have the last. Values that
        # lie in between the colors are interpolated linearly
        self.program['transferFunc'] = gloo.Texture1D(format='rgb', interpolation='linear', internalformat='rgb8',
                                                        data=np.array([(0,0,0), (1,0.4,0.3)]).astype(np.float32))


        # sphere look
        self.program['brightness'] = 1  # additional brightness control
        self.program['materialAlpha'] = 1.0  # set lower than one to make spheres transparent
        self.program['materialShininess'] = 4.0  # material shininess
        self.program['useTexture'] = False  # use the below texture for coloring (will be tinted according to set color)
        # provide a numpy array of shaper (x,y,3) for rgb pixels of the 2d image
        self.program['colorTexture'] = gloo.Texture2D(format='rgb', interpolation='linear', internalformat='rgb8',
                                                        data=_checkerboard().astype(np.float32) )
        self.program['uvUpY'] = False  # rotates texture by 90 degrees so that sphere poles are along the Y axis

        # settings for flat shading
        self.program['renderFlatDisks'] = False  # render flat discs instead of spheres
        self.program['flatFalloff'] = False  # when using flat discs, enable this darken the edges

        # settings for additional depth cues
        self.program['enableEdgeHighlights'] = False  # add black edge around the particles for better depth perception

        self.program['spriteScale'] = 1.1  # increase this if spheres appear to have cut off edges

        # style of blending
        self.useAdditiveBlending(False)

        ############################################

        # model matrix
        model = np.eye(4, dtype=np.float32)
        self.program['model'] = model

        # camera and view matrix
        self.cam = Camera(1, glm.vec3(3, 3, 3))
        self.program['view'] = self.cam.viewMatrix
        self.camInputHandler = CameraInputHandler(self.cam)

        # projection matrix
        self.resetProjection()

        # timing
        self._lastTime = time.time()

        # set opengl settings and show
        gloo.set_state(clear_color=(0.30, 0.30, 0.35, 1.00))
        self.show()

    def useAdditiveBlending(self, enable):
        if enable:
            gloo.set_blend_func('one','one')
            gloo.set_blend_equation('func_add')
            gloo.set_state(depth_test = False, blend = True)
        else:
            gloo.set_state(depth_test = True, blend = False)


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

        # draw particles
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