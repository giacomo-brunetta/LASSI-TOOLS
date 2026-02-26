// verilator lint_off BLKANDNBLK
// verilator lint_off BLKSEQ

`timescale 1ns / 1ps
// CONSTANTS DECLARATION
`define MAX_COMMENT_LENGTH 1000
`define INIT_TIME 100

`define NDEBUG


`ifdef __M64
typedef longint unsigned ptr_t;
`else
typedef int unsigned ptr_t;
`endif

// 
// Politecnico di Milano
// Code created using PandA - Version: PandA 2024.10 - Revision c2ba6936ca2ed63137095fea0b630a1c66e20e63 - Date 2026-02-23T23:56:58
// Bambu executed with: bambu -v3 --print-dot -lm --soft-float --compiler=I386_CLANG16 --device=xc7z020-1clg484 --clock-period=10 --experimental-setup=BAMBU-BALANCED-MP --channels-number=2 --memory-allocation-policy=ALL_BRAM --disable-function-proxy --generate-tb=../../forward_kernel_testbench.c --simulate --simulator=VERILATOR --verilator-parallel --top-fname=forward_kernel input.ll 
// 
// Send any bug to: panda-info@polimi.it
// ************************************************************************
// The following text holds for all the components tagged with PANDA_LGPLv3.
// They are all part of the BAMBU/PANDA IP LIBRARY.
// This library is free software; you can redistribute it and/or
// modify it under the terms of the GNU Lesser General Public
// License as published by the Free Software Foundation; either
// version 3 of the License, or (at your option) any later version.
// 
// This library is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
// Lesser General Public License for more details.
// 
// You should have received a copy of the GNU Lesser General Public
// License along with the PandA framework; see the files COPYING.LIB
// If not, see <http://www.gnu.org/licenses/>.
// ************************************************************************


`ifdef __ICARUS__
  `define _SIM_HAVE_CLOG2
`endif
`ifdef VERILATOR
  `define _SIM_HAVE_CLOG2
`endif
`ifdef MODEL_TECH
  `define _SIM_HAVE_CLOG2
`endif
`ifdef VCS
  `define _SIM_HAVE_CLOG2
`endif
`ifdef NCVERILOG
  `define _SIM_HAVE_CLOG2
`endif
`ifdef XILINX_SIMULATOR
  `define _SIM_HAVE_CLOG2
`endif
`ifdef XILINX_ISIM
  `define _SIM_HAVE_CLOG2
`endif

// This component is part of the BAMBU/PANDA IP LIBRARY
// Copyright (C) 2004-2024 Politecnico di Milano
// Author(s): Fabrizio Ferrandi <fabrizio.ferrandi@polimi.it>
// License: PANDA_LGPLv3
`timescale 1ns / 1ps
module join_signal(in1,
  out1);
  parameter BITSIZE_in1=1, PORTSIZE_in1=2,
    BITSIZE_out1=1;
  // IN
  input [(PORTSIZE_in1*BITSIZE_in1)+(-1):0] in1;
  // OUT
  output [BITSIZE_out1-1:0] out1;
  
  generate
  genvar i1;
  for (i1=0; i1<PORTSIZE_in1; i1=i1+1)
    begin : L1
      assign out1[(i1+1)*(BITSIZE_out1/PORTSIZE_in1)-1:i1*(BITSIZE_out1/PORTSIZE_in1)] = in1[(i1+1)*BITSIZE_in1-1:i1*BITSIZE_in1];
    end
  endgenerate
endmodule

// This component is part of the BAMBU/PANDA IP LIBRARY
// Copyright (C) 2004-2024 Politecnico di Milano
// Author(s): Fabrizio Ferrandi <fabrizio.ferrandi@polimi.it>
// License: PANDA_LGPLv3
`timescale 1ns / 1ps
module split_signal(in1,
  out1);
  parameter BITSIZE_in1=1,
    BITSIZE_out1=1, PORTSIZE_out1=2;
  // IN
  input [BITSIZE_in1-1:0] in1;
  // OUT
  output [(PORTSIZE_out1*BITSIZE_out1)+(-1):0] out1;
  assign out1 = in1;
endmodule

