





"""


    def select_piece(self, button):
        self.pawn_promotion_view.dismiss()
        return button.text

    def prompt_for_promotion(self, color: Literal["W", "B"], inst) -> Literal["Q", "R", "B", "N"] | None:
        \"""
        Open a ModalView to prompt for pawn promotion piece choice
        \"""
        self.pieces = {
            "WQ": "\u2655",
            "WR": "\u2656",
            "WB": "\u2657",
            "WN": "\u2658",

            "BQ": "\u265B",
            "BR": "\u265C",
            "BB": "\u265D",
            "BN": "\u265E",
        }
        if not inst.pawn_promotion_view:
            box = GridLayout(rows=4, cols=1)
            box.add_widget(MDFlatButton(text=self.pieces["WQ"], on_release=self.select_piece))
            box.add_widget(MDFlatButton(text=self.pieces["WR"], on_release=self.select_piece))
            box.add_widget(MDFlatButton(text=self.pieces["WB"], on_release=self.select_piece))
            box.add_widget(MDFlatButton(text=self.pieces["WN"], on_release=self.select_piece))
            inst.pawn_promotion_view = ModalView(
                size_hint=(None, None),
                size=(75, 310),
                background_color=(255, 255, 255, 1),
                overlay_color=(0, 0, 0, 0.4),
                padding=5
                )
            inst.pawn_promotion_view.add_widget(box)
        inst.pawn_promotion_view.open()
        print("opened") # does it wait?

"""









from kivy.lang import Builder
from kivy.properties import StringProperty

from kivymd.app import MDApp
from kivy.uix.modalview import ModalView
from kivy.uix.gridlayout import GridLayout
from kivymd.uix.button import MDFlatButton

KV = '''
<MDFlatButton>
    font_name: "DejaVuSans"
    font_size: 50

MDFloatLayout:

    MDFlatButton:
        text: "ALERT DIALOG"
        pos_hint: {'center_x': .5, 'center_y': .5}
        on_release: app.show_simple_dialog()
'''


class Example(MDApp):
    pawn_promotion_view = None

    def build(self):
        return Builder.load_string(KV)
    
    def select_piece(self, button):
        print(button, button.text)
        self.pawn_promotion_view.dismiss()


    def show_simple_dialog(self):
        self.piece_map = {
            "WK": "\u2654",
            "WQ": "\u2655",
            "WR": "\u2656",
            "WB": "\u2657",
            "WN": "\u2658",
            "WP": "\u2659",
            "BK": "\u265A",
            "BQ": "\u265B",
            "BR": "\u265C",
            "BB": "\u265D",
            "BN": "\u265E",
            "BP": "\u265F",
            "  ": "  "
        }
        if not self.pawn_promotion_view:
            box = GridLayout(rows=4, cols=1)
            box.add_widget(MDFlatButton(text=self.piece_map["WQ"], on_release=self.select_piece))
            box.add_widget(MDFlatButton(text=self.piece_map["WR"], on_release=self.select_piece))
            box.add_widget(MDFlatButton(text=self.piece_map["WB"], on_release=self.select_piece))
            box.add_widget(MDFlatButton(text=self.piece_map["WN"], on_release=self.select_piece))
            self.pawn_promotion_view = ModalView(
                size_hint=(None, None),
                size=(75, 310),
                background_color=(255, 255, 255, 1),
                overlay_color=(0, 0, 0, 0.4),
                padding=5
                )
            self.pawn_promotion_view.add_widget(box)
        self.pawn_promotion_view.open()


Example().run()

"""
    def show_simple_dialog(self):
        self.piece_map = {
            "WK": "\u2654",
            "WQ": "\u2655",
            "WR": "\u2656",
            "WB": "\u2657",
            "WN": "\u2658",
            "WP": "\u2659",
            "BK": "\u265A",
            "BQ": "\u265B",
            "BR": "\u265C",
            "BB": "\u265D",
            "BN": "\u265E",
            "BP": "\u265F",
            "  ": "  "
        }
        if not self.dialog:
            size = (Window.size[0]//2.75, Window.size[1]//4)
            self.dialog = MDDialog(
                title="",
                type="simple",
                buttons=[MDFlatButton(
                    text=self.piece_map[i], 
                    font_size=min(size)//5,
                    on_release=self.select_piece,
                    )
                    for i in ("WQ", "WR", "WB", "WN")],
                #radius=[20, 20, 20, 20],
                #size_hint=(0.5, 0.1),
                #size=size
            )
        self.dialog.open()
"""