from .. import command

class Widget(command.CommandObject):
    ALIGN_LEFT, ALIGN_RIGHT = 1,2
    WIDTH_AUTO = -1
    def __init__(self, name, width, align=ALIGN_LEFT):
        self.name = name
        self.width_req = width
        self.align = align
        self.wibox = None
        self.theme = None

    def _configure(self, wibox, theme):
        self.wibox = wibox
        self.theme = theme
    
    def draw(self, canvas):
        raise NotImplementedError, "Widget must have a draw function"

    def click(self, x, y):
        pass

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
