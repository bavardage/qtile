import libpry
from libqtile.layout.sublayout.sublayout import Rect

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



tests = [
    uRect(),
    ]
