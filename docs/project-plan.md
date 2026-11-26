# NanoGPU architecture

NanoGPU uses the digital `1x2` Sky130A Tiny Tapeout footprint of
161.00 × 225.76 µm and the standard byte-wide pin interface. The target clock
is 10 MHz. The same two lanes run host-loaded byte programs and shade
rectangles on a 64 × 64 canvas. The host controls traffic and holds the
framebuffer. See the [official tile sizes](https://github.com/TinyTapeout/tt-support-tools/blob/main/tech/sky130A/tile_sizes.yaml).

## Datapath

- Each lane has an 8-bit working register and a fixed operand for each job.
  A shared adder in each lane implements add, subtract, and unsigned maximum.
- Two signed 8 × 8 multipliers each produce a full 16-bit product. A register
  splits the product and writeback into two cycles. The same multiplier feeds
  an 8-bit scaled pixel result or a 32-bit running sum.
- Two independent sums retain partial dot products across commands. The host
  can clear or read them. The burst command streams up to 255 operand groups
  through the two multipliers and returns both sums together.
- The vector and graphics commands reuse the same arithmetic. In a rectangle
  draw, coordinate counters seed the lanes and the output bus serializes the
  neighboring pixels. An odd row emits one pixel for the last pair.

See the [instruction set and byte protocol](info.md) for precise operations,
error responses, and a demo packet. The [area study](area-study.md) records
the early arithmetic probes.

## Performance and verification

The burst benchmark measures cycles from the command byte through the last
sum byte. That includes serialized host transfers. The multiplier stage
works on two pairs in parallel while the host bus transfers one byte per cycle.

The [verification report](verification.md) records the original 1×1 build,
the resized baseline, and the checks on the signed MAC implementation. Routed
area, timing, slew, and physical rules determine the available margin. The
measurement artifacts and demos can be reproduced from the source with the
[local and GitHub tooling](windows-and-github.md).
