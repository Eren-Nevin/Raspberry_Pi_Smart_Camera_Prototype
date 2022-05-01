from gtts import gTTS
import os

def say(text):
    my_speech = gTTS(text=text, lang='en', slow=False)
    my_speech.save("Welcome.mp3")
    os.system("cvlc Welcome.mp3")
