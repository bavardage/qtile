from Xlib import Xatom
from ... import window, command

class Rect:
    def __init__(self, x=0, y=0, w=0, h=0):
        self.x = x
        self.y = y
        self.w = w
        self.h = h

    def split_vertical(self, ratio=0.5, width=None):
        if not width:
            width = int(ratio*self.w)
        if width > self.w:
            raise Exception, "You're trying to take too much of the rectangle"
        return (Rect(self.x,
                     self.y,
                     width,
                     self.h),
                Rect(self.x + width,
                     self.y,
                     self.w - width,
                     self.h)
                )
    
    def split_horizontal(self, ratio=0.5, height=None):
        if not height:
            height = int(ratio*self.h)
        if height > self.h:
            raise Exception, "You're trying to take too much of this rectange"
        return (Rect(self.x,
                     self.y,
                     self.w,
                     height),
                Rect(self.x,
                     self.y + height,
                     self.w,
                     self.h - height)
                )
    

    def __repr__(self):
        return "(%s, %s, %s, %s)" % (self.x, self.y, self.w, self.h)


class SubLayout(command.CommandObject):
    def __init__(self, clientStack, parent=None, autohide=True):
        """
           autohide - does it hide itself if there are no clients
        """
        self.clientStack = clientStack
        self.theme = self.clientStack.theme
        self.clients = []
        self.sublayouts = []
        self.sublayout_names = {}
        self.parent = parent
        self.autohide = autohide
        self.windows = []
        self._init_sublayouts()
        self.active_border = None
    
    def _init_bordercolors(self):
        colormap = self.clientStack.group.qtile.display.screen().default_colormap
        color = lambda color: colormap.alloc_named_color(color).pixel
        name = self.__class__.__name__.lower()
        theme = self.theme
        self.active_border = color(theme.border_active)
        self.focused_border = color(theme.border_focus)
        self.normal_border = color(theme.border_normal)
        self.border_width = theme.border_width

    def _init_sublayouts(self):
        """
           Define sublayouts here, and so, only override init if you really must
        """
        pass

    def filter_windows(self, windows):
        return [w for w in windows if self.filter(w)]

    def filter(self, client):
        raise NotImplementedError

    def add(self, client):
        """
            Receives a client that this SubLayout may be interested in.
        """
        self.clients.append(client) #keep a copy regardless
        if self.sublayouts:
            for sl in self.sublayouts:
                sl.add(client)


    def focus(self, client):
        """
           Some client in the ClientStack got focus, no clue if it concerns us
        """

    def remove(self, client):
        if client in self.clients:
            self.clients.remove(client)

    def request_rectangle(self, rectangle, windows):
        """

            Define what rectangle this sublayout 'wants'. Don't be greedy..
            well.. if you have to

            :rectangle - the total rectangle available. DON'T BE GREEDY!
            :windows - the windows that will be layed out with this - so you
            can know if you're gonna not have anything to lay out

            Return a tuple containing the rectangle you want, and the rectangle that's left.
        """
        raise NotImplementedError

    def layout(self, rectangle, windows):
        """
           Layout the list of windows in the specified rectangle
        """
        self.windows = windows
        # setup colors
        if not self.active_border:
            self._init_bordercolors()
        # done
        if self.sublayouts:
            sls = []
            for sl in self.sublayouts:
                filtered = sl.filter_windows(windows)
                rect, rect_remaining = sl.request_rectangle(rectangle, filtered)
                sls.append((sl, rect, filtered))
                rectangle = rect_remaining
                windows = [w for w in windows if w not in filtered]
            for sl, rect, clients in sls:
                sl.layout(rect, clients)
            
        else:
            for c in self.windows:
                self.configure(rectangle, c)

    def index_of(self, client):
        if self.parent:
            return self.parent.windows.index(client)
        else:
            return self.clientStack.index_of(client)

    def configure(self, rectangle, client):
        """
            Place a window
        """
        raise NotImplementedError, "this is %s" % self.__class__.__name__

    def place(self, client, x, y, w, h):
        bc = (self.focused_border \
                  if self.clientStack.focus_history \
                  and self.clientStack.focus_history[0] is client \
                  else self.normal_border)
              

        next_placement = {
            'x': x,
            'y': y,
            'w': w - 2*self.border_width,
            'h': h - 2*self.border_width,
            'bw': self.border_width,
            'bc': bc,
            'hi': False,
            }
        #copy key by key, since not all values are given e.g. hidden
        for k,v in next_placement.items():
            client.next_placement[k] = v
    
    def hide_client(self, client):
        client.next_placement['hi'] = True

############
# Commands #
############
    def _items(self, name):
        if name == 'sl':
            return True, self.sublayout_names.keys()
    
    def _select(self, name, sel):
        if name == 'sl':
            return self.sublayout_names[sel]

    def cmd_info(self):
        return dict(
            name=self.__class__.__name__,
            )

