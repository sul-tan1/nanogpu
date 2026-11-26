# Tools and GitHub workflow

## On this computer

Open `digital-final.code-workspace` from the parent folder. The project lives in
`ttsky-digital-final` and has its own Git history. The ALU project is retained as a
reference and a source of the already installed tools. The barrel-shifter files
are archived under the parent `.archive/` folder and are outside this workspace.

From the NanoGPU project folder, run:

```powershell
.\tt.cmd doctor
.\tt.cmd lint
.\tt.cmd test
Start-Process .\test\output\nanogpu.png
```

Look for `TESTS=4 PASS=4 FAIL=0`. The PNG shows the gradient and shaded inset
assembled from simulated pixel output. Run `.\tt.cmd synth` for a Yosys
structural check or `.\tt.cmd wave` to see the clock, bus, and handshakes.

If the tools are missing, run `.\tt.cmd setup`. Setup automatically reuses
`../tqt_tt_workshop_ex/.tools/oss-cad-suite` and its
Python packages when available. A small project-local CPython runtime keeps this
project's test modules separate. Keep the ALU folder in place while sharing its
tools. To use a shared tools directory elsewhere, set `TT_SHARED_TOOLS` to it
and rerun setup. `OSS_CAD_SUITE` can override just the extracted suite directory.

If the shared installation is unavailable, setup can extract your archive into
the project's ignored `.tools/` directory and download the portable Python and
test dependencies:

```powershell
.\tt.cmd setup -Archive 'C:\path\to\oss-cad-suite-windows-x64-20261120.tgz'
```

The launcher activates the suite for its process, handles the Windows Icarus
backend/VPI paths, and uses a process-scoped PowerShell script-policy option.
It does not modify your global PATH or persistent execution policy.

Local commands are also available from **Terminal > Run Task** in VS Code.
The Surfer extension recommended by the template can open `test/tb.fst` directly.
`tt.cmd wave` uses GTKWave with the saved signal selection.

## GitHub repository

NanoGPU's `origin` is [sul-tan1/nanogpu](https://github.com/sul-tan1/nanogpu).
The local `main` tracks `origin/main`. After making and committing a change in
this project, run:

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
again without making a commit, open [Actions](https://github.com/sul-tan1/nanogpu/actions),
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
