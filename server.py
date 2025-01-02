import asyncio
import pyautogui as py
import time
import random
import logging
from websockets import serve, ConnectionClosedOK

py.PAUSE = 0
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')  # Configure logging

keyboard_layout = {
    'q': (0, 0), 'w': (1, 0), 'e': (2, 0), 'r': (3, 0), 't': (4, 0), 'y': (5, 0), 'u': (6, 0), 'i': (7, 0), 'o': (8, 0), 'p': (9, 0),
    'a': (0.3, 1), 's': (1.3, 1), 'd': (2.3, 1), 'f': (3.3, 1), 'g': (4.3, 1), 'h': (5.3, 1), 'j': (6.3, 1), 'k': (7.3, 1), 'l': (8.3, 1), ';': (9.3, 1), "'": (10.3, 1),
    'z': (0.6, 2), 'x': (1.6, 2), 'c': (2.6, 2), 'v': (3.6, 2), 'b': (4.6, 2), 'n': (5.6, 2), 'm': (6.6, 2), ',': (7.6, 2), '.': (8.6, 2), '/': (9.6, 2),
    ' ': (2.3, 3)
}

# 5 = pinkie, 1 = thumb
finger_tracker = {
    'left_5': 'a', 'left_4': 's', 'left_3': 'd', 'left_2': 'f', 'left_1': ' ',
    'right_2': 'j', 'right_3': 'k', 'right_4': 'l', 'right_5': ';', 'right_1': 'n'
}

# Config
SERVER_PORT = 8001
BASE_DELAY = 60 / 150 / 5 / 3 # 60 / WPM / Avg. word length / Random factor
DEFAULT_DELAY = 0.08
DISTANCE_FACTOR = 0.01
DELAY_SAME_KEY_MIN = 0.016
DELAY_SAME_KEY_MAX = 0.030
DISTANCE_RAND_MUL_MIN = 0.7
DISTANCE_RAND_MUL_MAX = 1.2
BASE_FATIGUE = 1.0
MAX_FATIGUE = 1.5
FATIGUE_INCR = 0.001
FATIGUE_RAND_ADD_MIN = 0.0005
FATIGUE_RAND_ADD_MAX = 0.002
MISTAKE_CHANCE = 0.01  # 1% chance of making a mistake
HOLD_TIME_SPECIAL_MIN = 0.05
HOLD_TIME_SPECIAL_MAX = 0.07
HOLD_TIME_SPACE_MIN = 0.02
HOLD_TIME_SPACE_MAX = 0.05
HOLD_TIME_NORMAL_MIN = 0.02
HOLD_TIME_NORMAL_MAX = 0.04

class FatigueManager:
    def __init__(self):
        self.factor = BASE_FATIGUE
        self.increment = FATIGUE_INCR
        self.max_factor = MAX_FATIGUE

    def update_fatigue(self):
        self.factor += random.uniform(FATIGUE_RAND_ADD_MIN, FATIGUE_RAND_ADD_MAX)
        self.factor = min(self.factor, self.max_factor)

    def reset_fatigue(self):
        self.factor = BASE_FATIGUE

fatigue_manager = FatigueManager()

def calculate_delay(prev_char, current_char):
    """Calculate delay based on the position of the keys."""
    if prev_char not in keyboard_layout or current_char not in keyboard_layout:
        return DEFAULT_DELAY

    prev_pos = keyboard_layout[prev_char]

    if current_char == 'a' or current_char == 'q' or current_char == 'z':
        current_pos = keyboard_layout[finger_tracker['left_5']]
        finger_tracker['left_5'] = current_char
    elif current_char == 'w' or current_char == 's' or current_char == 'x':
        current_pos = keyboard_layout[finger_tracker['left_4']]
        finger_tracker['left_4'] = current_char
    elif current_char == 'e' or current_char == 'd' or current_char == 'c':
        current_pos = keyboard_layout[finger_tracker['left_3']]
        finger_tracker['left_3'] = current_char
    elif current_char == 'r' or current_char == 'f' or current_char == 'v' or current_char == 't' or current_char == 'g' or current_char == 'b':
        current_pos = keyboard_layout[finger_tracker['left_2']]
        finger_tracker['left_2'] = current_char
    elif current_char == 'y' or current_char == 'h' or current_char == 'n' or current_char == 'u' or current_char == 'j' or current_char == 'm':
        current_pos = keyboard_layout[finger_tracker['right_2']]
        finger_tracker['right_2'] = current_char
    elif current_char == 'i' or current_char == 'k' or current_char == ',':
        current_pos = keyboard_layout[finger_tracker['right_3']]
        finger_tracker['right_3'] = current_char
    elif current_char == 'o' or current_char == 'l' or current_char == '.':
        current_pos = keyboard_layout[finger_tracker['right_4']]
        finger_tracker['right_4'] = current_char
    elif current_char == 'p' or current_char == ';' or current_char == '/':
        current_pos = keyboard_layout[finger_tracker['right_5']]
        finger_tracker['right_5'] = current_char
    elif current_char == ' ':
        current_pos = keyboard_layout[finger_tracker['left_1']]
        finger_tracker['left_1'] = current_char
    else:
        current_pos = prev_pos

    distance = ((current_pos[0] - prev_pos[0]) ** 2 + (current_pos[1] - prev_pos[1]) ** 2) ** 0.5
    if distance == 0:
        delay = random.uniform(DELAY_SAME_KEY_MIN, DELAY_SAME_KEY_MAX)
    else:
        delay = random.uniform(DISTANCE_RAND_MUL_MIN, DISTANCE_RAND_MUL_MAX) * distance * DISTANCE_FACTOR

    delay = (BASE_DELAY + delay) * fatigue_manager.factor * random.uniform(0.8, 1)  # Adjust delay with fatigue

    return delay

