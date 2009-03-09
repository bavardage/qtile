from base import Widget
import Image
import ImageDraw
import ImageFont

class TextBox(Widget):
    def __init__(self, name, text, width=Widget.WIDTH_AUTO, align=Widget.ALIGN_LEFT):
        Widget.__init__(self, name, width, align)
        self.text = text
        self.font = None
        self.textheight = 0

    def _configure(self, wibox, theme):
        Widget._configure(self, wibox, theme)
        self.font = ImageFont.truetype(theme["%s_ttffont" % self.name],
                                       theme["%s_ttffontsize" % self.name],
                                       )
        if self.width_req == self.WIDTH_AUTO:
            self.width_req, self.textheight = self.font.getsize(self.text)
        else:
            self.textheight = self.font.getsize(self.text)[1]

    def draw(self, canvas):
        draw = ImageDraw.Draw(canvas)
        y = (canvas.size[1] - self.textheight)/2
        draw.text((0,y),
                  self.text,
                  font=self.font,
                  fill=self.theme["%s_fg_normal" % self.name],
                  )
        return canvas

    def set_text(self, text, redraw=True):
        self.text = text
        if redraw:
            self.wibox.update_widget(self)
            #TODO: do the whole width updating thing

    
    ##############
    # COMPATIBILITY: act like the old textbox
    ##############
            
    def cmd_update(self, text):
        """
            Update the text in a TextBox widget.
        """
        self.set_text(text)

    def cmd_get(self):
        """
            Retrieve the text in a TextBox widget.
        """
        return self.text
