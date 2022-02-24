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
from time import time
from kivy.animation import Animation

#TODO:
# possibly account for running out of words during the process? would probs essentially be reusing the thing of when not empty list to revert
# and just if it runs out go back to the generating screen until....
# maybe have it auto skip words that are real english words? may be slow/unnecessary tho
# account for dashes in some words when switching to phonetics (just use the original char if not in the a-z string)

# creating a screen manager
class Manager(ScreenManager):
    pass

# creating child classes of screen
# for splash screen on startup
class SplashScreen(Screen):
    pass

# for the main game
class DefineScreen(Screen):
    pass

class ExampleScreen(Screen):
    pass

# loading screen for while words are generating
class GeneratingScreen(Screen):
    pass

# and a screen to show previous definitions
class DefinitionsScreen(Screen):
    pass

# made the window roughly phone sized to check how it will look there
Window.size = (400,700)

class neoDict(MDApp):
    prompt_word = ""
    generated_words = []

    # building the app from kv file and screen class instances
    def build(self):
        # on close event for potentially ending threads etc
        Window.bind(on_request_close=self.on_request_close)
        #changing window name from default
        self.title = 'Vorpal Dictionary'

        # setting some colour themes
        self.theme_cls.primary_palette = "Blue"
        self.theme_cls.theme_style = "Dark"

        # adding screens to the screen manager
        sm = ScreenManager()
        self.splash_screen = SplashScreen()
        sm.add_widget(self.splash_screen)
        self.define_screen = DefineScreen()
        sm.add_widget(self.define_screen)
        self.example_screen = ExampleScreen()
        sm.add_widget(self.example_screen)
        self.gen_screen = GeneratingScreen()
        sm.add_widget(self.gen_screen)

        # starting thread for neural network
        threading.Thread(target=self.generate_words, daemon=True).start()

        # loading kv file with app components
        kv_file = Builder.load_file('app_ui.kv')

        #returning the loaded app with screen manager as root
        return kv_file

    def load_words(self):
        #method to optionally load the pregenerated words from a file, not in use currently/not the way words are given
        generated_words = open('generated_adjs.txt', 'r')
        generated_words = generated_words.read()

        self.words_list = list([i for i in set(generated_words.split(" ")) if len(i) > 0])
        random.shuffle(self.words_list)

        self.definitions_dict = {}

    def set_word(self):
        self.prompt_word = self.generated_words[0]
        prompt_text = "What does \n {} \n mean?".format(self.prompt_word)
        self.root.get_screen('Define').ids.prompttext.text = prompt_text

    # convert to full dictionary entry
    # makes a fake phonetic version with direct substitution of letters
    def make_phonetic(self, word):
      letters_phon = "æɓçɖɘɸɡʜɪjkɭɰɲøpqʁstʊʋwχyʒ"
      letters_alph = "abcdefghijklmnopqrstuvwxyz"
      replaced = [letters_phon[letters_alph.index(i)] for i in word]
      return "/{}/".format("".join(replaced))

    # puts everything together and appends entry to text file
    # probably not needed and may cause issues if some formatted differently
    def make_entries(self):
        # adjust this to add to the definitions screen
        # create a label? if possible
        for key, value in self.definitions_dict.items():
            #just add some newlines in between and join together
            self.definitions_dict[key] = key + " \n " + "[adjective]" + "\n" + " \n ".join(value) + "\n\n"
        # need to add entries to definitions screen not just make for saving to file!
        #*can probably remove this function!**

    def update_definition_screen(self):
        text_to_display = ""
        for key, value in self.definitions_dict.items():
            text_to_display += key + " \n " + "[adjective]" + "\n" + " \n ".join(value[1:]) + "\n\n"
        self.root.get_screen('Definitions').ids.definitions_text.text =  text_to_display

    def submit(self, definition):
        # switch text to ask for example in a sentence, maybe have a different screen
        self.root.get_screen('Example').ids.exampleprompttext.text = 'Ok. And what is an example of {} in a sentence'.format(self.prompt_word)
        phonetic = self.make_phonetic(self.prompt_word)
        self.definitions_dict[self.prompt_word] = [phonetic]
        self.definitions_dict[self.prompt_word].append(definition)

        self.root.current = 'Example'

    def example_submit(self, example):
        # need to add to dict which will be class property
        self.definitions_dict[self.prompt_word].append(example)
        # actually could probably convert to phonetic first and then store the whole thing with newlines etc.?

        print(self.definitions_dict.get(self.prompt_word))
        # here need to add logic to go on to the next word - new word and back to the screen
        self.skip()
        self.root.current = 'Define'
        self.update_definition_screen()
        print('Submitted example of use')
        self.check_not_out_of_words()

    def skip(self):
        self.generated_words = self.generated_words[1:]
        self.check_not_out_of_words()
        if self.root.current !='Generating':
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
            # print("Generating... \n Epoch: " + str(epoch))

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

                self.generated_words = list(set([i for i in self.generated_words + generated.split(" ") if len(i) > 0]))
                random.shuffle(self.generated_words)

                if self.root.current == 'Generating':
                    self.generating_ani.join()
                    self.root.current = 'Define'
                    self.set_word()

                print(self.generated_words)

        # model.save('adj_generate_model.h5')
        # generated_words = open('generated_adjs.txt', 'r')
        # generated_words = generated_words.read()

        # words_list = list([i for i in set(generated_words.split(" ")) if len(i) > 0])

        # rewriting the file without repeated words
        # with open("generated_adjs.txt", "w") as txt:
        #   for i in words_list:
        #           txt.write(i + "\n")

    def sample(self, preds, temperature=1.0):
        preds = np.asarray(preds).astype("float64")
        preds = np.log(preds) / temperature
        exp_preds = np.exp(preds)
        preds = exp_preds / np.sum(exp_preds)
        probas = np.random.multinomial(1, preds, 1)
        return np.argmax(probas)

    def on_request_close(self, *args):
        print("closing")

    def animate_generating_txt(self):
        gen_label = self.root.get_screen('Generating').ids.generating_label

        anim = Animation(color=(0, 0, 0, 1), duration=.5) + Animation(color=(1, 1, 1, 1), duration=.5)
        anim.repeat = True

        anim.start(gen_label)

    def start_animation(self):
        self.generating_ani = threading.Thread(target=self.animate_generating_txt, daemon=True)
        self.generating_ani.start()

    def save_to_file(self, filename='definitions_test'):
        # give a lil dialog box to ask if they want to change the filename?
        # self.make_entries()
        with open(filename + '.txt', 'w', encoding="utf-8") as file:
            for key, value in self.definitions_dict.items():
                file.write(key + " \n " + "[adjective]" + "\n" + " \n ".join(value) + "\n\n")

    def check_not_out_of_words(self):
        if len(self.generated_words) == 0:
            # go to generate screen basically and think the existing logic might handle it from there?
            self.root.current = 'Generating'


# running the app
if __name__ == '__main__':
    neoDict().run()
