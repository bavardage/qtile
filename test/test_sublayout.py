import libpry
from libqtile.layout.sublayout.sublayout import Rect, VerticalStack
from libqtile import layout
import utils

class uRect(libpry.AutoTree):
    def test_horizontal_split(self):
        r = Rect(100, 200, 300, 400)
        left, right = r.split_horizontal(ratio=0.1)
        assert left == Rect(100, 200, 300, 40)
        assert right == Rect(100, 240, 300, 360)

        r = Rect(100, 200, 300, 400)
        left, right = r.split_horizontal(height=40)
        assert left == Rect(100, 200, 300, 40)
        assert right == Rect(100, 240, 300, 360)

        libpry.raises(Exception, r.split_horizontal, ratio=1.1)
        libpry.raises(Exception, r.split_horizontal, height=401)

    def test_vertical_split(self):
        r = Rect(100, 200, 300, 400)
        left, right = r.split_vertical(ratio=0.1)
        assert left == Rect(100, 200, 30, 400)
        assert right == Rect(130, 200, 270, 400)

        r = Rect(100, 200, 300, 400)
        left, right = r.split_vertical(width=30)
        assert left == Rect(100, 200, 30, 400)
        assert right == Rect(130, 200, 270, 400)

        libpry.raises(Exception, r.split_vertical, ratio=1.1)
        libpry.raises(Exception, r.split_vertical, width=301)#

    def test_equality(self):
        assert Rect(1, 2, 3, 4) == Rect(1, 2, 3, 4)
        assert Rect(1, 2, 3, 4) != Rect(1, 2, 3, 3)

    def test_center(self):
        r = Rect(10, 20, 30, 40)
        assert r.center == (25, 40)

class VertStack(VerticalStack):
    '''
    Just fill in the methods ness to use this sublayout
    '''
    def filter(self, c):
        return True
    def request_rectangle(self, r, windows):
        return (r, Rect(0,0,0,0))

class Config:
    groups = ["a", "b", "c"]
    layouts = [
        layout.ClientStack(
            SubLayouts=[
                (VertStack, {}),
                (layout.SubFloating, {}),
                (layout.SubMax, {}),
                (layout.SubMagnify, {}),
                ],
            add_mode=layout.ClientStack.ADD_TO_BOTTOM,
            ),
           
        ]
    keys = []
    screens = []
    theme = None

class uTopLevelSublayout(utils.QtileTests):
    config = Config()
    
    def test_basic_command_interface(self):
        tlsl = self.c.layout.sublayouts['current']
        info = tlsl.info()
        assert info['windows'] == []
        assert info['name'] == 'TopLevelSubLayout'
        # we cannot compare the sublayouts directly, since
        # the list of sublayouts come from sublayout_names.keys() - 
        # we cannot be sure of the ordering
        sls = info['sublayouts']
        for sl in ['minimised', 'maximised', 'main', 'specialtypes', 'floating']:
            assert sl in sls
        assert len(sls) == 5

        main = tlsl.sl['main']
        info = main.info()
        assert info['name'] == 'VertStack'
        assert info['windows'] == []
        assert info['sublayouts'] == []

    def test_window_filtering(self):
        self.testWindow("one")
        self.testWindow("two")
        self.testWindow("three")
        
        tlsl = self.c.layout.sublayouts['current']
        info = tlsl.info()
        assert info['windows'] == ["one", "two", "three"]

        assert tlsl.sl['main'].info()['windows'] == ["one", "two", "three"]
        
        self.c.window.toggle_floating()

        assert tlsl.sl['main'].info()['windows'] == ["one", "two"]
        assert tlsl.sl['floating'].info()['windows'] == ["three"]

        self.c.window.minimise()

        assert tlsl.sl['main'].info()['windows'] == ["one", "two"]
        assert tlsl.sl['minimised'].info()['windows'] == ["three"]

        self.c.window.maximise()

        assert tlsl.sl['main'].info()['windows'] == ["one", "two"]
        assert tlsl.sl['maximised'].info()['windows'] == ["three"]

        #TODO: Test special types

class uMinimisedMaximisedFloating(utils.QtileTests):
    '''
    tests:
     - Maximised, Minimised, Floating
    '''
    config=Config()

    def test_minimised(self):
        self.testWindow("one")
        self.c.window.minimise()
        assert self.c.window.info()['next_placement']['hi'] == True
        self.c.window.unminimise()
        assert self.c.window.info()['next_placement']['hi'] == False

    def test_maximised(self):
        self.testWindow("one")
        self.testWindow("two")
        self.testWindow("three")

        screen = self.c.screen.info()

        self.c.window.maximise()
        info = self.c.window.info()
        assert info['width'] + 2*info['next_placement']['bw'] == screen['width']
        assert info['height'] + 2*info['next_placement']['bw'] == screen['height']
        assert info['x'] == screen['x']
        assert info['y'] == screen['y']

    def test_floating(self):
        self.testWindow("one")
        self.c.window.toggle_floating()
        info = self.c.window.info()
        fd = info['floatDimensions']
        assert fd['w'] == info['width']
        assert fd['h'] == info['height']
        assert fd['x'] == info['x']
        assert fd['y'] == info['y']

class uNormalSublayouts(utils.QtileTests):
    config=Config()
    def test_SubFloating(self):
        self.c.layout.nextsublayout()
        assert self.c.layout.sublayouts['current'].sl['main'].info()['name'] == 'SubFloating'
    
        self.testWindow("one")
        info = self.c.window.info()
        fd = info['floatDimensions']
        assert fd['w'] == info['width']
        assert fd['h'] == info['height']
        assert fd['x'] == info['x']
        assert fd['y'] == info['y']
        
        self.testWindow("two")
        info = self.c.window.info()
        fd = info['floatDimensions']
        assert fd['w'] == info['width']
        assert fd['h'] == info['height']
        assert fd['x'] == info['x']
        assert fd['y'] == info['y']

    def test_SubMax(self):
        self.c.layout.nextsublayout()
        self.c.layout.nextsublayout()
        assert self.c.layout.sublayouts['current'].sl['main'].info()['name'] == 'SubMax'
        
        screen = self.c.screen.info()

        self.testWindow("one")
        info = self.c.window.info()
        assert info['width'] + 2*info['next_placement']['bw'] == screen['width']
        assert info['height'] + 2*info['next_placement']['bw'] == screen['height']
        assert info['x'] == screen['x']
        assert info['y'] == screen['y']

        self.testWindow("two")
        info = self.c.window.info()
        assert info['width'] + 2*info['next_placement']['bw'] == screen['width']
        assert info['height'] + 2*info['next_placement']['bw'] == screen['height']
        assert info['x'] == screen['x']
        assert info['y'] == screen['y']


    def test_SubMagnify(self):
        self.c.layout.nextsublayout()
        self.c.layout.nextsublayout()
        self.c.layout.nextsublayout()
        assert self.c.layout.sublayouts['current'].sl['main'].info()['name'] == 'SubMagnify'

        self.testWindow("one")
        self.testWindow("two")
        self.testWindow("three")
        
        submagnify = self.c.layout.sublayouts['current'].sl['main']
        assert submagnify.sl['magnified'].info()['windows'] == ["three"]
        assert submagnify.sl['stack'].info()['windows'] == ["one", "two"]


tests = [
    uRect(),
    utils.xfactory(xinerama=False), [
        uTopLevelSublayout(),
        uMinimisedMaximisedFloating(),
        uNormalSublayouts(),
        ],
    ]
