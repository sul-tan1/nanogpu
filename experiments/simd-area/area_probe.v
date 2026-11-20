// Copyright (c) 2026 Emron Arsala
// SPDX-License-Identifier: Apache-2.0
// Exploration only. This is not the Tiny Tapeout top or a complete processor.
`default_nettype none
module area_probe #(
    parameter WIDTH = 8,
    parameter LANES = 2,
    parameter ENABLE_MUL = 0,
    parameter ENABLE_MAC = 0
) (
    input wire clk,
    input wire rst_n,
    input wire [LANES-1:0] load_a,
    input wire [LANES-1:0] load_b,
    input wire [WIDTH-1:0] data_in,
    input wire execute,
    input wire [2:0] opcode,
    output wire [LANES*2*WIDTH-1:0] result
);
    genvar lane;
    generate
        for (lane = 0; lane < LANES; lane = lane + 1) begin : lanes
            reg [WIDTH-1:0] a, b;
            reg [2*WIDTH-1:0] r;
            wire [2*WIDTH-1:0] a_ext = {{WIDTH{1'b0}}, a};
            wire [2*WIDTH-1:0] b_ext = {{WIDTH{1'b0}}, b};
            wire [2*WIDTH-1:0] product = ENABLE_MUL ? a * b : {2*WIDTH{1'b0}};
            always @(posedge clk or negedge rst_n) begin
                if (!rst_n) begin
                    a <= 0;
                    b <= 0;
                    r <= 0;
                end else begin
                    if (load_a[lane]) a <= data_in;
                    if (load_b[lane]) b <= data_in;
                    if (execute) begin
                        case (opcode)
                            3'd0: r <= a_ext + b_ext;
                            3'd1: r <= a_ext - b_ext;
                            3'd2: r <= (a > b) ? a_ext : b_ext;
                            3'd3: r <= a_ext >> 1;
                            3'd4: r <= product;
                            3'd5: r <= ENABLE_MAC ? r + product : {2*WIDTH{1'b0}};
                            3'd6: r <= a_ext ^ b_ext;
                            3'd7: r <= 0;
                        endcase
                    end
                end
            end
            assign result[lane*2*WIDTH +: 2*WIDTH] = r;
        end
    endgenerate
endmodule
`default_nettype wire
