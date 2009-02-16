from base import Widget
from .. import window

import Xlib
from Xlib import X

class SystemTray(Widget):
    height = 0
    def _configure(self, bar, theme):
        Widget._configure(self, bar, theme)
        self.qtile = self.bar.qtile
        self.icons = {}
        self._init_internal_window()

    def _init_internal_window(self):
        dsp = self.qtile.display
        self._OPCODE = dsp.intern_atom("_NET_SYSTEM_TRAY_OPCODE")
        manager = dsp.intern_atom("MANAGER")
        selection = dsp.intern_atom("_NET_SYSTEM_TRAY_S%d" % dsp.get_default_screen())

        self.window = \
            self.qtile.root.create_window(10, 10, 10, 10, #position
                                           0, #border width
                                           X.CopyFromParent, #depth
                                           )

        
        self.window.set_selection_owner(selection, X.CurrentTime)
        self.sendEvent(self.qtile.root, 
                       manager,
                       [X.CurrentTime, 
                        selection,
                        self.window.id
                        ], 
                       (X.StructureNotifyMask),
                       )
        self.qtile.internalMap[self.window] = self

    def handle_ClientMessage(self, e):
        print "HANDLE CLIENTMESSAGE :o"
        print e
        data = e.data[1][1] # opcode
        task = e.data[1][2] # taskid
        if e.client_type == self._OPCODE and data == 0:
            print "adding icon"
            icon_window = self.qtile.display.create_resource_object("window", task)
#            icon_window.reparent(self.window.id, 0, 0)
            icon_window.change_attributes(
                event_mask=(X.ExposureMask|X.StructureNotifyMask)
                )
            self.icons[icon_window.id] = icon_window
            self.qtile.internalMap[icon_window] = self
            print "the icon is", icon_window
            self.bar.update_widget(self)

    def handle_ConfigureNotify(self, e):
        print "CONFIGURE NOTIF|Y OMG"
        if e.window.id in self.icons:
            self.icons[e.window.id].configure(
                width=self.height, height=self.height
                )

    def handle_DestroyNotify(self, e):
        """ Remove the icon from the systray """
        print "DESTROY NOTIFY OMG"
        destroyed_id = e.window.id
        if destroyed_id in self.icons:
            del self.icons[destroyed_id]
            self.bar.update_widget(self)
        
    def sendEvent(self, win, ctype, data, mask=None):
        """ Send a ClientMessage event to the root """
        data = (data+[0]*(5-len(data)))[:5]
        ev = Xlib.protocol.event.ClientMessage(window=win, client_type=ctype, data=(32,(data)))

        if not mask:
            mask = (X.SubstructureRedirectMask|X.SubstructureNotifyMask)
        self.qtile.root.send_event(ev, event_mask=mask)

    def draw(self, canvas):
        width, height = canvas.size
        self.height = height #for configurenotify
        y = self.bar.window.y
        pos = \
            self.bar.widgetData[self]['offset'] + \
            canvas.size[0] + \
            self.bar.window.x
        print "offset is", pos
        for icoid, ico in self.icons.items():
            x = pos-height
            ico.configure(onerror=None, 
                          x=x, y=y, 
                          width=height,
                          height=height
                          )
            print "mapping"
            ico.map()
            pos -= height
        return canvas
