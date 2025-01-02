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

base_delay = 60 / 150 / 5 / 3

def calculate_delay(prev_char, current_char):
    """Calculate delay based on the position of the keys."""
    if prev_char not in keyboard_layout or current_char not in keyboard_layout:
        return 0.08

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
        delay = random.uniform(0.016, 0.030)
    else:
        delay = random.uniform(0.7, 1.2) * (distance * 0.01)

    return base_delay + delay

async def press_key_with_overlap(char, hold_time, fatigue_factor):
    """Simulate pressing a key with overlapping presses and fatigue."""
    py.keyDown(char)
    adjusted_hold_time = hold_time * fatigue_factor * random.uniform(1, 1.02) + random.uniform(-0.01, 0.02)
    await asyncio.sleep(adjusted_hold_time)  # Simulate hold time with fatigue
    py.keyUp(char)
    logging.info(f"Key '{char}' held for {adjusted_hold_time:.3f} seconds.")

async def make_mistake(current_char):
    """Simulate a mistake by pressing an incorrect key."""
    mistake_type = random.choice(['skip', 'incorrect'])

    if mistake_type == 'skip':
        logging.info("Mistake: Skipping key press.")
        return None  # Skip the key press
    else:
        # Simulate incorrect key press
        incorrect_char = random.choice(list(keyboard_layout.keys()))
        logging.info(f"Mistake: Pressing incorrect key '{incorrect_char}' instead of '{current_char}'.")
        return incorrect_char  # Return the incorrect character to press

async def handler(websocket):
    prev_char = None
    fatigue_factor = 1.000  # Start with no fatigue
    total_chars_typed = 0  # Keep track of the total characters typed
    fatigue_increment = 0.001  # Amount by which fatigue increases per character
    mistake_chance = 0.01  # 2% chance of making a mistake
    last_key_time = time.time()  # Track the last key press time

    try:
        async for message in websocket:
            logging.info(f"Received message: {message}")
            if message.startswith("Word: "):
                word = message.split('Word: ')[1]
                word += ' '
                tasks = []  # Store tasks to manage overlapping key presses
                for char in word:
                    total_chars_typed += 1

                    # Check if the time since the last key press is too long
                    current_time = time.time()
                    time_diff = current_time - last_key_time

                    if time_diff > 1:  # Reset fatigue if time since last key press > 1 second
                        logging.info("Time gap exceeded 1 second. Resetting fatigue.")
                        fatigue_factor = 1  # Reset fatigue

                    # Check for a mistake
                    if random.random() < mistake_chance and char != ' ':
                        mistaken_char = await make_mistake(char)
                        if mistaken_char is None:
                            continue  # Skip this character if it's a skipped mistake
                        else:
                            char = mistaken_char  # Replace with the incorrect key

                    # Increment fatigue factor gradually
                    fatigue_factor += random.uniform(0.0005, 0.002)  # Random increment
                    fatigue_factor = min(fatigue_factor, 1.5)  # Cap fatigue to prevent extreme slowness

                    delay = calculate_delay(prev_char, char) * fatigue_factor * random.uniform(0.8, 1)  # Adjust delay with fatigue
                    logging.info(f"Delay: {delay}")
                    # Determine the hold time for the current character
                    if char in ['.', ',', ';', ':', '?', '!']:
                        hold_time = random.uniform(0.05, 0.07)  # Slightly longer for punctuation
                    elif char == ' ':
                        hold_time = random.uniform(0.02, 0.05)  # Space bar is held slightly longer
                    else:
                        hold_time = random.uniform(0.02, 0.04)  # Regular keys

                    # Schedule the key press as an asynchronous task
                    tasks.append(asyncio.create_task(press_key_with_overlap(char, hold_time, fatigue_factor)))

                    # Wait for the delay before pressing the next key
                    await asyncio.sleep(delay)
                    prev_char = char
                    last_key_time = time.time()  # Update the last key press time

                # Wait for all key press tasks to complete
                await asyncio.gather(*tasks)
                logging.info(f"Typing completed for word: {word.strip()}. Total characters typed: {total_chars_typed}, Fatigue factor: {fatigue_factor}")
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
    async with serve(handler, "", 8001):
        await asyncio.get_running_loop().create_future()  # run forever

if __name__ == "__main__":
    asyncio.run(main())
