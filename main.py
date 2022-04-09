from kivy_classes.menu import MenuWindow, WindowManager
from kivy.core.window import Window
from kivy.app import App

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