"""B8X codec derived from the official Android SDK and verified captures."""
from dataclasses import dataclass

SERVICE = '0000ffe0-0000-1000-8000-00805f9b34fb'
WRITE = '0000ffe1-0000-1000-8000-00805f9b34fb'
NOTIFY = '0000ffe4-0000-1000-8000-00805f9b34fb'
STATUS_QUERY = b'\x13'


@dataclass(frozen=True)
class Status:
    cold_temperature: float
    hot_temperature: int
    rpm: int
    light: bool
    wind_level: int
    cold_level: int
    mode_raw: int
    raw: str


def parse_status(data):
    frame = bytes(data)
    if len(frame) != 20 or frame[0] != 0x13:
        raise ValueError('Not a complete B8X status frame')
    if frame[8] > 9 or frame[14] not in (0, 255):
        raise ValueError('Invalid B8X status fields')
    signed = lambda b: b if b < 128 else b - 256
    return Status(round(signed(frame[7]) + frame[8] / 10, 1), signed(frame[9]),
                  frame[12] * 100 + frame[13], frame[14] == 255,
                  frame[4] * 100 + frame[5], frame[3], frame[2] >> 4, frame.hex())


def light_command(enabled):
    if type(enabled) is not bool:
        raise ValueError('Light state must be boolean')
    return bytes((0x10, 255 if enabled else 0))


def level_command(status, kind, value):
    if type(value) is not int:
        raise ValueError('Level must be an integer')
    if status.mode_raw not in (0, 1):
        raise ValueError('Only automatic and manual modes are supported')
    wind, cold = status.wind_level, status.cold_level
    mode = status.mode_raw
    if kind == 'wind' and 4000 <= value <= 4500 and value % 100 == 0:
        wind = value
    elif kind == 'cold' and 92 <= value <= 175:
        cold = value
    elif kind == 'mode' and value in (0, 1):
        mode = value
    else:
        raise ValueError('Outside B8X normal, non-overclock range')
    frame = bytes.fromhex(status.raw)
    # Official B8X normal-mode UI uses fixed base values 92 / 4000.
    return bytes((0x20, mode, cold, *divmod(wind, 100), frame[6], 92, 40, 0))
