# Copyright (c) 2026 Emron Arsala
# SPDX-License-Identifier: Apache-2.0
"""Starter interface tests, shared by RTL and the GitHub gate-level job.

Replace/extend these when the final project's behavior is specified.
"""
import cocotb
from cocotb.triggers import Timer


async def cycle(dut):
    # 10 MHz, with enough settling time for the gate-level UNIT_DELAY model.
    dut.clk.value = 0
    await Timer(50, unit="ns")
    dut.clk.value = 1
    await Timer(50, unit="ns")


async def reset(dut):
    dut.clk.value = 0
    dut.ena.value = 1
    dut.ui_in.value = 0
    dut.uio_in.value = 0
    dut.rst_n.value = 1
    await Timer(50, unit="ns")
    dut.rst_n.value = 0
    await cycle(dut)
    assert int(dut.uo_out.value) == 0
    dut.rst_n.value = 1
    await cycle(dut)


@cocotb.test()
async def test_registered_data(dut):
    """All data values cross the wrapper and update only on a rising edge."""
    await reset(dut)
    previous = 0
    for value in range(256):
        dut.clk.value = 0
        dut.ui_in.value = value
        await Timer(50, unit="ns")
        assert int(dut.uo_out.value) == previous, "Output changed before the clock edge"
        dut.clk.value = 1
        await Timer(50, unit="ns")
        assert int(dut.uo_out.value) == value
        previous = value


@cocotb.test()
async def test_enable_and_reset(dut):
    """Enable holds state, and reset clears state even while enable is low."""
    await reset(dut)
    dut.ui_in.value = 0xA5
    await cycle(dut)
    assert int(dut.uo_out.value) == 0xA5
    dut.ena.value = 0
    for value in (0, 0xFF, 0x3C):
        dut.ui_in.value = value
        await cycle(dut)
        assert int(dut.uo_out.value) == 0xA5
    dut.clk.value = 0
    dut.rst_n.value = 0
    await Timer(50, unit="ns")
    assert int(dut.uo_out.value) == 0, "Reset must work without a clock edge"
    dut.rst_n.value = 1
    dut.ena.value = 1
    dut.ui_in.value = 0x3C
    await cycle(dut)
    assert int(dut.uo_out.value) == 0x3C


@cocotb.test()
async def test_bidirectional_pins(dut):
    """All unused bidirectional pins remain inputs with their output data low."""
    await reset(dut)
    for value in (0, 0x55, 0xAA, 0xFF):
        dut.uio_in.value = value
        await cycle(dut)
        assert int(dut.uio_oe.value) == 0
        assert int(dut.uio_out.value) == 0
        assert int(dut.uo_out.value) == 0