class TopLevelSubLayout(SubLayout):
    '''
       This class effectively wraps a sublayout, and automatically adds a floating sublayout,
    '''
    def __init__(self, sublayout_data, clientStack):
        WrappedSubLayout, args = sublayout_data
        SubLayout.__init__(self, clientStack)
        self.sublayouts.append(SpecialWindowTypes(clientStack,
                                                  parent=self
                                                  )
                               )
        self.sublayouts.append(Minimised(clientStack,
                                         parent=self
                                         )
                               )
        self.sublayouts.append(Maximised(clientStack,
                                         parent=self
                                         )
                               )
        self.sublayouts.append(Floating(clientStack,
                                        parent=self
                                        )
                               )
        self.sublayouts.append(WrappedSubLayout(clientStack,
                                         parent=self,
                                         **args
                                         )
                               )
        self.sublayout_names = {'specialtypes': self.sublayouts[0],
                                'minimised': self.sublayouts[1],
                                'maximised': self.sublayouts[2],
                                'floating': self.sublayouts[1],
                                'main': self.sublayouts[4],
                                }


class VerticalStack(SubLayout):
    def layout(self, rectangle, windows):
        SubLayout.layout(self, rectangle, windows)

    def configure(self, r, client):
        position = self.windows.index(client)
        cliheight = int(r.h / len(self.windows)) #inc border
        self.place(client,
                   r.x,
                   r.y + cliheight*position,
                   r.w,
                   cliheight,
                   )

class ResizableStack(SubLayout):
    def __init__(self, clientStack, parent=None, autohide=True,
                 min_ratio=0.05):
        SubLayout.__init__(self, 
                           clientStack, 
                           parent,
                           autohide,
                           )
        self.client_ratios = []
        self.min_ratio = min_ratio
    
    def layout(self, rect, clients):
        while len(self.client_ratios) > len(clients):
            removing = self.client_ratios[-1]
            share = removing/(len(self.client_ratios)-1)
            self.client_ratios = [r+share for r in self.client_ratios[:-1]]
        while len(self.client_ratios) < len(clients):
            l = len(self.client_ratios)
            self.client_ratios = [r*l/(l+1) for r in self.client_ratios]
            self.client_ratios.append(1.0/(l+1))
        SubLayout.layout(self, rect, clients)

    def init_ratios(self):
        has_ratios = [r for r in self.client_ratios if r]
        without_ratios = [r for r in self.client_ratios if not r]
        extra = 1 - sum(has_ratios)
        share = extra / len(without_ratios)
        self.client_ratios = [r or share for r in self.client_ratios]

    def configure(self, r, client):
        position = self.windows.index(client)
        height = int(self.client_ratios[position] * r.h)
        y = int(sum(self.client_ratios[:position]) * r.h)
        height = height or 1 #don't let zero height.., just hide?
        self.place(client,
                   r.x,
                   r.y + y,
                   r.w,
                   height,
                   )

    def cmd_inc_ratio(self, amount):
        focused = self.clientStack.focused
        if not focused:
            print "no focus, returning"
            return
        try:
            index = self.windows.index(focused)
        except ValueError:
            print "no focused window in the stack"
            return

        if len(self.windows) == 1:
            self.client_ratio[0] == 1.0
            return

        if index == len(self.windows) - 1: #last?
            to_reduce = index-1
        else:
            to_reduce = index+1

        new_ratio = self.client_ratios[to_reduce] - amount
        if new_ratio < self.min_ratio:
            difference = self.min_ratio - new_ratio
            amount -= difference
        new_ratio = self.client_ratios[index] + amount
        if new_ratio < self.min_ratio:
            difference = self.min_ratio - new_ratio
            amount += difference

        self.client_ratios[index] += amount
        self.client_ratios[to_reduce] -= amount

        self.clientStack.group.layoutAll()
        
class HorizontalStack(SubLayout):
    def configure(self, r, client):
        position = self.windows.index(client)
        cliwidth = int(r.w / len(self.windows))
        self.place(client,
                   r.x + cliwidth*position,
                   r.y,
                   cliwidth,
                   r.h
                   )


class Floating(SubLayout):
    def filter(self, client):
        return client.floating

    def request_rectangle(self, r, windows):
        return (Rect(), r) #we want nothing

    def configure(self, r, client):
        d = client.floatDimensions
        self.place(client, **d)


class Minimised(SubLayout):
    def filter(self, client):
        return client.minimised

    def request_rectangle(self, r, windows):
        return (Rect(), r) #we want nothing
    
    def configure(self, r, client):
        self.hide_client(client)

class Maximised(SubLayout):
    def filter(self, client):
        return client.maximised
    
    def request_rectangle(self, r, clients):
        return (r, r) #yeah sure let the others have their way...
            #UNDERNEATH US. muahahaha
    
    def configure(self, r, client):
        self.place(client,
                   r.x,
                   r.y,
                   r.w,
                   r.h
                   )

class SpecialWindowTypes(Floating):
    def filter(self, client):
        return client.window_type != "normal"
