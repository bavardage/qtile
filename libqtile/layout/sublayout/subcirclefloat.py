from sublayout import SubLayout, Rect
from math import sin, cos, pi

class SubCircleFloat(SubLayout):
    def __init__(self, clientStack, parent=None, autohide=True,
                 radius=300, offset = 0):
        self.radius = radius
        self.offset = offset
        SubLayout.__init__(self, clientStack, parent, autohide)

    def filter(self, client):
        return True

    def request_rectangle(self, rectangle, windows):
        return (rectangle, Rect())

    def layout(self, r, clients):
        self.windows = clients
        if not self.active_border:
            self._init_bordercolors()
        if not clients:
            return #avoid div by zero
        angle = pi*2/len(clients)
        current_angle = self.offset
        for client in clients:
            c_x, c_y = (self.radius*sin(current_angle),
                          self.radius*cos(current_angle))
            c_x += r.center[0]; c_y += r.center[1]
            x = c_x - client.floatDimensions['w']/2
            y = c_y - client.floatDimensions['h']/2
            self.place(client,
                       x, y,
                       client.floatDimensions['w'],
                       client.floatDimensions['h'],
                       )
            current_angle += angle

    def cmd_inc_radius(self, inc):
        self.radius += inc
        self.clientStack.group.layoutAll()
    
    def cmd_inc_offset(self, inc):
        self.offset += inc
        self.clientStack.group.layoutAll()
