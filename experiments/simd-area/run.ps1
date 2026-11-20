$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$suite = Join-Path $projectRoot '.tools\oss-cad-suite'
if ($env:OSS_CAD_SUITE) {
    $suite = [IO.Path]::GetFullPath($env:OSS_CAD_SUITE)
} elseif (-not (Test-Path -LiteralPath (Join-Path $suite 'environment.ps1'))) {
    $sharedTools = [IO.Path]::GetFullPath((Join-Path $projectRoot '..\tqt_tt_workshop_ex\.tools'))
    if ($env:TT_SHARED_TOOLS) { $sharedTools = [IO.Path]::GetFullPath($env:TT_SHARED_TOOLS) }
    $suite = Join-Path $sharedTools 'oss-cad-suite'
}
$env:YOSYSHQ_ROOT = $suite
. (Join-Path $suite 'environment.ps1')
& (Join-Path $projectRoot '.tools\python\python.exe') (Join-Path $PSScriptRoot 'sweep.py') @args
exit $LASTEXITCODE
