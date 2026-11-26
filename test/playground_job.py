"""Run a playground request through the same simulated pins as CI."""

import json
import os
from pathlib import Path

import cocotb

from test import Host, pixels_for


@cocotb.test()
async def run_playground_job(dut):
    request_path = Path(os.environ['NANOGPU_PLAYGROUND_REQUEST'])
    request = json.loads(request_path.read_text(encoding='utf-8'))
    host = Host(dut)
    await host.reset()
    start = host.cycles

    if request['mode'] == 'mac':
        groups = request['groups']
        sums = await host.mac_burst(groups)
        assert sums == [sum(a * b for a, b, _, _ in groups), sum(c * d for _, _, c, d in groups)]
        response = {'sums': sums, 'groups': len(groups), 'cycles': host.cycles - start}
    else:
        pixels = [request['background']] * (64 * 64)
        draw_cycles = []
        for layer in request['layers']:
            x, y, width, height = (layer[key] for key in ('x', 'y', 'width', 'height'))
            program = layer['program']
            await host.load(program)
            begin_draw = host.cycles
            region = await host.draw(x, y, width, height)
            draw_cycles.append(host.cycles - begin_draw)
            assert region == pixels_for(program, x, y, width, height)
            for row in range(height):
                start_pixel = (y + row) * 64 + x
                pixels[start_pixel:start_pixel + width] = region[row * width:(row + 1) * width]
        response = {'pixels': pixels, 'draw_cycles': draw_cycles, 'cycles': host.cycles - start}

    await host.expect_idle()
    request_path.with_name('response.json').write_text(json.dumps(response), encoding='utf-8')
