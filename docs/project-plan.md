# Final-project plan

## Current status

Infrastructure starter: a registered data path, reset/enable tests, local Windows
tools, lint/synthesis commands, and Tiny Tapeout workflows. Final behavior is
pending selection. This is a fresh local repository, separate from the ALU example.

## Candidate scope

Choose one core function and complete its verification and physical implementation
before adding features. For this area budget, avoid making a processor, a large
memory, or a collection of unrelated peripherals the first milestone.

| Direction | Small first implementation | Potential extension after measuring area |
| --- | --- | --- |
| UART controller | 8N1 TX/RX, explicit handshake, synchronized RX, framing-error detection, one baud rate | Very small receive FIFO, overrun flag, selectable divider |
| SPI controller | One chip select, mode 0, eight-bit transactions, programmable clock divider, ready/busy handshake | Another mode or short transaction queue |
| PWM/audio generator | Clock divider, duty-cycle register, deterministic waveform output | Small phase accumulator or simple noise source |

The UART is a useful first candidate because it connects state machines, counters,
input synchronization, interfaces, and protocol verification in one observable
demo. This is an engineering recommendation, not a guarantee of area fit. Start
without a FIFO and measure the hardened design before expanding it.

## Development order

1. Specify the behavior, pin map, clock, reset, handshakes, and error cases.
2. Implement one small module at a time and add tests for that behavior.
3. Integrate the Tiny Tapeout wrapper; update both source lists and the datasheet.
4. Run local lint, functional tests, and synthesis before pushing.
5. Run the GitHub GDS, precheck, and gate-level tests; inspect timing and utilization.
6. Demonstrate the design with a reproducible script and waveform/logic-analyzer capture.
7. Add optional features only while the physical results leave room.

## Evidence to retain

- A stable behavioral specification and a small architecture diagram.
- Directed tests plus reproducible randomized tests appropriate to the protocol.
- Reset, boundary, and error-case tests, with failing cases repaired in the RTL.
- A link to the exact commit with passing RTL, GDS, precheck, and gate-level checks.
- Measured area/utilization, target clock and timing slack, and the layout image.
- A short hardware or simulation demo and a clear explanation of design tradeoffs.

## Resume wording after completion

Use measured results and name the actual contribution. For example:

> Designed and verified a [function] in Verilog; implemented [features], built
> cocotb tests for [cases], and hardened the design into one Sky130 Tiny Tapeout
> tile with [measured timing/area result].

Fill those fields only after the corresponding implementation and checks exist.
Use "taped out" after submission, and "silicon-tested" after testing the fabricated chip.

## Constraints reference

The [official template](https://github.com/TinyTapeout/ttsky-verilog-template/blob/main/info.yaml)
defines the `1x1` option and fixed Tiny Tapeout pin groups. The
[Tiny Tapeout FAQ](https://tinytapeout.com/faq/)
explains why tile utilization and physical implementation must be checked. Keep
this workshop's matching `ttsky26d` workflow references until deliberately
migrating the project to another shuttle template.
