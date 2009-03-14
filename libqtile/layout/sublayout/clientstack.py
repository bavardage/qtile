from ..base import Layout
from sublayout import SubLayout, Rect, TopLevelSubLayout
from ... import command, utils, window
from ...manager import Hooks
from Xlib import X

class Layers:
    BOTTOM = 0
    DESKTOP = 10
    BELOW = 20
    NORMAL = 30
    ABOVE = 40
    DIALOG = 50
    FLOAT = 60
    MAXIMISE = 70
    FULLSCREEN = 80

types_states_to_layers = [
    #states first
    (lambda c:c.floating, Layers.FLOAT),
    (lambda c:c.maximised, Layers.MAXIMISE),
    (lambda c:c.fullscreen, Layers.FULLSCREEN),
    #then types
    (lambda c:c.window_type == "normal", Layers.NORMAL),
    (lambda c:c.window_type == "dialog", Layers.DIALOG),
    (lambda c:c.window_type == "desktop", Layers.DESKTOP),
    (lambda c:c.window_type == "dock", Layers.ABOVE),
    (lambda c: True, Layers.NORMAL), #fallback
]

def get_layer(tstl, client):
    for test, layer in tstl:
        if test(client):
            return layer
    return Layers.NORMAL

class ClientStack(Layout):
    name="tile"
    ADD_TO_TOP, ADD_TO_BOTTOM, ADD_TO_NEXT, ADD_TO_PREVIOUS = \
        (1, 2, 3, 4)
    FOCUS_TO_TOP, FOCUS_TO_BOTTOM, \
    FOCUS_TO_NEXT, FOCUS_TO_PREVIOUS, \
    FOCUS_TO_LAST_FOCUSED = \
        (5, 6, 7, 8, 9)
    def __init__(self, SubLayouts, Modifiers=None, add_mode=ADD_TO_TOP,
                 focus_mode=FOCUS_TO_TOP,
                 focus_history_length=10, mouse_warp = False):
        Layout.__init__(self)
        # store constructor values #
        self.add_mode = add_mode
        self.focus_mode = focus_mode
        self.focus_history_length = focus_history_length
        self.mouse_warp = mouse_warp
        # initialise other values #
        self.need_restack = True
        self.clients = []
        self.focus_history = []
        self.normal_border, self.active_border, self.focused_border = \
            None, None, None
        self.sublayouts = []
        self.current_sublayout = 0
        self.SubLayouts = SubLayouts
        self.layout_modifiers = {}
        self.Modifiers = (Modifiers if Modifiers else [])

    def restack(self):
        print "restacking..."
        self.need_restack = False
        tstl = types_states_to_layers
        layers = []
        for c in self.clients:
            layer = get_layer(tstl, c)
            if c is self.focused:
                layer += 1
            layers.append((layer, c))
        layers.sort()
        layers.extend([(-1, w.window) for w in self.group.screen.wiboxes \
                           if w.above]) #just let -1 be the layer
        layers.reverse()
        layers.extend([(-1, w.window) for w in self.group.screen.wiboxes \
                           if not w.above])
        
        last = X.NONE
        for l,client in layers:
            client.window.configure(
                sibling = last,
                stack_mode = X.Below,
                )
            last = client.window

    def layout(self, windows):
        sl = self.sublayouts[self.current_sublayout]
        # determine the area available
        rect = Rect(self.group.screen.dx,
                    self.group.screen.dy,
                    self.group.screen.dwidth,
                    self.group.screen.dheight,
                    )
        # set the windows' next_placement
        sl.layout(rect, self.clients)
        #restack if needs be
        if self.need_restack:
            self.restack()
        # modify the placement
        for c in self.clients:
            for name,m in self.layout_modifiers.items():
                if m.active:
                    m.modify(rect, c)
        #now actually place the windows
        for c in self.clients:
            p = c.next_placement
            try:
                c.place(p['x'], p['y'],
                        p['w'], p['h'],
                        p['bw'], p['bc'],
                        )
                if p['hi']:
                    c.hide()
                else:
                    c.unhide()
            except:
                print "Something went wrong"
                print "Window placement errored"
      
    def register_hooks(self):
        @Hooks("modifier-activated")
        @Hooks("modifier-disactivated")
        @Hooks("modifier-toggled")
        def modifiers_changed(datadict, qtile, modifier):
            self.group.layoutAll()
        @Hooks("client-state-changed")
        @Hooks("client-type-changed")
        @Hooks("client-focus")
        def restack_hook(datadict, qtile, *args):
            self.need_restack = True


    def configure(self, window):
        # Oh dear, this shouldn't be happening, oh dear what can the matter be, oh dear help help help
        self.group.layoutAll()
                
    def clone(self, group, theme):
        c = Layout.clone(self, group, theme)
        if not self.active_border:
            def color(color):
                colormap = group.qtile.display.screen().default_colormap
                return colormap.alloc_named_color(color).pixel
            c.active_border = color(theme["clientstack_border_active"])
            c.focused_border = color(theme["clientstack_border_focus"])
            c.normal_border = color(theme["clientstack_border_normal"])
        c.clients = []
        c.focus_history = []
        c.sublayouts = []
        for SL, kwargs in self.SubLayouts:
            c.sublayouts.append(TopLevelSubLayout((SL, kwargs),
                                                  c,
                                                  )
                                )
        c.layout_modifiers = {}
        for Modifier, kwargs in self.Modifiers:
            m = Modifier(**kwargs)
            c.layout_modifiers[m.name] = m
        c.register_hooks()
        c.current_sublayout = 0
        return c

    def focus(self, c):
        self.focus_history.insert(0, c)
        self.focus_history = self.focus_history[:self.focus_history_length]
        for sl in self.sublayouts:
            sl.focus(c)

    def add(self, c):
        if self.add_mode == ClientStack.ADD_TO_TOP:
            self.clients.insert(0, c)
        elif self.add_mode == ClientStack.ADD_TO_BOTTOM:
            self.clients.append(c)
        elif self.add_mode in (ClientStack.ADD_TO_NEXT, 
                               ClientStack.ADD_TO_PREVIOUS):
            if self.focus_history and \
                    self.focus_history[0] in self.clients:
                pos = self.clients.index(self.focus_history[0])
                offset = (1 if self.add_mode == ClientStack.ADD_TO_NEXT \
                              else 0)
                self.clients.insert(pos+offset, c)
            else:
                #bleh, just add it to the top???
                #TODO: define better behaviour
                self.clients.insert(0, c)
        else:
            raise NotImplementedError, "This mode is not catered for"
        for sl in self.sublayouts:
            sl.add(c)

    def remove(self, c):
        position = 0
        if c in self.clients:
            position = self.clients.index(c)
            self.clients.remove(c)
            for sl in self.sublayouts:
                sl.remove(c)
            while c in self.focus_history:
                self.focus_history.remove(c)
        if not self.clients:
            return None
        elif self.focus_mode == ClientStack.FOCUS_TO_TOP:
            return self.clients[0]
        elif self.focus_mode == ClientStack.FOCUS_TO_BOTTOM:
            return self.clients[-1]
        elif self.focus_mode == ClientStack.FOCUS_TO_NEXT:
            return self.clients[position]
        elif self.focus_mode == ClientStack.FOCUS_TO_PREVIOUS:
            return self.clients[position-1]
        elif self.focus_mode == ClientStack.FOCUS_TO_LAST_FOCUSED and self.focus_history:
            return self.focus_history[0]
        else:
            return None

    def index_of(self, client):
        return self.clients.index(client)

    @property
    def focused(self):
        if not self.focus_history:
            if self.group.currentWindow \
                    and self.group.currentWindow in self.clients:
                self.focus_history.insert(0, self.group.currentWindow)
            else:
                return None
        return self.focus_history[0]

    def change_focus(self, offset):
        if not self.clients:
            return
        if self.focused in self.clients:
            current_focus_index = self.clients.index(self.focused)
        else:
            current_focus_index = 0
        current_focus_index = (current_focus_index + offset) % len(self.clients)
        while self.clients[current_focus_index].minimised and \
                self.clients[current_focus_index] is not self.focused:
                    current_focus_index = (current_focus_index + offset) % len(self.clients)
        self.group.focus(self.clients[current_focus_index], self.mouse_warp)

