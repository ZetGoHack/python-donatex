import asyncio

from donatex import Client

async def main():
    client = Client(api_token="TEST", token_scopes={"donations.read", "z"})
    async with client as _:
        pass

    await client.start()
    await client.stop()

    print("[✅] aenter, manual start & stop [External token]")

asyncio.run(main())