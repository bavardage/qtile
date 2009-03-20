
import window
from newwidget import Widget
from manager import Hooks
from command import CommandObject, CommandError

import Image
from Xlib import X
import sys

'''
Note:
Although the wibox can be rotated, we code as if it were horizontal:
width is horizontal dimension,
height is vertical dimension,
x is horizontal displacement,
y is vertical displacement
'''

class NL(Widget):
    '''
    A semaphor class to indicate a New widget Layer
    '''
    def __init__(self):
        Widget.__init__(self, "newlayer", 0)


class WiboxConstants:
    AUTO_HEIGHT = 20
    dimensions = [
        "expand", #expand to fit all widgets' initial width request
        ]
    placements = ["top", "bottom", "right", "left", "floating"]
    placement_align = ["left", "center", "right"]
    rotation = [0, 90, 180, 270, "auto"]


class WidgetLayer(WiboxConstants):
    '''
    A horizontal group of widgets
    '''
    def __init__(self, wibox, widgets):
        self.wibox = wibox
        self.widgets = widgets
        self.widgetData = {}
        for w in self.widgets:
            self.widgetData[w] = w.widget_data
            w.widget_data.layer = self
        self.need_arrange = True

        self.w = "expand"
        self.h = "expand" #indicate that we're still in flux

    def _configure(self, width, height):
        self.w = width
        self.h = height

    def arrange_widgets(self):
        width = self.w
        ledge, redge = 0, width

        widgets = self.widgets
        lalign = [w for w in widgets \
                      if w.align == "left"]
        ralign = [w for w in widgets \
                      if w.align == "right"]
        ralign.reverse()

        for w in lalign:
            if redge - ledge <= 0:
                print >> sys.stderr, "not enough room to fit %s" % w.name
                break
            elif redge - ledge >= w.width_req:
                self.widgetData[w].width = w.width_req
                self.widgetData[w].xoffset = ledge
            else:
                self.widgetData[w].width = redge - ledge
                self.widgetData[w].xoffset = ledge
            ledge += self.widgetData[w].width
        
        for w in ralign:
            if redge - ledge <= 0:
                print >> sys.stderr, "not enough room to fit %s" % w.name
                break
            elif redge - ledge >= w.width_req:
                self.widgetData[w].width = width = w.width_req
                self.widgetData[w].xoffset = redge - width
            else:
                self.widgetData[w].width = width = redge - ledge
                self.widgetData[w].xoffset = redge - width
            redge -= self.widgetData[w].width

        self.need_arrange = False

    def draw_widget(self, w):
        data = self.widgetData[w]
        height = min(self.h, w.height_req)            
        im = w.draw(
            Image.new("RGBA", #the canvas
                      (data.width, height),
                      )
            )
        self.widgetData[w].image = im


    def draw(self, canvas, yoffset):
        ''' Draw this layer of widgets onto the canvas '''
        if self.need_arrange:
            self.arrange_widgets()
        for w, data in self.widgetData.items():
            if data.image is None:
                self.draw_widget(w)
            canvas.paste(data.image,
                         (data.xoffset, yoffset),
                         data.image,
                         )

    def click(self, x, y):
        for w, d in self.widgetData.items():
            if d.xoffset <= x <= d.xoffset + d.width and \
                    0 <= y <= min(self.h, w.height_req):
                w.click(x - d.xoffset, y)

    @classmethod
    def makeLayers(cls, wibox, widgets):
        widgetLists = cls.splitWidgetList(widgets)
        return [cls(wibox, wl) for wl in widgetLists]
    @classmethod
    def splitWidgetList(cls, widgets):
        '''
        Split a list of widgets into sublists,
        breaking when a widget of class NL is found
        '''        
        layers = []
        currentList = []
        for w in widgets:
            if isinstance(w, NL):
                layers.append(currentList)
                currentList = []
            else:
                currentList.append(w)
        if currentList:
            layers.append(currentList)
        return layers
    
    
