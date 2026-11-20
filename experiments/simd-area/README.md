# Cell-area exploration

This probe estimates SIMD datapath areas before choosing the complete architecture.
It is separate from the production `src/` starter.

See [method, results, limitations, and reproduction](../../docs/area-study.md).
On Windows, run `powershell.exe -NoProfile -ExecutionPolicy Bypass -File experiments\simd-area\run.ps1`
from the project root after providing the Liberty file described there.
