# Hardware verification

The current design targets two digital Sky130A Tiny Tapeout tiles (`1x2`) at a
100 ns clock period (10 MHz). Both builds below use the 161.00 × 225.76 µm
floorplan and LibreLane 3.0.14 with the same Sky130A PDK revision.

## Routed 1×2 results

| Measurement | Resized original datapath | Two signed MAC lanes |
| --- | ---: | ---: |
| Standard-cell area | 9,211.33 µm² | 26,855.80 µm² |
| Placement area utilization | 26.89% | 78.40% |
| Worst setup slack | +57.304 ns | +54.190 ns |
| Worst hold slack | +0.112 ns | +0.116 ns |
| Detailed-route DRC and LVS errors | 0 | 0 |
| Worst-corner transition violations | 50 | 142 |
| Hosted RTL and gate-level tests | 4 each passed | 7 each passed |
| Hosted Tiny Tapeout prechecks | 17 passed | 17 passed |

See the [resized baseline run](https://github.com/sul-tan1/nanogpu/actions/runs/45736173614)
and the [signed MAC run](https://github.com/sul-tan1/nanogpu/actions/runs/45736785320)
for exact revisions, reports, and layout artifacts. The signed MAC layout meets
the 10 MHz setup and hold checks. The transition violations are at the slow,
hot, low-voltage corner against the 0.75 ns limit and remain open for signoff.
The local slow-corner optimization trial reported 149 violations. The hosted
build retained the original optimization settings. Its gate netlist reproduced
the RTL simulation's PNGs and numerical reports byte for byte in a local run.

The current GDS, gate netlist, and timing metrics are available in the GDS run's
`tt_submission` artifact. The workspace copy is under `tt_submission/`.

## Original 1×1 implementation

The historical local layout below records source revision
`181d1579c3178f559b4621e5907c444cf1c6fb44`.

| Check or measurement | Result |
| --- | --- |
| RTL lint and Yosys structural synthesis | Passed |
| Cocotb RTL simulation | 4 tests passed |
| Cocotb Sky130 gate-level simulation | 4 tests passed |
| Detailed-route design rule violations | 0 |
| Layout versus schematic errors | 0 |
| Tiny Tapeout precheck | 16 checks passed |
| Tile footprint | 161.00 × 111.52 µm |
| Standard-cell area and core utilization | 8,876.01 µm² and 53.82% |
| Worst post-route setup and hold slack | +56.707 ns and +0.120 ns |
| Worst-corner maximum transition violations | 55 at slow process, 100 °C, 1.60 V |

The transition repair experiment reduced the worst-corner count from 223 to 55
with the same 0.75 ns transition limit and 100 ns clock period. Those remaining
warnings need review during tapeout signoff.

## What the simulations check

The cocotb host sends command bytes through the Tiny Tapeout pins at 10 MHz. It
checks that bytes transfer when both ready and valid are high, and compares
the responses with a separate Python model. The same seven tests run on the
Verilog RTL and on the Sky130 gate-level netlist produced by the GDS flow.

| Test | What it checks |
| --- | --- |
| Shared program demo | Compares all 4,096 gradient pixels with the model, checks the cycle count, uses the same program to return the averages `7` and `14`, and verifies a second program shades an inset rectangle. |
| Compute reference and wrapping | Checks the reset default, all six instructions, and 190 two-lane jobs with boundary values and reproducibly randomized programs and operands. Examples include unsigned `255 + 1 = 0` and `0 − 1 = 255`. |
| Rectangle boundaries and errors | Checks even and odd widths, single pixels, final rows and columns, output order, and status bytes for invalid commands, dimensions, and instructions. A rejected program restores the identity program. |
| Stalls, enable, and reset | Pauses input partway through a request, waits before reading valid output, disables and resumes the chip, and resets during a draw. Checks that a waiting byte stays stable, the resumed draw returns every pixel, and reset clears the pending draw and restores the default program. |
| Signed dot products and accumulators | Computes the dense-layer outputs `37` and `-9`, checks multi-instruction writeback, signs, full-width products and sums, mode errors, and reset. |
| Burst protocol and throughput | Compares 32 MAC steps sent individually and in a burst, exercises zero and 255 count boundaries, and checks stalled reads, pause, and reset. |
| Multiply shader and Sobel demo | Checks all 4,096 multiply-shaded pixels and signed scaling. Compares both Sobel filter results at every interior pixel with independent Python dot products. |

Two additional local RTL checks compared all 65,536 signed input pairs with an
integer multiply reference and exercised positive and negative 32-bit wraparound
through burst packets of 133,110 terms per lane in total.

Physical precheck covers the GDS geometry, layers, and pin rules. See the
[original hosted physical run](https://github.com/sul-tan1/nanogpu/actions/runs/45729734282)
for the GDS, precheck, and gate-level artifacts.

## Demonstration and area comparison

The full 64×64 gradient takes 10,246 clock cycles from command transfer through
the last pixel, or 1.0246 ms at 10 MHz with the host ready. The same two-instruction
program then computes two averages. The RTL and gate-level simulations produced
byte-identical demo images after a second program shaded an inset rectangle.
The multiply shader also takes 10,246 cycles. A 32-step burst with two signed
products per step and final readback takes 203 cycles versus 330 for individual
MAC commands plus readback, a 38.5% reduction.

Each lane shares one adder across addition, subtraction, and unsigned maximum.
A Yosys SAT miter proved that the shared datapath agrees with direct arithmetic
for all opcodes and operands. Mapping the same complete processor with the same
Sky130 HD typical Liberty gave 5,903.16 µm² with separate operators and
5,829.34 µm² with the shared datapath, a 1.25% reduction in estimated mapped
cell area. The post-route area above comes from the separate physical flow.

## Historical local build artifacts

The local build used LibreLane 3.0.14, Tiny Tapeout support tools `0922544e`, and
Sky130A open_pdks `8afc8346a57fe1ab7934ba5a6056ea8b43078e71`. The Tiny Tapeout
precheck used its workflow PDK revision `0536d02d875c8f67dd7cca3902ac457e62f20005`.

| Local path from project root | Artifact |
| --- | --- |
| `build/physical-slew/tt_submission/` | GDS, LEF, gate netlist, extracted parasitics, and build metadata |
| `build/physical-slew/tt_submission/stats/metrics.csv` | Post-route area, timing, routing, and LVS metrics |
| `build/physical-slew/layout.png` | Layout preview |
| `build/physical-slew/precheck-results.md` | Results for the 16 prechecks |
| `build/physical-slew/gate-results.xml` | Gate-level simulation results |
| `build/synth/nano_lane_equivalence.log` | Arithmetic equivalence proof |
| `build/synth/nanogpu-final-*-compare.log` | Yosys area estimates for both datapaths |
| `test/output/nanogpu.png` | Simulated render |

On Windows, open the two previews from the project root:

```powershell
Start-Process .\test\output\nanogpu.png
Start-Process .\build\physical-slew\layout.png
```

See the [GitHub workflow guide](windows-and-github.md) for hosted checks and the
layout viewer. Manufacturing submission is pending. See the official
[Tiny Tapeout submission guide](https://www.tinytapeout.com/guides/advanced-workshop/submit-your-design/).
