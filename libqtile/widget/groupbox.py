from .. import bar
from ..manager import Hooks
import base

class GroupBox(base._Widget):
    BOXPADDING_SIDE = 8
    PADDING = 3
    BORDERWIDTH = 1
    def click(self, x, y):
        groupOffset = x/self.boxwidth
        if len(self.qtile.groups) - 1 >= groupOffset:
            self.bar.screen.setGroup(self.qtile.groups[groupOffset])

    def _configure(self, qtile, bar, theme):
        base._Widget._configure(self, qtile, bar, theme)
        self.textheight, self.textwidth = self._drawer.textsize(
                                                self._drawer.font,
                                                *[i.name for i in qtile.groups]
                                            )

        self.currentFG, self.currentBG = theme['groupbox_fg_focus'], theme['groupbox_bg_focus']
        self.activeFG, self.inactiveFG = theme['groupbox_fg_active'], theme['groupbox_fg_normal']
        self.urgentFG, self.urgentBG = theme['groupbox_fg_urgent'], theme['groupbox_bg_urgent']
        self.border = theme['groupbox_border_normal']
        if theme["groupbox_font"]:
            self.font = theme["groupbox_font"]

        self.boxwidth = self.BOXPADDING_SIDE*2 + self.textwidth
        self.width = self.boxwidth * len(qtile.groups) + 2 * self.PADDING
        self.setup_hooks()

    def group_has_urgent(self, group):
        return len([w for w in group.windows if w.urgent]) > 0

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
            self._drawer.textbox(
                i.name,
                x, 0, self.boxwidth, self.bar.size,
                padding = self.BOXPADDING_SIDE,
                foreground = foreground,
                background = background,
                alignment = base.CENTER,
            )
            if border:
                self._drawer.rectangle(
                    x, 0,
                    self.boxwidth - self.BORDERWIDTH,
                    self.bar.size - self.BORDERWIDTH,
                    borderWidth = self.BORDERWIDTH,
                    borderColor = self.border
                )
            x += self.boxwidth

    def setup_hooks(self):
        draw = self.draw
        @Hooks("client-new")
        @Hooks("client-urgent-hint-changed")
        @Hooks("client-killed")
        @Hooks("group-set")
        @Hooks("group-add")
        def hook_response(datadict, qtile, *args):
            self.draw()
            
