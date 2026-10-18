"""Short-lived BLE transactions, with physical status confirmation."""
import asyncio
import contextlib

from .protocol import NOTIFY, WRITE, STATUS_QUERY, parse_status, light_command, level_command


async def exchange(client, command=None):
    queue = asyncio.Queue(maxsize=8)

    def notified(sender, data):
        try:
            status = parse_status(data)
        except ValueError:
            return
        if queue.full():
            queue.get_nowait()
        queue.put_nowait(status)

    subscribed = False
    try:
        await client.start_notify(NOTIFY, notified)
        subscribed = True
        await client.write_gatt_char(WRITE, STATUS_QUERY, response=True)
        status = await asyncio.wait_for(queue.get(), 8)
        if command is None:
            return status
        kind, expected = command
        packet = light_command(expected) if kind == 'light' else level_command(status, kind, expected)
        before = status
        # Discard packets queued before the write, never confirm from cached state.
        while not queue.empty():
            queue.get_nowait()
        await client.write_gatt_char(WRITE, packet, response=True)
        async with asyncio.timeout(8):
            while True:
                status = await queue.get()
                actual = status.light if kind == 'light' else (
                    status.mode_raw if kind == 'mode' else
                    status.wind_level if kind == 'wind' else status.cold_level)
                preserved = kind == 'light' or ((kind == 'mode' or status.mode_raw == before.mode_raw)
                    and bytes.fromhex(status.raw)[6] == bytes.fromhex(before.raw)[6]
                    and (status.cold_level == before.cold_level and status.wind_level == before.wind_level
                         if kind == 'mode' else status.cold_level == before.cold_level if kind == 'wind'
                         else status.wind_level == before.wind_level))
                if actual == expected and preserved:
                    return status
    finally:
        if subscribed:
            with contextlib.suppress(Exception):
                await asyncio.wait_for(client.stop_notify(NOTIFY), 3)
