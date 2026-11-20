/*
 * Copyright (c) 2026 Emron Arsala
 * SPDX-License-Identifier: Apache-2.0
 */
`default_nettype none

module nano_gpu (
    input  wire       clk,
    input  wire       rst_n,
    input  wire       enable,
    input  wire [7:0] in_data,
    input  wire       in_valid,
    output wire       in_ready,
    output reg  [7:0] out_data,
    output wire       out_valid,
    input  wire       out_ready
);
    localparam [2:0] IDLE = 3'd0, LOAD = 3'd1, COLLECT = 3'd2,
                     STATUS = 3'd3, SEED_PIXELS = 3'd4, EXECUTE = 3'd5,
                     OUTPUT_0 = 3'd6, OUTPUT_1 = 3'd7;
    localparam [1:0] NO_JOB = 2'd0, COMPUTE = 2'd1, DRAW = 2'd2;
    localparam [1:0] OK = 2'd0, BAD_COMMAND = 2'd1,
                     BAD_PROGRAM = 2'd2, BAD_RECTANGLE = 2'd3;

    reg [2:0] state;
    reg [1:0] job, status, byte_index;

    // A program is one to four instructions. A missing or rejected program
    // selects a one-instruction identity program without resetting the RAM bits.
    reg [2:0] program_ops [0:3];
    reg [1:0] program_end, pc;
    reg       program_valid;
    wire [2:0] opcode = program_valid ? program_ops[pc] : 3'd0;
    wire [1:0] last_instruction = program_valid ? program_end : 2'd0;

    reg [7:0] result0, result1, operand0, operand1;
    reg [5:0] first_x, last_x, last_y, scan_x, scan_y;
    wire [5:0] lane1_x = scan_x + 6'd1;
    wire [6:0] next_pair_x = {1'b0, scan_x} + 7'd2;
    wire       last_pair_in_row = next_pair_x > {1'b0, last_x};
    wire       second_pixel_valid = scan_x < last_x;

    // Geometry uses an exclusive end up to 64. A widened sum rejects overflow
    // before we keep the six-bit inclusive end for rasterization.
    wire [5:0] extent_start = (byte_index == 2'd2) ? first_x : scan_y;
    wire [7:0] extent_end = {2'b0, extent_start} + {1'b0, in_data[6:0]};
    wire       bad_extent = in_data[7] || (in_data == 0) || (extent_end > 8'd64);
    wire [5:0] inclusive_end = extent_end[5:0] - 6'd1;

    // Both graphics and compute use this same pair of arithmetic lanes.
    wire [7:0] b0 = (job == DRAW) ? {2'b0, scan_y} : operand0;
    wire [7:0] b1 = (job == DRAW) ? {2'b0, scan_y} : operand1;
    wire [7:0] next_result0, next_result1;
    nano_lane lane0 (.opcode(opcode), .accumulator(result0), .operand(b0), .result(next_result0));
    nano_lane lane1 (.opcode(opcode), .accumulator(result1), .operand(b1), .result(next_result1));

    assign in_ready = enable && rst_n && (state == IDLE || state == LOAD || state == COLLECT);
    assign out_valid = enable && rst_n && (state == STATUS || state == OUTPUT_0 || state == OUTPUT_1);

    always @(*) begin
        case (state)
            STATUS:   out_data = {6'b0, status};
            OUTPUT_0: out_data = result0;
            OUTPUT_1: out_data = result1;
            default:  out_data = 8'd0;
        endcase
    end

    always @(posedge clk) begin
        if (!rst_n) begin
            state <= IDLE;
            program_valid <= 1'b0;
        end else if (enable) begin
            case (state)
                IDLE: if (in_valid) begin
                    byte_index <= 0;
                    status <= OK;
                    job <= NO_JOB;
                    if (in_data[7:2] == 6'b000100) begin
                        program_end <= in_data[1:0];
                        state <= LOAD;
                    end else if (in_data == 8'h20 || in_data == 8'h30) begin
                        job <= (in_data == 8'h20) ? COMPUTE : DRAW;
                        state <= COLLECT;
                    end else begin
                        status <= BAD_COMMAND;
                        state <= STATUS;
                    end
                end

                LOAD: if (in_valid) begin
                    program_ops[byte_index] <= in_data[2:0];
                    if (in_data > 8'd5)
                        status <= BAD_PROGRAM;
                    byte_index <= byte_index + 2'd1;
                    if (byte_index == program_end) begin
                        program_valid <= (status == OK) && (in_data <= 8'd5);
                        state <= STATUS;
                    end
                end

                COLLECT: if (in_valid) begin
                    if (job == COMPUTE) begin
                        case (byte_index)
                            2'd0: result0 <= in_data;
                            2'd1: operand0 <= in_data;
                            2'd2: result1 <= in_data;
                            2'd3: operand1 <= in_data;
                        endcase
                    end else begin
                        case (byte_index)
                            2'd0: begin
                                first_x <= in_data[5:0];
                                scan_x <= in_data[5:0];
                            end
                            2'd1: scan_y <= in_data[5:0];
                            2'd2: last_x <= inclusive_end;
                            2'd3: last_y <= inclusive_end;
                        endcase
                        if ((byte_index[1] && bad_extent) ||
                            (!byte_index[1] && in_data[7:6] != 0))
                            status <= BAD_RECTANGLE;
                    end
                    byte_index <= byte_index + 2'd1;
                    if (byte_index == 2'd3)
                        state <= STATUS;
                end

                STATUS: if (out_ready) begin
                    pc <= 0;
                    if (status != OK || job == NO_JOB)
                        state <= IDLE;
                    else if (job == COMPUTE)
                        state <= EXECUTE;
                    else
                        state <= SEED_PIXELS;
                end

                SEED_PIXELS: begin
                    result0 <= {2'b0, scan_x};
                    result1 <= {2'b0, lane1_x};
                    pc <= 0;
                    state <= EXECUTE;
                end

                EXECUTE: begin
                    result0 <= next_result0;
                    result1 <= next_result1;
                    pc <= pc + 2'd1;
                    if (pc == last_instruction)
                        state <= OUTPUT_0;
                end

                OUTPUT_0, OUTPUT_1: if (out_ready) begin
                    if (state == OUTPUT_0 && (job == COMPUTE || second_pixel_valid)) begin
                        state <= OUTPUT_1;
                    end else if (job == COMPUTE || (last_pair_in_row && scan_y == last_y)) begin
                        state <= IDLE;
                    end else begin
                        if (last_pair_in_row) begin
                            scan_y <= scan_y + 6'd1;
                            scan_x <= first_x;
                        end else begin
                            scan_x <= next_pair_x[5:0];
                        end
                        state <= SEED_PIXELS;
                    end
                end

                default: state <= IDLE;
            endcase
        end
    end
endmodule

module nano_lane (
    input  wire [2:0] opcode,
    input  wire [7:0] accumulator,
    input  wire [7:0] operand,
    output reg  [7:0] result
);
    // Subtraction and unsigned comparison both use A + ~B + 1. The
    // ninth sum bit indicates no borrow, so MAX also reuses the adder.
    wire subtract = (opcode == 3'd2) || (opcode == 3'd4);
    wire [7:0] adder_b = operand ^ {8{subtract}};
    wire [8:0] sum = {1'b0, accumulator} + {1'b0, adder_b} + {8'b0, subtract};

    always @(*) begin
        case (opcode)
            3'd1, 3'd2: result = sum[7:0];
            3'd3: result = accumulator ^ operand;
            3'd4: result = sum[8] ? accumulator : operand;
            3'd5: result = accumulator >> 1;
            default: result = accumulator;
        endcase
    end
endmodule

`default_nettype wire
