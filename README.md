# NanoGPU

NanoGPU is a programmable 2D renderer and vector processor. Two SIMD lanes
share a host-loaded program of one to four instructions. Each lane has a signed
8-bit multiplier and a 32-bit accumulator for dot products. In graphics mode,
on-chip counters generate pixel coordinates on a 64 × 64 canvas and feed the
same lanes. The host collects the grayscale pixels for display.

The design targets a digital Sky130A Tiny Tapeout `1x2` footprint and a 10 MHz
clock. See the [verification report](docs/verification.md) for the build history,
physical checks, and fabrication status.

## See it in action

| Multiply shader | Sobel input | Sobel edges |
| --- | --- | --- |
| <img src="docs/assets/multiply-gradient.png" width="192" height="192" alt="Multiplication gradient shaded by NanoGPU"> | <img src="docs/assets/sobel-input.png" width="192" height="192" alt="Grayscale scene built from two NanoGPU renders"> | <img src="docs/assets/sobel-edges.png" width="192" height="192" alt="Sobel edges from NanoGPU dot products"> |

- **Programmable shading.** The simulator draws a 64 × 64 gradient with
  `MUL_SHIFT4`, or `(x × y) >> 4`. Full-frame draw and readback take 10,246 cycles.
- **Edge detection.** The host assembles a scene from two chip renders and
  sends each 3 × 3 window to the chip. One lane computes each direction of the
  Sobel filter. The host combines their magnitudes and writes the image.
- **Dense layer.** Two MAC lanes take inputs `[3, 2, 4]` and weights
  `[5, 7, 2]` and `[-5, 7, -2]`, producing `37` and `-9`.
- **Burst throughput.** For 32 pairs of MAC operations and readback, the burst
  command uses 203 cycles versus 330 for individual commands, a 38.5% reduction.

[Open the 3D chip layout](https://sul-tan1.github.io/nanogpu/) · [View CI and download test artifacts](https://github.com/sul-tan1/nanogpu/actions)

## Run the simulation

Clone the repository using Git:

```sh
git clone https://github.com/sul-tan1/nanogpu.git
cd nanogpu
```

On Windows x64, download `oss-cad-suite-windows-x64-20261120.tgz` to your
Downloads folder. The setup command extracts the toolchain and installs the
Python test dependencies locally. [OSS CAD Suite release](https://github.com/YosysHQ/oss-cad-suite-build/releases/tag/2026-11-20)

```powershell
.\tt.cmd setup
.\tt.cmd test
Start-Process .\test\output\multiply-gradient.png
Start-Process .\test\output\sobel-edges.png
```

Expect `TESTS=7 PASS=7 FAIL=0`. The test writes PNGs and the dense-layer and
burst benchmark results to `test/output/`. For **Ubuntu or WSL**, an existing
Windows toolchain, or opening waveforms, see the [tooling guide](docs/windows-and-github.md).

## Open the playground

After setup, start the local playground from the repository root:

```powershell
.\tt.cmd playground
```

Choose **Diagonal ramp**, **XOR tiles**, or another preset. Edit the rectangle's
position, size, or instruction slots, then click **Render in RTL**. Add more
rectangles to layer them in draw order. Hover over the image to read a pixel
or download the 64 × 64 PNG. **MAC compute** accepts editable signed operand
groups and displays the two dot products.

Each run sends commands through the same Verilog pins as the automated tests.
The host applies the background and layers the returned rectangles. Keep the
terminal open while using the playground, then press **Ctrl+C** to stop it.
See the [Linux launcher](docs/windows-and-github.md#ubuntu-and-wsl) and the
[instruction set and host protocol](docs/info.md).

## Project files

| File | Purpose |
| --- | --- |
| `docs/project-plan.md` | Design constraints and architecture choices. |
| `src/nano_gpu.v` | Command decoder, scan counters, sequencer, and two arithmetic lanes. |
| `src/project.v` | Map the design onto Tiny Tapeout pins. |
| `test/test.py` | Shared functional tests for RTL and the generated gate-level netlist. |
| `info.yaml` | Project title, author, pinout, top module, source list, clock, and tile size. |
| `test/Makefile` | Keep `PROJECT_SOURCES` aligned with `info.yaml`. |
| `docs/info.md` | Datasheet, host protocol, and example transactions. |
| `src/config.json` | Physical implementation configuration and 100 ns clock period. |

GitHub Actions runs lint, RTL and gate-level simulation, GDS generation,
precheck, documentation, and layout publication. The optional FPGA workflow
runs manually. See the [tooling guide](docs/windows-and-github.md) for the
artifacts from each job.

The interface, configuration, and workflows derive from the
[Tiny Tapeout Verilog template](https://github.com/TinyTapeout/ttsky-verilog-template).
See [LICENSE](LICENSE) for the Apache-2.0 license.
