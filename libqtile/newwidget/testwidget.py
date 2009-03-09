from base import Widget

class TestWidget(Widget):
    def __init__(self, name, width, color, align=Widget.ALIGN_LEFT):
        print "initialising testwidget"
        Widget.__init__(self, name, width, align)
        self.color = color
        print "Done with init"

    def draw(self, canvas):
        w, h = canvas.size
        canvas.paste(self.color, (0,0,w,h))
        return canvas
