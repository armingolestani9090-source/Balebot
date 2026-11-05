import asyncio

from bale import BaleClient
from config import BALE_ACCESS_TOKEN


async def main():
    client = BaleClient(BALE_ACCESS_TOKEN)

    await client.connect()

    try:
        peer = await client.get_entity("@akhbartareek")

        print("TYPE:")
        print(type(peer))

        print("\nREPR:")
        print(repr(peer))

        print("\nATTRIBUTES:")

        for name in dir(peer):
            if not name.startswith("_"):
                try:
                    value = getattr(peer, name)

                    if not callable(value):
                        print(f"{name} = {value!r}")

                except Exception:
                    pass

    finally:
        await client.disconnect()


asyncio.run(main())