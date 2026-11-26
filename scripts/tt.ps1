[CmdletBinding()]
param(
    [ValidateSet('setup', 'doctor', 'lint', 'test', 'gl-test', 'synth', 'wave', 'viewer', 'playground', 'help')]
    [string]$Command = 'help',
    [string]$Archive = (Join-Path $env:USERPROFILE 'Downloads\oss-cad-suite-windows-x64-20261120.tgz'),
    [string]$Waveform = 'test\tb.fst',
    [switch]$NoBrowser
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$projectRoot = Split-Path -Parent $PSScriptRoot
$toolsDir = Join-Path $projectRoot '.tools'
$suiteDir = Join-Path $toolsDir 'oss-cad-suite'
$sharedToolsDir = [IO.Path]::GetFullPath((Join-Path $projectRoot '..\tqt_tt_workshop_ex\.tools'))
if ($env:TT_SHARED_TOOLS) { $sharedToolsDir = [IO.Path]::GetFullPath($env:TT_SHARED_TOOLS) }
if ($env:OSS_CAD_SUITE) {
    $suiteDir = [IO.Path]::GetFullPath($env:OSS_CAD_SUITE)
} elseif (-not (Test-Path -LiteralPath (Join-Path $suiteDir 'environment.ps1')) -and
          (Test-Path -LiteralPath (Join-Path $sharedToolsDir 'oss-cad-suite\environment.ps1'))) {
    $suiteDir = Join-Path $sharedToolsDir 'oss-cad-suite'
}
$sharedPackages = Join-Path $sharedToolsDir 'python\Lib\site-packages'
$useSharedPackages = (Test-Path -LiteralPath (Join-Path $sharedPackages 'cocotb')) -and
                     (Test-Path -LiteralPath (Join-Path $sharedPackages 'yaml'))
$pythonDir = Join-Path $toolsDir 'python'
$pythonExe = Join-Path $pythonDir 'python.exe'

function Assert-Exit([string]$Operation) {
    if ($LASTEXITCODE -ne 0) { throw "$Operation failed (exit $LASTEXITCODE)." }
}

function Enable-Suite {
    $environmentScript = Join-Path $suiteDir 'environment.ps1'
    if (-not (Test-Path -LiteralPath $environmentScript)) {
        throw 'OSS CAD Suite is missing. Run .\tt.cmd setup first.'
    }
    # Always select this project's suite, even if another suite was activated earlier.
    $env:YOSYSHQ_ROOT = $suiteDir
    . $environmentScript
    $env:VERILATOR_ROOT = Join-Path $suiteDir 'share\verilator'
}

try {
    if ($Command -eq 'help') {
        Write-Output @'
Run from the project folder:
  .\tt.cmd setup                 Reuse installed tools, or install them for this project
  .\tt.cmd doctor                Check the project and tools
  .\tt.cmd lint                  Check Verilog with Verilator
  .\tt.cmd test                  Run the shared RTL/gate-level cocotb tests
  .\tt.cmd synth                 Check/synthesize RTL with Yosys
  .\tt.cmd wave                  Open test/tb.fst in GTKWave
  .\tt.cmd wave -Waveform PATH   Open a downloaded RTL or gate-level waveform
  .\tt.cmd gl-test               Test an existing Sky130 netlist (requires PDK_ROOT)
  .\tt.cmd viewer                Open this repository's published 3D layout
  .\tt.cmd playground            Open the interactive RTL playground
See docs/windows-and-github.md for GitHub Actions, Pages, and local hardening.
'@
        exit 0
    }

    if ($Command -eq 'viewer') {
        $remoteUrl = & git -C $projectRoot config --get remote.origin.url
        if ($LASTEXITCODE -ne 0 -or -not $remoteUrl) { throw 'Add a GitHub origin and deploy the viewer first. See docs/windows-and-github.md.' }
        if ($remoteUrl -match '^(?:https://github\.com/|git@github\.com:)(?<owner>[^/]+)/(?<repo>[^/]+?)(?:\.git)?/?$') {
            Start-Process "https://$($Matches.owner).github.io/$($Matches.repo)/"
        } else {
            throw 'The origin is not a recognized github.com repository URL.'
        }
        exit 0
    }

    if ($Command -eq 'setup') {
        New-Item -ItemType Directory -Path $toolsDir -Force | Out-Null
        if (-not (Test-Path -LiteralPath (Join-Path $suiteDir 'environment.ps1'))) {
            if ($env:OSS_CAD_SUITE) { throw 'OSS_CAD_SUITE must point to an already extracted suite.' }
            if (-not (Test-Path -LiteralPath $Archive -PathType Leaf)) {
                throw "Archive not found: $Archive. Use .\tt.cmd setup -Archive 'C:\path\to\archive.tgz'."
            }
            Write-Output "Extracting $Archive ..."
            $entries = & tar.exe -tzf $Archive
            Assert-Exit 'Reading archive'
            foreach ($entry in $entries) {
                if ($entry -notmatch '^oss-cad-suite(/|$)' -or $entry -match '(^|/)\.\.(/|$)|\\') {
                    throw "Unexpected archive entry: $entry"
                }
            }
            & tar.exe -xzf $Archive -C $toolsDir
            Assert-Exit 'Extracting OSS CAD Suite'
        }

        # The suite bundles a MinGW Python. Use a separate CPython for the official
        # Windows cocotb wheels; keep both runtimes entirely inside this project.
        [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
        if (-not (Test-Path -LiteralPath $pythonExe)) {
            $pythonZip = Join-Path $toolsDir 'python-3.11.9-embed-amd64.zip'
            $sharedZip = Join-Path $sharedToolsDir 'python-3.11.9-embed-amd64.zip'
            if (Test-Path -LiteralPath $sharedZip) {
                Copy-Item -LiteralPath $sharedZip -Destination $pythonZip -Force
            } elseif (-not (Test-Path -LiteralPath $pythonZip)) {
                Write-Output 'Downloading portable CPython 3.11.9 from python.org ...'
                Invoke-WebRequest -UseBasicParsing -Uri 'https://www.python.org/ftp/python/3.11.9/python-3.11.9-embed-amd64.zip' -OutFile $pythonZip
            }
            Expand-Archive -LiteralPath $pythonZip -DestinationPath $pythonDir -Force
        }
        # The embedded runtime uses an explicit import path, also when loaded by vvp.
        $packagePath = 'Lib\site-packages'
        if ($useSharedPackages) { $packagePath = $sharedPackages }
        @('python311.zip', '.', $packagePath, '..\..\test', 'import site') |
            Set-Content -LiteralPath (Join-Path $pythonDir 'python311._pth') -Encoding ASCII
        if (-not $useSharedPackages -and -not (Test-Path -LiteralPath (Join-Path $pythonDir 'Lib\site-packages\pip\__main__.py'))) {
            $pipBootstrap = Join-Path $toolsDir 'get-pip.py'
            Invoke-WebRequest -UseBasicParsing -Uri 'https://bootstrap.pypa.io/get-pip.py' -OutFile $pipBootstrap
            & $pythonExe $pipBootstrap --disable-pip-version-check --no-warn-script-location
            Assert-Exit 'Installing pip'
        }
        if ($useSharedPackages) {
            Write-Output "Reusing Python packages from $sharedPackages"
        } else {
            & $pythonExe -m pip install --disable-pip-version-check --no-warn-script-location -r (Join-Path $PSScriptRoot 'requirements.txt')
            Assert-Exit 'Installing test dependencies'
        }
        Enable-Suite
        & $pythonExe (Join-Path $PSScriptRoot 'run.py') doctor
        Assert-Exit 'Checking setup'
        Write-Output 'Ready. Run .\tt.cmd test, then .\tt.cmd wave.'
        exit 0
    }

    Enable-Suite
    if ($Command -eq 'wave') {
        if (-not [IO.Path]::IsPathRooted($Waveform)) { $Waveform = Join-Path $projectRoot $Waveform }
        if (-not (Test-Path -LiteralPath $Waveform -PathType Leaf)) {
            throw "Waveform missing: $Waveform. Run .\tt.cmd test first, or pass -Waveform."
        }
        # GTKWave is the interactive window requested by this command.
        Start-Process -FilePath (Join-Path $suiteDir 'bin\gtkwave.exe') -WorkingDirectory $projectRoot -ArgumentList @(
            ('"{0}"' -f $Waveform), ('"{0}"' -f (Join-Path $projectRoot 'test\tb.gtkw'))
        )
        exit 0
    }
    if (-not (Test-Path -LiteralPath $pythonExe)) { throw 'Run .\tt.cmd setup to install the local test runtime.' }
    $runnerArgs = @($Command)
    if ($Command -eq 'playground' -and $NoBrowser) { $runnerArgs += '--no-browser' }
    & $pythonExe (Join-Path $PSScriptRoot 'run.py') @runnerArgs
    Assert-Exit $Command
} catch {
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 1
}
