import moderngl as mgl
import moderngl_window as mglw
import pygame as pg
from numpy import cos, pi, sin
from numpy.random import rand

from coloredText import bcolors as colors
from GUI import ImGUIManager
from scene import Scene
from shader_program import ShaderProgram
from TOMLParser import TOMLParser
from VAO import VAO


class Settings:
    TOMLParser = TOMLParser()
    TOMLParser.loadConfig("settings.toml")

    gl_version = TOMLParser.getValue("settings", "WINDOW/GLversion")
    title = TOMLParser.getValue("settings", "WINDOW/title")
    window_size = TOMLParser.getValue("settings", "WINDOW/resolution")
    resizable = TOMLParser.getValue("settings", "WINDOW/resizable")

    rt_samples = TOMLParser.getValue("settings", "RT/samples")
    rt_reflections = TOMLParser.getValue("settings", "RT/reflections")
    rt_accumframes = TOMLParser.getValue("settings", "RT/accumframes")
    rt_skyboxpath = TOMLParser.getValue("settings", "RT/skyboxpath")
    rt_scenepath = TOMLParser.getValue("settings", "RT/scenepath")


class App(mglw.WindowConfig):
    settings = Settings()
    gl_version = settings.gl_version
    title = settings.title
    window_size = settings.window_size
    resizable = False

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.initShaders()
        self.initSurfaces()
        self.initTextures()
        self.initScene()
        self.initUniforms()
        self.initCameraControls()

        self.gui = ImGUIManager(self)
        self.frames = 0

    def initCameraControls(self):
        self.allowCameraRotation = False
        self.allowCameraMovement = False
        self.cameraRotation = [0,0]
        self.cameraPosition = [0,0,0]
        self.tempDir = [0,0,0]


    def initShaders(self):
        self.shaders = ShaderProgram(self.ctx, "programs")
        self.shaders.load_program("pygameBlit")
        self.shaders.load_program("RT")
        self.shaders.load_program("accumulator")

    def initSurfaces(self):
        self.vao = VAO(self.ctx)
        self.screenSurface = self.vao.get_quadfs(self.shaders.programs["pygameBlit"])
        self.RTSurface = self.vao.get_quadfs(self.shaders.programs["RT"])
        self.AccumulatorSurface = self.vao.get_quadfs(self.shaders.programs["accumulator"])
        print(f"{colors.HEADER}initSurfaces{colors.ENDC} - {colors.OKGREEN}Success{colors.ENDC}")

    def initTextures(self):
        self.RTRenderTEX = self.ctx.texture(self.window_size, components=4, dtype="f4")
        self.RTRenderFBO = self.ctx.framebuffer(self.RTRenderTEX, self.ctx.depth_renderbuffer(self.window_size))

        self.AccumulatorTEX = self.ctx.texture(self.window_size, components=4, dtype="f4")
        self.AccumulatorFBO = self.ctx.framebuffer(self.AccumulatorTEX, self.ctx.depth_renderbuffer(self.window_size))

        self.geometryTexture = self.ctx.texture((1, 1), components=4, dtype="f4")
        self.materialTexture = self.ctx.texture((1, 1), components=4, dtype="f4")

        self.skyboxTexture = self.ctx.texture((1, 1), components=4, dtype='f4')
        print(f"{colors.HEADER}initTextures{colors.ENDC} - {colors.OKGREEN}Success{colors.ENDC}")


    def initScene(self):
        self.scene = Scene()

        self.scene.importFromFile(self.settings.rt_scenepath)
        self.createScene()
        self.createSkybox()
    
    def createScene(self):
        self.frames = 0
        self.geometryTexture.release()
        self.materialTexture.release()

        geometryData, materialData = self.scene.packObjects()

        geometryPixelCount = self.scene.getObjectCount(inPixels=True)
        materialPixelCount = self.scene.getMaterialPixelCount()
        geometryCount = self.scene.getObjectCount()
        self.set_uniform("RT", "geometryCount", geometryCount)
        self.set_uniform("RT", "geometryPixelCount", geometryPixelCount)
        data = b'' if geometryPixelCount == 0 else geometryData
        self.geometryTexture = self.ctx.texture(
            (geometryPixelCount, 1), components=4, dtype="f4", data=data
        )
        data = b'' if geometryPixelCount == 0 else materialData
        self.materialTexture = self.ctx.texture(
            (materialPixelCount, 1), components=4, dtype="f4", data=data
        )

        self.geometryTexture.use(location=2)
        self.materialTexture.use(location=3)

        sphereCount = self.scene.getObjectCount(countCategory="spheres")
        cubeCount = self.scene.getObjectCount(countCategory="cubes")
        cylinderCount = self.scene.getObjectCount(countCategory="cylinders")
        quadCount = self.scene.getObjectCount(countCategory="quads")
        self.set_uniform("RT", "sphereCount", sphereCount)
        self.set_uniform("RT", "cubeCount", cubeCount)
        self.set_uniform("RT", "cylinderCount", cylinderCount)
        self.set_uniform("RT", "quadCount", quadCount)
        print(f"{colors.HEADER}createScene - {colors.OKGREEN}Success{colors.ENDC}")

    def createSkybox(self):
        self.frames = 0
        #check if path exists
        self.skyboxTexture.release()
        try:
            f = open(self.settings.rt_skyboxpath, "r")
        except FileNotFoundError:
            print(f"{colors.HEADER}createSkybox{colors.ENDC} - {colors.WARNING}FileNotFoundError: {colors.ENDC}file {colors.OKBLUE}[{self.settings.rt_skyboxpath}]{colors.ENDC} doesn't exist!")
            self.set_uniform("RT", "skyboxType", 0)
            return

        skyboxPath = self.settings.rt_skyboxpath
        skybox = pg.image.load(skyboxPath)
        self.skyboxTexture = self.ctx.texture(
            size=skybox.get_size(),
            components=3,
            data=pg.image.tostring(skybox, "RGB"),
        )
        self.skyboxTexture.use(location=4)
        self.set_uniform("RT", "skyboxType", 1)
        print(f"{colors.HEADER}createSkybox - {colors.OKGREEN}Success{colors.ENDC}")

    def initUniforms(self):
        self.set_uniform("accumulator", "currentFrame", 1)
        self.RTRenderTEX.use(location=1)

        self.set_uniform("pygameBlit", "rtTexture", 5)
        self.set_uniform("accumulator", "accumFrame", 5)
        self.AccumulatorTEX.use(location=5)

        self.set_uniform("RT", "geometryTexture", 2)
        self.geometryTexture.use(location=2)

        self.set_uniform("RT", "materialTexture", 3)
        self.materialTexture.use(location=3)
        self.set_uniform("RT", "u_resolution", (self.window_size[0], self.window_size[1]))
        
        self.set_uniform("RT", "skybox", 4)

        self.updateRTuniforms()
        print(f"{colors.HEADER}initUniforms{colors.ENDC} - {colors.OKGREEN}Success{colors.ENDC}")

    def updateRTuniforms(self):
        self.frames = 0
        self.set_uniform("RT", "maxSamples", self.settings.rt_samples)
        self.set_uniform("RT", "maxReflections", self.settings.rt_reflections)
        print(f"{colors.HEADER}updateUniforms{colors.ENDC} - {colors.OKCYAN}RT{colors.ENDC} - {colors.OKGREEN}Success{colors.ENDC}")

    def updateCameraUniforms(self):
        self.set_uniform("RT", "u_cameraPos", self.cameraPosition)
        self.set_uniform("RT", "u_mousePos", self.cameraRotation)
    
    def updatePosition(self):
        yaw = self.cameraRotation[0]
        pitch = self.cameraRotation[1]
        fx = cos(yaw)*cos(pitch)
        fy = sin(yaw)*cos(pitch)
        fz = sin(pitch)

        rx = cos(yaw-pi/2)
        ry = sin(yaw-pi/2)
        rz = 0

        ux = 0#ry*fz - rz*fy
        uy = 0#rz*fx - rx*fz
        uz = 1#rx*fy - ry*fx

        dirx = fx*self.tempDir[0] + rx*self.tempDir[1] + ux*self.tempDir[2]
        diry = fy*self.tempDir[0] + ry*self.tempDir[1] + uy*self.tempDir[2]
        dirz = fz*self.tempDir[0] + rz*self.tempDir[1] + uz*self.tempDir[2]

        self.cameraPosition[0] += dirx/5
        self.cameraPosition[1] += dirz/5
        self.cameraPosition[2] += -diry/5

    def render(self, time: float, delta_time: float):
        # Update
        if self.allowCameraMovement:
            self.updatePosition()
            self.set_uniform("RT", "u_cameraPos", self.cameraPosition)
            self.frames = 0
        if self.allowCameraRotation:
            self.set_uniform("RT", "u_mousePos", self.cameraRotation)
            self.frames = 0

        # Render modernGL
        # Render RT
        self.set_uniform("RT", "u_frame", self.frames)
        self.set_uniform("accumulator", "frame", self.frames)
        self.RTRenderFBO.use()
        self.RTSurface.render()
        # Accumulate frames
        self.AccumulatorFBO.use()
        self.AccumulatorSurface.render()
        # Tonemap and display
        self.ctx.screen.use()
        self.screenSurface.render()

        # Render ImGUI
        self.frames = self.frames + 1 if self.settings.rt_accumframes else 0
        self.gui.render()

    def set_uniform(self, shader_name, uniform_name, value):
        try:
            self.shaders.programs[shader_name][uniform_name] = value
        except KeyError:
            print(f"{colors.HEADER}setUniform - {colors.WARNING}KeyError{colors.ENDC}: uniform {colors.OKBLUE}[{shader_name}]{colors.OKCYAN}[{uniform_name}]{colors.ENDC} is not used in the shader!")

    def close(self):
        self.shaders.destroy()

    def mouse_position_event(self, x, y, dx, dy):
        self.gui.imgui.mouse_position_event(x, y, dx, dy)

    def mouse_drag_event(self, x, y, dx, dy):
        self.gui.imgui.mouse_drag_event(x, y, dx, dy)

        if self.allowCameraRotation:
            self.cameraRotation[0] += dx * 0.0174533/9
            self.cameraRotation[1] += dy * 0.0174533/9

            #self.updateCameraUniforms()

    def mouse_scroll_event(self, x_offset, y_offset):
        self.gui.imgui.mouse_scroll_event(x_offset, y_offset)

    def mouse_press_event(self, x, y, button):
        self.gui.imgui.mouse_press_event(x, y, button)
        if button == 3:
            self.allowCameraMovement = True
            self.allowCameraRotation = True

    def mouse_release_event(self, x: int, y: int, button: int):
        self.gui.imgui.mouse_release_event(x, y, button)
        if button == 3:
            self.allowCameraMovement = False
            self.allowCameraRotation = False

    def key_event(self, key, action, modifiers):
    # Key presses
        if action == self.wnd.keys.ACTION_PRESS:
            if key == self.wnd.keys.SPACE:
                self.tempDir[2] = 1
            elif modifiers.ctrl:
                self.tempDir[2] = -1
            
            if key == self.wnd.keys.W:
                self.tempDir[0] = 1
            elif key == self.wnd.keys.S:
                self.tempDir[0] = -1
            
            if key == self.wnd.keys.D:
                self.tempDir[1] = 1
            elif key == self.wnd.keys.A:
                self.tempDir[1] = -1
            

    # Key releases
        elif action == self.wnd.keys.ACTION_RELEASE:
            if key == self.wnd.keys.SPACE or not modifiers.ctrl:
                self.tempDir[2] = 0
            if key == self.wnd.keys.W or key == self.wnd.keys.S:
                self.tempDir[0] = 0
            if key == self.wnd.keys.D or key == self.wnd.keys.A:
                self.tempDir[1] = 0
       

    def unicode_char_entered(self, char):
        self.gui.imgui.unicode_char_entered(char)


mglw.run_window_config(App)