// This component is part of the BAMBU/PANDA IP LIBRARY
// Copyright (C) 2023-2024 Politecnico di Milano
// Author(s): Michele Fiorito <michele.fiorito@polimi.it>
// License: PANDA_LGPLv3
`timescale 1ns / 1ps
module TestbenchDUT(clock,
  reset,
  start_port,
  P0,
  P1,
  P2,
  M_Rdata_ram,
  M_DataRdy,
  done_port,
  Mout_oe_ram,
  Mout_we_ram,
  Mout_addr_ram,
  Mout_Wdata_ram,
  Mout_data_ram_size);
  // IN
  input clock;
  input reset;
  input start_port;
  input [31:0] P0;
  input [31:0] P1;
  input [31:0] P2;
  input [63:0] M_Rdata_ram;
  input [1:0] M_DataRdy;
  // OUT
  output done_port;
  output [1:0] Mout_oe_ram;
  output [1:0] Mout_we_ram;
  output [63:0] Mout_addr_ram;
  output [63:0] Mout_Wdata_ram;
  output [11:0] Mout_data_ram_size;
  
  
  forward_kernel top(
    .clock(clock),
    .reset(reset),
    .start_port(start_port),
    .P0(P0),
    .P1(P1),
    .P2(P2),
    .M_Rdata_ram(M_Rdata_ram),
    .M_DataRdy(M_DataRdy),
    .done_port(done_port),
    .Mout_oe_ram(Mout_oe_ram),
    .Mout_we_ram(Mout_we_ram),
    .Mout_addr_ram(Mout_addr_ram),
    .Mout_Wdata_ram(Mout_Wdata_ram),
    .Mout_data_ram_size(Mout_data_ram_size));

endmodule

// This component is part of the BAMBU/PANDA IP LIBRARY
// Copyright (C) 2023-2024 Politecnico di Milano
// Author(s): Michele Fiorito <michele.fiorito@polimi.it>
// License: PANDA_LGPLv3
`timescale 1ns / 1ps
module TestbenchFSM(clock,
  done_port,
  reset,
  setup_port,
  start_port);
  parameter RESFILE="results.txt",
    RESET_ACTIVE=0,
    RESET_CYCLES=1,
    RESET_ALWAYS=0,
    CLOCK_PERIOD=2.0,
    MAX_SIM_CYCLES=200000000;
  // IN
  input clock;
  input done_port;
  // OUT
  output reset;
  output setup_port;
  output start_port;
  `ifdef VERILATOR
  timeunit 1ps;
  timeprecision 1ps;
  `endif
  
  import "DPI-C" function int unsigned m_next(input int unsigned state);
  import "DPI-C" function int m_fini();
  
  localparam [6:0] 
    STATE_READY   =7'b0000001,
    STATE_SETUP   =7'b0000010,
    STATE_RUNNING =7'b0000100,
    STATE_END     =7'b0001000,
    STATE_ERROR   =7'b0010000,
    STATE_ABORT   =7'b0100000,
    SIM_DONE      =7'b1000000;
  reg [$bits(STATE_READY)-1:0] state, state_next, state_succ, state_succ_next;
  
  reg rst, rst_next, setup, setup_next, start, start_next;
  integer rst_count, rst_count_next;
  time over_time;
  
  initial
  begin
    // Open file results will be written
    automatic integer res_file;
    res_file = $fopen(RESFILE, "w");
    if (res_file == 0)
    begin
      $display("ERROR - Error opening the res_file");
      $finish;// Terminate
    end
    $fwrite(res_file, "");
    $fclose(res_file);
    
    state = STATE_READY;
    state_next = STATE_READY;
    state_succ = STATE_READY;
    state_succ_next = STATE_READY;
    rst = RESET_ACTIVE;
    rst_next = RESET_ACTIVE;
    rst_count = RESET_CYCLES;
    rst_count_next = RESET_CYCLES;
    setup = 0;
    setup_next = 0;
    start = 0;
    start_next = 0;
    over_time = 0;
    
    $display("Results file: %s", RESFILE);
    $display("Reset active: %0s", RESET_ACTIVE ? "HIGH" : "LOW");
  end
  
  assign reset = rst;
  assign setup_port = setup;
  assign start_port = start;
  
  always @(posedge clock)
  begin
    state <= state_next;
    state_succ <= state_succ_next;
    rst <= rst_next;
    rst_count <= rst_count_next;
    setup <= setup_next;
    start <= start_next;
    case(state_next)
    STATE_READY:
      begin
        automatic integer unsigned next_state = m_next(STATE_READY);
        `ifndef NDEBUG
        $display("Sim: next state: %0d (retval: %0d)", next_state[$bits(state_succ)-1:0], next_state[15:8]);
        `endif
        state_succ <= next_state[$bits(state_succ)-1:0];
      end
    STATE_SETUP:
      begin
        automatic time start_time = $time + CLOCK_PERIOD;
        automatic time start_cycle = $rtoi($itor(start_time)/CLOCK_PERIOD);
        automatic integer res_file;
        if(setup_next)
        begin
          res_file = $fopen(RESFILE, "a");
          $fwrite(res_file, "%0d|", start_time);
          $fclose(res_file);
          `ifndef NDEBUG
          $display("Sim: Argument setup\nSim: Simulation started at cycle %0d", start_cycle);
          `endif
        end
        over_time <= start_cycle + MAX_SIM_CYCLES;
      end
    STATE_RUNNING:
      begin
        automatic time curr_cycle = $rtoi($itor($time)/CLOCK_PERIOD);
        if(curr_cycle >= over_time)
        begin
          automatic integer res_file;
          res_file = $fopen(RESFILE, "a");
          $fwrite(res_file, "X");
          $fclose(res_file);
          $display("Sim: Simulation exceeds %0d cycles", MAX_SIM_CYCLES);
          $finish;
        end
      end
    SIM_DONE:
      begin
        automatic time curr_time = $time;
        automatic time curr_cycle = $rtoi($itor(curr_time)/CLOCK_PERIOD);
        automatic integer res_file;
        res_file = $fopen(RESFILE, "a");
        $fwrite(res_file, "%0d,", curr_time);
        $fclose(res_file);
        `ifndef NDEBUG
        $display("Sim: DUT port writeback\nSim: Simulation ended at cycle %0d", curr_cycle);
        `endif
      end
    STATE_END:
      begin
        automatic integer r = m_fini();
        automatic integer res_file;
        res_file = $fopen(RESFILE, "a");
        $fwrite(res_file, "\n%0d\n", r[15:8]);
        $display("Sim: Testbench returned: %0d", r[15:8]);
        $fclose(res_file);
        $finish;
      end
    STATE_ABORT:
      begin
        automatic integer r = m_fini();
        automatic integer res_file;
        res_file = $fopen(RESFILE, "a");
        $fwrite(res_file, "\nA\n");
        $display("Sim: Testbench aborted");
        $fclose(res_file);
        $finish;
      end
    default:
      begin
      end
    endcase
  end
  
  always @(*)
  begin
    rst_next = rst;
    rst_count_next = rst_count;
    setup_next = setup;
    start_next = start;
    state_next = state;
    state_succ_next = state_succ;
    case(state)
    STATE_READY:
      begin
        state_next = state_succ;
        if(state_succ == STATE_SETUP)
        begin
          if(RESET_ALWAYS || rst_count > 0)
          begin
            rst_next = RESET_ACTIVE;
            rst_count_next = RESET_CYCLES;
          end
          else
          begin
            rst_count_next = 1;
          end
        end
      end
    STATE_SETUP:
      begin
        if(rst_count > 1)
        begin
          setup_next = rst_count == 0;
          rst_next = RESET_ACTIVE;
          rst_count_next = rst_count - 1;
        end
        else if(rst_count == 1)
        begin
          setup_next = 1;
          rst_next = ~RESET_ACTIVE;
          rst_count_next = 0;
        end
        else
        begin
          state_next = STATE_RUNNING;
          setup_next = 0;
          start_next = 1;
        end
      end
    STATE_RUNNING:
      begin
        start_next = 0;
        if(done_port)
        begin
          state_next = SIM_DONE;
        end
      end
    SIM_DONE:
      begin
        // A clock cycle must pass to allow interface modules 
        // finalization operations
        state_next = STATE_READY;
      end
    STATE_END:
      begin
      end
    STATE_ABORT:
      begin
      end
    default:
      begin
        state_next = STATE_READY;
      end
    endcase
  end
