# Local verification

NanoGPU was routed as a single digital Sky130A Tiny Tapeout tile at a 100 ns
clock period (10 MHz). The local layout package records source revision
`181d1579c3178f559b4621e5907c444cf1c6fb44`. Subsequent documentation edits retain
the same RTL and physical configuration.

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

## Demonstration and area comparison

The full 64×64 gradient takes 10,246 clock cycles from command transfer through
the last pixel, or 1.0246 ms at 10 MHz with the host ready. The same two-instruction
program then computes two averages. The RTL and gate-level simulations produced
byte-identical demo images after a second program shaded an inset rectangle.

Each lane shares one adder across addition, subtraction, and unsigned maximum.
A Yosys SAT miter proved that the shared datapath agrees with direct arithmetic
for all opcodes and operands. Mapping the same complete processor with the same
Sky130 HD typical Liberty gave 5,903.16 µm² with separate operators and
5,829.34 µm² with the shared datapath, a 1.25% reduction in estimated mapped
cell area. The post-route area above comes from the separate physical flow.

## Build artifacts

The local build used LibreLane 3.0.14, Tiny Tapeout support tools `0922544e`, and
Sky130A open_pdks `8afc8346a57fe1ab7934ba5a6056ea8b43078e71`. The Tiny Tapeout
precheck used its workflow PDK revision `0536d02d875c8f67dd7cca3902ac457e62f20005`.

| Local path from project root | Artifact |
| --- | --- |
| `tt_submission/` | GDS, LEF, gate netlist, extracted parasitics, and build metadata |
| `tt_submission/stats/metrics.csv` | Post-route area, timing, routing, and LVS metrics |
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
