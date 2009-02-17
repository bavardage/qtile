from base import Widget
from ..manager import Hooks

import ImageFont
import ImageDraw

class Taskbar(Widget):
    PADDING = 4
    def __init__(self, name, width, align=Widget.ALIGN_LEFT):
        Widget.__init__(self, name, width, align)
        self.qtile = None

    def _configure(self, bar, theme):
        Widget._configure(self, bar, theme)
        self.qtile = self.bar.qtile

        self.font = ImageFont.truetype(theme['taskbar_ttffont'],
                                       theme['taskbar_ttffontsize'],
                                       )
        
        self.setup_hooks()

    def draw(self, canvas):
        self.windows = self.bar.screen.group.windows
        if not self.windows:
            return canvas #no divide by zero for us
        self.box_width = canvas.size[0]/len(self.windows)
        
        names_colors = []        
        for w in self.windows:
            name = w.name
            if self.font.getsize(name)[0] > \
                    (self.box_width - 2*self.PADDING):
                name = [name, '...']
                while self.font.getsize("".join(name))[0] > \
                        (self.box_width - 2*self.PADDING):
                    name[0] = name[0][:-1]
                    if not name[0]:
                        break #It won't fit
                    #TODO: work out how to deal with this properly
                name = "".join(name)

            if w.urgent:
                fg = self.theme['taskbar_fg_urgent']
                bg = self.theme['taskbar_bg_urgent']
                border = self.theme['taskbar_border_urgent']
            elif w is self.bar.screen.group.currentWindow:
                fg = self.theme['taskbar_fg_focus']
                bg = self.theme['taskbar_bg_focus']
                border = self.theme['taskbar_border_focus']
            else:
                fg = self.theme['taskbar_fg_normal']
                bg = self.theme['taskbar_bg_normal']
                border = self.theme['taskbar_border_normal']
            
            names_colors.append((name, (fg, bg, border)))

                             
        y = (canvas.size[1] - self.font.getsize(names_colors[0][0])[1])/2
        x = 0
        draw = ImageDraw.Draw(canvas)
        for name, colors in names_colors:
            fg, bg, border = colors
            draw.rectangle((x+1,1,x+self.box_width-1,canvas.size[1]-1),
                           fill=bg, outline=border,
                           )
            text_width = self.font.getsize(name)[0]
            text_x = (self.box_width - text_width)/2 + x
            draw.text((text_x, y),
                      name,
                      font=self.font,
                      fill = fg,
                      )
            x += self.box_width
        return canvas

    def click(self, x, y):
        pos = 0
        for w in self.windows:
            if x < pos + self.box_width:
                w.minimised = False
                w.group.focus(w, False) #no mouse warp
                break
            else:
                pos += self.box_width

    def setup_hooks(self):
        @Hooks("group-to-screen")
        @Hooks("client-new")
        @Hooks("client-killed")
        @Hooks("client-urgent-hint-changed")
        @Hooks("client-focus")
        def update_hook(datadict, qtile, *args):
            self.bar.update_widget(self) #request a redraw
