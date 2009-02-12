
class Widget:
    ALIGN_LEFT, ALIGN_RIGHT = 1,2
    WIDTH_AUTO = -1
    def __init__(self, name, width, align=ALIGN_LEFT):
        self.name = name
        self.width_req = width
        self.align = align
        self.bar = None
        self.theme = None

    def _configure(self, bar, theme):
        self.bar = bar
        self.theme = theme
    
    def draw(self, canvas):
        raise NotImplementedError, "Widget must have a draw function"

    def click(self, x, y):
        pass