############
# Commands #
############

    def _items(self, name):
        if name == "modifiers":
            return True, self.layout_modifiers.keys()
        elif name == "sublayouts":
            return True, range(len(self.sublayouts)) + ['current']
        else:
            return Layout._items(self, name)

    def _select(self, name, sel):
        if name == "modifiers":
            return self.layout_modifiers[sel]
        elif name == "sublayouts":
            if sel == 'current':
                return self.sublayouts[self.current_sublayout]
            else:
                return self.sublayouts[sel]
        else:
            return Layout._select(self, name, sel)

    def cmd_up(self):
        """
            Switch focus to the previous window in the stack
        """
        self.change_focus(-1)
        
    def cmd_down(self):
        """
            Switch focus to the next window in the stack
        """
        self.change_focus(1)

    def cmd_shuffle_up(self):
        """
            Shuffle the order of the stack up
        """
        utils.shuffleUp(self.clients)
        self.group.layoutAll()

    def cmd_shuffle_down(self):
        utils.shuffleDown(self.clients)
        self.group.layoutAll()
        
    def cmd_nextsublayout(self):
        self.current_sublayout = (self.current_sublayout + 1) % len(self.sublayouts)
        self.group.layoutAll()

    def cmd_command_sublayout(self, mask, command, *args, **kwargs):
        self.sublayouts[self.current_sublayout].command(mask, command, *args, **kwargs)
        
    def info(self):
        return dict(
            clients = [c.name for c in self.clients],
            focus_history = [c.name for c in self.focus_history],
            )