endmodule

// This component is part of the BAMBU/PANDA IP LIBRARY
// Copyright (C) 2023-2024 Politecnico di Milano
// Author(s): Michele Fiorito <michele.fiorito@polimi.it>
// License: PANDA_LGPLv3
`timescale 1ns / 1ps
module if_utils();
  parameter ID=0,
    BITSIZE_data=32;
  
  import "DPI-C" function int m_read (input byte unsigned id, output logic [4095:0] data, input shortint unsigned bitsize, input ptr_t addr, input byte unsigned shift);
  import "DPI-C" function int m_write (input byte unsigned id, input logic [4095:0] data, input shortint unsigned bitsize, input ptr_t addr, input byte unsigned shift);
  import "DPI-C" function int m_state (input byte unsigned id, input int data);
  
  function automatic integer log2;
    input integer value;
    `ifdef _SIM_HAVE_CLOG2
      log2 = $clog2(value);
    `else
      automatic integer temp_value = value-1;
      for (log2=0; temp_value > 0; log2=log2+1)
        temp_value = temp_value >> 1;
    `endif
  endfunction
  
  localparam BITSIZE_strobe=log2(BITSIZE_data) > 3 ? (1<<(log2(BITSIZE_data)-3)) : 1;
  
  function automatic [BITSIZE_data-1:0] read();
    automatic reg [4095:0] _data = 0;
    void'(m_read(ID, _data, BITSIZE_data, 0, 0));
    return _data[BITSIZE_data-1:0];
  endfunction
  
  function automatic [BITSIZE_data-1:0] read_a(input ptr_t addr);
    automatic reg [4095:0] _data = 0;
    void'(m_read(ID, _data, BITSIZE_data, addr, 0));
    return _data[BITSIZE_data-1:0];
  endfunction
  
  function automatic [BITSIZE_data-1:0] read_i(output int info);
    automatic reg [4095:0] _data = 0;
    info = m_read(ID, _data, BITSIZE_data, 0, 0);
    return _data[BITSIZE_data-1:0];
  endfunction
  
  function automatic [BITSIZE_data-1:0] read_ai(input ptr_t addr, output int info);
    automatic reg [4095:0] _data = 0;
    info = m_read(ID, _data, BITSIZE_data, addr, 0);
    return _data[BITSIZE_data-1:0];
  endfunction
  
  function automatic [BITSIZE_data-1:0] pop(output int info);
    automatic reg [4095:0] _data = 0;
    info = m_read(ID, _data, BITSIZE_data, 0, 1);
    return _data[BITSIZE_data-1:0];
  endfunction
  
  function automatic int write(input logic [BITSIZE_data-1:0] data);
    automatic reg [4095:0] _data = 0;
    _data[BITSIZE_data-1:0] = data;
    return m_write(ID, _data, BITSIZE_data, 0, 0);
  endfunction
  
  function automatic int write_a(input logic [BITSIZE_data-1:0] data, input ptr_t addr);
    automatic reg [4095:0] _data = 0;
    _data[BITSIZE_data-1:0] = data;
    return m_write(ID, _data, BITSIZE_data, addr, 0);
  endfunction
  
  function automatic int write_sa(input logic [BITSIZE_data-1:0] data, input shortint unsigned bitsize, input ptr_t addr);
    automatic reg [4095:0] _data = 0;
    _data[BITSIZE_data-1:0] = data;
    return m_write(ID, _data, bitsize, addr, 0);
  endfunction
  
  function automatic int write_strobe(input logic [BITSIZE_data-1:0] data, input logic [BITSIZE_strobe-1:0] strobe, input ptr_t addr);
    automatic shortint unsigned size = 0;
    
    while(strobe != 0 && !strobe[0])
    begin
      addr = addr + 1;
      strobe = strobe >> 1;
    end
    while(strobe[0])
    begin
      size = size + 8;
      strobe = strobe >> 1;
    end
    if(strobe != 0)
    begin
      $display("Scattered strobe write operations not supported");
      $finish;
    end
  
    return write_sa(data, size, addr);
  endfunction
  
  function automatic int push(input logic [BITSIZE_data-1:0] data);
    automatic reg [4095:0] _data = 0;
    _data[BITSIZE_data-1:0] = data;
    return m_write(ID, _data, BITSIZE_data, 0, 1);
  endfunction
  
  function automatic int state(input int data);
    return m_state(ID, data);
  endfunction
