import moderngl_window as mglw
import moderngl as mgl
from settings import TOMLParser
from VAO import VAO
from scene import Scene
from shader_program import ShaderProgram
from coloredText import bcolors as colors
import pygame as pg

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
        

        pg.init()
        self.pgSurface = pg.Surface( self.window_size, pg.SRCALPHA )

    def initShaders( self):
        self.shaders = ShaderProgram( self.ctx, "programs" )
        self.shaders.load_program( "pygameBlit" )
        self.shaders.load_program( "RT")

    def initSurfaces( self ):
        self.vao = VAO( self.ctx )
        self.screenSurface = self.vao.get_quadfs(
            self.shaders.programs[ "pygameBlit" ]
        )
        self.RTSurface = self.vao.get_quadfs(
            self.shaders.programs[ "RT" ]
        )

    def initTextures( self ):
        self.pgTexture = self.ctx.texture( self.window_size, components=4 )
        self.pgTexture.filter = mgl.NEAREST, mgl.NEAREST

        self.RTRenderTEX = self.ctx.texture(self.window_size, components=4, dtype="f4")
        self.RTRenderFBO = self.ctx.framebuffer(
            self.RTRenderTEX, self.ctx.depth_renderbuffer( self.window_size )
        )

    def initScene( self ):
        self.scene = Scene()
        self.scene.addSphere( (0,0,0), 0.5)
        self.scene.addSphere( (0,0,1), 0.4)
        self.scene.addCube( (0,1,0), (0.5,0.5,0.5))
        geometryData = self.scene.packObjects()
        pixelCount = self.scene.getObjectCount( inPixels=True )
        geometryCount = self.scene.getObjectCount()
        self.geometryTexture = self.ctx.texture( ( pixelCount ,1 ), 4, dtype="f4" )
        self.geometryTexture.write( geometryData )
        self.set_uniform( "RT", "geometryCount", geometryCount )
        self.set_uniform( "RT", "geometryPixelCount", pixelCount )
        sphereCount = self.scene.getObjectCount( countCategory="spheres" )
        cubeCount = self.scene.getObjectCount( countCategory="cubes" )
        self.set_uniform( "RT", "sphereCount", sphereCount )
        self.set_uniform( "RT", "cubeCount", cubeCount )

    def initUniforms( self ):
        self.set_uniform( "pygameBlit", "pgTexture", 0 )
        self.pgTexture.use(location=0)

        self.set_uniform( "pygameBlit", "rtTexture", 1)
        self.RTRenderTEX.use(location=1)

        self.set_uniform( "RT", "geometryTexture", 2)
        self.geometryTexture.use( location=2 )

        self.set_uniform( "RT", "u_resolution", (self.window_size[0],self.window_size[1]) )
        

    def close( self ):
        self.shaders.destroy()
    
    def render( self, time: float, delta_time: float ):
        #Render pygame
        self.pgSurface.fill( (0,0,0,0) )
        pg.draw.rect( self.pgSurface, (255,21,255,255), (200,200,200,200))

        self.pgTexture.write( self.pgSurface.get_view('1') )

        #Render modernGL
        #Render RT
        self.RTRenderFBO.use()
        self.RTSurface.render()
        #Blit RT with pygame onto the screen
        self.ctx.screen.use()
        self.screenSurface.render()
    
    def set_uniform(self, shader_name, uniform_name, value):
        try:
            self.shaders.programs[shader_name][uniform_name] = value
        except KeyError:
            print(f"{colors.WARNING}Warning{colors.ENDC} - uniform path [{shader_name}][{uniform_name}] not defined in shader!")


    
    
    
    
    
    
    def key_event(self, key, action, modifiers): ...

    def mouse_position_event(self, x, y, dx, dy):
        print("Mouse position:", x, y, dx, dy)

    def mouse_drag_event(self, x, y, dx, dy):
        print("Mouse drag:", x, y, dx, dy)

    def mouse_scroll_event(self, x_offset: float, y_offset: float):
        print("Mouse wheel:", x_offset, y_offset)

    def mouse_press_event(self, x, y, button):
        print("Mouse button {} pressed at {}, {}".format(button, x, y))

    def mouse_release_event(self, x: int, y: int, button: int):
        print("Mouse button {} released at {}, {}".format(button, x, y))

mglw.run_window_config(App)