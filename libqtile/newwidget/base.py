from .. import command
from ..manager import Hooks

class WidgetData:
    width = 0
    xoffset = 0
    yoffset = 0
    image = None
    layer = None
    def __init__(self, widget):
        self.widget = widget

'''
Concerning Widget Sizing
------------------------
Since widgets have to be able to cope with varying sizes of bar, the sizing can be an issue.

This is how sizing goes:

 - before _configure returns, widgets must have set a height_req and a width_req.

 - wiboxes will size themselves based on these widths

 - _reconfigure will be called. At this point widgets will know what height/widths the layers and wiboxes will have. They can then change their width_req and height_req
 
 - things will be drawn, and we will see that it was good

Note:
 if width_req and height_req are not set accurately, the 
 widget may miss out on click events and such things
  - if height_req is not used, it will be set to the layer height in _reconfigure

'''

FALLBACK_HEIGHT = 20 #don't let things request totally no height

class Widget(command.CommandObject):
    aligns = ["left", "right"]
    height_req = None
    width_req = None
    def __init__(self, name, width, align="left", height=FALLBACK_HEIGHT):
        self.widget_data = WidgetData(self)
        self.name = name
        self.width_req = width
        self.height_req = height
        self.align = align
        self.wibox = None
        self.theme = None

        self.need_resize = False
        self._init_hooks()

    def _configure(self, wibox, theme):
        self.wibox = wibox
        self.theme = theme

    def _reconfigure(self):
        if not self.height_req:
            self.height_req = self.widget_data.layer.h
    
    def draw(self, canvas):
        raise NotImplementedError, "Widget must have a draw function"

    def click(self, x, y):
        pass

    def request_resize(self):
        self.need_resize = True

    def _init_hooks(self):
        @Hooks("wibox-drawn")
        def update_size(datadict, qtile, *args):
            if self.need_resize:
                self.wibox.update_widget_size(self)
            self.need_resize = False

    ############
    # Commands #
    ############
    def _items(self, name):
        if name == "wibox":
            return self.wibox

    def _select(self, name, sel):
        if name == "wibox":
            return self.wibox

    def cmd_info(self):
        return self.info()

    def info(self):
        return dict(
            name = self.name,
            align = self.align,
            width_req = self.width_req,
            )
