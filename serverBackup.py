import asyncio
import pyautogui as py
import time
import random
import logging
from websockets import serve, ConnectionClosedOK

py.PAUSE = 0

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

target_wpm = 150

async def handler(websocket):
    prev_char = None
    async for message in websocket:
        logging.info(f"Received message: {message}")
        if message.startswith("Word: "):
            word = message.split('Word: ')[1]
            word += ' '
            for char in word:
                delay = 0.08
                logging.info(f"Typing character: '{char}' with delay: {delay:.3f}s")
                py.press(char)
                time.sleep(delay)
                #await asyncio.sleep(delay)
            #py.write(word)

async def main():
    logging.info("Starting server on port 8001")
    async with serve(handler, "", 8001):
        await asyncio.get_running_loop().create_future()  # run forever

if __name__ == "__main__":
    asyncio.run(main())
