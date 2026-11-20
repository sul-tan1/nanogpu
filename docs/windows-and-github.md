# Tools and GitHub workflow

## On this computer

Open `digital-final.code-workspace` from the parent folder. The project lives in
`ttsky-digital-final` and has its own Git history. The ALU project is retained as a
reference and a source of the already installed tools. The barrel-shifter files
are archived under the parent `.archive/` folder and are outside this workspace.

```powershell
cd C:\Users\Shot\Downloads\tapeoutproject\ttsky-digital-final
.\tt.cmd setup
.\tt.cmd doctor
.\tt.cmd lint
.\tt.cmd test
.\tt.cmd synth
.\tt.cmd wave
```

Setup automatically reuses `../tqt_tt_workshop_ex/.tools/oss-cad-suite` and its
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

## Connect a GitHub repository

The project starts locally with no remote, so it cannot overwrite the ALU fork.
Create a new empty repository in your GitHub account (without generating another
README or license), then run these commands using its actual URL:

```powershell
git remote add origin https://github.com/YOUR_ACCOUNT/YOUR_REPOSITORY.git
git push -u origin main
```

Enable Actions in that repository. Under **Settings > Pages**, set the publishing
**Source** to **GitHub Actions**. If the `github-pages` environment restricts
branches, allow `main`. The viewer job declares its Pages and identity permissions.
Pages availability depends on repository visibility and your GitHub plan; see
[GitHub's Pages documentation](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages).

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

The first three workflows start on pushes. The physical checks, gate-level test,
and viewer wait for the `gds` job. Each workflow also supports **Run workflow**.
The FPGA workflow is manual by default.

After a successful viewer deployment, use the links in the GDS run summary, or
run `.\tt.cmd viewer`; it derives the Pages address from this project's origin.
If Pages deployment fails, verify its source setting and start a fresh workflow
run. See the [Tiny Tapeout FAQ](https://tinytapeout.com/faq/#my-github-action-is-failing-on-the-pages-part).

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