class Wibox(CommandObject, WiboxConstants):
    _above = None
    _hidden = None
    def __init__(self, name, widgets, placement, 
                 x=0, y=0, width="expand", 
                 height=WiboxConstants.AUTO_HEIGHT,
                 placement_align="center",
                 rotation="auto",
                 above=False,
                 hidden=False):
        #TODO: add error checking for parameters
        self.name = name
        self.widgets = widgets
        self.widgetData = {}
        for w in self.widgets:
            self.widgetData[w] = w.widget_data
        self.widgetLayers = []
        self.placement = placement
        self.placement_align = placement_align
        self.rotation = rotation
        self._above = above
        self._hidden = hidden
        
        self.x = x
        self.y = y
        self.w = width
        self.h = height

        self.qtile = None
        self.screen = None
        self.window = None
        self.gc = None
        self.theme = None

        self.need_arrange = True
        self.baseimage = None

        self.keyboard_grabbers = []

    def getHidden(self):
        return self._hidden
    def setHidden(self, hidden):
        changed = (hidden != self._hidden)
        self._hidden = hidden
        if changed:
            if self.hidden:
                self.window.hide()
            else:
                self.window.unhide()
            Hooks.call_hook("wibox-hidden-changed", self)
    hidden = property(getHidden, setHidden)

    def getAbove(self):
        return self._above
    def setAbove(self, above):
        changed = self._above
        self._above = above
        if changed:
            Hooks.call_hook("wibox-above-changed", self)
    above = property(getAbove, setAbove)

    def destroy(self):
        self.screen.remove_wibox(self)
        self.window.window.destroy()
        for wl in self.widgetLayers:
            for w in wl.widgets:
                del self.qtile.widgetMap[w.name]

    def _configure(self, qtile, screen, theme):
        self.qtile = qtile
        self.screen = screen
        self.theme = theme

        self.widgetLayers = WidgetLayer.makeLayers(self, self.widgets)
        self.widgets = [w for w in self.widgets \
                            if not isinstance(w, NL)]

        for w in self.widgets:
            qtile.registerWidget(w)
            w._configure(self, theme)

        self._init_rotation()
        self._init_size()

        for w in self.widgets:
            w._reconfigure()

        self._init_position()
        self._init_margin()
        self._init_window()

    def _init_size(self):
        if self.w == "expand":
            layerWidths = []
            for wl in self.widgetLayers:
                layerWidths.append(
                    sum([w.width_req \
                             for w in wl.widgets]
                        )
                    )
            print "layerWidths", layerWidths
            self.w = max(layerWidths)
            
        expanded_height = False
        if self.h == "expand":
            expanded_height = True
            layerHeights = []
            for wl in self.widgetLayers:
                layerHeights.append(
                    max([w.height_req \
                             for w in wl.widgets]
                        )
                    )
            self.h = sum(layerHeights)
            
        for wl in self.widgetLayers:
            if expanded_height:
                wl._configure(self.w, 
                             max([(w.height_req or self.AUTO_HEIGHT) \
                                      for w in wl.widgets])
                             )
            else:
                wl._configure(self.w,
                             self.h/len(self.widgetLayers)
                             )
                         

    def _init_position(self):
        p = self.placement
        pa = self.placement_align
        #remember, we code as if we were always vertical
        # only place when we shouldn't do this, is in place..
        #TODO: add margins and stuff, and use dheight, dwidth or w/e
        #TODO: position rotated floating things better
        #TODO: allow x and y for bars... don't assume they are auto?
        # should I? maybe not...
        if p in ("right", "left"):
            self.y = 0
            if pa == "center":
                self.x = (self.screen.height - self.w)/2
            elif pa == "right":
                self.x = (self.screen.height - self.w)
            else: #left
                self.x = 0
        elif p == "top":
            self.y = 0
            if pa == "center":
                self.x = (self.screen.width - self.w)/2
            elif pa == "right":
                self.x = (self.screen.width - self.w)
            else:
                self.x = 0
        elif p == "bottom":
            self.y = self.screen.height - self.h
            if pa == "center":
                self.x = (self.screen.width - self.w)/2
            elif pa == "right":
                self.x = (self.screen.width - self.w)
            else:
                self.x = 0
        elif p == "floating":
            pass          

    def _init_margin(self):
        if self.placement in ("left", "right", "top", "bottom"):
            self.screen.increase_margin(self.placement, self.h)
    
    def _init_rotation(self):
        if self.rotation != "auto":
            return
        p = self.placement            
        rotations = {"top": 0,
                     "bottom": 0,
                     "left": 90,
                     "right": 270,
                     "floating": 0
                     }
        self.rotation = rotations[p]

    def _init_window(self):
        c = self.qtile.display.screen().default_colormap.alloc_named_color(
            "black"
            ).pixel
    
        if self.placement in ("top", "bottom"):
            x,y,w,h = self.x, self.y, self.w, self.h
        elif self.placement == "right":
            x = self.screen.width - self.y - self.h
            y = self.x
            w = self.h
            h = self.w
        elif self.placement == "left":
            x = self.y
            y = self.screen.height - self.x - self.w
            w = self.h
            h = self.w
        elif self.placement == "floating":
            if self.rotation in (0, 180):
                x = self.x
                y = self.y
                w = self.w
                h = self.h
            elif self.rotation in (90, 270):
                x = self.x
                y = self.y
                w,h = self.h, self.w
        
        self.window = window.Internal.create(self.qtile,
                                             c,
                                             x, y, w, h,
                                             self.theme["bar_opacity"]
                                             )
        self.window.name = "qtile-bar"
        self.window.handle_Expose = self.handle_Expose
        self.window.handle_ButtonPress = self.handle_ButtonPress
        self.window.handle_KeyPress = self.handle_KeyPress
        self.qtile.internalMap[self.window.window] = self.window

        self.gc = self.window.window.create_gc()
        self.window.addMask(X.KeyPressMask) #allow keygrabbing stuff
        if self.hidden:
            self.window.hide()
        else:
            self.window.unhide()

    def _init_baseimage(self):
        self.baseimage = Image.new("RGBA",
                                   (self.w, self.h),
                                   self.theme["bar_bg_normal"],
                                   )
        Hooks.call_hook("wibox-draw", self.baseimage)

    
    def _screen_resize():
        pass #TODO: handle this nicely

    def draw(self):
        if not self.baseimage:
            self._init_baseimage()

        self.image = self.baseimage.copy()
        
        yoffset = 0
        for wl in self.widgetLayers:
            wl.draw(self.image, yoffset)
            yoffset += wl.h

        rgbimage = self.image.convert("RGB")
        rgbimage = rgbimage.rotate(self.rotation, expand=1)

        Hooks.call_hook("wibox-drawn", rgbimage)

        self.window.window.put_pil_image(self.gc,
                                         0, 0,
                                         rgbimage,
                                         )
    def update_widget(self, w):
        self.widgetData[w].image = None
        self.draw()

    def update_widget_size(self, w):
        for wl in self.widgetLayers:
            if w in wl.widgets:
                wl.need_arrange = True
        self.draw()

    def coords_window_to_wibox(self, x,y,w,h):
        if self.rotation == 0:
            pass
        elif self.rotation == 270:
            x,y = y, (self.h - x - w)
            w,h = h,w
        elif self.rotation == 180:
            x,y = (self.w - x - w), (self.h - y - h)
        elif self.rotation == 90:
            x,y = (self.w - y - h), x
            w,h = h,w
        return x,y,w,h
    def coords_wibox_to_window(self, x,y,w,h):
        if self.rotation == 0:
            pass
        elif self.rotation == 270:
            x,y = (self.h - y - h), x
            w,h = h,w
        elif self.rotation == 180:
            x,y = (self.w - x - w), (self.h - y - h)
        elif self.rotation == 90:
            x,y = y, (self.w - x - w)
            w,h = h,w
        return x,y,w,h
        
    def handle_Expose(self, e):
        self.draw()
    def handle_ButtonPress(self, e):
        x,y = e.event_x, e.event_y
        x,y = self.coords_window_to_wibox(x,y,0,0)[:2]
        yoffset = 0
        print "Button press at", x, y
        for wl in self.widgetLayers:
            if yoffset <= y <= yoffset + wl.h:
                print "yes for layer"
                wl.click(x, y-yoffset)
            else:
                print "no for layer"
            yoffset += wl.h
    def handle_KeyPress(self, e):
        if not self.keyboard_grabbers:
            return
        else:
            self.keyboard_grabbers[-1].handle_KeyPress(e)
    
    def grab_keyboard(self, widget):
        need_grab = not self.keyboard_grabbers
        
        if widget in self.keyboard_grabbers:
            self.keyboard_grabbers.remove(widget)
            self.keyboard_grabbers.append(widget)
        else:
            self.keyboard_grabbers.append(widget)

        if need_grab:
            self.window.window.grab_keyboard(0,
                                             X.GrabModeAsync,
                                             X.GrabModeAsync,
                                             X.CurrentTime
                                             )
        else:
            #it's already grabbed, but we'll now get the keyboard events
            return
    def ungrab_keyboard(self, widget):
        try:
            self.keyboard_grabbers.remove(widget)
            if not self.keyboard_grabbers:
                self.qtile.display.ungrab_keyboard(X.CurrentTime)
        except:
            pass

    ############
    # Commands #
    ############
    def _items(self, name):
        if name == "screen":
            return True, None
    
    def _select(self, name, sel):
        if name == "screen":
            return self.screen

    def cmd_fake_click(self, x, y):
        class _fake: pass
        fake = _fake()
        fake.event_x = x
        fake.event_y = y
        self.handle_ButtonPress(fake)

    def cmd_fake_keypress(self, modifiers, key):
        from Xlib import XK
        from . import utils
        import Xlib.protocol.event as event
        keysym = XK.string_to_keysym(key)
        if keysym == 0:
            raise CommandError("Unknown key: %s" % key)
        keycode = self.qtile.display.keysym_to_keycode(keysym)
        try:
            mask = utils.translateMasks(modifiers)
        except QtileError, v:
            return str(v)
        class _fake: pass
        fake = _fake()
        fake.state = mask
        fake.detail = keycode
        self.handle_KeyPress(fake)
    
    def cmd_info(self):
        return self.info()

    def info(self):
        widgetdata = {}
        for k,v in self.widgetData.items():
            widgetdata[k.name] = {'xoffset': v.offset, 
                                  'width': v.width }
        return dict(
            placement = self.placement,
            rotation = self.rotation,
            placement_align = self.placement_align,
            width = self.w,
            height = self.h,
            window = self.window.window.id,
            widgets = [i.info() for i in self.widgets],
            widgetdata = widgetdata,
            )

    def cmd_hide(self):
        self.hidden = True

    def cmd_unhide(self):
        self.hidden = False
    
    def cmd_toggle_hidden(self):
        self.hidden = not self.hidden

    def cmd_set_above(self):
        self.above = True
    
    def cmd_unset_above(self):
        self.above = False

    def cmd_toggle_above(self):
        self.above = not self.above

    def cmd_destroy(self):
        self.destroy()
