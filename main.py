import moderngl_window as mglw
import moderngl as mgl
import imgui
from moderngl_window.integrations.imgui import ModernglWindowRenderer

from settings import TOMLParser
from VAO import VAO
from scene import Scene
from shader_program import ShaderProgram
from coloredText import bcolors as colors

import pygame as pg
from numpy.random import rand



class App( mglw.WindowConfig ):
    TOMLParser = TOMLParser()
    TOMLParser.loadConfig( "settings.toml" )
    
    gl_version  = TOMLParser.getValue( "settings", "WINDOW/GLversion" )
    title       = TOMLParser.getValue( "settings", "WINDOW/title" )
    window_size = TOMLParser.getValue( "settings", "WINDOW/resolution" )
    resizable   = TOMLParser.getValue( "settings", "WINDOW/resizable" )

    def __init__( self, **kwargs ):
        super().__init__( **kwargs )

        self.initShaders()
        self.initSurfaces()
        self.initTextures()
        self.initScene()
        self.initUniforms()

        self.frames = 0
        imgui.create_context()
        self.imgui = ModernglWindowRenderer(self.wnd)

    def initShaders( self):
        self.shaders = ShaderProgram( self.ctx, "programs" )
        self.shaders.load_program( "pygameBlit" )
        self.shaders.load_program( "RT" )
        self.shaders.load_program( "accumulator" )

    def initSurfaces( self ):
        self.vao = VAO( self.ctx )
        self.screenSurface = self.vao.get_quadfs(
            self.shaders.programs[ "pygameBlit" ]
        )
        self.RTSurface = self.vao.get_quadfs(
            self.shaders.programs[ "RT" ]
        )
        self.AccumulatorSurface = self.vao.get_quadfs(
            self.shaders.programs[ "accumulator" ]
        )

    def initTextures( self ):
        self.RTRenderTEX = self.ctx.texture(self.window_size, components=4, dtype="f4")
        self.RTRenderFBO = self.ctx.framebuffer(
            self.RTRenderTEX, self.ctx.depth_renderbuffer( self.window_size )
        )

        self.AccumulatorTEX = self.ctx.texture(self.window_size, components=4, dtype="f4")
        self.AccumulatorFBO = self.ctx.framebuffer(
            self.AccumulatorTEX, self.ctx.depth_renderbuffer( self.window_size )
        )

    def initScene( self ):
        self.scene = Scene()

        scenePath = self.TOMLParser.getValue( "settings", "SCENE/scenefile")
        if scenePath != "":
            pass
        skyboxPath = self.TOMLParser.getValue( "settings", "SCENE/skyboxfile")
        if skyboxPath != "":
            skybox = pg.image.load(skyboxPath)
            self.skyboxTexture = self.ctx.texture(size=skybox.get_size(), components=3, data=pg.image.tostring(skybox, 'RGB'))
            self.set_uniform("RT", "skyboxType", 1)
        else:
            self.skyboxTexture = self.ctx.texture(size=(128,128), components=3, data=b'\xff\x00\xff\x00\x00\x00'*128*64)
            self.set_uniform("RT", "skyboxType", 0)

        self.set_uniform( "RT", "skybox", 4)
        self.skyboxTexture.use(location=4)
        
        self.scene.addQuad(( 0,-3,-3), ( 0, 3,-3), ( 0, 3, 3), ( 0,-3, 3), (0.8,0.8,0.8), (0.8,0.8,0.8), (0.1, 0.0, 0.0, 0.0)) # back wall
        self.scene.addQuad(( 0,-3,-3), ( 0, 3,-3), (-3, 3,-3), (-3,-3,-3), (0.8,0.1,0.1), (0.8,0.1,0.1), (0.1, 0.0, 0.0, 0.0)) # left wall
        self.scene.addQuad(( 0, 3, 3), ( 0,-3, 3), (-3,-3, 3), (-3, 3, 3), (0.1,0.8,0.1), (0.1,0.8,0.1), (0.1, 0.0, 0.0, 0.0)) # right wall
        self.scene.addQuad(( 0, 3,-3), ( 0, 3, 3), (-3, 3, 3), (-3, 3,-3), (0.8,0.8,0.8), (0.8,0.8,0.8), (0.1, 0.0, 0.0, 0.0)) # top wall
        self.scene.addQuad(( 0,-3,-3), ( 0,-3, 3), (-3,-3, 3), (-3,-3,-3), (0.8,0.8,0.8), (0.8,0.8,0.8), (0.1, 0.0, 0.0, 0.0)) # bottom wall
        
        self.scene.addQuad((-1, 2.999,-1.5), (-1, 2.999, 1.5), (-2, 2.999, 1.5), (-2, 2.999,-1.5), (0.8,0.8,0.45), (0.8,0.8,0.8), (0.9, 0.0, 12.0, 0.0)) # top light
        self.scene.addSphere((-1,-1.0,0), 1., (1,1,1), (1,1,1), (0,0.5,0,1))
        
        
        geometryData, materialData = self.scene.packObjects()

        geometryPixelCount = self.scene.getObjectCount( inPixels=True )
        materialPixelCount = self.scene.getMaterialPixelCount()
        geometryCount = self.scene.getObjectCount()
        self.set_uniform( "RT", "geometryCount", geometryCount )
        self.set_uniform( "RT", "geometryPixelCount", geometryPixelCount )

        self.geometryTexture = self.ctx.texture((geometryPixelCount, 1), components=4, dtype="f4" )
        self.geometryTexture.write(geometryData)
        self.materialTexture = self.ctx.texture((materialPixelCount, 1), components=4, dtype="f4" )
        self.materialTexture.write(materialData)

        sphereCount = self.scene.getObjectCount( countCategory="spheres" )
        cubeCount = self.scene.getObjectCount( countCategory="cubes" )
        cylinderCount = self.scene.getObjectCount( countCategory="cylinders" )
        quadCount = self.scene.getObjectCount( countCategory="quads" )
        self.set_uniform( "RT", "sphereCount", sphereCount )
        self.set_uniform( "RT", "cubeCount", cubeCount )
        self.set_uniform( "RT", "cylinderCount", cylinderCount )
        self.set_uniform( "RT", "quadCount", quadCount)

    def initUniforms( self ):
       
        self.set_uniform( "accumulator", "currentFrame", 1)
        self.RTRenderTEX.use(location=1)

        self.set_uniform( "pygameBlit", "rtTexture", 5)
        self.set_uniform( "accumulator", "accumFrame", 5)
        self.AccumulatorTEX.use(location=5)

        self.set_uniform( "RT", "geometryTexture", 2)
        self.geometryTexture.use( location=2 )

        self.set_uniform( "RT", "materialTexture", 3)
        self.materialTexture.use( location=3 )

        self.set_uniform( "RT", "u_resolution", (self.window_size[0],self.window_size[1]) )
        
    def render( self, time: float, delta_time: float ):
        #self.pgRenderer.render()
        #pg.transform.scale_by(self.pgRenderer.surface, )
        #self.pgTexture.write( self.pgRenderer.surface.get_view('1') )

        #Render modernGL
        #Render RT
        self.set_uniform("RT", "u_frame", self.frames)
        self.set_uniform("accumulator", "frame", self.frames)
        self.RTRenderFBO.use()
        self.RTSurface.render()

        self.AccumulatorFBO.use()
        self.AccumulatorSurface.render()
        #Blit RT with pygame onto the screen
        self.ctx.screen.use()
        self.screenSurface.render()

        #Render ImGUI
        self.render_ui()

        self.frames += 1
    
    def render_ui( self ):
        imgui.new_frame()

        #Render each Window
        if imgui.begin("mainMenu"):
            imgui.push_item_width(imgui.get_window_width() * 0.33)
            changed,testVar = imgui.input_int(
                "Test", 5, step=1024, step_fast=2**15
            )
            imgui.pop_item_width()

        #if imgui.begin("Appearance"):
        #    pass

        imgui.end()
        imgui.render()
        self.imgui.render(imgui.get_draw_data())

    def set_uniform(self, shader_name, uniform_name, value):
        try:
            self.shaders.programs[shader_name][uniform_name] = value
        except KeyError:
            print(f"{colors.HEADER}setUniform - {colors.WARNING}KeyError{colors.ENDC}: uniform {colors.OKBLUE}[{shader_name}]{colors.OKCYAN}[{uniform_name}]{colors.ENDC} is not used in the shader!")


    
    
    
    def close( self ):
        self.shaders.destroy()
    
    
    def mouse_position_event(self, x, y, dx, dy):
        self.imgui.mouse_position_event(x, y, dx, dy)

    def mouse_drag_event(self, x, y, dx, dy):
        self.imgui.mouse_drag_event(x, y, dx, dy)

    def mouse_scroll_event(self, x_offset, y_offset):
        self.imgui.mouse_scroll_event(x_offset, y_offset)

    def mouse_press_event(self, x, y, button):
        self.imgui.mouse_press_event(x, y, button)

    def mouse_release_event(self, x: int, y: int, button: int):
        self.imgui.mouse_release_event(x, y, button)

    def unicode_char_entered(self, char):
        self.imgui.unicode_char_entered(char)

mglw.run_window_config(App)