endmodule

// This component is part of the BAMBU/PANDA IP LIBRARY
// Copyright (C) 2023-2024 Politecnico di Milano
// Author(s): Michele Fiorito <michele.fiorito@polimi.it>
// License: PANDA_LGPLv3
`timescale 1ns / 1ps
module TestbenchMEMMinimal(clock,
  reset,
  done_port,
  M_DataRdy,
  M_Rdata_ram,
  Mout_oe_ram,
  Mout_we_ram,
  Mout_addr_ram,
  Mout_data_ram_size,
  Mout_Wdata_ram,
  Mout_back_pressure,
  Sout_DataRdy,
  Sout_Rdata_ram,
  S_oe_ram,
  S_we_ram,
  S_addr_ram,
  S_data_ram_size,
  S_Wdata_ram);
  parameter index=0,
    MEM_DELAY_READ=2,
    MEM_DELAY_WRITE=1,
    base_addr=1073741824,
    MEM_DUMP=0,
    MEM_DUMP_FILE="memdump.csv",
    QUEUE_SIZE=4,
    BITSIZE_M_DataRdy=1,
    BITSIZE_M_Rdata_ram=8,
    BITSIZE_Mout_oe_ram=1,
    BITSIZE_Mout_we_ram=1,
    BITSIZE_Mout_addr_ram=1,
    BITSIZE_Mout_data_ram_size=4,
    BITSIZE_Mout_Wdata_ram=8,
    BITSIZE_Mout_back_pressure=1,
    BITSIZE_Sout_DataRdy=1,
    BITSIZE_Sout_Rdata_ram=8,
    BITSIZE_S_oe_ram=1,
    BITSIZE_S_we_ram=1,
    BITSIZE_S_addr_ram=1,
    BITSIZE_S_data_ram_size=4,
    BITSIZE_S_Wdata_ram=8;
  // IN
  input clock;
  input reset;
  input done_port;
  input [BITSIZE_Mout_oe_ram-1:0] Mout_oe_ram;
  input [BITSIZE_Mout_we_ram-1:0] Mout_we_ram;
  input [BITSIZE_Mout_addr_ram-1:0] Mout_addr_ram;
  input [BITSIZE_Mout_data_ram_size-1:0] Mout_data_ram_size;
  input [BITSIZE_Mout_Wdata_ram-1:0] Mout_Wdata_ram;
  input [BITSIZE_Sout_DataRdy-1:0] Sout_DataRdy;
  input [BITSIZE_Sout_Rdata_ram-1:0] Sout_Rdata_ram;
  // OUT
  output [BITSIZE_M_DataRdy-1:0] M_DataRdy;
  output [BITSIZE_M_Rdata_ram-1:0] M_Rdata_ram;
  output [BITSIZE_Mout_back_pressure-1:0] Mout_back_pressure;
  output [BITSIZE_S_oe_ram-1:0] S_oe_ram;
  output [BITSIZE_S_we_ram-1:0] S_we_ram;
  output [BITSIZE_S_addr_ram-1:0] S_addr_ram;
  output [BITSIZE_S_data_ram_size-1:0] S_data_ram_size;
  output [BITSIZE_S_Wdata_ram-1:0] S_Wdata_ram;
  
  function automatic integer log2;
    input integer value;
    `ifdef _SIM_HAVE_CLOG2
      log2 = $clog2(value);
    `else
      automatic integer temp_value = value-1;
      for (log2=0; temp_value > 0; log2=log2+1)
        temp_value = temp_value >> 1;
    `endif
  endfunction
  
  localparam MEM_DELAY_MAX= MEM_DELAY_READ > MEM_DELAY_WRITE ? MEM_DELAY_READ : MEM_DELAY_WRITE,
    ACTIVE_READ= MEM_DELAY_READ > 1 ? (MEM_DELAY_READ-2) : 0,
    ACTIVE_WRITE= MEM_DELAY_WRITE > 1 ? (MEM_DELAY_WRITE-2) : 0,
    CHANNELS_NUMBER=BITSIZE_Mout_oe_ram,
    BITSIZE_oe=1,
    BITSIZE_we=1,
    BITSIZE_addr=BITSIZE_Mout_addr_ram/CHANNELS_NUMBER,
    BITSIZE_Wsize=BITSIZE_Mout_data_ram_size/CHANNELS_NUMBER,
    BITSIZE_Wdata=BITSIZE_Mout_Wdata_ram/CHANNELS_NUMBER,
    BITSIZE_ready=1,
    BITSIZE_Rdata=BITSIZE_M_Rdata_ram/CHANNELS_NUMBER,
    BITSIZE_item=BITSIZE_Wdata+BITSIZE_Wsize+BITSIZE_addr+BITSIZE_we+BITSIZE_oe,
    OFFSET_oe=0,
    OFFSET_we=OFFSET_oe+BITSIZE_oe,
    OFFSET_addr=OFFSET_we+BITSIZE_we,
    OFFSET_Wsize=OFFSET_addr+BITSIZE_addr,
    OFFSET_Wdata=OFFSET_Wsize+BITSIZE_Wsize,
    BITSIZE_S_Rdata=BITSIZE_Sout_Rdata_ram/BITSIZE_S_oe_ram,
    BITSIZE_S_ready=1,
    SLAVE_VALID=BITSIZE_Mout_oe_ram == BITSIZE_S_oe_ram,
    QUEUE_BITSIZE=QUEUE_SIZE > 1 ? log2(QUEUE_SIZE) : 1;
  
  genvar i;
  integer dump_file;
  wire [BITSIZE_M_DataRdy-1:0] _M_DataRdy, _M_DataRdy_reg;
  wire [BITSIZE_M_Rdata_ram-1:0] _M_Rdata_ram;
  
  assign S_oe_ram = Mout_oe_ram;
  assign S_we_ram = Mout_we_ram;
  assign S_addr_ram = Mout_addr_ram;
  assign S_data_ram_size = Mout_data_ram_size;
  assign S_Wdata_ram = Mout_Wdata_ram;
  assign M_DataRdy = _M_DataRdy;
  assign M_Rdata_ram = _M_Rdata_ram;
  
  generate
    if(MEM_DUMP)
    begin
      initial
      begin
        dump_file = $fopen(MEM_DUMP_FILE, "w");
        $fwrite(dump_file, "Channel,Operation,Address,Bitwidth,Data\n");
      end
  
      always@(posedge clock)
      begin
        if(done_port)
        begin
          $fflush(dump_file);
        end
      end
    end
  endgenerate
  
  if_utils #(index, BITSIZE_Rdata) m_utils();
  
  generate
    for(i = 0; i < CHANNELS_NUMBER; i = i + 1)
    begin : channel
      wire [MEM_DELAY_MAX*BITSIZE_item-1:0] queue_next;
      wire [BITSIZE_oe-1:0] oe;
      wire [BITSIZE_we-1:0] we;
      ptr_t Waddr, Raddr;
      shortint unsigned Wsize;
      wire [BITSIZE_Wdata-1:0] Wdata;
      reg [BITSIZE_ready-1:0] Wready, Rready, Wready_reg;
      reg [BITSIZE_Rdata-1:0] Rdata;
  
      reg [QUEUE_BITSIZE-1:0] queue_counter;
      wire [QUEUE_BITSIZE-1:0] queue_counter_next;
  
      if(MEM_DELAY_WRITE == 1)
      begin
        always@(posedge clock)
        begin
          Wready_reg <= Wready;
        end
      end
      else
      begin
        assign Wready_reg = Wready;
      end
      if(QUEUE_SIZE > 1)
      begin
        assign Mout_back_pressure[i] = queue_counter == 0 ? 0 : (queue_counter - _M_DataRdy_reg[BITSIZE_ready*i+:BITSIZE_ready]) == (QUEUE_SIZE - 1);
      end
      else
      begin
        assign Mout_back_pressure[i] = queue_counter && !_M_DataRdy_reg[BITSIZE_ready*i+:BITSIZE_ready];
      end
  
      always @(posedge clock)
      begin
        if(reset == 1'b0)
        begin
          queue_counter <= 0;
        end
        else
        begin
          queue_counter <= queue_counter_next;
        end
      end
  
      if(QUEUE_SIZE > 1)
      begin
        assign queue_counter_next = queue_counter + (((Mout_we_ram[i] || Mout_oe_ram[i]) && !Mout_back_pressure[i] && base_addr <= Mout_addr_ram[i*BITSIZE_addr +: BITSIZE_addr]) && (queue_counter == 0 ? 1 : ((queue_counter  - _M_DataRdy_reg[BITSIZE_ready*i+:BITSIZE_ready]) < (QUEUE_SIZE - 1)))) - _M_DataRdy_reg[BITSIZE_ready*i+:BITSIZE_ready];
      end
      else
      begin
        assign queue_counter_next = ((Mout_we_ram[i] || Mout_oe_ram[i]) && !Mout_back_pressure[i] && base_addr <= Mout_addr_ram[i*BITSIZE_addr +: BITSIZE_addr]) || (queue_counter && !_M_DataRdy_reg[BITSIZE_ready*i+:BITSIZE_ready]);
      end
  
      
      if(MEM_DELAY_MAX > 1)
      begin : requests_queue
        reg [MEM_DELAY_MAX*BITSIZE_item-1:0] queue;
        wire [BITSIZE_item-1:0] new_elem;
  
              assign new_elem = Mout_back_pressure[i] ? {BITSIZE_item{1'b0}} : 
                          {Mout_Wdata_ram[BITSIZE_Wdata*i+:BITSIZE_Wdata],
                          Mout_data_ram_size[BITSIZE_Wsize*i+:BITSIZE_Wsize],
                          Mout_addr_ram[BITSIZE_addr*i+:BITSIZE_addr],
                          Mout_we_ram[BITSIZE_we*i+:BITSIZE_we],
                          Mout_oe_ram[BITSIZE_oe*i+:BITSIZE_oe]};
  
              assign queue_next = {queue[(MEM_DELAY_MAX-1)*BITSIZE_item-1:0],new_elem};
  
        always@(posedge clock)
        begin
          if(reset == 1'b0)
          begin
            queue <= 0;
          end
          else
          begin
            queue <= queue_next;
          end
        end
      end
      else
      begin
        assign queue_next = {Mout_Wdata_ram[BITSIZE_Wdata*i+:BITSIZE_Wdata], 
          Mout_data_ram_size[BITSIZE_Wsize*i+:BITSIZE_Wsize],
          Mout_addr_ram[BITSIZE_addr*i+:BITSIZE_addr],
          Mout_we_ram[BITSIZE_we*i+:BITSIZE_we],
          Mout_oe_ram[BITSIZE_oe*i+:BITSIZE_oe]};
      end
  
      assign oe = queue_next[ACTIVE_READ*BITSIZE_item+OFFSET_oe+:BITSIZE_oe];
      assign Raddr = queue_next[ACTIVE_READ*BITSIZE_item+OFFSET_addr+:BITSIZE_addr];
      assign _M_DataRdy[BITSIZE_ready*i+:BITSIZE_ready] = Wready | Rready | (Sout_DataRdy[BITSIZE_S_ready*i*SLAVE_VALID+:BITSIZE_S_ready] === 1'b1);
      assign _M_DataRdy_reg[BITSIZE_ready*i+:BITSIZE_ready] = Wready_reg | Rready; // Used to update at posedge clock of the queue_counter;
      assign _M_Rdata_ram[BITSIZE_Rdata*i+:BITSIZE_Rdata] = Rdata | (Sout_Rdata_ram[BITSIZE_S_Rdata*i*SLAVE_VALID+:BITSIZE_S_Rdata] & {BITSIZE_S_Rdata{Sout_DataRdy[BITSIZE_S_ready*i*SLAVE_VALID+:BITSIZE_S_ready] === 1'b1}});
  
      if(MEM_DELAY_READ > 1)
      begin : read_channel
        always@(posedge clock)
        begin : read_channel
          automatic reg [BITSIZE_Rdata-1:0] data;
          Rready <= 0;
          Rdata <= 0;
          if(oe && base_addr <= Raddr)
          begin
            data = m_utils.read_a(Raddr);
            Rdata <= data;
            Rready <= 1;
            if(MEM_DUMP)
            begin
              $fwrite(dump_file, "%0d,r,%0X,%0d,%0X\n", i, Raddr, BITSIZE_Rdata, data);
            end
          end
        end
      end
      else
      begin
        always@(negedge clock)
        begin : read_channel
          automatic reg [BITSIZE_Rdata-1:0] data;
          Rready <= 0;
          Rdata <= 0;
          if(oe && base_addr <= Raddr)
          begin
            data = m_utils.read_a(Raddr);
            Rdata <= data;
            Rready <= 1;
            if(MEM_DUMP)
            begin
              $fwrite(dump_file, "%0d,r,%0X,%0d,%0X\n", i, Raddr, BITSIZE_Rdata, data);
            end
          end
        end
      end
  
      assign we = queue_next[ACTIVE_WRITE*BITSIZE_item+OFFSET_we+:BITSIZE_we];
      assign Waddr = queue_next[ACTIVE_WRITE*BITSIZE_item+OFFSET_addr+:BITSIZE_addr];
      assign Wsize = {{16-BITSIZE_Wsize{1'b0}}, queue_next[ACTIVE_WRITE*BITSIZE_item+OFFSET_Wsize+:BITSIZE_Wsize]};
      assign Wdata = queue_next[ACTIVE_WRITE*BITSIZE_item+OFFSET_Wdata+:BITSIZE_Wdata];
  
      if(MEM_DELAY_WRITE > 1)
      begin : write_channel
        always@(posedge clock)
        begin : write_channel
          Wready <= 0;
          if(we && base_addr <= Waddr)
          begin
            void'(m_utils.write_sa(Wdata, Wsize, Waddr));
            Wready <= 1;
            if(MEM_DUMP)
            begin
              $fwrite(dump_file, "%0d,w,%0X,%0d,%0X\n", i, Waddr, Wsize, Wdata);
            end
          end
        end
      end
      else
      begin
        always@(negedge clock)
        begin : write_channel
          Wready <= 0;
          if(we && base_addr <= Waddr)
          begin
            void'(m_utils.write_sa(Wdata, Wsize, Waddr));
            Wready <= 1;
            if(MEM_DUMP)
            begin
              $fwrite(dump_file, "%0d,w,%0X,%0d,%0X\n", i, Waddr, Wsize, Wdata);
            end
          end
        end
      end
  
      always @(posedge clock)
      begin
        if (we & oe)
        begin
          $display("ERROR - Mout_we_ram and Mout_oe_ram both enabled on channel %0d!", i);
          $finish;
        end
      end
    end
  endgenerate
endmodule

// This component is part of the BAMBU/PANDA IP LIBRARY
// Copyright (C) 2023-2024 Politecnico di Milano
// Author(s): Michele Fiorito <michele.fiorito@polimi.it>
// License: PANDA_LGPLv3
`timescale 1ns / 1ps
module IF_PORT_IN(clock,
  setup_port,
  val_port);
  parameter index=0,
    BITSIZE_val_port=1;
  // IN
  input clock;
  input setup_port;
  // OUT
  output [BITSIZE_val_port-1:0] val_port;
  if_utils #(index, BITSIZE_val_port) m_utils();
  reg [BITSIZE_val_port-1:0] val;
  wire [BITSIZE_val_port-1:0] val_next;
  
  initial val = 0;
  
  assign val_port = val;
  assign val_next = val;
  
  always @(posedge clock) 
  begin
    val <= val_next;
    if(setup_port)
    begin
      val <= m_utils.read();
    end
  end

endmodule

// Testbench top component
// This component has been derived from the input source code and so it does not fall under the copyright of PandA framework, but it follows the input source code copyright, and may be aggregated with components of the BAMBU/PANDA IP LIBRARY.
// Author(s): Component automatically generated by bambu
// License: THIS COMPONENT IS PROVIDED "AS IS" AND WITHOUT ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, WITHOUT LIMITATION, THE IMPLIED WARRANTIES OF MERCHANTIBILITY AND FITNESS FOR A PARTICULAR PURPOSE.
`timescale 1ns / 1ps
module bambu_testbench_impl(clock);
  // IN
  input clock;
  // Component and signal declarations
  wire [1:0] sig_M_DataRdy;
  wire [63:0] sig_M_Rdata_ram;
  wire [63:0] sig_Mout_Wdata_ram;
  wire [63:0] sig_Mout_addr_ram;
  wire [11:0] sig_Mout_data_ram_size;
  wire [1:0] sig_Mout_oe_ram;
  wire [1:0] sig_Mout_we_ram;
  wire [31:0] sig_P0;
  wire [31:0] sig_P1;
  wire [31:0] sig_P2;
  wire sig_done_port;
  wire sig_reset;
  wire sig_setup_port;
  wire sig_start_port;
  
  TestbenchDUT DUT (.done_port(sig_done_port),
    .Mout_oe_ram(sig_Mout_oe_ram),
    .Mout_we_ram(sig_Mout_we_ram),
    .Mout_addr_ram(sig_Mout_addr_ram),
    .Mout_Wdata_ram(sig_Mout_Wdata_ram),
    .Mout_data_ram_size(sig_Mout_data_ram_size),
    .clock(clock),
    .reset(sig_reset),
    .start_port(sig_start_port),
    .P0(sig_P0),
    .P1(sig_P1),
    .P2(sig_P2),
    .M_Rdata_ram(sig_M_Rdata_ram),
    .M_DataRdy(sig_M_DataRdy));
  TestbenchFSM #(.RESFILE("results.txt"),
    .RESET_ACTIVE(0),
    .RESET_CYCLES(1),
    .RESET_ALWAYS(0),
    .CLOCK_PERIOD(2.0),
    .MAX_SIM_CYCLES(200000000)) SystemFSM (.reset(sig_reset),
    .setup_port(sig_setup_port),
    .start_port(sig_start_port),
    .clock(clock),
    .done_port(sig_done_port));
  TestbenchMEMMinimal #(.index(3),
    .MEM_DELAY_READ(2),
    .MEM_DELAY_WRITE(1),
    .base_addr(1073741824),
    .MEM_DUMP(0),
    .MEM_DUMP_FILE("memdump.csv"),
    .QUEUE_SIZE(4),
    .BITSIZE_M_DataRdy(2),
    .BITSIZE_M_Rdata_ram(64),
    .BITSIZE_Mout_oe_ram(2),
    .BITSIZE_Mout_we_ram(2),
    .BITSIZE_Mout_addr_ram(64),
    .BITSIZE_Mout_data_ram_size(12),
    .BITSIZE_Mout_Wdata_ram(64),
    .BITSIZE_Mout_back_pressure(2),
    .BITSIZE_Sout_DataRdy(1),
    .BITSIZE_Sout_Rdata_ram(8),
    .BITSIZE_S_oe_ram(1),
    .BITSIZE_S_we_ram(1),
    .BITSIZE_S_addr_ram(1),
    .BITSIZE_S_data_ram_size(4),
    .BITSIZE_S_Wdata_ram(8)) SystemMEM (.M_DataRdy(sig_M_DataRdy),
    .M_Rdata_ram(sig_M_Rdata_ram),
    .clock(clock),
    .reset(sig_reset),
    .done_port(sig_done_port),
    .Mout_oe_ram(sig_Mout_oe_ram),
    .Mout_we_ram(sig_Mout_we_ram),
    .Mout_addr_ram(sig_Mout_addr_ram),
    .Mout_data_ram_size(sig_Mout_data_ram_size),
    .Mout_Wdata_ram(sig_Mout_Wdata_ram));
  IF_PORT_IN #(.index(0),
    .BITSIZE_val_port(32)) if_default_P0 (.val_port(sig_P0),
    .clock(clock),
    .setup_port(sig_setup_port));
  IF_PORT_IN #(.index(1),
    .BITSIZE_val_port(32)) if_default_P1 (.val_port(sig_P1),
    .clock(clock),
    .setup_port(sig_setup_port));
  IF_PORT_IN #(.index(2),
    .BITSIZE_val_port(32)) if_default_P2 (.val_port(sig_P2),
    .clock(clock),
    .setup_port(sig_setup_port));

endmodule


// MODULE DECLARATION
module bambu_testbench(clock);

  input clock;
  
  initial
  begin
    `ifndef VERILATOR
    // VCD file generation
    $dumpfile("HLS_output/simulation/test.vcd");
    `ifdef GENERATE_VCD
    $dumpvars;
    `endif
    `endif
  end
  
  bambu_testbench_impl system(.clock(clock));
  
endmodule

`ifndef VERILATOR
module clocked_bambu_testbench;
parameter HALF_CLOCK_PERIOD=1.0;
  
  reg clock;
  initial clock = 1;
  always # HALF_CLOCK_PERIOD clock = !clock;
  
  bambu_testbench bambu_testbench(.clock(clock));
  
endmodule
`endif

// verilator lint_on BLKANDNBLK
// verilator lint_on BLKSEQ
