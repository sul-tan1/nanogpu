# Verification

On Windows, run `..\tt.cmd test` from this folder, or `.\tt.cmd test` from the
project root. On Linux, install `requirements.txt` and run `make` here.

The same tests run on RTL and the Sky130 gate netlist. They exercise the chip
through the actual ready/valid pins and compare results to an independent Python
model. The full-frame test and a shaded inset produce `test/output/nanogpu.png`.

Cases cover program reuse across both modes, wraparound, lane order, dimensions
at the canvas boundary, odd row widths, malformed packets, input gaps, output
backpressure, pause on disable, and reset during a draw. The simulation samples
after a 50 ns settling interval so the same bus driver works with gate delays.

`test/tb.fst` is the waveform and `test/results.xml` is the JUnit result file.
Inspect them locally with `tt.cmd wave` or download them from the GitHub test
artifacts. Tests must report a nonzero exit status when assertions fail.
