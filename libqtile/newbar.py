
import window
from newwidget import Widget

import Image

'''
Note:
Although the bar could be rotated, we code as if the bar were horizontal:
width is horizontal dimension,
height is vertical dimension,
x is horizontal displacement,
y is vertical displacement
'''


class Bar:

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

        self.edge = edge
        self.width = width
        self.height = height
        
        self.qtile = None
        self.screen = None
        self.window = None
        self.gc = None
        self.theme = None

        self.need_arrange = True
        
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
            self.x = (self.screen.dheight + self.screen.dx) - (self.screen.dheight - self.width)/2
       
        if edge in (self.TOP, self.LEFT):
            self.y = 0
        elif edge == BOTTOM:
            self.y = self.screen.height - self.height
        elif edge == RIGHT:
            self.y = self.screen.width - self.height
        
        self._init_window()

        for w in self.widgets:
            w._configure(self, theme) #all that they need to know

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
        self.window.handle_Expose = self.handle_Expose
        self.window.handle_ButtonPress = self.handle_ButtonPress
        self.qtile.internalMap[self.window.window] = self.window
        
        self.gc = self.window.window.create_gc()

        self.window.unhide()  

    
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

    def draw(self):
        if self.need_arrange:
            self.arrange_widgets()
        self.image = Image.new("RGBA", 
                               (self.width, self.height), 
                               self.theme["bar_bg_normal"]
                               )
        for w, data in self.widgetData.items():
            im = w.draw(Image.new("RGBA",
                                  (data['width'], self.height)
                                  ))
            self.image.paste(im,
                             (data['offset'], 0),
                             im
                             )
        rgbimage = self.image.convert("RGB")
        self.window.window.put_pil_image(self.gc,
                                         0, 0,
                                         rgbimage
                                         )


    def handle_Expose(self, e):
        self.draw()
        
    def handle_ButtonPress(self, e):
        for w, d in self.widgetData.items():
            if d['offset'] <= e.event_x < d['offset'] + d['width']:
                w.click(e.event_x - d['offset'], e.event_y)
                
                                             


    #############
    # COMPATIBILITY: act like an old bar
    #############
    @property
    def size(self):
        return self.width
        
