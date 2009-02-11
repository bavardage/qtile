from base import Widget
from .. import command
import Image

class IconBox(Widget):
    def __init__(self, name, icon, align=Widget.ALIGN_LEFT, resize=True):
        self.icon = Image.open(icon)
        self.resize = resize
        Widget.__init__(self, name, self.icon.size[0], align)
        
    def _configure(self, bar, theme):
        Widget._configure(self, bar, theme)
        if self.resize:
            w,h = self.icon.size
            self.width_req = self.bar.height
            scale = float(self.bar.height)/h
            new_size = (int(scale * w), int(scale * h))
            self.icon.thumbnail(new_size,
                                Image.ANTIALIAS
                                )
    
    def draw(self, canvas):
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
            status, val = self.bar.qtile.server.call(
                (c.selectors, c.name, c.args, c.kwargs)
                )
            if status in (command.ERROR, command.EXCEPTION):
                s = "ClickableIcon command error %s: %s" % (c.name, val)
        else:
            return
