/*
 * Tiny Tapeout interface derived from the Apache-2.0 project template.
 * Copyright (c) 2026 Emron Arsala
 * SPDX-License-Identifier: Apache-2.0
 */
`default_nettype none

module tt_um_sul_tan1_digital (
    input  wire [7:0] ui_in,
    output wire [7:0] uo_out,
    input  wire [7:0] uio_in,
    output wire [7:0] uio_out,
    output wire [7:0] uio_oe,
    input  wire       ena,
    input  wire       clk,
    input  wire       rst_n
);

    digital_core core (
        .clk      (clk),
        .rst_n    (rst_n),
        .enable   (ena),
        .data_in  (ui_in),
        .data_out (uo_out)
    );

    // The starter uses only dedicated input and output pins.
    assign uio_out = 8'b0;
    assign uio_oe  = 8'b0;
    wire _unused = &{uio_in, 1'b0};

endmodule

`default_nettype wire
