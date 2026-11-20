# NanoGPU

NanoGPU is a programmable 2D renderer and vector processor by Emron Arsala.
Two 8-bit arithmetic lanes share a four-instruction program. A rectangle command
generates its own pixel coordinates on chip. A compute command supplies ordinary
operands to the same lanes. The host collects the result bytes and displays any
image in its own framebuffer.

The target is one digital Sky130A Tiny Tapeout tile with a 10 MHz clock. The
design uses the `ttsky26d` workflow. See the [pinout, commands, and instruction set](docs/info.md).

## Start here

Open `../digital-final.code-workspace` in VS Code, or open this folder directly.
In a PowerShell terminal:

```powershell
.\tt.cmd doctor
.\tt.cmd lint
.\tt.cmd test
.\tt.cmd synth
.\tt.cmd wave
```

Setup is already prepared on this computer. If tool locations change, run
`.\tt.cmd setup`. It can reuse the ALU project's installed suite, or install a
local suite from your downloaded archive. See [Windows and GitHub setup](docs/windows-and-github.md).

The simulation checks a 64×64 render, reuses the same program to compute two
averages, then draws a second rectangle with a different program. The image
assembled from simulator output is saved to `test/output/nanogpu.png`.

See [local verification and layout results](docs/verification.md) for the
measured area, timing, and status of the fabrication submission.

## Project files

| File | Purpose |
| --- | --- |
| `docs/project-plan.md` | Design constraints and remaining architecture experiments. |
| `src/nano_gpu.v` | Command decoder, scan counters, sequencer, and two arithmetic lanes. |
| `src/project.v` | Map the design onto Tiny Tapeout pins. |
| `test/test.py` | Shared functional tests for RTL and the generated gate-level netlist. |
| `info.yaml` | Project title, author, pinout, top module, source list, clock, and tile size. |
| `test/Makefile` | Keep `PROJECT_SOURCES` aligned with `info.yaml`. |
| `docs/info.md` | Datasheet, host protocol, and hardware demo. |
| `src/config.json` | Physical implementation configuration and 100 ns clock period. |

The GitHub workflow includes RTL lint/tests, GDS generation, precheck, gate-level
simulation, documentation, and the layout viewer. FPGA builds are optional and
manual. This local repository needs its own GitHub origin before those workflows
can run remotely.

Build reports appear in `build/synth/` and waveforms in `test/`. See the
[Windows and GitHub setup](docs/windows-and-github.md) for hardening and artifact locations.

The interface, configuration, and workflows derive from the
[Tiny Tapeout Verilog template](https://github.com/TinyTapeout/ttsky-verilog-template).
See [LICENSE](LICENSE) for the Apache-2.0 license.
