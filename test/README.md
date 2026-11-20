# Verification

On Windows, run `..\tt.cmd test` from this folder, or `.\tt.cmd test` from the
project root. On Linux, install `requirements.txt` and run `make` here.

The current tests verify the registered-loopback starter, including all byte
values, clock-edge behavior, enable/hold, asynchronous reset/recovery, and unused
bidirectional pins. They also run in the GitHub gate-level job.

When implementing the final application, replace or extend these assertions to
match the specification. Add a Python reference model and protocol drivers when
appropriate. Keep clock/reset stimulus and enough settling time for gate-level
simulation. Add every new RTL file to `info.yaml` and `PROJECT_SOURCES` in the
Makefile.

`test/tb.fst` is the waveform and `test/results.xml` is the JUnit result file.
Inspect them locally with `tt.cmd wave` or download them from the GitHub test
artifacts. Tests must report a nonzero exit status when assertions fail.
