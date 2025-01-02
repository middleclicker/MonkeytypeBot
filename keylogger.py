from pynput import keyboard
import time

class EscapeException(Exception): pass

lastTime = time.time()

def on_press(key):
    global lastTime

    text = ""
    if key == keyboard.Key.enter:
        text += "\n"
    elif key == keyboard.Key.tab:
        text += "\t"
    elif key == keyboard.Key.space:
        text += " "
    elif key == keyboard.Key.shift:
        pass
    elif key == keyboard.Key.backspace and len(text) == 0:
        pass
    elif key == keyboard.Key.backspace and len(text) > 0:
        text = text[:-1]
    elif key == keyboard.Key.ctrl_l or key == keyboard.Key.ctrl_r:
        pass
    elif key == keyboard.Key.esc:
        raise EscapeException(key)
    else:
        # We do an explicit conversion from the key object to a string and then append that to the string held in memory.
        text += str(key).strip("'")

    print(f"{text}: {time.time() - lastTime}")
    lastTime = time.time()

with keyboard.Listener(on_press=on_press) as listener:
    # We start of by sending the post request to our server.
    try:
        listener.join()
    except EscapeException as e:
        print(f"{e.args[0]} was pressed")
