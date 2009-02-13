from textbox import TextBox
from base import Widget
from ..manager import Hooks

from Xlib import XK

class PromptBox(TextBox):
    def __init__(self, name, prompt, width, align=Widget.ALIGN_LEFT):
        TextBox.__init__(self, name, prompt, width, align)
        self.prompt = prompt
        self.command_text = ''

    def _configure(self, bar, theme):
        TextBox._configure(self, bar, theme)

    def grab_keyboard(self):
        self.bar.grab_keyboard(self)

    def ungrab_keyboard(self):
        self.bar.ungrab_keyboard(self)

    def done(self):
        Hooks.call_hook("promptbox-%s-done", self.command_text)
        self.abort()

    def abort(self):
        self.command_text = ""
        self.ungrab_keyboard()
        self.update()

    def update(self):
        self.set_text(" ".join((self.prompt, self.command_text)))

    def handle_KeyPress(self, e):
        keysym = self.bar.qtile.display.keycode_to_keysym(e.detail, 0)
        keystring = XK.keysym_to_string(keysym)
        if keystring == '\x1b':
            self.abort()
        elif keystring == '\r':
            self.done()
        else:
            if keystring:
                self.command_text += keystring
                self.update()

    def cmd_start_grab(self):
        self.grab_keyboard()
