# Definer App

App wrapped version of a previous project which can be found [here](https://github.com/CZboop/Vorpal-Dictionary) where a neural network generates realistic nonsense words that the user can then define into a 'dictionary' entry.
Uses multithreading to enable the neural network to continue generating words in the background, while the user interacts with the app on a different thread. The app will show the user words that have been generated live just in the time since the app was launched, which means there is a slight initial delay and potential for further small delays depending on the speed at which the user uses the app or how quickly they skip. However, the app will automatically redirect the user to the main functionality once new words have been generated.

Made using Kivy/KivyMD, Python and Keras/Tensorflow
