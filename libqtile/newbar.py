
import window
from newwidget import Widget
from manager import Hooks
from command import CommandObject, CommandError

import Image
from Xlib import X

'''
Note:
Although the bar could be rotated, we code as if the bar were horizontal:
width is horizontal dimension,
height is vertical dimension,
x is horizontal displacement,
y is vertical displacement
'''


class Bar(CommandObject):

    new_bar = True

    WIDTH_SCREEN = 1
    TOP, BOTTOM, RIGHT, LEFT = 1,2,3,4
    def __init__(self, widgets, edge,
                 width=WIDTH_SCREEN, height=20):
        self.widgets = widgets
        self.widgetData = {}
        for w in self.widgets:
            self.widgetData[w] = {}
            self.widgetData[w]['width'] = 0
            self.widgetData[w]['offset'] = 0
            self.widgetData[w]['image'] = None

        self.edge = edge
        self.width = width
        self.height = height
        
        self.qtile = None
        self.screen = None
        self.window = None
        self.gc = None
        self.theme = None

        self.need_arrange = True
        self.baseimage = None
        
        self.keyboard_grabbers = []
        
    def _configure(self, qtile, screen, theme):
        self.qtile = qtile
        self.screen = screen
        self.theme = theme

        edge = self.edge
        
        if self.width == self.WIDTH_SCREEN:
            if edge in (self.TOP, self.BOTTOM): #is it horizontal
                self.width = self.screen.width
            else:
                self.width = self.screen.dheight

        if edge in (self.TOP, self.BOTTOM): #is it horizontal
            self.x = (self.screen.width - self.width)/2 #assume center
            #TODO: make the bars alignable
        else:
            self.x = (self.screen.height - self.width)/2 #assume center
       
        if edge in (self.TOP, self.LEFT):
            self.y = 0
        elif edge == self.BOTTOM:
            self.y = self.screen.height - self.height
        elif edge == self.RIGHT:
            self.y = self.screen.width - self.height
        
        self._init_window()

        for w in self.widgets:
            self.qtile.registerWidget(w)
            w._configure(self, theme) #all that they need to know

    
    def _init_baseimage(self):
        self.baseimage = Image.new("RGBA", 
                               (self.width, self.height), 
                               self.theme["bar_bg_normal"]
                               )
        
        Hooks.call_hook("bar-draw", self.baseimage)

    def _init_window(self):
        c = self.qtile.display.screen().default_colormap.alloc_named_color(
            "black").pixel
        if self.edge in (self.TOP, self.BOTTOM):
            x,y,w,h = self.x, self.y, self.width, self.height
        else:
            x,y,w,h = self.y, self.x, self.height, self.width
        self.window = window.Internal.create(self.qtile,
                                             c,
                                             x, y, w, h,
                                             self.theme["bar_opacity"]
                                             )
        self.window.name = "qtile-newbar"
        self.window.handle_Expose = self.handle_Expose
        self.window.handle_ButtonPress = self.handle_ButtonPress
        self.window.handle_KeyPress = self.handle_KeyPress
        self.qtile.internalMap[self.window.window] = self.window
        
        self.gc = self.window.window.create_gc()

        self.window.unhide()  

        self.window.addMask(X.KeyPressMask)

    
    def arrange_widgets(self):
        width = self.width
        ledge, redge = 0, width
 
        widgets = self.widgets
        lalign = [w for w in widgets \
                      if w.align == Widget.ALIGN_LEFT]
        ralign = [w for w in widgets \
                      if w.align == Widget.ALIGN_RIGHT]
        ralign.reverse()

        for w in lalign:
            if redge - ledge <= 0:
                print "not enough room to fit %s" % w.name
                break
            elif redge - ledge >= w.width_req:
                self.widgetData[w]['width'] = w.width_req
                self.widgetData[w]['offset'] = ledge
            else:
                self.widgetData[w]['width'] = redge - ledge
                self.widgetData[w]['offset'] = ledge
            ledge += self.widgetData[w]['width']

        for w in ralign:
            if redge - ledge <= 0:
                print "not enough room to fit %s" % w.name
                break
            elif redge - ledge >= w.width_req:
                self.widgetData[w]['width'] = w.width_req
                self.widgetData[w]['offset'] = redge - \
                    self.widgetData[w]['width']
            else:
                self.widgetData[w]['width'] = redge - ledge
                self.widgetData[w]['offset'] = redge - \
                    self.widgetData[w]['width']
            redge -= self.widgetData[w]['width']

        self.need_arrange = False

    def draw_widget(self, w):
        data = self.widgetData[w]
        im = w.draw(Image.new("RGBA",
                              (data['width'], self.height)
                              ))
        self.widgetData[w]['image'] = im
            

    def draw(self):
        if self.need_arrange:
            self.arrange_widgets()
        if not self.baseimage:
            self._init_baseimage()

        self.image = self.baseimage.copy()
        
        for w, data in self.widgetData.items():    
            if data['image'] is None:
                self.draw_widget(w)
            im = data['image']
            self.image.paste(im,
                             (data['offset'], 0),
                             im
                             )
        rgbimage = self.image.convert("RGB")

        if self.edge == self.LEFT:
            rgbimage = rgbimage.rotate(90, expand=1)
        elif self.edge == self.RIGHT:
            rgbimage = rgbimage.rotate(-90, expand=1)
        
        self.window.window.put_pil_image(self.gc,
                                         0, 0,
                                         rgbimage
                                         )

    def update_widget(self, w):
        self.widgetData[w]['image'] = None
        self.draw()

    def handle_Expose(self, e):
        self.draw()
        
    def handle_ButtonPress(self, e):
        x, y = e.event_x, e.event_y
        if self.edge == self.LEFT:
            x,y = (self.width - y), x
        elif self.edge == self.RIGHT:
            x, y = y, (self.height - x)
        for w, d in self.widgetData.items():
            if d['offset'] <= x < d['offset'] + d['width']:
                w.click(x - d['offset'], y)
                

    def handle_KeyPress(self, e):
        if not self.keyboard_grabbers:
            print "no grabbing atm"
            return
        else:
            self.keyboard_grabbers[-1].handle_KeyPress(e)

    def grab_keyboard(self, widget):
        self.keyboard_grabbers.append(widget)
        if len(self.keyboard_grabbers) == 1:
            self.window.window.grab_keyboard(0, X.GrabModeAsync, X.GrabModeAsync, X.CurrentTime)
        else:
            #it's already grabbed
            return

    def ungrab_keyboard(self, widget):
        try:
            self.qtile.display.ungrab_keyboard(X.CurrentTime)
            self.keyboard_grabbers.remove(widget)
        except:
            pass

    #############
    # COMPATIBILITY: act like an old bar
    #############
    @property
    def size(self):
        return self.height   

    @property
    def position(self):
        if self.edge == self.TOP:
            return "top"
        elif self.edge == self.BOTTOM:
            return "bottom"
        elif self.edge == self.LEFT:
            return "left"
        elif self.edge == self.RIGHT:
            return "right"

    #############
    # COMMAND OBJECT STUFF
    #############
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
        print "in barinfo"
        widgetdata = {}
        for k,v in self.widgetData.items():
            widgetdata[k.name] = {'offset': v['offset'], 
                                  'width': v['width'] }
        return dict(
            edge = self.edge,
            width = self.width,
            height = self.height,
            window = self.window.window.id,
            widgets = [i.info() for i in self.widgets],
            widgetdata = widgetdata,
            )
