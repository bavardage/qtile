import libpry
import libqtile.layout, libqtile.newbar, libqtile.newwidget, libqtile.manager
from libqtile.command import _Call
import utils

theme = libqtile.manager.Theme(
    values= {
        'ttffont': '/usr/share/fonts/TTF/Vera.ttf',
        'ttffontsize': 10,
        }
    )

class GBConfig:
    keys = []
    groups = ['a', 'b', 'c', 'd']
    layouts = [libqtile.layout.stack.Stack(stacks=1)]
    screens = [
        libqtile.manager.Screen(
            top = libqtile.newbar.Bar(
                [
                    libqtile.newwidget.ClickableIcon("myicon",
                                                     "/usr/share/pixmaps/xterm_32x32.xpm",
                                                     _Call([('group', 'd')], 'toscreen'),
                                                     ),
                    ],
                libqtile.newbar.Bar.TOP,
                height=20,
                width=600,
                ),
            bottom = libqtile.newbar.Bar(
                [
                    libqtile.newwidget.GroupBox("groupbox"),
                    libqtile.newwidget.TextBox("textbox",
                                               "default",
                                               ),
                    libqtile.newwidget.PromptBox("prompt",
                                                 ">",
                                                 width=100,
                                                 ),
                    ],
                libqtile.newbar.Bar.BOTTOM,
                height=20,
                width=800,
                ),
            left = libqtile.newbar.Bar(
                [
                    libqtile.newwidget.Taskbar("taskbar", 400),
                    ],
                libqtile.newbar.Bar.LEFT,
                height=20,
                width=400,
                ),
            )
        ]
    theme = theme

class uWidgets(utils.QtileTests):
    config = GBConfig()

    def test_draw(self):
        b = self.c.bar['bottom'].info()
        assert b['widgets'][0]['name'] == "groupbox"

    def test_textbox(self):
        assert "textbox" in self.c.list_widgets()
        self.c.widget["textbox"].update("testing")
        assert self.c.widget["textbox"].get() == "testing"

    def test_groupbox_click(self):
        self.c.group["c"].toscreen()
        assert self.c.groups()["a"]["screen"] == None
        self.c.bar["bottom"].fake_click(10, 10)
        assert self.c.groups()["a"]["screen"] == 0

    def test_taskbar_click(self):
        one = self.testWindow("one")
        two = self.testWindow("two")
        assert self.c.groups()["a"]["focus"] == "two"
        self.c.bar["left"].fake_click(10,10)
        assert self.c.groups()["a"]["focus"] == "one"
        #note: this won't actually ALWAYS pass
        #since the taskbar gets its list of windows from group
        #which stores them as a set
        #which doesn't guarentee ordering
        #so the first item on the taskbar isn't guarenteed

    def test_clickableicon(self):
        self.c.group["a"].toscreen()
        assert self.c.groups()["d"]["screen"] == None
        self.c.bar["top"].fake_click(10,10)
        assert self.c.groups()["d"]["screen"] == 0

    def test_promptbox(self):
        self.c.widget["prompt"].start_grab()
        self.c.bar["bottom"].fake_keypress([], "a")
        assert self.c.widget["prompt"].get() == "a"

        self.c.bar["bottom"].fake_keypress([], "BackSpace")
        assert self.c.widget["prompt"].get() == ""

        self.c.bar["bottom"].fake_keypress([], "a")
        self.c.bar["bottom"].fake_keypress([], "Left")
        self.c.bar["bottom"].fake_keypress([], "b")
        assert self.c.widget["prompt"].get() == "ba"
        assert self.c.widget["prompt"].cursor_position() == 1
        
        self.c.bar["bottom"].fake_keypress([], "Escape")
        assert self.c.widget["prompt"].get() == ""

        self.c.widget["prompt"].start_grab()
        self.c.bar["bottom"].fake_keypress([], "a")
        self.c.bar["bottom"].fake_keypress([], "b")
        self.c.bar["bottom"].fake_keypress([], "c")
        self.c.bar["bottom"].fake_keypress([], "d")
        self.c.bar["bottom"].fake_keypress([], "e")
        assert self.c.widget["prompt"].cursor_position() == 5
        self.c.bar["bottom"].fake_keypress([], "Home")
        assert self.c.widget["prompt"].cursor_position() == 0
        self.c.bar["bottom"].fake_keypress([], "End")
        assert self.c.widget["prompt"].cursor_position() == 5

        self.c.bar["bottom"].fake_keypress([], "Return")

class PositioningConfig:
    keys = []
    groups = ['a']
    layouts = [libqtile.layout.stack.Stack(stacks=1)]
    screens = [
        libqtile.manager.Screen(
            top = libqtile.newbar.Bar(
                [
                    libqtile.newwidget.TestWidget("1", 100, "#ff0000"),
                    libqtile.newwidget.TestWidget("2", 50, "#00ff00"),
                    libqtile.newwidget.TestWidget("1r", 100,
                                                  "#0000ff",
                                                  align=libqtile.newwidget.base.Widget.ALIGN_RIGHT),
                    libqtile.newwidget.TestWidget("2r", 50,
                                                  "#0000ff",
                                                  align=libqtile.newwidget.base.Widget.ALIGN_RIGHT),
                    ],
                libqtile.newbar.Bar.TOP,
                height=20,
                width=800,
                ),
            bottom = libqtile.newbar.Bar(
                [
                    libqtile.newwidget.TestWidget("ok", 500, "#ff0000"),
                    libqtile.newwidget.TestWidget("greedy", 100000, "#00ff00"),
                    libqtile.newwidget.TestWidget("gone", 100000, "#0000ff"),
                    ],
                libqtile.newbar.Bar.BOTTOM,
                height=20,
                width=600,
                ),
            )
        ]
    theme = theme
                    

class uPositioning(utils.QtileTests):
    config = PositioningConfig()
    
    def test_normal_positioning(self):
        data = self.c.bar["top"].info()['widgetdata']
        assert data["1"] == {'width': 100, 'offset': 0}
        assert data["2"] == {'width': 50, 'offset': 100}
        assert data["1r"] == {'width': 100, 'offset': 650}
        assert data["2r"] == {'width': 50, 'offset': 750}

    def test_extreme_positioning(self):
        #EXTREME!!!
        data = self.c.bar["bottom"].info()['widgetdata']
        assert data["ok"] == {'width': 500, 'offset': 0}
        assert data["greedy"] == {'width': 100, 'offset': 500}
        assert data["gone"] == {'width': 0, 'offset': 0}

tests = [
    utils.xfactory(xinerama=True), [
        uWidgets(),
        uPositioning(),
        ]
    ]
