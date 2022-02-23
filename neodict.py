import random
from functools import partial
from kivy.app import App
from kivy.clock import Clock
from kivy.graphics.texture import Texture
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from kivymd.uix.button import MDRaisedButton
from kivy.uix.widget import Widget
from kivy.uix.gridlayout import GridLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.button import Button
from kivy.graphics import Color
from kivy.graphics import Rectangle
from kivy.core.window import Window
from kivymd.app import MDApp
from kivymd.uix.label import MDLabel, MDIcon
from kivy.uix.textinput import TextInput
from kivy.properties import ObjectProperty
from kivy.utils import get_color_from_hex
import pandas as pd
import csv
import numpy as np
import random
import io
from tensorflow import keras
from tensorflow.keras import layers

# creating a screen manager
class Manager(ScreenManager):
    pass

# creating child classes of screen
# for splash screen on startup
class SplashScreen(Screen):
    pass

# for the main game
class MainScreen(Screen):
    pass

# and a screen to show previous definitions
class DefinitionsScreen(Screen):
    pass

# made the window roughly phone sized to check how it will look there
Window.size = (400,700)

class neoDict(MDApp):

    # building the app from kv file and screen class instances
    def build(self):
        #changing window name from default
        self.title = 'Vorpal Dictionary'
        # setting some colour themes
        self.theme_cls.primary_palette = "Blue"
        self.theme_cls.theme_style = "Dark"

        # adding screens to the screen manager
        sm = ScreenManager()
        self.splash_screen = SplashScreen()
        sm.add_widget(self.splash_screen)
        self.main_screen = MainScreen()
        sm.add_widget(self.main_screen)
        self.def_screen = DefinitionsScreen()
        sm.add_widget(self.def_screen)

        # loading kv file with app components
        kv_file = Builder.load_file('app_ui.kv')

        #returning the loaded app with screen manager root
        return kv_file

    def load_words(self):
        #load the file, get words into a list and start sending to app or
        generated_words = open('generated_adjs.txt', 'r')
        generated_words = generated_words.read()

        self.words_list = list([i for i in set(generated_words.split(" ")) if len(i) > 0])
        random.shuffle(self.words_list)

        self.definitions_dict = {}

    def set_word(self):
        self.prompt_word = self.words_list[0]
        prompt_text = "What does \n {} \n mean?".format(self.prompt_word)
        self.root.get_screen('Main').ids.prompttext.text = prompt_text
        # and add a skip word button, exit button?, and text input to ui


    # convert to full dictionary entry

    # makes a fake phonetic version with direct substitution of letters
    def make_phonetic(self, word):
      letters_phon = "æɓçɖɘɸɡʜɪjkɭɰɲøpqʁstʊʋwχyʒ"
      letters_alph = "abcdefghijklmnopqrstuvwxyz"
      replaced = [letters_phon[letters_alph.index(i)] for i in word]
      return "/{}/".format("".join(replaced))

    # puts everything together and appends entry to text file
    def make_entries(self, filename='new_dictionary'):
      for key, value in definitions_dict.items():
        entry = key + "\n adjective \n" + make_phonetic(key) + "\n" + value[0] + "\n" + "- {}".format(value[1])

        with open(filename + ".txt", "a") as txt:
                txt.write(entry + "\n\n")

    def submit(self, definition):
        # switch text to ask for example in a sentence, maybe have a different screen
        self.root.get_screen('Main').ids.prompttext.text = 'Ok. And what is an example of {} in a sentence'.format(self.prompt_word)
        self.state = example
        # could also do


    def skip(self):
        self.words_list = self.words_list[1:]
        self.set_word()



# running the app
if __name__ == '__main__':
    neoDict().run()
