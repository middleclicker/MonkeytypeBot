import random
target_wpm = 150 # Target words per minute (WPM)
average_word_length = 5 # Average word length in characters (including spaces)

base_delay = 60 / (target_wpm * average_word_length) # Calculate base delay between characters to match target WPM
burst_delay = 60 / ((target_wpm+30) * average_word_length)

keyboard_layout = {
    'q': (0, 0), 'w': (1, 0), 'e': (2, 0), 'r': (3, 0), 't': (4, 0), 'y': (5, 0), 'u': (6, 0), 'i': (7, 0), 'o': (8, 0), 'p': (9, 0),
    'a': (0.3, 1), 's': (1.3, 1), 'd': (2.3, 1), 'f': (3.3, 1), 'g': (4.3, 1), 'h': (5.3, 1), 'j': (6.3, 1), 'k': (7.3, 1), 'l': (8.3, 1),
    'z': (0.6, 2), 'x': (1.6, 2), 'c': (2.6, 2), 'v': (3.6, 2), 'b': (4.6, 2), 'n': (5.6, 2), 'm': (6.6, 2),
    ' ': (2.3, 3)
}

def calculate_delay(prev_char, current_char):
    """Calculate delay based on the position of the keys."""
    if prev_char not in keyboard_layout or current_char not in keyboard_layout:
        return base_delay

    prev_pos = keyboard_layout[prev_char]
    current_pos = keyboard_layout[current_char]
    distance = ((current_pos[0] - prev_pos[0]) ** 2 + (current_pos[1] - prev_pos[1]) ** 2) ** 0.5
    #print(distance)
    distanceEdit = random.uniform(1, 1.3) * (distance * 0.01)
    # print(distanceEdit)
    #print(burst_delay)
    delay = distanceEdit
    return delay


print(calculate_delay('w', 's'))
