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
        np = client.next_placement
        x,w,bw = np['x'], np['w'], np['bw']
        np['x'] = screen.x + screen.w - \
            (x + w + 2*bw) + screen.x


class HorizontalReflect(Modifier):
    def modify(self, screen, client):
        np = client.next_placement
        y,h,bw = np['y'], np['h'], np['bw']
        np['y'] = screen.y + screen.h - \
            (y + h + 2*bw) + screen.y


class Rotation(Modifier):
    right_angles = 0
    cos = [1,0,-1,0] # cosine for angles 0,90,180,270
    sin = [0,1,0,-1] # ... and same for sin
    
    def transform(self, matrix, point):
        '''multiple the given matrix by the point'''
        x,y = point
        x1 = x*matrix[0] + y*matrix[1]
        y1 = x*matrix[2] + y*matrix[3]
        return (x1,y1)
        
    def modify(self, screen, client):
        '''rotate the client about the centre of the screen - ahhh'''
        centre = (screen.w/2,
                  screen.h/2)
        r = self.right_angles
        matrix = (self.cos[r], -self.sin[r], self.sin[r], self.cos[r])
        np = client.next_placement

        #take off screen offsets
        x,y = np['x'] - screen.x, np['y'] - screen.y, 
        #take into account borders on width, height - take off after
        w,h = np['w'] + 2*np['bw'], np['h'] + 2*np['bw']
        
        top_left = (x - centre[0], y - centre[1])
        top_left = self.transform(matrix, top_left)

        bottom_right = (x + w - centre[0], y + h - centre[1])
        bottom_right = self.transform(matrix, bottom_right)

        x = min(top_left[0], bottom_right[0])
        y = min(top_left[1], bottom_right[1])

        w = abs(top_left[0] - bottom_right[0])
        h = abs(top_left[1] - bottom_right[1])
        
        # now deal with the fact that screens aren't square
        # it would be so much easier if they were :(
        # only scale when rotating by 90 or 270 degrees
        if r in (1, 3): #do we have to scale?
            x = int(float(x)/screen.h * screen.w)
            y = int(float(y)/screen.w * screen.h)
            w = int(float(w)/screen.h * screen.w)
            h = int(float(h)/screen.w * screen.h)
        
        x += centre[0]
        y += centre[1]
        
        np['x'], np['y'] = x+screen.x, y+screen.y
        np['w'], np['h'] = w-2*np['bw'], h-2*np['bw']

    def cmd_toggle(self):
        if not self.active:
            self.active = True
        self.right_angles += 1
        self.right_angles %= 4
        if not self.right_angles:
            self.active = False
        Hooks.call_hook("modifier-toggled", self)
