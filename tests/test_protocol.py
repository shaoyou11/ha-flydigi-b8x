import asyncio
import importlib
import sys
import types
import unittest
from pathlib import Path

ROOT = Path(__file__).parent
if ROOT.name == 'tests':
    ROOT = ROOT.parent
package = types.ModuleType('b8x_test')
package.__path__ = [str(ROOT / 'custom_components/flydigi_b8x')]
sys.modules['b8x_test'] = package
p = importlib.import_module('b8x_test.protocol')
session = importlib.import_module('b8x_test.session')
FRAME = bytes.fromhex('13000291280006050922378a2300ff0c030f006f')


class CodecTests(unittest.TestCase):
    def test_capture(self):
        status = p.parse_status(FRAME)
        self.assertEqual((status.cold_temperature, status.hot_temperature, status.rpm), (5.9, 34, 3500))
        self.assertEqual((status.wind_level, status.cold_level, status.light), (4000, 145, True))

    def test_truncated_or_wrong_frame(self):
        for frame in (FRAME[:-1], b'\x51' + FRAME[1:], FRAME + b'\x00'):
            with self.assertRaises(ValueError):
                p.parse_status(frame)

    def test_invalid_decimal(self):
        frame = bytearray(FRAME)
        frame[8] = 10
        with self.assertRaises(ValueError):
            p.parse_status(frame)

    def test_light_frames(self):
        self.assertEqual(p.light_command(False), b'\x10\x00')
        self.assertEqual(p.light_command(True), b'\x10\xff')
        with self.assertRaises(ValueError):
            p.light_command(1)

    def test_preserve_group(self):
        status = p.parse_status(FRAME)
        self.assertEqual(p.level_command(status, 'wind', 4100).hex(), '2000912900065c2800')
        self.assertEqual(p.level_command(status, 'cold', 144).hex(), '2000902800065c2800')

    def test_block_overclock_and_invalid_levels(self):
        for kind, value in [('wind', 5700), ('wind', 3900), ('wind', 4050),
                            ('cold', 230), ('cold', 0), ('cold', 144.5), ('other', 1)]:
            with self.assertRaises(ValueError):
                p.level_command(p.parse_status(FRAME), kind, value)

    def test_block_unverified_mode(self):
        frame = bytearray(FRAME)
        frame[2] = 0x42
        with self.assertRaises(ValueError):
            p.level_command(p.parse_status(frame), 'cold', 144)

    def test_mode_command_preserves_settings(self):
        self.assertEqual(p.level_command(p.parse_status(FRAME), 'mode', 1).hex(), '2001912800065c2800')
        with self.assertRaises(ValueError):
            p.level_command(p.parse_status(FRAME), 'mode', 2)

    def test_manual_level_keeps_mode(self):
        frame = bytearray(FRAME)
        frame[2] = 0x12
        self.assertEqual(p.level_command(p.parse_status(frame), 'cold', 144).hex(), '2001902800065c2800')


class FakeClient:
    def __init__(self, acknowledge=True):
        self.frame = bytearray(FRAME)
        self.callback = None
        self.writes = []
        self.stopped = False
        self.acknowledge = acknowledge

    async def start_notify(self, uuid, callback):
        self.callback = callback

    async def stop_notify(self, uuid):
        self.stopped = True

    async def write_gatt_char(self, uuid, data, response):
        self.writes.append(bytes(data))
        if data == b'\x13':
            self.callback(None, self.frame)
        elif self.acknowledge:
            if data[0] == 0x10:
                self.frame[14] = data[1]
            else:
                self.frame[2] = (data[1] << 4) | (self.frame[2] & 15)
                self.frame[3] = data[2]
                self.frame[4:6] = data[3:5]
            self.callback(None, self.frame)


class SessionTests(unittest.IsolatedAsyncioTestCase):
    async def test_read(self):
        client = FakeClient()
        status = await session.exchange(client)
        self.assertEqual(status.rpm, 3500)
        self.assertEqual(client.writes, [b'\x13'])
        self.assertTrue(client.stopped)

    async def test_light_confirmed(self):
        client = FakeClient()
        status = await session.exchange(client, ('light', False))
        self.assertFalse(status.light)
        self.assertTrue(client.stopped)

    async def test_group_confirmed_from_fresh_snapshot(self):
        client = FakeClient()
        client.frame[6] = 12
        status = await session.exchange(client, ('wind', 4100))
        self.assertEqual(status.wind_level, 4100)
        self.assertEqual(client.writes[-1].hex(), '20009129000c5c2800')
        self.assertTrue(client.stopped)

    async def test_cold(self):
        status = await session.exchange(FakeClient(), ('cold', 144))
        self.assertEqual(status.cold_level, 144)

    async def test_mode(self):
        status = await session.exchange(FakeClient(), ('mode', 1))
        self.assertEqual(status.mode_raw, 1)
        self.assertEqual(status.cold_level, 145)
        self.assertEqual(status.wind_level, 4000)

    async def test_unconfirmed_not_optimistic(self):
        client = FakeClient(acknowledge=False)
        task = asyncio.create_task(session.exchange(client, ('cold', 144)))
        await asyncio.sleep(0.01)
        self.assertFalse(task.done())
        task.cancel()
        with self.assertRaises(asyncio.CancelledError):
            await task
        self.assertTrue(client.stopped)

    async def test_rejected_command_still_releases_notify(self):
        client = FakeClient()
        with self.assertRaises(ValueError):
            await session.exchange(client, ('cold', 230))
        self.assertTrue(client.stopped)


if __name__ == '__main__':
    unittest.main()
