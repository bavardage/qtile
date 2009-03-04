from sublayout import VerticalStack, SubLayout, Rect

class SubMagnify(SubLayout):
    def __init__(self, clientStack, parent=None, ratio=0.7):
        self.ratio = ratio
        SubLayout.__init__(self, clientStack, parent)

    def _init_sublayouts(self):
        class Magnified(VerticalStack):
            def filter(self, client):
                return client is self.clientStack.focused
            def request_rectangle(self, r, windows):
                bw = int((r.w - (r.w * self.parent.ratio))/2)
                bh = int((r.h - (r.h * self.parent.ratio))/2)
                return (Rect(r.x + bw,
                             r.y + bh,
                             r.w - 2*bw,
                             r.h - 2*bh
                             ),
                        r
                        )
        class VertStack(VerticalStack):
            def filter(self, client):
                return True
            def request_rectangle(self, r, windows):
                return (r, Rect())
        self.sublayouts.append(Magnified(self.clientStack,
                                         parent=self,
                                         )
                               )
        self.sublayouts.append(VertStack(self.clientStack,
                                         parent=self,
                                         )
                               )
        self.sublayout_names = {'magnified': self.sublayouts[0],
                                'stack': self.sublayouts[1],
                                }
    
    def filter(self, client):
        return True

    def request_rectangle(self, r, windows):
        return (r, Rect())
                                            
