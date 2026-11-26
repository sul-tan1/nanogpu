# SPDX-License-Identifier: Apache-2.0
"""Exercise the complete Tiny Tapeout pin interface in RTL and gate simulation."""

import json
from pathlib import Path
import random
import struct
import zlib

import cocotb
from cocotb.triggers import Timer


NOP, ADD, SUB, XOR, MAX, SHR1, MUL_SHIFT4, MAC = range(8)
OK, BAD_COMMAND, BAD_PROGRAM, BAD_RECTANGLE, BAD_COUNT, BAD_MODE = range(6)
COMPUTE, CLEAR_ACC, READ_ACC, MAC_BURST, DRAW = 0x20, 0x21, 0x22, 0x23, 0x30
OUTPUT = Path(__file__).resolve().parent / "output"


def signed_byte(value):
    return value if value < 128 else value - 256


def reference(program, a, b):
    for opcode in program:
        if opcode == ADD:
            a += b
        elif opcode == SUB:
            a -= b
        elif opcode == XOR:
            a ^= b
        elif opcode == MAX:
            a = max(a, b)
        elif opcode == SHR1:
            a //= 2
        elif opcode == MUL_SHIFT4:
            a = signed_byte(a) * signed_byte(b) // 16
        a %= 256
    return a


class Host:
    def __init__(self, dut):
        self.dut = dut
        self.enabled = True
        self.cycles = 0

    async def cycle(self, tx=None, rx=False):
        dut = self.dut
        dut.clk.value = 0
        dut.ena.value = self.enabled
        dut.ui_in.value = 0 if tx is None else tx
        dut.uio_in.value = int(tx is not None) | (int(rx) << 1)
        # Test at 10 MHz and sample after the gate-level combinational settle.
        await Timer(50, unit="ns")
        assert int(dut.uio_oe.value) == 0x0C
        flags = int(dut.uio_out.value)
        assert flags & 0xF3 == 0
        in_ready = bool(flags & 4)
        out_valid = bool(flags & 8)
        out_data = int(dut.uo_out.value) if out_valid else None
        dut.clk.value = 1
        await Timer(50, unit="ns")
        self.cycles += 1
        return in_ready, out_data

    async def reset(self):
        self.dut.rst_n.value = 0
        assert await self.cycle() == (False, None)
        self.dut.rst_n.value = 1
        await self.expect_idle()

    async def expect_idle(self):
        assert await self.cycle() == (True, None)

    async def write(self, *payload):
        for byte in payload:
            for _ in range(32):
                ready, _ = await self.cycle(tx=byte)
                if ready:
                    break
            else:
                raise AssertionError(f"Timed out sending {byte:#04x}")

    async def read(self, count):
        output = []
        for _ in range(count):
            for _ in range(32):
                _, byte = await self.cycle(rx=True)
                if byte is not None:
                    output.append(byte)
                    break
            else:
                raise AssertionError(f"Timed out after {len(output)} response bytes")
        return output

    async def load(self, program):
        await self.write(0x10 + len(program) - 1, *program)
        assert await self.read(1) == [OK]

    async def compute(self, a0, b0, a1, b1):
        await self.write(COMPUTE, a0 & 255, b0 & 255, a1 & 255, b1 & 255)
        status, *results = await self.read(3)
        assert status == OK
        return results

    async def clear_acc(self):
        await self.write(CLEAR_ACC)
        assert await self.read(1) == [OK]

    async def _read_sums(self):
        status, *payload = await self.read(9)
        assert status == OK
        return [int.from_bytes(bytes(payload[i:i + 4]), "little", signed=True)
                for i in (0, 4)]

    async def read_acc(self):
        await self.write(READ_ACC)
        return await self._read_sums()

    async def mac_burst(self, pairs):
        await self.write(MAC_BURST, len(pairs))
        for pair in pairs:
            await self.write(*(value & 255 for value in pair))
        return await self._read_sums()

    async def draw(self, x, y, width, height):
        await self.write(DRAW, x, y, width, height)
        assert await self.read(1) == [OK]
        return await self.read(width * height)


def pixels_for(program, x, y, width, height):
    return [reference(program, px, py)
            for py in range(y, y + height) for px in range(x, x + width)]


def save_demo(pixels, width, height, name="nanogpu.png"):
    def chunk(name, data):
        return (struct.pack(">I", len(data)) + name + data
                + struct.pack(">I", zlib.crc32(name + data)))

    # PNG stores one filter byte before each grayscale scanline.
    scanlines = b"".join(b"\0" + bytes(pixels[y:y + width])
                         for y in range(0, len(pixels), width))
    OUTPUT.mkdir(exist_ok=True)
    (OUTPUT / name).write_bytes(
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 0, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(scanlines)) + chunk(b"IEND", b""))


def save_report(name, data):
    OUTPUT.mkdir(exist_ok=True)
    (OUTPUT / name).write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


