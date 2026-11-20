## How it works

The current starter is an enabled eight-bit register. On a rising clock edge,
`DATA_OUT[7:0]` captures `DATA_IN[7:0]` while `ena` is high. When `ena` is low,
the output holds its previous value. Driving `rst_n` low clears the output
asynchronously. All bidirectional pins remain inputs; their output data is zero.

This verifies the project infrastructure. Replace this description, the pinout,
and the tests when implementing the selected final application.

The initial target is one digital tile at 10 MHz. The configured tile size is a
target; final fit, timing, and physical checks must be established by the GDS flow.

## How to test

Run `.\tt.cmd test` on Windows, or `make` from `test/` on Linux. The starter tests
check all 256 data values, clock-edge behavior, enable/hold, asynchronous reset,
reset recovery, and unused bidirectional pin controls. The GitHub gate-level job
runs the same test module against the generated netlist.

For a hardware demo of the starter, select the design, assert and release reset,
set the eight input pins to a byte, and provide the clock. The output pins show
the byte captured on the rising edge. Update these directions for the final design.

## External hardware

For the starter: a Tiny Tapeout demo board or another source of digital input
signals and clock, plus LEDs or a logic analyzer to observe the outputs.
