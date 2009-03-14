from clientstack import ClientStack
from sublayout import VerticalStack, SubLayout, Rect


class SubTile(SubLayout):
    def __init__(self, clientStack, parent=None, autohide=True, master_windows=1, ratio=0.618, expand=True):
        self.master_windows = master_windows
        self.ratio = ratio
        self.expand = expand
        SubLayout.__init__(self, clientStack, parent, autohide)

    def _init_sublayouts(self):
        class MasterWindows(VerticalStack):
            def filter(self, client):
                return self.index_of(client) < self.parent.master_windows
            def request_rectangle(self, r, windows):
                #just take the lot, since this is called AFTER slave windows
                # - let the slaves take what they want, we'll have the rest
                return (r, Rect())

        class SlaveWindows(VerticalStack):
            def filter(self, client):
                return self.index_of(client) >= self.parent.master_windows
            def request_rectangle(self, r, windows):
                if self.autohide and len(windows) == 0:
                    return (Rect(), r)
                else:
                    rmaster, rslave = r.split_vertical(ratio=self.parent.ratio)
                    return (rslave, rmaster)
            
        self.sublayouts.append(SlaveWindows(self.clientStack,
                                            parent=self,
                                            autohide=self.expand,
                                            )
                               )
        self.sublayouts.append(MasterWindows(self.clientStack,
                                             parent=self,
                                             autohide=False
                                             )
                               )
        self.sublayout_names = {'masters': self.sublayouts[0],
                                'slaves': self.sublayouts[1]}
                   
    def filter(self, client):
        return True #TAKE THEM ALL

    def request_rectangle(self, rectangle, windows):
        #        rectangle I want           rectangle left = NOTHING!!
        return (rectangle, Rect())

    def cmd_inc_ratio(self, inc):
        self.ratio += inc
        if self.ratio < 0: self.ratio = 0.0
        if self.ratio > 1: self.ratio = 1.0
        self.clientStack.group.layoutAll()

    def cmd_inc_nmaster(self, inc=1):
        self.master_windows += inc
        self.clientStack.group.layoutAll()
