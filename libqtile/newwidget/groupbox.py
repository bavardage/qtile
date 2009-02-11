from base import Widget
from ..manager import Hooks

import ImageFont
import ImageDraw

class GroupBox(Widget):
    PADDING = 4
    def __init__(self, name, align=Widget.ALIGN_LEFT):
        Widget.__init__(self, name, width=-1, align=align)
        self.qtile = None
        self.groups = []
        self.groupnamewidths = {} #dict of text and widths
        self.setup_hooks()

    def _configure(self, bar, theme):
        Widget._configure(self, bar, theme)
        
        self.qtile = self.bar.qtile

        self.font = ImageFont.truetype(theme['groupbox_ttffont'],
                                       theme['groupbox_ttffontsize'],
                                       )

        self.groups = self.qtile.groups
        for group in self.groups:
            self.groupnamewidths[group.name] = \
                self.font.getsize(group.name)[0]

        self.width_req = sum([w for g,w in self.groupnamewidths.items()]) + \
            len(self.groups) * self.PADDING * 2 #pad each side

    def has_urgent(self, group):
        return len([w for w in group.windows if w.urgent]) > 0

    def draw(self, canvas):
        draw = ImageDraw.Draw(canvas)
        y = (canvas.size[1] - self.font.getsize(self.groups[0].name)[1])/2
        
        x = self.PADDING
        for g in self.groups:
            if g.screen:
                fg = self.theme["groupbox_fg_focus"]
            elif self.has_urgent(g):
                fg = self.theme["groupbox_fg_urgent"]
            elif g.windows:
                fg = self.theme["groupbox_fg_active"]
            else:
                fg = self.theme["groupbox_fg_normal"]
            draw.text((x,y),
                      g.name,
                      font=self.font,
                      fill=fg
                      )
            x += self.groupnamewidths[g.name] + 2 * self.PADDING
        return canvas
                      

    def click(self, x, y):
        print "GROUPBOX GOT A CLICK"
        print "it was at %s %s" % (x,y)
        pos = 0
        for g in self.groups:
            w = self.groupnamewidths[g.name] +  2*self.PADDING
            print "Group: %s, pos %s, pos+w %s" % (g.name, pos, pos+w)
            if x < pos + w:
                g.cmd_toscreen()
                break
            else:
                pos += w


    def setup_hooks(self):
        @Hooks("group-to-screen")
        @Hooks("client-new")
        @Hooks("client-killed")
        @Hooks("client-urgent-hint-changed")
        def update_hook(datadict, qtile, *args):
            print "%s needs redraw" % self.name