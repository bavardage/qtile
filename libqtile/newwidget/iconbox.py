from base import Widget
from .. import command
import Image

FALLBACK_SIZE = 20

#TODO: handle resizing better

'''
Resizing
--------
There are several ways this widget will be sized.

'''

class IconBox(Widget):
    min_width = FALLBACK_SIZE
    min_height = FALLBACK_SIZE
    resizes = ["none", "auto"]
    def __init__(self, name, icon, width=None, align="left",
                 resize=True, expand_bar_height=True):

        self.orig_icon = Image.open(icon)
        self.icon = None
        self.image_size = list(self.orig_icon.size)
        self.resize = resize
        self.expand_bar_height = expand_bar_height
        Widget.__init__(self,
                        name,
                        width,
                        align
                        )
        self.waiting_for_size = True
        
    def _configure(self, wibox, theme):
        Widget._configure(self, wibox, theme)
        if self.width_req and self.resize:
            imw,imh = self.orig_icon.size
            imh = float(self.width_req)/imw*imh
            imw = self.width_req
            self.image_size = [imw, imh]
            if self.expand_bar_height:
                self.height_req = imh
            else:
                pass #don't set height_req
            self.waiting_for_size = False
        elif self.width_req:
            self.image_size[0] = self.width_req
            if self.expand_bar_height:
                self.height_req = self.image_size[1]
        elif self.resize:
            # will resize later,
            self.width_req = 0
            self.height_req = 0
        else:
            self.width_req = self.orig_icon.size[0]
            if self.expand_bar_height:
                self.height_req = self.orig_icon.size[1]
            self.waiting_for_size = False #keep it as it is

    def _reconfigure(self):
        if self.waiting_for_size:
            imh = self.widget_data.layer.h
            w,h = self.orig_icon.size
            imw = float(imh)/h*w
            self.image_size = [imw, imh]
            self.width_req, self.height_req = self.image_size
            self.waiting_for_size = False
            

    def generate_icon(self):
        if self.icon:
            return
        self.icon = self.orig_icon.copy()
        self.icon.thumbnail(self.image_size,
                            Image.ANTIALIAS,
                            )
        if self.icon.mode != "RGBA":
            self.icon = self.icon.convert("RGBA")

    def draw(self, canvas):
        canvas_width, canvas_height = canvas.size        
        self.generate_icon()
        w,h = self.icon.size
        canvas.paste(self.icon, (0,0, w, h), self.icon)
        return canvas


class ClickableIcon(IconBox):
    def __init__(self, name, icon, command, width=None,
                 align="left", resize=True, expand_bar_height=True):
        self.command = command
        IconBox.__init__(self, name, icon, width, align, 
                         resize, expand_bar_height)

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
