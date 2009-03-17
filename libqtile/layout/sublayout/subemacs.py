from sublayout import Rect, SubLayout
import sys #for stderr

def diff(l1, l2):
    return [i for i in l1 if i not in l2]


class Frame(SubLayout):
    '''This lays out one window'''
    def __init__(self, clientStack, parent=None, autohide=True):
        SubLayout.__init__(self, clientStack, parent, autohide)
        self.assigned_windows = []
    def filter_windows(self, windows):
        return [w for w in windows \
                    if w in self.assigned_windows]                        
    def layout(self, rect, ws):
        self.assigned_windows = \
            [w for w in self.assigned_windows \
                 if w in ws]
        SubLayout.layout(self, rect, ws)
    def configure(self, r, window):
        if window is self.assigned_windows[0]:
            self.place(window,
                       r.x,
                       r.y,
                       r.w,
                       r.h
                       )
        else:
            self.hide_client(window)

    def split(self, direction):
        split = Split(self.clientStack,
                      self.parent,
                      direction=direction,
                      )
        split.first = self

        asd_ws = list(self.assigned_windows)

        split.first.assigned_windows = asd_ws[:1]
        split.second.assigned_windows = asd_ws[1:]

        if self.parent.first is self:
            self.parent.first = split
        else:
            self.parent.second = split
        self.parent = split

    def next(self):
        '''returns the 'next' frame'''
        node = self
        while node.parent.second is node:
            node = node.parent
        node = node.parent.second
        if isinstance(node.parent, SubEmacs):
            node = node.parent.first #we wrapped
        if isinstance(node, Frame):
            return node
        while isinstance(node, Split): 
            node = node.first
            if isinstance(node, Frame):
                return node
                    
    
    def remove(self, client):
        if client in self.assigned_windows:
            self.assigned_windows.remove(client)

    def active_frame(self, focus):
        return self

class Split(SubLayout):
    ratio = 0.5
    def __init__(self, clientStack, parent=None, autohide=True,
                 direction="horizontal"):
        self.direction = direction
        SubLayout.__init__(self, clientStack, parent, autohide)

        self.first = Frame(clientStack, self, autohide)
        self.second = Frame(clientStack, self, autohide)

    def filter_windows(self, windows):
        fw = self.first.filter_windows(windows)
        windows = diff(windows, fw)
        sw = self.second.filter_windows(windows)
        return (fw + sw)

    def request_rectangle(self, r, windows):
        return (r, Rect())

    def layout(self, rect, ws):
        self.windows = ws
        if not self.active_border:
            self._init_bordercolors()
        
        split_function = (rect.split_horizontal \
                              if self.direction == "horizontal" \
                              else rect.split_vertical)
        frect, srect = split_function(ratio=self.ratio)
        
        fw = self.first.filter_windows(ws)
        rem = diff(ws, fw)
        sw = self.second.filter_windows(rem)
        rem = diff(rem, sw)

        self.first.layout(frect, fw)
        self.second.layout(srect, sw)

        for w in rem:
            self.hide_client(w)

    def remove(self, client):
        for frame in (self.first, self.second):
            frame.remove(client)

    def active_frame(self, focused=None):
        focused = (focused if focused else self.clientStack.focused)
        if focused in self.first.windows:
            return self.first.active_frame(focused)
        elif focused in self.second.windows:
            return self.second.active_frame(focused)
        else:
            return None

    def active_split(self, focused=None):
        focused = (focused if focused else self.clientStack.focused)
        active_frame = self.active_frame(focused)
        if active_frame:
            return active_frame.parent
        else:
            return None

    def unsplit(self):
        '''unsplit ourselves'''
        #unsplit childen
        for fm in (self.first, self.second):
            if isinstance(fm, Split):
                fm.unsplit()
        frame = self.first
        frame.assigned_windows.extend(self.second.assigned_windows)
        frame.windows.extend(self.second.windows)
        frame.parent = self.parent
        if self.parent.first is self:
            self.parent.first = frame
        else:
            self.parent.second = frame

    def do_focus(self):
        active_frame = self.active_frame()
        if active_frame:
            if active_frame.assigned_windows[0] is self.clientStack.focus:
                self.clientStack.group.layoutAll()
            else:
                self.clientStack.group.focus(active_frame.assigned_windows[0],
                                             True
                                             )
        else:
            pass
        
    def cmd_unsplit(self):
        self.unsplit()
        self.do_focus()

    def cmd_next(self):
        frame = self.active_frame()
        if not frame:
            return
        if frame.assigned_windows:
            top = frame.assigned_windows[-1]
            frame.assigned_windows.remove(top)
            frame.assigned_windows.insert(0, top)
        else:
            top = None
        self.do_focus()

class SubEmacs(Split):
    '''
    A top level split
    '''
    already_split=False

    def layout(self, rect, windows):
        self.windows = windows
        if not self.active_border:
            self._init_bordercolors()
        fw = self.first.filter_windows(windows)
        self.first.layout(rect, fw) 

    def add(self, client):
        active = self.active_frame()
        if not active:
            first = self.first
            while isinstance(first, Split):
                first = first.first
            active = first
        active.assigned_windows.insert(0, client)
        active.offset = 0

    def unsplit(self):
        active_split = self.active_split()
        if not active_split:
            print >> sys.stderr,  "no active split - cannot unsplit"
            return
        active_split.unsplit()

    def cmd_split(self, direction):
        active_frame = self.active_frame()
        if not active_frame:
            print >> sys.stderr, "no active frame - cannot split"
            return
        active_frame.split(direction)
        self.clientStack.group.layoutAll()

    def cmd_move_client_to_next(self):
        active_frame = self.active_frame()
        if not active_frame:
            print >> sys.stderr, "no active frame - cannot move"
            return
        next = active_frame.next()
        c = active_frame.assigned_windows[0]

        active_frame.assigned_windows.remove(c)
        next.assigned_windows.insert(0, c)
        next.windows.insert(0, c)

        self.clientStack.group.layoutAll()

    def cmd_inc_ratio(self, inc):
        active_split = self.active_split()
        if not active_split:
            print >> sys.stderr, "no active split - cannot inc ratio"
            return
        active_split.ratio += inc
        if active_split.ratio < 0:
            active_split.ratio = 0
        elif active_split.ratio > 1:
            active_split.ratio = 1.0
        self.clientStack.group.layoutAll()

    def cmd_embed_sublayout(self, name):
        import libqtile.layout
        active_frame = self.active_frame()
        if not active_frame:
            print >> sys.stderr, "no active frame - cannot embed"
            return
        if not hasattr(libqtile.layout, name):
            print >> sys.stderr, "that sublayout doesn't exist"
            return
        sublayout = getattr(libqtile.layout, name)
        if not issubclass(sublayout, SubLayout):
            print >> sys.stderr,  "that is not a sublayout"
            return
        sl = sublayout(self.clientStack,
                       parent=active_frame,
                       )
        active_frame.sublayouts = [sl,]
        self.clientStack.group.layoutAll()
                   
