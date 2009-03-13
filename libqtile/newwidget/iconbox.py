from base import Widget
from .. import command
import Image

FALLBACK_WIDTH = 32

#TODO: handle resizing better

class IconBox(Widget):
    def __init__(self, name, icon, align=Widget.ALIGN_LEFT, resize=True):
        self.orig_icon = Image.open(icon)
        self.resize = resize
        Widget.__init__(self, name, self.orig_icon.size[0], align)
        
    def _configure(self, wibox, theme):
        Widget._configure(self, wibox, theme)
        if self.resize:
            self.width_req = self.wibox.h 
            if self.width_req == "expand":
                self.width_req = FALLBACK_WIDTH
                self.height_req = FALLBACK_WIDTH
        else:
            self.width_req = self.orig_icon.size[0]
            self.height_req = self.orig_icon.size[1]
        print "icon's w_req is", self.width_req
    
    def draw(self, canvas):
        canvas_width, canvas_height = canvas.size
        self.icon = self.orig_icon.copy()
        if self.resize:
            w,h = self.icon.size
            scale = float(canvas_height)/h
            new_size = (int(scale * w), int(scale * h))
            self.icon.thumbnail(new_size,
                                Image.ANTIALIAS
                                )
            if self.icon.mode != "RGBA":
                self.icon = self.icon.convert("RGBA")

        w,h = self.icon.size
        canvas.paste(self.icon, (0,0, w, h), self.icon)
        return canvas


class ClickableIcon(IconBox):
    def __init__(self, name, icon, command, align=Widget.ALIGN_LEFT, resize=True):
        IconBox.__init__(self, name, icon, align, resize)
        self.command = command

    def click(self, x, y):
        c = self.command
        if c.check(self):
            status, val = self.wibox.qtile.server.call(
                (c.selectors, c.name, c.args, c.kwargs)
                )
            if status in (command.ERROR, command.EXCEPTION):
                s = "ClickableIcon command error %s: %s" % (c.name, val)
        else:
            return
