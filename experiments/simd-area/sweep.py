"""Estimate datapath cell areas, not routed fit, using a Sky130 HD Liberty."""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[2]
LIB_SOURCE = 'https://raw.githubusercontent.com/The-OpenROAD-Project/OpenROAD-flow-scripts/master/flow/platforms/sky130hd/lib/sky130_fd_sc_hd__tt_025C_1v80.lib'
CASES = [
    ('two_lane_8bit_basic', 8, 2, 0, 0),
    ('two_lane_8bit_parallel_mul', 8, 2, 1, 0),
    ('two_lane_8bit_parallel_mac', 8, 2, 1, 1),
    ('two_lane_4bit_parallel_mac', 4, 2, 1, 1),
]


def quoted(path):
    return '"' + Path(path).resolve().as_posix().replace('"', '\\"') + '"'


def cell_areas(library):
    text = library.read_text(encoding='utf-8')
    starts = list(re.finditer(r'\bcell\s*\(\s*"?(sky130_fd_sc_hd__[^"\s)]+)"?\s*\)\s*\{', text))
    areas = {}
    for i, match in enumerate(starts):
        end = starts[i + 1].start() if i + 1 < len(starts) else len(text)
        area = re.search(r'\barea\s*:\s*([\d.eE+-]+)\s*;', text[match.end():end])
        if area:
            areas[match[1]] = float(area[1])
    if len(areas) < 100:
        raise RuntimeError('Could not parse the expected Sky130 HD cell areas.')
    return areas


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--liberty', type=Path, default=ROOT / '.tools/area-study/sky130_fd_sc_hd__tt_025C_1v80.lib')
    args = parser.parse_args()
    if not args.liberty.is_file():
        raise SystemExit(f'Download the Liberty from {LIB_SOURCE} and pass --liberty PATH.')
    yosys = shutil.which('yosys')
    if not yosys:
        raise SystemExit('Yosys is not on PATH; use run.ps1 on Windows.')
    areas = cell_areas(args.liberty)
    source = Path(__file__).with_name('area_probe.v')
    output = ROOT / 'build/simd-area'
    output.mkdir(parents=True, exist_ok=True)
    rows = []
    for name, width, lanes, mul, mac in CASES:
        case_dir = output / name
        case_dir.mkdir(exist_ok=True)
        script = case_dir / 'synth.ys'
        netlist = case_dir / 'mapped.json'
        commands = [
            f'read_liberty -lib {quoted(args.liberty)}',
            f'read_verilog {quoted(source)}',
            f'chparam -set WIDTH {width} -set LANES {lanes} -set ENABLE_MUL {mul} -set ENABLE_MAC {mac} area_probe',
            'synth -top area_probe -flatten',
            f'dfflibmap -liberty {quoted(args.liberty)}',
            f'abc -liberty {quoted(args.liberty)} -dont_use sky130_fd_sc_hd__lpflow_* -dont_use sky130_fd_sc_hd__probe*',
            'clean', 'check -assert',
            f'stat -liberty {quoted(args.liberty)}',
            f'write_json {quoted(netlist)}',
        ]
        script.write_text('\n'.join(commands) + '\n', encoding='utf-8')
        subprocess.run([yosys, '-q', '-l', str(case_dir / 'yosys.log'), '-s', str(script)], check=True, cwd=ROOT)
        cells = json.loads(netlist.read_text())['modules']['area_probe']['cells']
        counts = Counter(cell['type'] for cell in cells.values())
        unknown = set(counts) - set(areas)
        if unknown:
            raise RuntimeError(f'Unmapped or unknown cells: {sorted(unknown)}')
        if any('__lpflow_' in cell or '__probe' in cell for cell in counts):
            raise RuntimeError('The mapped design retained an excluded special-purpose cell.')
        area = sum(areas[cell] * count for cell, count in counts.items())
        row = dict(variant=name, width=width, lanes=lanes, parallel_multiply=bool(mul), mac=bool(mac),
                   cells=sum(counts.values()), cell_area_um2=round(area, 3),
                   cell_area_over_gross_tile_pct=round(100 * area / (161 * 111.52), 2), cells_by_type=dict(counts))
        rows.append(row)
        print(f'{name}: {row["cells"]} cells; {area:.1f} um^2; {row["cell_area_over_gross_tile_pct"]}% of gross tile area', flush=True)
    report = dict(
        scope='DATAPATH ONLY; no host interface, instruction storage/sequencer, placement, CTS, routing, or timing signoff',
        mapping='Yosys + dfflibmap + ABC, typical-corner Sky130 HD; not the pinned LibreLane signoff flow',
        excluded_cell_patterns=['sky130_fd_sc_hd__lpflow_*', 'sky130_fd_sc_hd__probe*'],
        liberty_source=LIB_SOURCE, liberty_sha256=hashlib.sha256(args.liberty.read_bytes()).hexdigest(),
        yosys_version=subprocess.check_output([yosys, '-V'], text=True).strip(),
        tile_width_um=161, tile_height_um=111.52,
        results=rows,
    )
    (output / 'summary.json').write_text(json.dumps(report, indent=2) + '\n')
    print(f'Datapath estimates only. Report: {output / "summary.json"}', flush=True)


if __name__ == '__main__':
    main()
