import moderngl as mgl
import moderngl_window as mglw
import pygame as pg
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

        self.gui = ImGUIManager(self)
        self.frames = 0
        # imgui.create_context()

    # self.imgui = ModernglWindowRenderer(self.wnd)

    def initShaders(self):
        self.shaders = ShaderProgram(self.ctx, "programs")
        self.shaders.load_program("pygameBlit")
        self.shaders.load_program("RT")
        self.shaders.load_program("accumulator")

    def initSurfaces(self):
        self.vao = VAO(self.ctx)
        self.screenSurface = self.vao.get_quadfs(self.shaders.programs["pygameBlit"])
        self.RTSurface = self.vao.get_quadfs(self.shaders.programs["RT"])
        self.AccumulatorSurface = self.vao.get_quadfs(
            self.shaders.programs["accumulator"]
        )
        print(f"{colors.HEADER}initSurfaces - {colors.OKGREEN}Success{colors.ENDC}")

    def initTextures(self):
        self.RTRenderTEX = self.ctx.texture(self.window_size, components=4, dtype="f4")
        self.RTRenderFBO = self.ctx.framebuffer(
            self.RTRenderTEX, self.ctx.depth_renderbuffer(self.window_size)
        )

        self.AccumulatorTEX = self.ctx.texture(
            self.window_size, components=4, dtype="f4"
        )
        self.AccumulatorFBO = self.ctx.framebuffer(
            self.AccumulatorTEX, self.ctx.depth_renderbuffer(self.window_size)
        )
        print(f"{colors.HEADER}initTextures - {colors.OKGREEN}Success{colors.ENDC}")

    def initScene(self):
        self.scene = Scene()

        scenePath = self.settings.rt_scenepath
        if scenePath != "":
            pass
        skyboxPath = self.settings.rt_skyboxpath
        if skyboxPath != "":
            skybox = pg.image.load(skyboxPath)
            self.skyboxTexture = self.ctx.texture(
                size=skybox.get_size(),
                components=3,
                data=pg.image.tostring(skybox, "RGB"),
            )
            self.set_uniform("RT", "skyboxType", 1)
        else:
            self.skyboxTexture = self.ctx.texture(
                size=(128, 128),
                components=3,
                data=b"\xff\x00\xff\x00\x00\x00" * 128 * 64,
            )
            self.set_uniform("RT", "skyboxType", 0)

        self.set_uniform("RT", "skybox", 4)
        self.skyboxTexture.use(location=4)

        self.scene.addQuad(
            (0, -3, -3),
            (0, 3, -3),
            (0, 3, 3),
            (0, -3, 3),
            (0.8, 0.8, 0.8),
            (0.8, 0.8, 0.8),
            (0.1, 0.0, 0.0, 0.0),
        )  # back wall
        self.scene.addQuad(
            (0, -3, -3),
            (0, 3, -3),
            (-3, 3, -3),
            (-3, -3, -3),
            (0.8, 0.1, 0.1),
            (0.8, 0.1, 0.1),
            (0.1, 0.0, 0.0, 0.0),
        )  # left wall
        self.scene.addQuad(
            (0, 3, 3),
            (0, -3, 3),
            (-3, -3, 3),
            (-3, 3, 3),
            (0.1, 0.8, 0.1),
            (0.1, 0.8, 0.1),
            (0.1, 0.0, 0.0, 0.0),
        )  # right wall
        self.scene.addQuad(
            (0, 3, -3),
            (0, 3, 3),
            (-3, 3, 3),
            (-3, 3, -3),
            (0.8, 0.8, 0.8),
            (0.8, 0.8, 0.8),
            (0.1, 0.0, 0.0, 0.0),
        )  # top wall
        self.scene.addQuad(
            (0, -3, -3),
            (0, -3, 3),
            (-3, -3, 3),
            (-3, -3, -3),
            (0.8, 0.8, 0.8),
            (0.8, 0.8, 0.8),
            (0.1, 0.0, 0.0, 0.0),
        )  # bottom wall

        self.scene.addQuad(
            (-1, 2.999, -1.5),
            (-1, 2.999, 1.5),
            (-2, 2.999, 1.5),
            (-2, 2.999, -1.5),
            (0.8, 0.8, 0.45),
            (0.8, 0.8, 0.8),
            (0.9, 0.0, 12.0, 0.0),
        )  # top light
        self.scene.addSphere(
            (-1, -1.0, 0), 1.0, (1, 0.7, 1), (1, 1, 1), (0.0, 0.0, 0, 1)
        )

        geometryData, materialData = self.scene.packObjects()

        geometryPixelCount = self.scene.getObjectCount(inPixels=True)
        materialPixelCount = self.scene.getMaterialPixelCount()
        geometryCount = self.scene.getObjectCount()
        self.set_uniform("RT", "geometryCount", geometryCount)
        self.set_uniform("RT", "geometryPixelCount", geometryPixelCount)

        self.geometryTexture = self.ctx.texture(
            (geometryPixelCount, 1), components=4, dtype="f4"
        )
        self.geometryTexture.write(geometryData)
        self.materialTexture = self.ctx.texture(
            (materialPixelCount, 1), components=4, dtype="f4"
        )
        self.materialTexture.write(materialData)

        sphereCount = self.scene.getObjectCount(countCategory="spheres")
        cubeCount = self.scene.getObjectCount(countCategory="cubes")
        cylinderCount = self.scene.getObjectCount(countCategory="cylinders")
        quadCount = self.scene.getObjectCount(countCategory="quads")
        self.set_uniform("RT", "sphereCount", sphereCount)
        self.set_uniform("RT", "cubeCount", cubeCount)
        self.set_uniform("RT", "cylinderCount", cylinderCount)
        self.set_uniform("RT", "quadCount", quadCount)
        print(f"{colors.HEADER}initScene    - {colors.OKGREEN}Success{colors.ENDC}")

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
        self.set_uniform(
            "RT", "u_resolution", (self.window_size[0], self.window_size[1])
        )

        self.updateRTuniforms()
        self.updateAccumUniforms()
        print(f"{colors.HEADER}initUniforms - {colors.OKGREEN}Success{colors.ENDC}")

    def updateRTuniforms(self):
        self.frames = 0
        self.set_uniform("RT", "maxSamples", self.settings.rt_samples)
        self.set_uniform("RT", "maxReflections", self.settings.rt_reflections)
        print(
            f"{colors.HEADER}updateUniforms{colors.ENDC} - {colors.OKCYAN}RT{colors.ENDC} - {colors.OKGREEN}Success{colors.ENDC}"
        )

    def updateAccumUniforms(self):
        self.frames = 0
        self.set_uniform("accumulator", "accumulate", self.settings.rt_accumframes)
        print(
            f"{colors.HEADER}updateUniforms{colors.ENDC} - {colors.OKCYAN}accumulator{colors.ENDC} - {colors.OKGREEN}Success{colors.ENDC}"
        )

    def render(self, time: float, delta_time: float):
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
        self.frames += 1
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

    def mouse_scroll_event(self, x_offset, y_offset):
        self.gui.imgui.mouse_scroll_event(x_offset, y_offset)

    def mouse_press_event(self, x, y, button):
        self.gui.imgui.mouse_press_event(x, y, button)

    def mouse_release_event(self, x: int, y: int, button: int):
        self.gui.imgui.mouse_release_event(x, y, button)

    def unicode_char_entered(self, char):
        self.gui.imgui.unicode_char_entered(char)


mglw.run_window_config(App)
