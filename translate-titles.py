import os
import asyncio
from googletrans import Translator

async def main():
    folder = os.path.dirname(os.path.abspath(__file__))
    async with Translator() as translator:
        for filename in os.listdir(folder):
            if filename.endswith(".txt"):
                name = os.path.splitext(filename)[0]
                try:
                    result = await translator.translate(name, src='en', dest='ru')
                    new_name = result.text + ".txt"
                    os.rename(os.path.join(folder, filename), os.path.join(folder, new_name))
                except:
                    pass

asyncio.run(main())
