## How it works

NanoGPU has two 8-bit arithmetic lanes and a shared sequencer. A host loads one
to four instructions and reuses that program for compute and graphics commands.
Compute starts each lane with a supplied pair of operands. Graphics starts it
with a pixel's absolute `(x, y)` coordinates on a 64×64 logical canvas. On-chip
counters generate the covered positions of a filled rectangle in row order.
The same two lanes shade neighboring pixels in parallel and a shared output bus
sends their bytes in order. Each lane also has a signed 8-bit multiplier and a
32-bit running sum. The host holds the framebuffer and displays the image.

### Synchronous host interface

| Pins | Function |
| --- | --- |
| `ui_in[7:0]` | Host command and data byte |
| `uo_out[7:0]` | Response byte |
| `uio[0]` | `IN_VALID` from host |
| `uio[1]` | `OUT_READY` from host |
| `uio[2]` | `IN_READY` from chip |
| `uio[3]` | `OUT_VALID` from chip |
| `uio[7:4]` | Unused inputs |

A byte transfers on the rising edge of `clk` when its valid and ready signals
are both high. Use the same clock for host transactions and obey input setup
and hold times. The host holds an input byte and `IN_VALID` until it is accepted.
The chip holds a valid response byte until `OUT_READY` is asserted. Finish
reading the response before sending the next command. `ena` low pauses work
and suppresses ready and valid. Hold `rst_n` low for at least one rising edge to
discard any pending request, clear both running sums, and restore the
one-instruction identity program.

### Commands and instructions

| Request bytes in bus order | Response after request |
| --- | --- |
| `0x10 + (length − 1)`, instruction bytes | One status byte. Length is 1–4. |
| `0x20`, `a0`, `b0`, `a1`, `b1` | Status followed on success by result 0 and result 1. |
| `0x21` | Clear both running sums and return status. |
| `0x22` | Status followed by the current sums, four bytes per lane. |
| `0x23`, count, then `count` groups of `a0`, `b0`, `a1`, `b1` | Add each group's signed products to the sums. Return status followed by the updated sums. Count is 1–255. |
| `0x30`, `x`, `y`, `width`, `height` | Status followed on success by `width × height` grayscale bytes in row order. |

Coordinates must be 0–63, dimensions must be 1–64, and the whole rectangle
must lie inside the canvas. The final lane is skipped for an odd row width.
Status `0` means success, `1` means unknown command, `2` means invalid program,
`3` means invalid rectangle, `4` means zero burst count, and `5` means a `DRAW`
was requested with a program containing `MAC`. An error returns just the
status byte. The chip consumes all bytes of a rejected program load or draw
request. An invalid rectangle takes precedence over the draw's program error.
A rejected program load restores the identity program. A zero burst count
ends the request after its count byte.

The two running sums are signed, two's complement, and wrap modulo `2^32`.
For `READ_ACC` and `MAC_BURST`, read lane 0's four little-endian bytes, then
lane 1's four little-endian bytes. A burst adds to the existing sums and
preserves the loaded program. The host can send each group as soon as
`IN_READY` is high. There is one response for the whole burst.

At the start of each batch the byte register `r` is set to `a` and operand `b`
stays fixed. In graphics mode `a` and `b` are the pixel's `x` and `y`. Each lane
has a separate running sum `acc`. The multiplier interprets both input bytes
as signed two's complement. Each multiply instruction takes two core cycles.

| Byte | Instruction | Update |
| --- | --- | --- |
| `0x00` | `NOP` | Keep `r` |
| `0x01` | `ADD` | `r = (r + b) mod 256` |
| `0x02` | `SUB` | `r = (r − b) mod 256` |
| `0x03` | `XOR` | `r = r XOR b` |
| `0x04` | `MAX` | `r = max(r, b)` using unsigned comparison |
| `0x05` | `SHR1` | `r = r >> 1` with a zero entering the top bit |
| `0x06` | `MUL_SHIFT4` | `r = (signed(r) * signed(b)) >>> 4`, keep the low eight bits |
| `0x07` | `MAC` | `acc = acc + signed(r) * signed(b)`, keep `r` for subsequent instructions. Compute mode only. |

## How to test

Run `.\tt.cmd test` on Windows or `make` from `test/` on Linux. The tests check
rendered pixels and arithmetic against a Python model and cover program reloads,
odd widths, both canvas boundaries, invalid commands, reset, and stalled output.
They also check signed products, accumulator readback, burst handling, and
a two-lane Sobel image filter. The tests run on the physical flow's gate netlist
and save the images and cycle measurements in `test/output/`.

For a host demo, reset the chip and send the following decimal byte sequences.
Read each complete response before proceeding.

1. Send `17, 1, 5` to load `ADD` then `SHR1`. Read status `0`.
2. Send `48, 0, 0, 64, 64` to draw the full canvas. Read status `0`, then store
   4,096 pixel bytes in row order. Pixel `(x, y)` should equal `(x + y) >> 1`.
3. Send `32, 10, 4, 20, 8` to reuse the loaded program for compute. The response
   is `0, 7, 14`.
4. Send `33` to clear both sums. Read status `0`. Send the burst bytes
   `35, 3, 3, 5, 3, 251, 2, 7, 2, 7, 4, 2, 4, 254`. The response is
   `0, 37, 0, 0, 0, 247, 255, 255, 255`, representing sums of `37` and `−9`.

## External hardware

Use a Tiny Tapeout demo board and a synchronous GPIO host, such as the board's
microcontroller or an FPGA. The host collects pixels and can send them to a PC
for display. The initial clock target is 10 MHz. A host may clock the chip more
slowly during bring-up.
