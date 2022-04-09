import kivy
from kivy.app import App
from kivy.lang import Builder
from kivy.core.window import Window
# screen
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.scrollview import ScrollView
from kivy.graphics import Color, Rectangle
from kivy.uix.filechooser import FileChooserIconView
# object
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.image import Image
#from kivy.uix.image import Image
#from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.button import Button
# layout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from functools import partial
# prop
from kivy.properties import NumericProperty, StringProperty, ObjectProperty
# python
import json, os
import numpy as np
from decoder.decoder import decode

class MenuWindow(Screen):
    def __init__(self,**kwargs):
        super(MenuWindow,self).__init__(**kwargs)
        # set name        
        self.name = "menu"
        self.path_image = ""

    def on_leave(self):
        self.clear_widgets()
        
    def on_enter(self):
        # add title label
        self.title_label = Label(text="Calisthenics Evaluator 3000", 
                             pos_hint={"center_x":0.5,"top":0.98},
                             size_hint= (0.1, 0.05),
                             font_size= (self.width**2 + self.height**2) / 5**4)
        self.add_widget(self.title_label)

        # Image
        ratio_hw = Window.height / Window.width
        print(ratio_hw)
        self.image_plot = Image(pos_hint={'top':0.93,'center_x':0.5}, size_hint=(0.9,0.4), source="", allow_stretch=True)
        self.add_widget(self.image_plot)
        
        # file chooser
        self.file_chooser = FileChooserIconView(pos_hint={'top':0.45}, size_hint=(1,0.45), sort_func=self.order_by_date)
        self.file_chooser.bind(on_submit=partial(self.onFileSelected,self.file_chooser.selection))
        self.add_widget(self.file_chooser)
        print(self.file_chooser.file_system)

        # Evaluate button
        button_evaluate = Button(text='Evaluate', 
                             pos_hint={"center_x":0.1,"top":0.5},
                             size_hint= (0.1, 0.05))
        button_evaluate.bind(on_press=self.onPressed_evaluate)
        self.add_widget(button_evaluate)
        self.label_evaluate = Label(text='', 
                                pos_hint={"center_x":0.4,"top":0.5},
                                size_hint= (0.3, 0.05))
                                #font_size= (self.width**2 + self.height**2) / 7**4)
        self.add_widget(self.label_evaluate)

    def order_by_date(self, files, filesystem):
        list_file = sorted(f for f in files if filesystem.is_dir(f)) + sorted((f for f in files if not filesystem.is_dir(f)), key=lambda fi: os.stat(fi).st_mtime, reverse = True)
        return list_file

        
    def onFileSelected(self, entry, parent, selection, instance):
        try:
            self.path_image = selection[0]
            self.image_plot.source = selection[0]
        except:
            pass

    def onPressed_evaluate(self, instance):
        # run ia on it and return a score, that is showed in self.label_evaluate
        dic_res = decode(self.path_image)
        if dic_res != None:
            text_to_show = "This looks like a {}".format(dic_res['name'])
            for metric_key in dic_res['metrics']:
                text_to_show += '\n{}: {:.0%}'.format(metric_key,dic_res['metrics'][metric_key])
            self.label_evaluate.text = text_to_show
        else:
            text_to_show = "This looks like nothing known, please do better."
            self.label_evaluate.text = text_to_show

 
class WindowManager(ScreenManager):
    pass
    

if __name__ == "__main__":   
    sm = WindowManager()
    sm.add_widget(MenuWindow(name='menu'))
    sm.current = "menu"
    
    
    class MyMainApp(App):
        def build(self):
            return sm
        
    Window.fullscreen = False
    Window.size = (1080,2042)
    import sys
    app = MyMainApp()
    sys.exit(app.run())
    