@cocotb.test()
async def shared_program_demo(dut):
    host = Host(dut)
    await host.reset()
    gradient = [ADD, SHR1]
    await host.load(gradient)
    start = host.cycles
    pixels = await host.draw(0, 0, 64, 64)
    assert pixels == pixels_for(gradient, 0, 0, 64, 64)
    elapsed = host.cycles - start
    assert elapsed == 10_246
    dut._log.info("64x64 gradient: %d cycles including command and readback", elapsed)
    assert await host.compute(10, 4, 20, 8) == [7, 14]

    # A different program shades a smaller rectangle onto the host framebuffer.
    pattern = [XOR, ADD, ADD, ADD]
    await host.load(pattern)
    x, y, width, height = 9, 7, 45, 49
    inset = await host.draw(x, y, width, height)
    assert inset == pixels_for(pattern, x, y, width, height)
    for row in range(height):
        start = (y + row) * 64 + x
        pixels[start:start + width] = inset[row * width:(row + 1) * width]
    await host.expect_idle()
    save_demo(pixels, 64, 64)


@cocotb.test()
async def compute_reference_and_wrapping(dut):
    host = Host(dut)
    await host.reset()
    assert await host.compute(0xA5, 19, 0x5A, 20) == [0xA5, 0x5A]
    rng = random.Random(20261120)
    programs = [[op] for op in range(6)]
    programs += [[rng.randrange(6) for _ in range(length)]
                 for length in range(1, 5) for _ in range(8)]
    for program in programs:
        await host.load(program)
        for a0, b0, a1, b1 in [(255, 1, 0, 255), (0, 1, 128, 127)] + [
            tuple(rng.randrange(256) for _ in range(4)) for _ in range(3)
        ]:
            actual = await host.compute(a0, b0, a1, b1)
            assert actual == [reference(program, a0, b0), reference(program, a1, b1)]
    await host.expect_idle()


@cocotb.test()
async def rectangle_boundaries_and_error_responses(dut):
    host = Host(dut)
    await host.reset()
    program = [ADD, XOR]
    await host.load(program)
    for x, y, width, height in [(63, 63, 1, 1), (62, 62, 2, 2), (61, 61, 3, 3),
                                (0, 63, 64, 1), (63, 0, 1, 64), (15, 7, 6, 5)]:
        assert await host.draw(x, y, width, height) == pixels_for(program, x, y, width, height)
        await host.expect_idle()
    for payload in [(64, 0, 1, 1), (0, 255, 1, 1), (1, 1, 0, 1), (1, 1, 1, 0),
                    (63, 63, 2, 1), (63, 63, 1, 2), (0, 0, 65, 1), (0, 0, 1, 128)]:
        await host.write(DRAW, *payload)
        assert await host.read(1) == [BAD_RECTANGLE]
        await host.expect_idle()
    for command in (0, 0x14, 0x24, 0x31, 0xFF):
        await host.write(command)
        assert await host.read(1) == [BAD_COMMAND]
    assert await host.compute(5, 3, 22, 9) == [reference(program, 5, 3), reference(program, 22, 9)]
    for malformed in ([0xFF, NOP], [NOP, 0x82]):
        await host.write(0x11, *malformed)
        assert await host.read(1) == [BAD_PROGRAM]
        assert await host.compute(1, 9, 2, 8) == [1, 2]


@cocotb.test()
async def stalls_enable_and_reset(dut):
    host = Host(dut)
    await host.reset()
    await host.load([ADD])
    await host.write(DRAW, 61, 62, 3)
    for _ in range(3):
        assert await host.cycle() == (True, None)
    await host.write(2)
    for _ in range(3):
        assert await host.cycle(tx=0xFF) == (False, OK)
    assert await host.read(1) == [OK]
    for _ in range(16):
        if (await host.cycle())[1] is not None:
            break
    else:
        raise AssertionError("No pixel after status")
    for _ in range(3):
        assert await host.cycle() == (False, 123)
    host.enabled = False
    assert await host.cycle(tx=0xFF, rx=True) == (False, None)
    host.enabled = True
    assert await host.read(6) == pixels_for([ADD], 61, 62, 3, 2)
    await host.expect_idle()

    await host.write(DRAW, 0, 0, 64, 64)
    assert await host.read(2) == [OK, 0]
    await host.reset()
    assert await host.compute(0xFF, 1, 0, 1) == [0xFF, 0]


@cocotb.test()
async def signed_dot_products_and_accumulators(dut):
    host = Host(dut)
    await host.reset()
    assert await host.read_acc() == [0, 0]
    await host.load([MAC])
    inputs = [3, 2, 4]
    weights0 = [5, 7, 2]
    weights1 = [-5, 7, -2]
    for value, w0, w1 in zip(inputs, weights0, weights1):
        assert await host.compute(value, w0, value, w1) == [value, value]
    dot_products = await host.read_acc()
    assert dot_products == [37, -9]
    dut._log.info("Two dense-layer outputs: %s", dot_products)
    save_report("dense-layer.json", dict(inputs=inputs, weights=[weights0, weights1],
                                         outputs=dot_products))

    await host.write(DRAW, 0, 0, 2, 2)
    assert await host.read(1) == [BAD_MODE]
    await host.expect_idle()
    assert await host.read_acc() == dot_products

    await host.clear_acc()
    await host.load([ADD, MAC, SHR1, MAC])
    assert await host.compute(3, 5, 0, -3) == [4, 126]
    assert await host.read_acc() == [60, -369]

    await host.load([MAC])
    for _ in range(5):
        await host.compute(-128, -128, -128, 127)
    assert await host.read_acc() == [60 + 5 * 16384, -369 - 5 * 16256]
    await host.reset()
    assert await host.read_acc() == [0, 0]


