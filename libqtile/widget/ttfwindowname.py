import ttftextbox
from .. import bar

class TTFWindowName(ttftextbox.TTFTextBox):
    def __init__(self, width=bar.STRETCH):
        ttftextbox.TTFTextBox.__init__(self, "windowname", width=width)

    def _configure(self, qtile, bar, event, theme):
        ttftextbox.TTFTextBox._configure(self, qtile, bar, event, theme)
        self.event.subscribe("window_name_change", self.update)
        self.event.subscribe("focus_change", self.update)
        self.event.subscribe("setgroup", self.update)
        self.event.subscribe("window_add", self.update)

    def update(self):
        w = self.bar.screen.group.currentWindow
        text = w.name if w else " "
        ttftextbox.TTFTextBox.update(self, text)