def calculate_hold_time(char):
    if char in ['.', ',', ';', ':', '?', '!']:
        hold_time = random.uniform(HOLD_TIME_SPECIAL_MIN, HOLD_TIME_SPECIAL_MAX)  # Slightly longer for punctuation
    elif char == ' ':
        hold_time = random.uniform(HOLD_TIME_SPACE_MIN, HOLD_TIME_SPACE_MAX)  # Space bar is held slightly longer
    else:
        hold_time = random.uniform(HOLD_TIME_NORMAL_MIN, HOLD_TIME_NORMAL_MAX)  # Regular keys
    return hold_time

async def press_key_with_overlap(char, hold_time, fatigue_factor):
    """Simulate pressing a key with overlapping presses and fatigue."""
    py.keyDown(char)
    adjusted_hold_time = hold_time * fatigue_factor * random.uniform(1, 1.02) + random.uniform(-0.01, 0.02)
    await asyncio.sleep(adjusted_hold_time)  # Simulate hold time with fatigue
    py.keyUp(char)
    logging.info(f"Key '{char}' held for {adjusted_hold_time:.3f} seconds.")

async def simulate_mistake(current_char):
    if random.random() < MISTAKE_CHANCE and current_char != ' ':
        mistake_type = random.choice(["Skip", "Incorrect"])
        if mistake_type == "Skip":
            return None  # No key press
        elif mistake_type == "Incorrect":
            incorrect_char = random.choice(list(keyboard_layout.keys()))
            return incorrect_char  # Incorrect key
    return None  # No mistake

async def handler(websocket):
    global fatigue_manager
    prev_char = None
    last_key_time = time.time()  # Track the last key press time

    try:
        async for message in websocket:
            logging.info(f"Received message: {message}")
            if message.startswith("Word: "):
                word = message.split('Word: ')[1]
                word += ' '
                tasks = []  # Store tasks to manage overlapping key presses
                for char in word:
                    # Check if the time since the last key press is too long
                    current_time = time.time()
                    time_diff = current_time - last_key_time

                    if time_diff > 1:  # Reset fatigue if time since last key press > 1 second
                        logging.info("Time gap exceeded 1 second. Resetting fatigue.")
                        fatigue_manager.reset_fatigue()

                    # Check for a mistake
                    mistake = await simulate_mistake(char)
                    if mistake == "Skip":
                        continue
                    elif mistake != None:
                        char = mistaken_char

                    fatigue_manager.update_fatigue()
                    delay = calculate_delay(prev_char, char)
                    hold_time = calculate_hold_time(char)

                    # Schedule the key press as an asynchronous task
                    tasks.append(asyncio.create_task(press_key_with_overlap(char, hold_time, fatigue_manager.factor)))

                    # Wait for the delay before pressing the next key
                    await asyncio.sleep(delay)
                    prev_char = char
                    last_key_time = time.time()  # Update the last key press time

                # Wait for all key press tasks to complete
                await asyncio.gather(*tasks)
                logging.info(f"Typing completed for word: {word.strip()}. Fatigue factor: {fatigue_manager.factor}")
            elif message == "New Test":
                py.press("tab")
                await asyncio.sleep(2)
                py.press(" ")
    except ConnectionClosedOK:
        logging.info("Connection closed gracefully.")
    except ConnectionClosedError as e:
        logging.error(f"Connection closed unexpectedly with error: {e}")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")

async def main():
    logging.info("Starting server on port 8001")
    async with serve(handler, "", SERVER_PORT):
        await asyncio.get_running_loop().create_future()  # run forever

if __name__ == "__main__":
    asyncio.run(main())
