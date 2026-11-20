/*
 * Copyright (c) 2026 Emron Arsala
 * SPDX-License-Identifier: Apache-2.0
 */
`default_nettype none

// Starter behavior: an enabled 8-bit register with an active-low reset.
// Replace or extend this core when the final project's specification is chosen.
module digital_core (
    input  wire       clk,
    input  wire       rst_n,
    input  wire       enable,
    input  wire [7:0] data_in,
    output reg  [7:0] data_out
);

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            data_out <= 8'b0;
        else if (enable)
            data_out <= data_in;
    end

endmodule

`default_nettype wire
