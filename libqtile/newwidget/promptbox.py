import os

from textbox import TextBox
from base import Widget
from ..manager import Hooks

from Xlib import XK

class Completer:
    def complete(text):
        ''' returns a generator '''
        raise NotImplementedError
    
class PathCompleter(Completer):
    def __init__(self):
        path = os.path.expandvars('$PATH').split(':')
        self.completions = set()
        for directory in path:
            try:
                self.completions.update(
                    os.listdir(directory)
                    )
            except:
                pass
        self.completions = list(self.completions)
        self.completions.sort()
        
    def complete(self, text):
        if not self.completions:
            raise StopIteration
        suggested_once = True
        while suggested_once: #keep suggesting
            suggested_once = False
            for comp in self.completions:
                if comp[:len(text)] == text:
                    yield comp
                    suggested_once = True

class PromptBox(TextBox):
    def __init__(self, name, prompt, width, align="left", completer=None):
        TextBox.__init__(self, name, prompt, width, align)
        self.prompt = prompt
        self.command_text = ''
        self.cursor_position = 0
        self.completer = (completer if completer else PathCompleter())
        self.completer_generator = None

    def _configure(self, wibox, theme):
        TextBox._configure(self, wibox, theme)

    def grab_keyboard(self):
        self.wibox.grab_keyboard(self)

    def ungrab_keyboard(self):
        self.wibox.ungrab_keyboard(self)

    def done(self):
        Hooks.call_hook("promptbox-%s-done" % self.name, self.command_text)
        self.abort()

    def abort(self):
        self.command_text = ""
        self.cursor_position = 0
        self.stop_completion()
        self.ungrab_keyboard()
        self.update()

    def update(self):
        self.set_text(" ".join((self.prompt, self.command_text)))

    def move_cursor(self, amount):
        print "Moving cursor", amount
        if amount == 'beginning':
            self.cursor_position = 0
        elif amount == 'end':
            self.cursor_position = len(self.command_text)
        else:
            self.cursor_position += amount
            if self.cursor_position < 0 or \
                    self.cursor_position > len(self.command_text):
                if self.command_text:
                    self.cursor_position %= len(self.command_text)
                else:
                    self.cursor_position = 0

    def do_completion(self):
        if not self.completer_generator:
            self.completer_generator = \
                self.completer.complete(self.command_text)
        try:
            result = self.completer_generator.next()
            self.command_text = result
            self.move_cursor('end')
        except:
            self.stop_completion()
            return

    def stop_completion(self):
        self.completer_generator = None
            
    def handle_KeyPress(self, e):
        keysym = self.wibox.qtile.display.keycode_to_keysym(e.detail, e.state)
        keystring = self.wibox.qtile.display.lookup_string(keysym)
        print "keysym", keysym
        print "keycode", e.detail
        print "keystring", keystring
        print "state", e.state
        if keysym != XK.XK_Tab:
            self.stop_completion()
        if keysym == XK.XK_Tab:
            self.do_completion()
        if keysym == XK.XK_Escape:
            self.abort()
        elif keysym == XK.XK_Return:
            self.done()
        elif keysym == XK.XK_BackSpace:
            if self.command_text:
                self.command_text = \
                    self.command_text[:self.cursor_position-1] + \
                    self.command_text[self.cursor_position:]
                self.move_cursor(-1)
                self.update()
        elif keysym == XK.XK_Delete:
            if self.command_text:
                self.command_text = \
                    self.command_text[:self.cursor_position] + \
                    self.command_text[self.cursor_position+1:]
                self.update()
        elif keysym == XK.XK_Left:
            self.move_cursor(-1)
        elif keysym == XK.XK_Right:
            self.move_cursor(1)
        elif keysym == XK.XK_Home:
            self.move_cursor('beginning')
        elif keysym == XK.XK_End:
            self.move_cursor('end')
        else:
            if keystring:
                self.command_text = list(self.command_text)
                self.command_text.insert(self.cursor_position, keystring)
                self.command_text = "".join(self.command_text)
                self.cursor_position += 1
                self.update()

    def click(self, x, y):
        self.grab_keyboard()

    def cmd_start_grab(self):
        self.grab_keyboard()

    def cmd_get(self):
        return self.command_text

    def cmd_cursor_position(self):
        return self.cursor_position
