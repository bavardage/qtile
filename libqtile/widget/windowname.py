import base
from ..manager import Hooks

class WindowName(base._TextBox):
    def _configure(self, qtile, bar, theme):
        base._Widget._configure(self, qtile, bar, theme)
        self.setup_hooks()

    def setup_hooks(self):
        @Hooks("client-focus")
        @Hooks("client-name-changed")
        def hook_response(datadict, qtile, *args):
            self.update()

    def update(self):
        w = self.bar.screen.group.currentWindow
        self.text = w.name if w else " "
        self.draw()


