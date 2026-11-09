"""Byte-counting TCP relay in front of local Postgres.

Listens on 127.0.0.1:5433, forwards to 127.0.0.1:5432, and counts bytes in each
direction. "down" = server -> client (what Neon bills as network transfer).
A control port (5434) answers each connection with "down up connections\n".
"""

import asyncio
import contextlib
import sys

LISTEN, TARGET, CONTROL = 5433, 5432, 5434
totals = {"down": 0, "up": 0, "conns": 0}


async def pipe(reader, writer, key):
    try:
        while data := await reader.read(65536):
            totals[key] += len(data)
            writer.write(data)
            await writer.drain()
    except (ConnectionError, asyncio.IncompleteReadError):
        pass
    finally:
        with contextlib.suppress(Exception):
            writer.close()


async def handle(client_r, client_w):
    totals["conns"] += 1
    server_r, server_w = await asyncio.open_connection("127.0.0.1", TARGET)
    await asyncio.gather(pipe(client_r, server_w, "up"), pipe(server_r, client_w, "down"))


async def control(_r, w):
    w.write(f"{totals['down']} {totals['up']} {totals['conns']}\n".encode())
    await w.drain()
    w.close()


async def main():
    a = await asyncio.start_server(handle, "127.0.0.1", LISTEN)
    b = await asyncio.start_server(control, "127.0.0.1", CONTROL)
    print("relay up", flush=True)
    async with a, b:
        await asyncio.gather(a.serve_forever(), b.serve_forever())


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
