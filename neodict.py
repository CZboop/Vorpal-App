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
import threading

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
    prompt_word = ""

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

        # starting thread for neural network.....
        threading.Thread(target=self.generate_words, daemon=True).start()
        # nice seems to work well, but need to have something in place to stop the neural net loop when app is exited
        # could always start it with some of the premade ones 
        # TODO: add generating screen and manage switch to definitions after first epoch or whenever

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
        self.state = "example"
        # could also do


    def skip(self):
        self.words_list = self.words_list[1:]
        self.set_word()

    def generate_words(self):
        # lstm text gen, just store in a class property and can then have an option to save the result of later processing as file or pickle and reload?

        # loading training data and doing some setup
        adjs_df = pd.read_csv('Adjectives.csv',  usecols=[1], header = 0, delimiter=",", quoting=csv.QUOTE_NONE,
                               encoding='utf-8')
        adjs_df.columns = ['word']

        adjs = adjs_df.word.tolist()
        adjs = [i.replace(" ", "") for i in adjs]
        text = " ".join(adjs).lower().replace("\"", "")
        # print(text[:100], len(text))

        chars = sorted(list(set(text)))
        # print(chars)

        # making dicts for encoding of characters
        char_indices = dict((v, c) for c,v in enumerate(chars))
        indices_char = dict((c, v) for c,v in enumerate(chars))

        maxlen = 30
        step = 3
        sequences = []
        next_char = []

        for i in range(0, len(text) - maxlen, step):
          sequences.append(text[i : i + maxlen])
          next_char.append(text[i + maxlen])

        x = np.zeros((len(sequences), maxlen, len(chars)), dtype=np.bool)
        y = np.zeros((len(sequences), len(chars)), dtype=np.bool)
        #
        for i, sequence in enumerate(sequences):
            for t, char in enumerate(sequence):
                x[i, t, char_indices[char]] = 1
            y[i, char_indices[next_char[i]]] = 1

        model = keras.models.load_model('adj_generate_model.h5', custom_objects=None, compile=True, options=None)


        epochs = 40
        batch_size = 128

        for epoch in range(epochs):
            model.fit(x, y, batch_size=batch_size, epochs=1)
            print("Generating... \n Epoch: " + str(epoch))

            start_index = random.randint(0, len(text) - maxlen - 1)
            for diversity in [0.2, 0.5, 1.0, 1.2]:
                generated = ""
                sentence = text[start_index : start_index + maxlen]

                for i in range(400):
                    x_pred = np.zeros((1, maxlen, len(chars)))
                    for t, char in enumerate(sentence):
                        x_pred[0, t, char_indices[char]] = 1.0
                    preds = model.predict(x_pred, verbose=0)[0]
                    next_index = self.sample(preds, diversity)
                    next_char = indices_char[next_index]
                    sentence = sentence[1:] + next_char
                    generated += next_char
                # print("Generated: ", generated)

                with open("generated_adjs.txt", "a") as txt:
                  # tend to get a lot of repeats for some seeds, filter out when reading back the file
                  txt.write(generated + " ")
        model.save('adj_generate_model.h5')
        generated_words = open('generated_adjs.txt', 'r')
        generated_words = generated_words.read()

        words_list = list([i for i in set(generated_words.split(" ")) if len(i) > 0])

        # rewriting the file without repeated words
        with open("generated_adjs.txt", "w") as txt:
          for i in words_list:
                  txt.write(i + "\n")

    def sample(self, preds, temperature=1.0):
        preds = np.asarray(preds).astype("float64")
        preds = np.log(preds) / temperature
        exp_preds = np.exp(preds)
        preds = exp_preds / np.sum(exp_preds)
        probas = np.random.multinomial(1, preds, 1)
        return np.argmax(probas)




# running the app
if __name__ == '__main__':
    neoDict().run()
