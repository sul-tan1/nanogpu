# Final-project plan: GPU-inspired SIMD compute

## Hard constraints

- One digital tile; larger allocations are outside the project scope.
- Workshop dimensions: approximately 161 x 111 micrometers. The official Sky130A
  template specifies 161.00 x 111.52 micrometers; preserve its supplied geometry.
- Digital circuitry only, using the template's standard pin interface.
- Fit, timing, and physical correctness must pass the actual GDS, precheck, and
  gate-level flow. The budget includes storage, control, interface, and physical
  implementation overhead as well as arithmetic.

## Current status

The first NanoGPU implementation shares two 8-bit SIMD lanes between a rectangle
renderer and vector compute. It runs a host-loaded program of up to four
instructions. See the [datasheet](info.md) for the implemented protocol and the
[area study](area-study.md) for earlier arithmetic variants.

## Implemented scope and experiments

The shared instruction set includes add, subtract, maximum, XOR, right shift by
one, and identity. A synchronous byte interface transports commands and results.
The rasterizer supplies pixel coordinates on a 64×64 canvas and the host stores
the output image. The host can replace the program between commands.

Compare parallel and iterative multiplication at the same precision, workload,
and implementation constraints. An 8-bit by 8-bit multiply has a full 16-bit
product. Define signedness, accumulator width, and overflow behavior for MAC;
include it only when the full design has enough implementation margin.

The early basic two-lane datapath estimate is about 3,223 square micrometers of
Sky130 HD cells. Parallel multiply raises it to about 7,321 and MAC to about 8,484.
These estimates exclude important complete-chip costs; see the area-study limits.
A 4-bit version is another comparison point with different numerical capability.

The simulation demo shades a rectangle and reuses its program in compute mode.
The chip generates every pixel coordinate after the draw command. Report core
throughput and host-transfer throughput separately.

## Development order

1. Specify instructions, registers/writeback, arithmetic rules, pin map, clock,
   reset, host handshakes, and invalid-command behavior.
2. Implement one small module at a time and add tests for that behavior.
3. Integrate the Tiny Tapeout wrapper; update both source lists and the datasheet.
4. Run local lint, functional tests, and synthesis before pushing.
5. Run the GitHub GDS, precheck, and gate-level tests; inspect timing and utilization.
6. Demonstrate the design with a reproducible script and waveform/logic-analyzer capture.
7. Add optional features only while the physical results leave room.

## Evidence to retain

- A stable behavioral specification and a small architecture diagram.
- Directed tests plus reproducible randomized tests appropriate to the protocol.
- Reset, boundary, and error-case tests, with failing cases repaired in the RTL.
- A link to the exact commit with passing RTL, GDS, precheck, and gate-level checks.
- Measured area/utilization, target clock and timing slack, and the layout image.
- A short hardware or simulation demo and a clear explanation of design tradeoffs.

## Resume wording after completion

Use measured results and name the actual contribution. For example:

> Designed and verified a [function] in Verilog; implemented [features], built
> cocotb tests for [cases], and hardened the design into one Sky130 Tiny Tapeout
> tile with [measured timing/area result].

Fill those fields only after the corresponding implementation and checks exist.
Use "taped out" after submission, and "silicon-tested" after testing the fabricated chip.

## Constraints reference

The [official tile sizes](https://github.com/TinyTapeout/tt-support-tools/blob/main/tech/sky130A/tile_sizes.yaml)
and [1x1 floorplan](https://github.com/TinyTapeout/tt-support-tools/blob/main/tech/sky130A/def/tt_block_1x1_pg.def)
define the geometry. The [project template](https://github.com/TinyTapeout/ttsky-verilog-template/blob/main/info.yaml)
defines the fixed Tiny Tapeout pin groups. The
[Tiny Tapeout FAQ](https://tinytapeout.com/faq/)
explains why tile utilization and physical implementation must be checked. Keep
this workshop's matching `ttsky26d` workflow references until deliberately
migrating the project to another shuttle template.
