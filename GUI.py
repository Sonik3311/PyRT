import imgui
from moderngl_window.integrations.imgui import ModernglWindowRenderer


class ImGUIManager:
    def __init__(self, app):
        self.app = app
        imgui.create_context()
        self.imgui = ModernglWindowRenderer(self.app.wnd)

        self.openMenus = {
            "fileMenu": [False, {}],
            "settingsMenu": [False, {"render": [False, {}]}],
        }

    def closeTree_exclude_startNode(self, node):
        for nodes in node[1]:
            self.closeTree(node[1][nodes])

    def closeTree(self, node):
        node[0] = False
        for nodes in node[1]:
            self.closeTree(node[1][nodes])

    def render(self):
        imgui.new_frame()
        changedSettings = False
        # Render each Window (garbage)
        if imgui.begin(
            "mainMenu",
            flags=imgui.WINDOW_NO_TITLE_BAR
            | imgui.WINDOW_NO_MOVE
            | imgui.WINDOW_NO_RESIZE
            | imgui.WINDOW_NO_SCROLLBAR,
        ):
            if imgui.button(label="File"):
                self.openMenus["fileMenu"][0] = not self.openMenus["fileMenu"][0]
                self.closeTree(self.openMenus["settingsMenu"])

            imgui.same_line()

            if imgui.button(label="Settings"):
                self.openMenus["settingsMenu"][0] = not self.openMenus["settingsMenu"][0]
                if not self.openMenus["settingsMenu"][0]:
                    self.closeTree(self.openMenus["settingsMenu"])
                #else:
                self.closeTree(self.openMenus["fileMenu"])
        imgui.end()

        ##############################################################################

        if self.openMenus["fileMenu"][0] and imgui.begin(
            "fileMenu",
            flags=imgui.WINDOW_NO_TITLE_BAR
            | imgui.WINDOW_NO_MOVE
            | imgui.WINDOW_NO_RESIZE
            | imgui.WINDOW_NO_SCROLLBAR,
        ):
            imgui.end()

        ##############################################################################

        if self.openMenus["settingsMenu"][0] and imgui.begin(
            "settingsMenu",
            flags=imgui.WINDOW_NO_TITLE_BAR
            | imgui.WINDOW_NO_MOVE
            | imgui.WINDOW_NO_RESIZE
            | imgui.WINDOW_NO_SCROLLBAR,
        ):
            if imgui.button(label="Render"):
                self.openMenus["settingsMenu"][1]["render"][0] = not self.openMenus[
                    "settingsMenu"
                ][1]["render"][0]
            imgui.end()

        ##############################################################################

        if self.openMenus["settingsMenu"][1]["render"][0] and imgui.begin(
            "RenderSettings",
            flags=imgui.WINDOW_NO_TITLE_BAR
            | imgui.WINDOW_NO_MOVE
            | imgui.WINDOW_NO_RESIZE
            | imgui.WINDOW_NO_SCROLLBAR,
        ):
            clicked, backend_flags = imgui.checkbox(
                label="Accumulate frames", state=self.app.settings.rt_accumframes
            )
            if clicked:
                self.app.settings.rt_accumframes = not self.app.settings.rt_accumframes
                changedSettings = True

            imgui.push_item_width(40)
            changedsmp, samples = imgui.input_int(
                "Samples", max(self.app.settings.rt_samples, 1), step=0
            )
            if changedsmp:
                self.app.settings.rt_samples = min(max(samples, 1), 1024)
                changedSettings = True

            changedrfl, reflections = imgui.input_int(
                "Reflections", max(self.app.settings.rt_reflections, 2), step=0
            )
            if changedrfl:
                self.app.settings.rt_reflections = min(max(reflections, 2), 1024)
                changedSettings = True
            imgui.pop_item_width()
            imgui.end()

        if changedSettings:
            self.app.updateRTuniforms()
            self.app.updateAccumUniforms()

        imgui.render()
        self.imgui.render(imgui.get_draw_data())
