from groupbox import GroupBox
import base
class TTFGroupBox(GroupBox):

    def _configure(self, qtile, bar, event, theme):
        print "Config groupbox"
        GroupBox._configure(self, qtile, bar, event, theme)
        self.borderwidth = theme['groupbox_border_width']
        self.ttffontdata = (theme['groupbox_ttffont'],
                            theme['groupbox_ttffontsize'])
    
    def draw(self):
        self.clear()
        x = self.offset + self.PADDING
        for i in self.qtile.groups:
            foreground, background, border = None, None, None
            if i.screen:
                if self.bar.screen.group.name == i.name:
                    background = self.currentBG
                    foreground = self.currentFG
                else:
                    background = self.bar.background
                    foreground = self.currentFG
                    border = True
            elif self.group_has_urgent(i):
                foreground = self.urgentFG
                background = self.urgentBG
            elif i.windows:
                foreground = self.activeFG
                background = self.bar.background
            else:
                foreground = self.inactiveFG
                background = self.bar.background
            self._drawer.ttf_textbox(i.name,
                                     x,
                                     0,
                                     self.boxwidth,
                                     self.bar.size,
                                     foreground,
                                     background,
                                     self.ttffontdata,
                                     alignment = base.CENTER,
                                     )
            if border:
                self._drawer.rectangle(
                    x, 0,
                    self.boxwidth - self.borderwidth,
                    self.bar.size - self.borderwidth,
                    borderWidth=self.borderwidth,
                    borderColor=self.border
                    )
            x += self.boxwidth
                                    
