/*
 * Tiny Tapeout interface derived from the Apache-2.0 project template.
 * Copyright (c) 2026 Emron Arsala
 * SPDX-License-Identifier: Apache-2.0
 */
`default_nettype none

module tt_um_sul_tan1_nanogpu (
    input  wire [7:0] ui_in,
    output wire [7:0] uo_out,
    input  wire [7:0] uio_in,
    output wire [7:0] uio_out,
    output wire [7:0] uio_oe,
    input  wire       ena,
    input  wire       clk,
    input  wire       rst_n
);

    wire in_ready, out_valid;
    nano_gpu core (
        .clk      (clk),
        .rst_n    (rst_n),
        .enable   (ena),
        .in_data   (ui_in),
        .in_valid  (uio_in[0]),
        .in_ready  (in_ready),
        .out_data  (uo_out),
        .out_valid (out_valid),
        .out_ready (uio_in[1])
    );

    assign uio_out = {4'b0, out_valid, in_ready, 2'b0};
    assign uio_oe  = 8'b00001100;
    wire _unused = &{uio_in[7:2], 1'b0};

endmodule

`default_nettype wire
