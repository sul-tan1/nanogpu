# SIMD datapath area study

These preliminary cell-area estimates guide architecture selection. They do not
establish complete-chip fit, maximum clock frequency, or physical correctness.

## Tile constraint

The workshop limit is one digital tile, approximately 161 x 111 micrometers.
The [official Sky130A definition](https://github.com/TinyTapeout/tt-support-tools/blob/main/tech/sky130A/tile_sizes.yaml)
specifies 161.00 x 111.52 micrometers, or 17,954.72 square micrometers of gross
footprint. The actual placement region is smaller and must leave room for routing
and implementation overhead.

## Estimates measured November 20, 2026

| Probe | Mapped cells | Sum of cell areas (um^2) | Cell area / gross tile area |
| --- | ---: | ---: | ---: |
| Two 8-bit lanes, basic operations | 361 | 3,223.1 | 17.95% |
| Two 8-bit lanes, parallel multiply | 875 | 7,320.8 | 40.77% |
| Two 8-bit lanes, parallel multiply-accumulate | 1,034 | 8,484.4 | 47.25% |
| Two 4-bit lanes, parallel multiply-accumulate | 357 | 2,977.9 | 16.59% |

These percentages are ratios to the gross tile footprint, not routed utilization
or the percentage of a finished design that fits. Cell count is not NAND-equivalent
gate count; cells differ in size and function. The 4-bit case also changes precision.

## What is modeled

`experiments/simd-area/area_probe.v` has two operand registers and one result
register per lane, load enables, operation selection, execute enable, and active-low
reset. Results are twice the input width. The basic operations are add, subtract,
maximum, shift right by one, XOR, and clear. Optional multiplication is parallel;
optional MAC accumulates modulo the result width. Arithmetic is unsigned.

All result bits are observable. The synthesis script requires every retained
cell to map to a known Sky130 cell and checks the mapped design for structural
problems. Some register bits are optimized away in the basic case.

The probe omits host packet decoding, result serialization, program storage and
sequencing, instruction handshaking, and added writeback paths. Its ports are an
experiment interface, not the final Tiny Tapeout pin mapping. It is not included
in `info.yaml` and does not replace the production starter or its tests.

## Method and limitations

Yosys `synth -flatten`, `dfflibmap`, and ABC map the probe to the Sky130 HD
typical-corner Liberty distributed by the
[OpenROAD flow platform](https://github.com/The-OpenROAD-Project/OpenROAD-flow-scripts/tree/master/flow/platforms/sky130hd).
The script sums mapped instance areas and records the library SHA-256 and Yosys
version in `build/simd-area/summary.json`. Special-purpose `lpflow_*` and `probe*`
cells are excluded, consistent with the OpenROAD platform guidance.

This mapping exercise is not the pinned Tiny Tapeout LibreLane flow and does not
apply its full cell exclusion list, sizing, timing constraints, or physical
optimization. It has no placement, clock-tree synthesis, routing, parasitic
extraction, DRC, or LVS. The variants have not been functionally verified as
finished processor implementations.

ABC reported a merged-library conversion warning, then successfully used its
Liberty fallback. Each mapped netlist passed the structural check and contained
only recognized, non-excluded library cells.

The basic core is a reasonable next prototype. The larger multiply/MAC variants
need complete-chip measurements. An iterative multiplier is the next comparison;
no iterative area result is claimed here.

## Reproduce on this computer

The downloaded Liberty is cached under the ignored `.tools/area-study/` folder.
From the project root:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File experiments\simd-area\run.ps1
```

On another computer, use the local CAD/Python setup and download
`sky130_fd_sc_hd__tt_025C_1v80.lib` from the linked OpenROAD platform into
`.tools/area-study/`. The command also accepts `--liberty C:\path\to\library.lib`.

For Linux, activate Yosys and run `python experiments/simd-area/sweep.py --liberty PATH`.
Generated logs, scripts, mapped netlists, and summary are in `build/simd-area/`
and remain excluded from Git. The initial library SHA-256 is
`ec0e1067a35c8bf20b11e58d1e8ac53326067e4dac84a125cc1b917a3518d0d9`.
