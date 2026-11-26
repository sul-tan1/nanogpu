# Tools and GitHub workflow

## Windows x64

Follow the [fresh-clone steps](../README.md#run-the-simulation) in the README.
From the repository root, use `-Archive` if the OSS CAD Suite archive is
outside the Downloads folder:

```powershell
.\tt.cmd setup -Archive 'C:\path\to\oss-cad-suite-windows-x64-20261120.tgz'
```

To use an extracted suite, point `OSS_CAD_SUITE` to the folder containing
`environment.ps1` and run setup from the same PowerShell session:

```powershell
$env:OSS_CAD_SUITE = 'C:\path\to\oss-cad-suite'
.\tt.cmd setup
```

The launcher sets the CAD tool paths for each run and installs a portable
CPython and test packages under `.tools/`. Run `.\tt.cmd doctor` to check the
setup, `.\tt.cmd lint` to run Verilator, or `.\tt.cmd synth` for a Yosys structural
check. Run `.\tt.cmd wave` after a test to inspect the clock, bus, and handshakes
in GTKWave, or open `test/tb.fst` with Surfer in VS Code.

## Ubuntu and WSL

Install the simulation tools and run the testbench from a clone:

```sh
sudo apt-get update
sudo apt-get install -y git make iverilog verilator python3 python3-venv
git clone https://github.com/sul-tan1/nanogpu.git
cd nanogpu
python3 -m venv .tools/venv
source .tools/venv/bin/activate
python -m pip install -r scripts/requirements.txt
python scripts/run.py lint
cd test
make
python -m cocotb_tools.check_results results.xml
```

The demo is `test/output/nanogpu.png` and the waveform is `test/tb.fst`, relative
to the repository root.

## GitHub repository

The upstream repository is [sul-tan1/nanogpu](https://github.com/sul-tan1/nanogpu).
With write access, commit your changes and push to start the workflows. You can
also experiment in your own fork.

```powershell
git push
```

## Jobs on a push

| Workflow/job | What it checks or produces |
| --- | --- |
| `test` | Verilator lint and cocotb RTL tests; `test-results` contains waveform/results. |
| `gds` / `gds` | LibreLane Sky130A implementation for the configured tile; GDS/OAS and implementation logs. |
| `gds` / `precheck` | Physical submission checks using the generated layout. |
| `gds` / `gl_test` | The same cocotb testbench run on the generated netlist and PDK models. |
| `gds` / `viewer` | GitHub Pages publication, 3D layout, Explorer link, and 2D preview. |
| `docs` | Project datasheet generated from `info.yaml` and `docs/info.md`. |
| `fpga` | Optional manual build for TT ASIC Sim ICE40UP5K hardware. |

The `test`, `docs`, and `gds` workflows start on pushes. The physical checks,
gate-level test, and viewer wait for the `gds` job. To test the current `main`
again, users with write access can open [Actions](https://github.com/sul-tan1/nanogpu/actions),
pick the workflow, and select **Run workflow**. The `test-results` artifact from
the `test` run includes the render, JUnit results, and waveform.

Open the [3D viewer](https://sul-tan1.github.io/nanogpu/) with `.\tt.cmd viewer`
or from the GDS run summary, which also links to the layout explorer. If the
viewer job fails, verify that **Settings > Pages > Source** is **GitHub Actions**
and start a fresh `gds` run. See the [Tiny Tapeout FAQ](https://tinytapeout.com/faq/#my-github-action-is-failing-on-the-pages-part).

Do not upload `.tools/`, PDKs, `runs/`, or `build/` to GitHub. Download artifacts
from the exact commit whose implementation you want to inspect. A successful
local synthesis does not establish final area fit, timing, DRC, or LVS.

## Optional local gate-level test and hardening

To run an existing gate-level netlist locally, copy it to
`test/gate_level_netlist.v`, set `PDK_ROOT` to the matching extracted Sky130 PDK,
then run `.\tt.cmd gl-test`. The GitHub gate-level job provisions these itself.

For local GDS generation, use the supplied Linux dev container and the official
[local hardening guide](https://tinytapeout.com/guides/local-hardening/).
The Windows suite handles simulation and synthesis; the full ASIC flow needs the
additional Linux toolchain and PDK. The GitHub flow works without local Docker.
