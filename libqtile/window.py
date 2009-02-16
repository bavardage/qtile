# Copyright (c) 2008, Aldo Cortesi. All rights reserved.
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import marshal, sys
import Xlib
from Xlib import X, Xatom
import Xlib.protocol.event as event
import command, utils
import manager

class _Window(command.CommandObject):
    def __init__(self, window, qtile):
        self.window, self.qtile = window, qtile
        self.hidden = True
        window.change_attributes(event_mask=self._windowMask)
        self.x, self.y, self.width, self.height = None, None, None, None
        self.borderwidth = 0
        self.name = "<no name>"
        self.floating = False
        self.floatDimensions = {'x': 0, 'y': 0, 'w': 0, 'h': 0}
        self.urgent = False
        self.updateName()
        self.updateFloating()            
        self.updateUrgency()

    def updateName(self):
        try:
            self.name = self.window.get_wm_name()
            manager.Hooks.call_hook("client-name-changed")
        except (Xlib.error.BadWindow, Xlib.error.BadValue):
            # This usually means the window has just been deleted, and a new
            # focus will be acquired shortly. We don't raise an event for this.
            pass

    def updateFloating(self):
        win = self.window
        d = self.qtile.display
        dialog_atom = d.intern_atom('_NET_WM_WINDOW_TYPE_DIALOG')
        try:
            win_type = win.get_full_property(
                d.intern_atom('_NET_WM_WINDOW_TYPE'),
                Xatom.ATOM,
                )
        except:
            self.floating = False
        if win_type and \
                win_type.value and \
                win_type.value[0] == dialog_atom:
            self.floating = True
        else:
            self.floating = False
        g = win.get_geometry()
        self.floatDimensions = {
            'x': g.x,
            'y': g.y,
            'w': g.width,
            'h': g.height,
            }
        self.x, self.y, self.width, self.height = g.x, g.y, g.width, g.height

    def updateUrgency(self):
        old_value = self.urgent
        h = self.window.get_wm_hints()
        if h is None:
            return
        flags = h.flags

        if flags & 256: # 256 is UrgencyHint, but for some reason, Xutil doesn't seem to have it
                        # no clue why not :(
            self.urgent = True
        else:
            self.urgent = False
        if self.urgent != old_value:
            manager.Hooks.call_hook("client-urgent-hint-changed", self)


    def info(self):
        return dict(
            name = self.name,
            x = self.x,
            y = self.y,
            width = self.width,
            height = self.height,
            id = str(hex(self.window.id))
        )

    @property
    def opacity(self):
        opacity = self.window.get_property(
            self.qtile.display.get_atom('_NET_WM_WINDOW_OPACITY'),
            Xatom.CARDINAL,
            0,
            32
            )
        if not opacity:
            return 1.0
        else:
            value = opacity.value[0]
            as_float = round(
                (float(value)/0xffffffff), 
                2  #2 decimal places
                )
            return as_float

    def setOpacity(self, opacity):
        if 0.0 <= opacity <= 1.0:
            real_opacity = int(opacity * 0xffffffff)
            self.window.change_property(
                self.qtile.display.get_atom('_NET_WM_WINDOW_OPACITY'),
                Xatom.CARDINAL,
                32,
                [real_opacity,],
                )
        else:
            return
            
    def notify(self):
        e = event.ConfigureNotify(
                window = self.window,
                event = self.window,
                x = self.x,
                y = self.y,
                width = self.width,
                height = self.height,
                border_width = self.borderwidth,
                override = False,
                above_sibling = X.NONE
        )
        self.window.send_event(e)

    def kill(self):
        if self.hasProtocol("WM_DELETE_WINDOW"):
            e = event.ClientMessage(
                    window = self.window,
                    client_type = self.qtile.display.intern_atom("WM_PROTOCOLS"),
                    data = [
                        # Use 32-bit format:
                        32,
                        # Must be exactly 20 bytes long:
                        [
                            self.qtile.display.intern_atom("WM_DELETE_WINDOW"),
                            X.CurrentTime,
                            0,
                            0,
                            0
                        ]
                    ]
            )
            self.window.send_event(e)
        else:
            self.window.kill_client()

    def hide(self):
        # We don't want to get the UnmapNotify for this unmap
        self.disableMask(X.StructureNotifyMask)
        self.window.unmap()
        self.resetMask()
        self.hidden = True

    def unhide(self):
        self.window.map()
        self.hidden = False

    def disableMask(self, mask):
        self.window.change_attributes(
            event_mask=self._windowMask&(~mask)
        )

    def resetMask(self):
        self.window.change_attributes(
            event_mask=self._windowMask
        )

    def place(self, x, y, width, height, border, borderColor):
        """
            Places the window at the specified location with the given size.
        """
        self.x, self.y, self.width, self.height = x, y, width, height
        self.window.configure(
            x=x,
            y=y,
            width=width,
            height=height,
            border_width=border
        )
        if borderColor is not None:
            self.window.change_attributes(
                border_pixel = borderColor
            )

    def focus(self, warp):
        if not self.hidden:
            self.window.set_input_focus(
                X.RevertToPointerRoot,
                X.CurrentTime
            )
            self.window.configure(
                stack_mode = X.Above
            )
            if warp:
                self.window.warp_pointer(0, 0)
        manager.Hooks.call_hook("client-focus", self)

    def hasProtocol(self, name):
        s = set()
        d = self.qtile.display
        for i in self.window.get_wm_protocols():
            s.add(d.get_atom_name(i))
        return name in s

    def setProp(self, name, data):
        self.window.change_property(
            self.qtile.atoms[name],
            self.qtile.atoms["python"],
            8,
            marshal.dumps(data)
        )

    def _items(self, name, sel):
        return None

    def _select(self, name, sel):
        return None

    def cmd_info(self):
        """
            Returns a dictionary of info for this object.
        """
        return dict(
            id = self.window.id
        )


    def cmd_inspect(self):
        """
            Tells you more than you ever wanted to know about a window.
        """
        a = self.window.get_attributes()
        attrs = {
            "backing_store": a.backing_store,
            "visual": a.visual,
            "class": a.win_class,
            "bit_gravity": a.bit_gravity,
            "win_gravity": a.win_gravity,
            "backing_bit_planes": a.backing_bit_planes,
            "backing_pixel": a.backing_pixel,
            "save_under": a.save_under,
            "map_is_installed": a.map_is_installed,
            "map_state": a.map_state,
            "override_redirect": a.override_redirect,
            #"colormap": a.colormap,
            "all_event_masks": a.all_event_masks,
            "your_event_mask": a.your_event_mask,
            "do_not_propagate_mask": a.do_not_propagate_mask
        }
        props = [self.qtile.display.get_atom_name(x) for x in self.window.list_properties()]
        
        h = self.window.get_wm_normal_hints()
        if h:
            normalhints = dict(
                flags = h.flags,
                min_width = h.min_width,
                min_height = h.min_height,
                max_width = h.max_width,
                max_height = h.max_height,
                width_inc = h.width_inc,
                height_inc = h.height_inc,
                min_aspect = dict(num=h.min_aspect["num"], denum=h.min_aspect["denum"]),
                max_aspect = dict(num=h.max_aspect["num"], denum=h.max_aspect["denum"]),
                base_width = h.base_width,
                base_height = h.base_height,
                win_gravity = h.win_gravity
            )
        else:
            normalhints = None
        
        h = self.window.get_wm_hints()
        if h:
            hints = dict(
                flags = h.flags,
                input = h.input,
                initial_state = h.initial_state,
                icon_window = h.icon_window.id,
                icon_x = h.icon_x,
                icon_y = h.icon_y,
                window_group = h.window_group.id
            )
        else:
            hints = None

        protocols = []
        for i in self.window.get_wm_protocols():
            protocols.append(self.qtile.display.get_atom_name(i))

        state = self.window.get_wm_state()

        return dict(
            attributes=attrs,
            properties=props,
            name = self.window.get_wm_name(),
            wm_class = self.window.get_wm_class(),
            wm_transient_for = self.window.get_wm_transient_for(),
            protocols = protocols,
            wm_icon_name = self.window.get_wm_icon_name(),
            wm_client_machine = self.window.get_wm_client_machine(),
            normalhints = normalhints,
            hints = hints,
            state = state
        )


