from libqtile import command
from libqtile.manager import Hooks

class Modifier(command.CommandObject):
    active = False
    def __init__(self, name):
        self.name = name
    def modify(self, screen, client):
        raise NotImplementedError

    def cmd_activate(self):
        self.active = True
        Hooks.call_hook("modifier-activated", self)

    
    def cmd_disactivate(self):
        self.active = False
        Hooks.call_hook("modifier-disactivated", self)

    def cmd_toggle(self):
        self.active = not self.active
        Hooks.call_hook("modifier-toggled", self)
        
class VerticalReflect(Modifier):
    def modify(self, screen, client):
        print "vertical modifier"
        np = client.next_placement
        x,w = np['x'], np['w']
        np['x'] = screen.x + screen.w - \
            (x + w)

class HorizontalReflect(Modifier):
    def modify(self, screen, client):
        np = client.next_placement
        y,h = np['y'], np['h']
        np['y'] = screen.y + screen.h - \
            (y + h)
