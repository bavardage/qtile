from base import Widget

class TestWidget(Widget):
    def __init__(self, name, width, color, align="left",
                 reconfigure_width=None):
        print "initialising testwidget"
        Widget.__init__(self, name, width, align)
        self.color = color
        self.reconfigure_width = reconfigure_width
        print "Done with init"

    def _reconfigure(self):
        if self.reconfigure_width:
            self.width_req = self.reconfigure_width

    def draw(self, canvas):
        w, h = canvas.size
        canvas.paste(self.color, (0,0,w,h))
        return canvas
