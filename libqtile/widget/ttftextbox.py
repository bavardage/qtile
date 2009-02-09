import base
import Image
import ImageDraw
import ImageFont


class TTFTextBox(base._Widget):
    WIDTH_AUTO = -2
    def __init__(self, name, text=" ", width=WIDTH_AUTO):
        self.name = name
        self.text = text
        #some defaults
        self.width, self.height = width,0
        self.updated = True
        self.ttffont = None
        self.font_im = None
        self.fgcolor = None
        self.bgcolor = None

    def _configure(self, qtile, bar, event, theme):
        base._Widget._configure(self, qtile, bar, event, theme)
        self.height = self.bar.size
        self.fgcolor = theme['%s_fg_normal' % self.name]
        self.bgcolor = theme['%s_bg_normal' % self.name]
        try:
            self.ttffont = \
                ImageFont.truetype(theme['%s_ttffont' % self.name], 
                                   theme['%s_ttffontsize' % self.name]
                                   )
            if self.width == self.WIDTH_AUTO:
                self.width, self.height = self.ttffont.getsize(self.text)
        except IOError:
            raise IOError, "Font file not valid - oh noes"
        self.updated = True
                
    def draw(self):
        if self.updated:
            self.font_im = self._drawer.ttf_pil_image(self.text,
                                                      self.fgcolor,
                                                      self.bgcolor,
                                                      self.ttffont,
                                                      width=self.width
                                                      )
            self.updated = False
        self._drawer.win.put_pil_image(self._drawer.gc,
                                       self.offset,
                                       0,
                                       self.font_im
                                       )

    def update(self, text):
        self.text = text
        self.updated = True
        self.draw()

    def cmd_update(self, text):
        self.update(text)

    def cmd_get(self):
        return self.text