class Internal(_Window):
    """
        An internal window, that should not be managed by qtile.
    """
    _windowMask = X.StructureNotifyMask |\
                 X.PropertyChangeMask |\
                 X.EnterWindowMask |\
                 X.FocusChangeMask |\
                 X.ExposureMask |\
                 X.ButtonPressMask
    @classmethod
    def create(klass, qtile, background_pixel, x, y, width, height, opacity=1.0):
        win = qtile.root.create_window(
                    x, y, width, height, 0,
                    X.CopyFromParent, X.InputOutput,
                    X.CopyFromParent,
                    background_pixel = background_pixel,
                    event_mask = X.StructureNotifyMask | X.ExposureMask
               )
        i = Internal(win, qtile)
        i.place(x, y, width, height, 0, None)
        i.setProp("internal", True)
        i.setOpacity(opacity)
        return i

    def __repr__(self):
        return "Internal(%s)"%self.name


class Window(_Window):
    _windowMask = X.StructureNotifyMask |\
                 X.PropertyChangeMask |\
                 X.EnterWindowMask |\
                 X.FocusChangeMask
    group = None
    def handle_EnterNotify(self, e):
        manager.Hooks.call_hook("client-mouse-enter", self)
        self.group.focus(self, False)
        if self.group.screen and self.qtile.currentScreen != self.group.screen:
            self.qtile.toScreen(self.group.screen.index)

    def handle_ConfigureRequest(self, e):
        if self.group.screen:
            self.group.layout.configure(self)
            self.notify()

    def handle_PropertyNotify(self, e):
        if e.atom == Xatom.WM_TRANSIENT_FOR:
            utils.outputToStderr("transient")
        elif e.atom == Xatom.WM_HINTS:
            self.updateUrgency()
            utils.outputToStderr("hints")
        elif e.atom == Xatom.WM_NORMAL_HINTS:
            utils.outputToStderr("normal_hints")
        elif e.atom == Xatom.WM_NAME:
            self.updateName()
            manager.Hooks.call_hook("client-name-updated", self)
        else:
            utils.outputToStderr(e)

    def _items(self, name):
        if name == "group":
            return True, None
        elif name == "layout":
            return True, range(len(self.group.layouts))
        elif name == "screen":
            return True, None

    def _select(self, name, sel):
        if name == "group":
            return self.group
        elif name == "layout":
            if sel is None:
                return self.group.layout
            else:
                return utils.lget(self.group.layouts, sel)
        elif name == "screen":
            return self.group.screen

    def __repr__(self):
        return "Window(%s)"%self.name

    def cmd_kill(self):
        """
            Kill this window. Try to do this politely if the client support
            this, otherwise be brutal.
        """
        self.kill()

    def cmd_togroup(self, groupName):
        """
            Move window to a specified group.

            Examples:

                togroup("a")
        """
        group = self.qtile.groupMap.get(groupName)
        if group is None:
            raise command.CommandError("No such group: %s"%groupName)
        if self.group is not group:
            self.hide()
            self.group.remove(self)
            group.add(self)
            self.group.layoutAll()
            group.layoutAll()

    def cmd_move_floating(self, x, y):
        self.floatDimensions['x'] += x
        self.floatDimensions['y'] += y
        self.group.layoutAll()

    def cmd_move_to_screen_edge(self, edge):
        if edge == 'Left':
            self.floatDimensions['x'] = 0
        elif edge == 'Up':
            self.floatDimensions['y'] = 0
        elif edge == 'Right':
            self.floatDimensions['x'] = \
                self.group.screen.dwidth - self.floatDimensions['w']
        elif edge == 'Down':
            self.floatDimensions['y'] = \
                self.group.screen.dheight - self.floatDimensions['h']
        self.group.layoutAll()
        

    def cmd_resize_floating(self, xinc, yinc):
        self.floatDimensions['w'] += xinc
        self.floatDimensions['h'] += yinc
        self.group.layoutAll()

    def cmd_toggle_floating(self):
        self.floating = not self.floating
        self.group.layoutAll()

    def cmd_semitransparent(self):
        self.setOpacity(0.5)

    def cmd_opacity(self, opacity):
        self.setOpacity(opacity)
