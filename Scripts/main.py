import moderngl as mgl
import moderngl_window as mglw
import pygame as pg
from numpy import cos, pi, sin
from numpy.random import rand

from scene import Scene
from shader_program import ShaderProgram
from TOMLParser import TOMLParser
from VAO import VAO
from GUI import ImGUIManager
from coloredText import bcolors as colors


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

    app_shaderPath = TOMLParser.getValue("settings", "APP/shaderPath")


class App(mglw.WindowConfig):
    settings = Settings()
    gl_version = settings.gl_version
    title = settings.title
    window_size = settings.window_size
    resizable = False
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.initShaders()
        self.initVAO()
        self.initTextures()
        self.initScene()
        self.initCamera()
        self.initUniforms()
        

        self.gui = ImGUIManager(self)
        self.frames = 0
    
    def initShaders(self):
        resourcePath = self.settings.app_shaderPath

        if not resourcePath:
            print(f"{colors.HEADER}initShaders{colors.ENDC} - {colors.FAIL}PathNotFound{colors.ENDC} - Terminating!")
            exit()

        self.shaders = ShaderProgram(self.ctx, resourcePath)
        self.shaders.load_program("pygameBlit")
        self.shaders.load_program("RT")
        self.shaders.load_program("accumulator")

        print(f"{colors.HEADER}initShaders{colors.ENDC} - {colors.OKGREEN}Success{colors.ENDC}")

    def initVAO(self):
        self.vao = VAO(self.ctx)
        self.screen_surface = self.vao.get_quadfs(self.shaders.programs["pygameBlit"])
        self.RT_surface = self.vao.get_quadfs(self.shaders.programs["RT"])
        self.accumulator_surface = self.vao.get_quadfs(self.shaders.programs["accumulator"])
        print(f"{colors.HEADER}initSurfaces{colors.ENDC} - {colors.OKGREEN}Success{colors.ENDC}")

    def initTextures(self):
        self.RT_render_texture = self.ctx.texture(self.window_size, components=4, dtype="f4")
        self.RT_FBO = self.ctx.framebuffer(self.RT_render_texture, self.ctx.depth_renderbuffer(self.window_size))

        self.accumulator_texture = self.ctx.texture(self.window_size, components=4, dtype="f4")
        self.accumulator_FBO = self.ctx.framebuffer(self.accumulator_texture, self.ctx.depth_renderbuffer(self.window_size))

        self.geometry_texture = self.ctx.texture((1, 1), components=4, dtype="f4")
        self.material_texture = self.ctx.texture((1, 1), components=4, dtype="f4")

        self.maskybox_texture = self.ctx.texture((1, 1), components=4, dtype='f4')
        print(f"{colors.HEADER}initTextures{colors.ENDC} - {colors.OKGREEN}Success{colors.ENDC}")

    def initScene(self):
        self.scene = Scene()
        self.scene.importFromFile(self.settings.rt_scenepath)
        self.createScene()
        self.createSkybox()

    def initUniforms(self):
        self.set_uniform("accumulator", "currentFrame", 1)
        self.RT_render_texture.use(location=1)

        self.set_uniform("pygameBlit", "rtTexture", 5)
        self.set_uniform("accumulator", "accumFrame", 5)
        self.accumulator_texture.use(location=5)

        self.set_uniform("RT", "u_geometry_texture", 2)
        self.geometry_texture.use(location=2)

        self.set_uniform("RT", "u_material_texture", 3)
        self.material_texture.use(location=3)
        self.set_uniform("RT", "u_resolution", (self.window_size[0], self.window_size[1]))
        
        self.set_uniform("RT", "u_skybox_texture", 4)

        self.updateRTuniforms()
        self.updateCameraUniforms()

        print(f"{colors.HEADER}initUniforms{colors.ENDC} - {colors.OKGREEN}Success{colors.ENDC}")

    def initCamera(self):
        self.allowCameraTranslation = False
        self.cameraRotation = [0,0]
        self.cameraPosition = [0,0,0]
        self.tempDir = [0,0,0]


    def createScene(self):
        self.frames = 0
        self.geometry_texture.release()
        self.material_texture.release()

        geometry_data, material_data = self.scene.pack_data()

        geometry_pixel_count = self.scene.get_object_count(in_pixels=True)
        material_pixel_count = self.scene.get_material_pixel_count()
        geometry_count = self.scene.get_object_count()
        
        self.set_uniform("RT", "u_geometry_count", geometry_count)
        self.set_uniform("RT", "u_geometry_pixel_count", geometry_pixel_count)
        
        self.geometry_texture = self.ctx.texture(
            (geometry_pixel_count, 1), 
            components=4, 
            dtype="f4", 
            data=geometry_data
        )

        self.material_texture = self.ctx.texture(
            (material_pixel_count, 1), 
            components=4, 
            dtype="f4", 
            data=material_data
        )

        self.geometry_texture.use(location=2)
        self.material_texture.use(location=3)

        sphere_count = self.scene.get_object_count(count_category="spheres")
        cube_count = self.scene.get_object_count(count_category="cubes")
        cylinder_count = self.scene.get_object_count(count_category="cylinders")
        quad_count = self.scene.get_object_count(count_category="quads")
        
        self.set_uniform("RT", "u_sphere_count", sphere_count)
        self.set_uniform("RT", "u_cube_count", cube_count)
        self.set_uniform("RT", "u_cylinder_count", cylinder_count)
        self.set_uniform("RT", "u_quad_count", quad_count)
        
        print(f"{colors.HEADER}createScene - {colors.OKGREEN}Success{colors.ENDC}")

    def createSkybox(self):
        self.frames = 0
        self.maskybox_texture.release()

        try:
            f = open(self.settings.rt_skyboxpath, "r")
            self.set_uniform("RT", "u_skybox_type", 1)
        except FileNotFoundError:
            self.set_uniform("RT", "u_skybox_type", 0)
            print(f"{colors.HEADER}createSkybox{colors.ENDC} - {colors.WARNING}FileNotFoundError: {colors.ENDC}file {colors.OKBLUE}[{self.settings.rt_skyboxpath}]{colors.ENDC} doesn't exist!")
            return       

        skyboxPath = self.settings.rt_skyboxpath
        skybox = pg.image.load(skyboxPath)

        self.maskybox_texture = self.ctx.texture(
            size=skybox.get_size(),
            components=3,
            data=pg.image.tostring(skybox, "RGB"),
        )

        self.maskybox_texture.use(location=4)

        print(f"{colors.HEADER}createSkybox - {colors.OKGREEN}Success{colors.ENDC}")


    def updateRTuniforms(self):
        self.frames = 0
        
        self.set_uniform("RT", "u_max_samples", self.settings.rt_samples)
        self.set_uniform("RT", "u_max_reflections", self.settings.rt_reflections)

    def updateCameraUniforms(self):
        self.frames = 0

        self.set_uniform("RT", "u_cameraPos", self.cameraPosition)
        self.set_uniform("RT", "u_mousePos", self.cameraRotation)

    def updateCameraPosition(self):
        yaw = self.cameraRotation[0]
        pitch = self.cameraRotation[1]
        fx = cos(yaw)*cos(pitch)
        fy = sin(yaw)*cos(pitch)
        fz = sin(pitch)

        rx = cos(yaw-pi/2)
        ry = sin(yaw-pi/2)
        rz = 0

        ux = 0 # ry*fz - rz*fy
        uy = 0 # rz*fx - rx*fz
        uz = 1 # rx*fy - ry*fx

        dirx = fx*self.tempDir[0] + rx*self.tempDir[1] + ux*self.tempDir[2]
        diry = fy*self.tempDir[0] + ry*self.tempDir[1] + uy*self.tempDir[2]
        dirz = fz*self.tempDir[0] + rz*self.tempDir[1] + uz*self.tempDir[2]

        self.cameraPosition[0] += dirx/5
        self.cameraPosition[1] += dirz/5
        self.cameraPosition[2] += -diry/5

    def update(self):
        if self.allowCameraTranslation:
            self.frames = 0
            self.updateCameraPosition()
            self.updateCameraUniforms()
            #print(self.cameraPosition)
        

    def render(self, time, delta_time):
        self.update()

        # Render modernGL
        # Render RT

        self.set_uniform("RT", "u_frame", self.frames)
        self.set_uniform("accumulator", "frame", self.frames)
        self.RT_FBO.use()
        self.RT_surface.render()

        # Accumulate frames

        self.accumulator_FBO.use()
        self.accumulator_surface.render()

        # Tonemap and display

        self.ctx.screen.use()
        self.screen_surface.render()
        self.gui.render()

        self.frames = self.frames + 1 if self.settings.rt_accumframes else 0


    def mouse_position_event(self, x, y, dx, dy):
        self.gui.imgui.mouse_position_event(x, y, dx, dy)

    def mouse_drag_event(self, x, y, dx, dy):
        self.gui.imgui.mouse_drag_event(x, y, dx, dy)

        if self.allowCameraTranslation:
            self.cameraRotation[0] += dx * 0.0174533/9
            self.cameraRotation[1] += dy * 0.0174533/9

    def mouse_scroll_event(self, x_offset, y_offset):
        self.gui.imgui.mouse_scroll_event(x_offset, y_offset)

    def mouse_press_event(self, x, y, button):
        self.gui.imgui.mouse_press_event(x, y, button)
        if button == 3:
            self.allowCameraTranslation = True

    def mouse_release_event(self, x: int, y: int, button: int):
        self.gui.imgui.mouse_release_event(x, y, button)
        if button == 3:
            self.allowCameraTranslation = False

    def key_event(self, key, action, modifiers):
        if action == self.wnd.keys.ACTION_PRESS:
            
            if key == self.wnd.keys.SPACE: self.tempDir[2] = 1
            elif modifiers.ctrl:           self.tempDir[2] = -1
            
            if key == self.wnd.keys.W:     self.tempDir[0] = 1
            elif key == self.wnd.keys.S:   self.tempDir[0] = -1
            
            if key == self.wnd.keys.D:     self.tempDir[1] = 1
            elif key == self.wnd.keys.A:   self.tempDir[1] = -1


            if key == self.wnd.keys.M: self.gui.isHidden = not self.gui.isHidden

        elif action == self.wnd.keys.ACTION_RELEASE:
            
            if key == self.wnd.keys.SPACE or not modifiers.ctrl:    self.tempDir[2] = 0
            if key == self.wnd.keys.W or key == self.wnd.keys.S:    self.tempDir[0] = 0
            if key == self.wnd.keys.D or key == self.wnd.keys.A:    self.tempDir[1] = 0
       
    def unicode_char_entered(self, char):
        self.gui.imgui.unicode_char_entered(char)


    def set_uniform(self, shader_name, uniform_name, value):
        try:
            self.shaders.programs[shader_name][uniform_name] = value
        except KeyError:
            print(f"{colors.HEADER}setUniform - {colors.WARNING}KeyError{colors.ENDC}: uniform {colors.OKBLUE}[{shader_name}]{colors.OKCYAN}[{uniform_name}]{colors.ENDC} is not used in the shader!")


if __name__ == "__main__":
    mglw.run_window_config(App)
