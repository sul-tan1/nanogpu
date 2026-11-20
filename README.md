# Digital ASIC final project

Author: Emron Arsala. Target: one digital Tiny Tapeout Sky130A tile (`1x1`).
The initial target clock is 10 MHz. The workflow version remains `ttsky26d`,
matching the workshop setup that passed for the ALU project.

This is a working project scaffold. Its current behavior is an enabled 8-bit
register with active-low asynchronous reset. The working direction is a GPU-inspired
two-lane SIMD coprocessor, with an [initial area study](docs/area-study.md).
The application is not implemented yet. Passing starter tests validates the interface and
tools; it is not evidence of a completed final design or a 1x1 physical build.

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

## Where to work

| File | Purpose |
| --- | --- |
| `docs/project-plan.md` | Choose a bounded final design and record milestones and measured results. |
| `src/digital_core.v` | Replace the small starter core with your design. |
| `src/project.v` | Map the design onto Tiny Tapeout pins. |
| `test/test.py` | Shared functional tests for RTL and the generated gate-level netlist. |
| `info.yaml` | Project title, author, pinout, top module, source list, clock, and tile size. |
| `test/Makefile` | Keep `PROJECT_SOURCES` aligned with `info.yaml`. |
| `docs/info.md` | Datasheet: describe the actual implemented behavior and hardware demo. |
| `src/config.json` | Physical implementation configuration; starter clock period is 100 ns. |

The GitHub workflow includes RTL lint/tests, GDS generation, precheck, gate-level
simulation, documentation, and the layout viewer. FPGA builds are optional and
manual. This local repository needs its own GitHub origin before those workflows
can run remotely.

## Results

Local reports appear in `build/synth/`; waveforms and simulation results appear
in `test/`. They are excluded from Git along with `.tools/` and PDK/build data.
The generic Yosys cell count is useful during development. Only a successful
Sky130 GDS build and physical checks establish that the final design fits `1x1`.
Record that evidence before describing the project as hardened or taped out.

The interface, configuration, and workflows derive from the
[Tiny Tapeout Verilog template](https://github.com/TinyTapeout/ttsky-verilog-template).
See [LICENSE](LICENSE) for the Apache-2.0 license.