@cocotb.test()
async def burst_protocol_and_throughput(dut):
    host = Host(dut)
    await host.reset()
    rng = random.Random(0x26D)
    pairs = [tuple(rng.randrange(-128, 128) for _ in range(4)) for _ in range(32)]
    expected = [sum(a * b for a, b, _, _ in pairs), sum(c * d for _, _, c, d in pairs)]
    await host.load([MAC])
    start = host.cycles
    for pair in pairs:
        await host.compute(*pair)
    assert await host.read_acc() == expected
    regular_cycles = host.cycles - start

    await host.clear_acc()
    start = host.cycles
    assert await host.mac_burst(pairs) == expected
    burst_cycles = host.cycles - start
    assert (regular_cycles, burst_cycles) == (330, 203)
    dut._log.info("32 MAC steps plus readback: %d cycles individually, %d in burst",
                  regular_cycles, burst_cycles)
    save_report("mac-benchmark.json", dict(steps=len(pairs), products=2 * len(pairs),
                                           individual_cycles=regular_cycles, burst_cycles=burst_cycles,
                                           outputs=expected))

    # A zero count reports a single error byte and preserves the sums.
    await host.write(MAC_BURST, 0)
    assert await host.read(1) == [BAD_COUNT]
    await host.expect_idle()
    assert await host.read_acc() == expected

    # A burst ignores the loaded program, preserves it, and adds to existing sums.
    await host.load([SHR1])
    extreme = [(-128, -128, -128, 127)] * 255
    for batch in range(1, 4):
        assert await host.mac_burst(extreme) == [expected[0] + batch * 255 * 16384,
                                                expected[1] - batch * 255 * 16256]
    assert await host.compute(128, 0, 255, 0) == [64, 127]

    await host.clear_acc()
    await host.write(MAC_BURST, 1, 2, 3)
    assert await host.cycle() == (True, None)
    host.enabled = False
    assert await host.cycle(tx=0xFF) == (False, None)
    host.enabled = True
    await host.write(4, 5)
    assert await host.read(1) == [OK]
    for _ in range(3):
        assert await host.cycle() == (False, 6)
    assert await host.read(8) == [6, 0, 0, 0, 20, 0, 0, 0]
    await host.expect_idle()

    await host.write(MAC_BURST, 2, 1, 2, 3, 4, 5)
    await host.reset()
    assert await host.read_acc() == [0, 0]


@cocotb.test()
async def multiply_shader_and_sobel_demo(dut):
    host = Host(dut)
    await host.reset()
    await host.load([MUL_SHIFT4])
    start = host.cycles
    gradient = await host.draw(0, 0, 64, 64)
    assert host.cycles - start == 10_246
    assert gradient == [x * y // 16 for y in range(64) for x in range(64)]
    assert await host.compute(-128, 127, 127, 127) == [8, 240]
    assert await host.compute(-1, 1, -128, -128) == [255, 0]
    save_demo(gradient, 64, 64, "multiply-gradient.png")

    # Build an input image from two hardware renders, then downsample on the host.
    await host.load([XOR, ADD, ADD, ADD])
    width, height, x0, y0 = 43, 45, 9, 7
    inset = await host.draw(x0, y0, width, height)
    for y in range(height):
        row = (y + y0) * 64 + x0
        gradient[row:row + width] = inset[y * width:(y + 1) * width]
    size = 32
    image = [gradient[y * 128 + x * 2] for y in range(size) for x in range(size)]
    save_demo(image, size, size, "sobel-input.png")

    # One lane computes the horizontal Sobel kernel and the other the vertical.
    kernel_x = (-1, 0, 1, -2, 0, 2, -1, 0, 1)
    kernel_y = (-1, -2, -1, 0, 0, 0, 1, 2, 1)
    edges = [0] * (size * size)
    for y in range(1, size - 1):
        for x in range(1, size - 1):
            window = [image[(y + dy) * size + x + dx] - 128
                      for dy in (-1, 0, 1) for dx in (-1, 0, 1)]
            await host.clear_acc()
            gx, gy = await host.mac_burst([(p, wx, p, wy)
                                           for p, wx, wy in zip(window, kernel_x, kernel_y)])
            assert gx == sum(p * weight for p, weight in zip(window, kernel_x))
            assert gy == sum(p * weight for p, weight in zip(window, kernel_y))
            edges[y * size + x] = min(255, (abs(gx) + abs(gy)) // 4)
    assert max(edges) > 100
    save_demo(edges, size, size, "sobel-edges.png")
