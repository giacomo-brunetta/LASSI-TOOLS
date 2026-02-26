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
// Author(s): Fabrizio Ferrandi <fabrizio.ferrandi@polimi.it>, Christian Pilato <christian.pilato@polimi.it>
// License: PANDA_LGPLv3
`timescale 1ns / 1ps
module constant_value(out1);
  parameter BITSIZE_out1=1,
    value=1'b0;
  // OUT
  output [BITSIZE_out1-1:0] out1;
  assign out1 = value;
endmodule

// This component is part of the BAMBU/PANDA IP LIBRARY
// Copyright (C) 2004-2024 Politecnico di Milano
// Author(s): Fabrizio Ferrandi <fabrizio.ferrandi@polimi.it>
// License: PANDA_LGPLv3
`timescale 1ns / 1ps
module register_SE(clock,
  reset,
  in1,
  wenable,
  out1);
  parameter BITSIZE_in1=1,
    BITSIZE_out1=1;
  // IN
  input clock;
  input reset;
  input [BITSIZE_in1-1:0] in1;
  input wenable;
  // OUT
  output [BITSIZE_out1-1:0] out1;
  
  reg [BITSIZE_out1-1:0] reg_out1 =0;
  assign out1 = reg_out1;
  always @(posedge clock)
    if (wenable)
      reg_out1 <= in1;
endmodule

// This component is part of the BAMBU/PANDA IP LIBRARY
// Copyright (C) 2004-2024 Politecnico di Milano
// Author(s): Fabrizio Ferrandi <fabrizio.ferrandi@polimi.it>
// License: PANDA_LGPLv3
`timescale 1ns / 1ps
module register_STD(clock,
  reset,
  in1,
  wenable,
  out1);
  parameter BITSIZE_in1=1,
    BITSIZE_out1=1;
  // IN
  input clock;
  input reset;
  input [BITSIZE_in1-1:0] in1;
  input wenable;
  // OUT
  output [BITSIZE_out1-1:0] out1;
  reg [BITSIZE_out1-1:0] reg_out1 =0;
  assign out1 = reg_out1;
  always @(posedge clock)
    reg_out1 <= in1;

endmodule

// This component is part of the BAMBU/PANDA IP LIBRARY
// Copyright (C) 2004-2024 Politecnico di Milano
// Author(s): Fabrizio Ferrandi <fabrizio.ferrandi@polimi.it>
// License: PANDA_LGPLv3
`timescale 1ns / 1ps
module UUdata_converter_FU(in1,
  out1);
  parameter BITSIZE_in1=1,
    BITSIZE_out1=1;
  // IN
  input [BITSIZE_in1-1:0] in1;
  // OUT
  output [BITSIZE_out1-1:0] out1;
  generate
  if (BITSIZE_out1 <= BITSIZE_in1)
  begin
    assign out1 = in1[BITSIZE_out1-1:0];
  end
  else
  begin
    assign out1 = {{(BITSIZE_out1-BITSIZE_in1){1'b0}},in1};
  end
  endgenerate
endmodule

// This component is part of the BAMBU/PANDA IP LIBRARY
// Copyright (C) 2020-2024 Politecnico di Milano
// Author(s): Fabrizio Ferrandi <fabrizio.ferrandi@polimi.it>
// License: PANDA_LGPLv3
`timescale 1ns / 1ps
module ui_extract_bit_expr_FU(in1,
  in2,
  out1);
  parameter BITSIZE_in1=1,
    BITSIZE_in2=1;
  // IN
  input [BITSIZE_in1-1:0] in1;
  input [BITSIZE_in2-1:0] in2;
  // OUT
  output out1;
  assign out1 = (in1 >> in2)&1;
endmodule

// This component is part of the BAMBU/PANDA IP LIBRARY
// Copyright (C) 2016-2024 Politecnico di Milano
// Author(s): Fabrizio Ferrandi <fabrizio.ferrandi@polimi.it>
// License: PANDA_LGPLv3
`timescale 1ns / 1ps
module lut_expr_FU(in1,
  in2,
  in3,
  in4,
  in5,
  in6,
  in7,
  in8,
  in9,
  out1);
  parameter BITSIZE_in1=1,
    BITSIZE_out1=1;
  // IN
  input [BITSIZE_in1-1:0] in1;
  input in2;
  input in3;
  input in4;
  input in5;
  input in6;
  input in7;
  input in8;
  input in9;
  // OUT
  output [BITSIZE_out1-1:0] out1;
  reg[7:0] cleaned_in0;
  wire [7:0] in0;
  wire[BITSIZE_in1-1:0] shifted_s;
  assign in0 = {in9, in8, in7, in6, in5, in4, in3, in2};
  generate
    genvar i0;
    for (i0=0; i0<8; i0=i0+1)
    begin : L0
          always @(*)
          begin
             if (in0[i0] == 1'b1)
                cleaned_in0[i0] = 1'b1;
             else
                cleaned_in0[i0] = 1'b0;
          end
    end
  endgenerate
  assign shifted_s = in1 >> cleaned_in0;
  assign out1[0] = shifted_s[0];
  generate
     if(BITSIZE_out1 > 1)
       assign out1[BITSIZE_out1-1:1] = 0;
  endgenerate

endmodule

// This component is part of the BAMBU/PANDA IP LIBRARY
// Copyright (C) 2004-2024 Politecnico di Milano
// Author(s): Fabrizio Ferrandi <fabrizio.ferrandi@polimi.it>
// License: PANDA_LGPLv3
`timescale 1ns / 1ps
module multi_read_cond_FU(in1,
  out1);
  parameter BITSIZE_in1=1, PORTSIZE_in1=2,
    BITSIZE_out1=1;
  // IN
  input [(PORTSIZE_in1*BITSIZE_in1)+(-1):0] in1;
  // OUT
  output [BITSIZE_out1-1:0] out1;
  assign out1 = in1;
endmodule

// This component is part of the BAMBU/PANDA IP LIBRARY
// Copyright (C) 2004-2024 Politecnico di Milano
// Author(s): Fabrizio Ferrandi <fabrizio.ferrandi@polimi.it>
// License: PANDA_LGPLv3
`timescale 1ns / 1ps
module BMEMORY_CTRLN(clock,
  in1,
  in2,
  in3,
  in4,
  sel_LOAD,
  sel_STORE,
  out1,
  Min_oe_ram,
  Mout_oe_ram,
  Min_we_ram,
  Mout_we_ram,
  Min_addr_ram,
  Mout_addr_ram,
  M_Rdata_ram,
  Min_Wdata_ram,
  Mout_Wdata_ram,
  Min_data_ram_size,
  Mout_data_ram_size,
  M_DataRdy);
  parameter BITSIZE_in1=1, PORTSIZE_in1=2,
    BITSIZE_in2=1, PORTSIZE_in2=2,
    BITSIZE_in3=1, PORTSIZE_in3=2,
    BITSIZE_in4=1, PORTSIZE_in4=2,
    BITSIZE_sel_LOAD=1, PORTSIZE_sel_LOAD=2,
    BITSIZE_sel_STORE=1, PORTSIZE_sel_STORE=2,
    BITSIZE_out1=1, PORTSIZE_out1=2,
    BITSIZE_Min_oe_ram=1, PORTSIZE_Min_oe_ram=2,
    BITSIZE_Min_we_ram=1, PORTSIZE_Min_we_ram=2,
    BITSIZE_Mout_oe_ram=1, PORTSIZE_Mout_oe_ram=2,
    BITSIZE_Mout_we_ram=1, PORTSIZE_Mout_we_ram=2,
    BITSIZE_M_DataRdy=1, PORTSIZE_M_DataRdy=2,
    BITSIZE_Min_addr_ram=1, PORTSIZE_Min_addr_ram=2,
    BITSIZE_Mout_addr_ram=1, PORTSIZE_Mout_addr_ram=2,
    BITSIZE_M_Rdata_ram=8, PORTSIZE_M_Rdata_ram=2,
    BITSIZE_Min_Wdata_ram=8, PORTSIZE_Min_Wdata_ram=2,
    BITSIZE_Mout_Wdata_ram=8, PORTSIZE_Mout_Wdata_ram=2,
    BITSIZE_Min_data_ram_size=1, PORTSIZE_Min_data_ram_size=2,
    BITSIZE_Mout_data_ram_size=1, PORTSIZE_Mout_data_ram_size=2;
  // IN
  input clock;
  input [(PORTSIZE_in1*BITSIZE_in1)+(-1):0] in1;
  input [(PORTSIZE_in2*BITSIZE_in2)+(-1):0] in2;
  input [(PORTSIZE_in3*BITSIZE_in3)+(-1):0] in3;
  input [PORTSIZE_in4-1:0] in4;
  input [PORTSIZE_sel_LOAD-1:0] sel_LOAD;
  input [PORTSIZE_sel_STORE-1:0] sel_STORE;
  input [PORTSIZE_Min_oe_ram-1:0] Min_oe_ram;
  input [PORTSIZE_Min_we_ram-1:0] Min_we_ram;
  input [(PORTSIZE_Min_addr_ram*BITSIZE_Min_addr_ram)+(-1):0] Min_addr_ram;
  input [(PORTSIZE_M_Rdata_ram*BITSIZE_M_Rdata_ram)+(-1):0] M_Rdata_ram;
  input [(PORTSIZE_Min_Wdata_ram*BITSIZE_Min_Wdata_ram)+(-1):0] Min_Wdata_ram;
  input [(PORTSIZE_Min_data_ram_size*BITSIZE_Min_data_ram_size)+(-1):0] Min_data_ram_size;
  input [PORTSIZE_M_DataRdy-1:0] M_DataRdy;
  // OUT
  output [(PORTSIZE_out1*BITSIZE_out1)+(-1):0] out1;
  output [PORTSIZE_Mout_oe_ram-1:0] Mout_oe_ram;
  output [PORTSIZE_Mout_we_ram-1:0] Mout_we_ram;
  output [(PORTSIZE_Mout_addr_ram*BITSIZE_Mout_addr_ram)+(-1):0] Mout_addr_ram;
  output [(PORTSIZE_Mout_Wdata_ram*BITSIZE_Mout_Wdata_ram)+(-1):0] Mout_Wdata_ram;
  output [(PORTSIZE_Mout_data_ram_size*BITSIZE_Mout_data_ram_size)+(-1):0] Mout_data_ram_size;
  
  parameter max_n_writes = PORTSIZE_sel_STORE > PORTSIZE_Mout_we_ram ? PORTSIZE_sel_STORE : PORTSIZE_Mout_we_ram;
  parameter max_n_reads = PORTSIZE_sel_LOAD > PORTSIZE_Mout_oe_ram ? PORTSIZE_sel_STORE : PORTSIZE_Mout_oe_ram;
  parameter max_n_rw = max_n_writes > max_n_reads ? max_n_writes : max_n_reads;
  wire  [(PORTSIZE_in2*BITSIZE_in2)-1:0] tmp_addr;
  wire [PORTSIZE_sel_LOAD-1:0] int_sel_LOAD;
  wire [PORTSIZE_sel_STORE-1:0] int_sel_STORE;
  assign int_sel_LOAD = sel_LOAD & in4;
  assign int_sel_STORE = sel_STORE & in4;
  assign tmp_addr = in2;
  generate
  genvar i;
    for (i=0; i<max_n_rw; i=i+1)
    begin : L0
      assign Mout_addr_ram[(i+1)*BITSIZE_Mout_addr_ram-1:i*BITSIZE_Mout_addr_ram] = ((i < PORTSIZE_sel_LOAD && int_sel_LOAD[i]) || (i < PORTSIZE_sel_STORE && int_sel_STORE[i])) ? (tmp_addr[(i+1)*BITSIZE_in2-1:i*BITSIZE_in2]) : Min_addr_ram[(i+1)*BITSIZE_Min_addr_ram-1:i*BITSIZE_Min_addr_ram];
    end
    endgenerate
  assign Mout_oe_ram = int_sel_LOAD | Min_oe_ram;
  assign Mout_we_ram = int_sel_STORE | Min_we_ram;
  generate
    for (i=0; i<max_n_reads; i=i+1)
    begin : L1
      assign out1[(i+1)*BITSIZE_out1-1:i*BITSIZE_out1] = M_Rdata_ram[i*BITSIZE_M_Rdata_ram+BITSIZE_out1-1:i*BITSIZE_M_Rdata_ram];
  end
  endgenerate
  generate
    for (i=0; i<max_n_rw; i=i+1)
    begin : L2
      assign Mout_Wdata_ram[(i+1)*BITSIZE_Mout_Wdata_ram-1:i*BITSIZE_Mout_Wdata_ram] = int_sel_STORE[i] ? in1[(i+1)*BITSIZE_in1-1:i*BITSIZE_in1] : Min_Wdata_ram[(i+1)*BITSIZE_Min_Wdata_ram-1:i*BITSIZE_Min_Wdata_ram];
  end
  endgenerate
  generate
    for (i=0; i<max_n_rw; i=i+1)
    begin : L3
      assign Mout_data_ram_size[(i+1)*BITSIZE_Mout_data_ram_size-1:i*BITSIZE_Mout_data_ram_size] = ((i < PORTSIZE_sel_LOAD && int_sel_LOAD[i]) || (i < PORTSIZE_sel_STORE && int_sel_STORE[i])) ? (in3[(i+1)*BITSIZE_in3-1:i*BITSIZE_in3]) : Min_data_ram_size[(i+1)*BITSIZE_Min_data_ram_size-1:i*BITSIZE_Min_data_ram_size];
    end
    endgenerate

endmodule

// This component is part of the BAMBU/PANDA IP LIBRARY
// Copyright (C) 2004-2024 Politecnico di Milano
// Author(s): Fabrizio Ferrandi <fabrizio.ferrandi@polimi.it>
// License: PANDA_LGPLv3
`timescale 1ns / 1ps
module ui_bit_and_expr_FU(in1,
  in2,
  out1);
  parameter BITSIZE_in1=1,
    BITSIZE_in2=1,
    BITSIZE_out1=1;
  // IN
  input [BITSIZE_in1-1:0] in1;
  input [BITSIZE_in2-1:0] in2;
  // OUT
  output [BITSIZE_out1-1:0] out1;
  assign out1 = in1 & in2;
endmodule

// This component is part of the BAMBU/PANDA IP LIBRARY
// Copyright (C) 2016-2024 Politecnico di Milano
// Author(s): Fabrizio Ferrandi <fabrizio.ferrandi@polimi.it>
// License: PANDA_LGPLv3
`timescale 1ns / 1ps
module ui_bit_ior_concat_expr_FU(in1,
  in2,
  in3,
  out1);
  parameter BITSIZE_in1=1,
    BITSIZE_in2=1,
    BITSIZE_in3=1,
    BITSIZE_out1=1,
    OFFSET_PARAMETER=1;
  // IN
  input [BITSIZE_in1-1:0] in1;
  input [BITSIZE_in2-1:0] in2;
  input [BITSIZE_in3-1:0] in3;
  // OUT
  output [BITSIZE_out1-1:0] out1;
  localparam nbit_out = BITSIZE_out1 > OFFSET_PARAMETER ? BITSIZE_out1 : 1+OFFSET_PARAMETER;
  wire [nbit_out-1:0] tmp_in1;
  wire [OFFSET_PARAMETER-1:0] tmp_in2;
  generate
    if(BITSIZE_in1 >= nbit_out)
      assign tmp_in1=in1[nbit_out-1:0];
    else
      assign tmp_in1={{(nbit_out-BITSIZE_in1){1'b0}},in1};
  endgenerate
  generate
    if(BITSIZE_in2 >= OFFSET_PARAMETER)
      assign tmp_in2=in2[OFFSET_PARAMETER-1:0];
    else
      assign tmp_in2={{(OFFSET_PARAMETER-BITSIZE_in2){1'b0}},in2};
  endgenerate
  assign out1 = {tmp_in1[nbit_out-1:OFFSET_PARAMETER] , tmp_in2};
endmodule

// This component is part of the BAMBU/PANDA IP LIBRARY
// Copyright (C) 2004-2024 Politecnico di Milano
// Author(s): Fabrizio Ferrandi <fabrizio.ferrandi@polimi.it>
// License: PANDA_LGPLv3
`timescale 1ns / 1ps
module ui_bit_ior_expr_FU(in1,
  in2,
  out1);
  parameter BITSIZE_in1=1,
    BITSIZE_in2=1,
    BITSIZE_out1=1;
  // IN
  input [BITSIZE_in1-1:0] in1;
  input [BITSIZE_in2-1:0] in2;
  // OUT
  output [BITSIZE_out1-1:0] out1;
  assign out1 = in1 | in2;
endmodule

// This component is part of the BAMBU/PANDA IP LIBRARY
// Copyright (C) 2004-2024 Politecnico di Milano
// Author(s): Fabrizio Ferrandi <fabrizio.ferrandi@polimi.it>
// License: PANDA_LGPLv3
`timescale 1ns / 1ps
module ui_cond_expr_FU(in1,
  in2,
  in3,
  out1);
  parameter BITSIZE_in1=1,
    BITSIZE_in2=1,
    BITSIZE_in3=1,
    BITSIZE_out1=1;
  // IN
  input [BITSIZE_in1-1:0] in1;
  input [BITSIZE_in2-1:0] in2;
  input [BITSIZE_in3-1:0] in3;
  // OUT
  output [BITSIZE_out1-1:0] out1;
  assign out1 = in1 != 0 ? in2 : in3;
endmodule

// This component is part of the BAMBU/PANDA IP LIBRARY
// Copyright (C) 2004-2024 Politecnico di Milano
// Author(s): Fabrizio Ferrandi <fabrizio.ferrandi@polimi.it>
// License: PANDA_LGPLv3
`timescale 1ns / 1ps
module ui_eq_expr_FU(in1,
  in2,
  out1);
  parameter BITSIZE_in1=1,
    BITSIZE_in2=1,
    BITSIZE_out1=1;
  // IN
  input [BITSIZE_in1-1:0] in1;
  input [BITSIZE_in2-1:0] in2;
  // OUT
  output [BITSIZE_out1-1:0] out1;
  assign out1 = in1 == in2;
endmodule

// This component is part of the BAMBU/PANDA IP LIBRARY
// Copyright (C) 2004-2024 Politecnico di Milano
// Author(s): Fabrizio Ferrandi <fabrizio.ferrandi@polimi.it>
// License: PANDA_LGPLv3
`timescale 1ns / 1ps
module ui_lshift_expr_FU(in1,
  in2,
  out1);
  parameter BITSIZE_in1=1,
    BITSIZE_in2=1,
    BITSIZE_out1=1,
    PRECISION=1;
  // IN
  input [BITSIZE_in1-1:0] in1;
  input [BITSIZE_in2-1:0] in2;
  // OUT
  output [BITSIZE_out1-1:0] out1;
  `ifndef _SIM_HAVE_CLOG2
    function integer log2;
       input integer value;
       integer temp_value;
      begin
        temp_value = value-1;
        for (log2=0; temp_value>0; log2=log2+1)
          temp_value = temp_value>>1;
      end
    endfunction
  `endif
  `ifdef _SIM_HAVE_CLOG2
    localparam arg2_bitsize = $clog2(PRECISION);
  `else
    localparam arg2_bitsize = log2(PRECISION);
  `endif
  generate
    if(BITSIZE_in2 > arg2_bitsize)
      assign out1 = in1 << in2[arg2_bitsize-1:0];
    else
      assign out1 = in1 << in2;
  endgenerate
endmodule

// This component is part of the BAMBU/PANDA IP LIBRARY
// Copyright (C) 2004-2024 Politecnico di Milano
// Author(s): Fabrizio Ferrandi <fabrizio.ferrandi@polimi.it>
// License: PANDA_LGPLv3
`timescale 1ns / 1ps
module ui_lt_expr_FU(in1,
  in2,
  out1);
  parameter BITSIZE_in1=1,
    BITSIZE_in2=1,
    BITSIZE_out1=1;
  // IN
  input [BITSIZE_in1-1:0] in1;
  input [BITSIZE_in2-1:0] in2;
  // OUT
  output [BITSIZE_out1-1:0] out1;
  assign out1 = in1 < in2;
endmodule

// This component is part of the BAMBU/PANDA IP LIBRARY
// Copyright (C) 2004-2024 Politecnico di Milano
// Author(s): Fabrizio Ferrandi <fabrizio.ferrandi@polimi.it>
// License: PANDA_LGPLv3
`timescale 1ns / 1ps
module ui_mult_expr_FU(clock,
  in1,
  in2,
  out1);
  parameter BITSIZE_in1=1,
    BITSIZE_in2=1,
    BITSIZE_out1=1,
    PIPE_PARAMETER=0;
  // IN
  input clock;
  input [BITSIZE_in1-1:0] in1;
  input [BITSIZE_in2-1:0] in2;
  // OUT
  output [BITSIZE_out1-1:0] out1;
  
  generate
    if(PIPE_PARAMETER==1)
    begin
      reg [BITSIZE_out1-1:0] out1_reg;
      assign out1 = out1_reg;
      always @(posedge clock)
      begin
        out1_reg <= in1 * in2;
      end
    end
    else if(PIPE_PARAMETER>1)
    begin
      reg [BITSIZE_in1-1:0] in1_in;
      reg [BITSIZE_in2-1:0] in2_in;
      wire [BITSIZE_out1-1:0] mult_res;
      reg [BITSIZE_out1-1:0] mul [PIPE_PARAMETER-2:0];
      integer i;
      assign mult_res = in1_in * in2_in;
      always @(posedge clock)
      begin
        in1_in <= in1;
        in2_in <= in2;
        mul[PIPE_PARAMETER-2] <= mult_res;
        for (i=0; i<PIPE_PARAMETER-2; i=i+1)
          mul[i] <= mul[i+1];
      end
      assign out1 = mul[0];
    end
    else
    begin
      assign out1 = in1 * in2;
    end
  endgenerate

endmodule

// This component is part of the BAMBU/PANDA IP LIBRARY
// Copyright (C) 2004-2024 Politecnico di Milano
// Author(s): Fabrizio Ferrandi <fabrizio.ferrandi@polimi.it>
// License: PANDA_LGPLv3
`timescale 1ns / 1ps
module ui_ne_expr_FU(in1,
  in2,
  out1);
  parameter BITSIZE_in1=1,
    BITSIZE_in2=1,
    BITSIZE_out1=1;
  // IN
  input [BITSIZE_in1-1:0] in1;
  input [BITSIZE_in2-1:0] in2;
  // OUT
  output [BITSIZE_out1-1:0] out1;
  assign out1 = in1 != in2;
endmodule

// This component is part of the BAMBU/PANDA IP LIBRARY
// Copyright (C) 2004-2024 Politecnico di Milano
// Author(s): Fabrizio Ferrandi <fabrizio.ferrandi@polimi.it>
// License: PANDA_LGPLv3
`timescale 1ns / 1ps
module ui_plus_expr_FU(in1,
  in2,
  out1);
  parameter BITSIZE_in1=1,
    BITSIZE_in2=1,
    BITSIZE_out1=1;
  // IN
  input [BITSIZE_in1-1:0] in1;
  input [BITSIZE_in2-1:0] in2;
  // OUT
  output [BITSIZE_out1-1:0] out1;
  assign out1 = in1 + in2;
endmodule

// This component is part of the BAMBU/PANDA IP LIBRARY
// Copyright (C) 2004-2024 Politecnico di Milano
// Author(s): Fabrizio Ferrandi <fabrizio.ferrandi@polimi.it>
// License: PANDA_LGPLv3
`timescale 1ns / 1ps
module ui_pointer_plus_expr_FU(in1,
  in2,
  out1);
  parameter BITSIZE_in1=1,
    BITSIZE_in2=1,
    BITSIZE_out1=1,
    LSB_PARAMETER=-1;
  // IN
  input [BITSIZE_in1-1:0] in1;
  input [BITSIZE_in2-1:0] in2;
  // OUT
  output [BITSIZE_out1-1:0] out1;
  wire [BITSIZE_out1-1:0] in1_tmp;
  wire [BITSIZE_out1-1:0] in2_tmp;
  assign in1_tmp = in1;
  assign in2_tmp = in2;generate if (BITSIZE_out1 > LSB_PARAMETER) assign out1[BITSIZE_out1-1:LSB_PARAMETER] = (in1_tmp[BITSIZE_out1-1:LSB_PARAMETER] + in2_tmp[BITSIZE_out1-1:LSB_PARAMETER]); else assign out1 = 0; endgenerate
  generate if (LSB_PARAMETER != 0 && BITSIZE_out1 > LSB_PARAMETER) assign out1[LSB_PARAMETER-1:0] = 0; endgenerate
endmodule

// This component is part of the BAMBU/PANDA IP LIBRARY
// Copyright (C) 2004-2024 Politecnico di Milano
// Author(s): Fabrizio Ferrandi <fabrizio.ferrandi@polimi.it>
// License: PANDA_LGPLv3
`timescale 1ns / 1ps
module ui_rshift_expr_FU(in1,
  in2,
  out1);
  parameter BITSIZE_in1=1,
    BITSIZE_in2=1,
    BITSIZE_out1=1,
    PRECISION=1;
  // IN
  input [BITSIZE_in1-1:0] in1;
  input [BITSIZE_in2-1:0] in2;
  // OUT
  output [BITSIZE_out1-1:0] out1;
  `ifndef _SIM_HAVE_CLOG2
    function integer log2;
       input integer value;
       integer temp_value;
      begin
        temp_value = value-1;
        for (log2=0; temp_value>0; log2=log2+1)
          temp_value = temp_value>>1;
      end
    endfunction
  `endif
  `ifdef _SIM_HAVE_CLOG2
    localparam arg2_bitsize = $clog2(PRECISION);
  `else
    localparam arg2_bitsize = log2(PRECISION);
  `endif
  generate
    if(BITSIZE_in2 > arg2_bitsize)
      assign out1 = in1 >> (in2[arg2_bitsize-1:0]);
    else
      assign out1 = in1 >> in2;
  endgenerate

endmodule

// This component is part of the BAMBU/PANDA IP LIBRARY
// Copyright (C) 2004-2024 Politecnico di Milano
// Author(s): Fabrizio Ferrandi <fabrizio.ferrandi@polimi.it>
// License: PANDA_LGPLv3
`timescale 1ns / 1ps
module ui_ternary_plus_expr_FU(in1,
  in2,
  in3,
  out1);
  parameter BITSIZE_in1=1,
    BITSIZE_in2=1,
    BITSIZE_in3=1,
    BITSIZE_out1=1;
  // IN
  input [BITSIZE_in1-1:0] in1;
  input [BITSIZE_in2-1:0] in2;
  input [BITSIZE_in3-1:0] in3;
  // OUT
  output [BITSIZE_out1-1:0] out1;
  assign out1 = in1 + in2 + in3;
endmodule

// This component is part of the BAMBU/PANDA IP LIBRARY
// Copyright (C) 2004-2024 Politecnico di Milano
// Author(s): Fabrizio Ferrandi <fabrizio.ferrandi@polimi.it>
// License: PANDA_LGPLv3
`timescale 1ns / 1ps
module UIdata_converter_FU(in1,
  out1);
  parameter BITSIZE_in1=1,
    BITSIZE_out1=1;
  // IN
  input [BITSIZE_in1-1:0] in1;
  // OUT
  output signed [BITSIZE_out1-1:0] out1;
  generate
  if (BITSIZE_out1 <= BITSIZE_in1)
  begin
    assign out1 = in1[BITSIZE_out1-1:0];
  end
  else
  begin
    assign out1 = {{(BITSIZE_out1-BITSIZE_in1){1'b0}},in1};
  end
  endgenerate
endmodule

// This component is part of the BAMBU/PANDA IP LIBRARY
// Copyright (C) 2004-2024 Politecnico di Milano
// Author(s): Fabrizio Ferrandi <fabrizio.ferrandi@polimi.it>
// License: PANDA_LGPLv3
`timescale 1ns / 1ps
module IUdata_converter_FU(in1,
  out1);
  parameter BITSIZE_in1=1,
    BITSIZE_out1=1;
  // IN
  input signed [BITSIZE_in1-1:0] in1;
  // OUT
  output [BITSIZE_out1-1:0] out1;
  generate
  if (BITSIZE_out1 <= BITSIZE_in1)
  begin
    assign out1 = in1[BITSIZE_out1-1:0];
  end
  else
  begin
    assign out1 = {{(BITSIZE_out1-BITSIZE_in1){in1[BITSIZE_in1-1]}},in1};
  end
  endgenerate
endmodule

// This component is part of the BAMBU/PANDA IP LIBRARY
// Copyright (C) 2004-2024 Politecnico di Milano
// Author(s): Fabrizio Ferrandi <fabrizio.ferrandi@polimi.it>
// License: PANDA_LGPLv3
`timescale 1ns / 1ps
module ASSIGN_UNSIGNED_FU(in1,
  out1);
  parameter BITSIZE_in1=1,
    BITSIZE_out1=1;
  // IN
  input [BITSIZE_in1-1:0] in1;
  // OUT
  output [BITSIZE_out1-1:0] out1;
  assign out1 = in1;
endmodule

// This component is part of the BAMBU/PANDA IP LIBRARY
// Copyright (C) 2004-2024 Politecnico di Milano
// Author(s): Fabrizio Ferrandi <fabrizio.ferrandi@polimi.it>
// License: PANDA_LGPLv3
`timescale 1ns / 1ps
module lshift_expr_FU(in1,
  in2,
  out1);
  parameter BITSIZE_in1=1,
    BITSIZE_in2=1,
    BITSIZE_out1=1,
    PRECISION=1;
  // IN
  input signed [BITSIZE_in1-1:0] in1;
  input [BITSIZE_in2-1:0] in2;
  // OUT
  output signed [BITSIZE_out1-1:0] out1;
  `ifndef _SIM_HAVE_CLOG2
    function integer log2;
       input integer value;
       integer temp_value;
      begin
        temp_value = value-1;
        for (log2=0; temp_value>0; log2=log2+1)
          temp_value = temp_value>>1;
      end
    endfunction
  `endif
  `ifdef _SIM_HAVE_CLOG2
    localparam arg2_bitsize = $clog2(PRECISION);
  `else
    localparam arg2_bitsize = log2(PRECISION);
  `endif
  generate
    if(BITSIZE_in2 > arg2_bitsize)
      assign out1 = in1 <<< in2[arg2_bitsize-1:0];
    else
      assign out1 = in1 <<< in2;
  endgenerate
endmodule

// This component is part of the BAMBU/PANDA IP LIBRARY
// Copyright (C) 2004-2024 Politecnico di Milano
// Author(s): Fabrizio Ferrandi <fabrizio.ferrandi@polimi.it>
// License: PANDA_LGPLv3
`timescale 1ns / 1ps
module rshift_expr_FU(in1,
  in2,
  out1);
  parameter BITSIZE_in1=1,
    BITSIZE_in2=1,
    BITSIZE_out1=1,
    PRECISION=1;
  // IN
  input signed [BITSIZE_in1-1:0] in1;
  input [BITSIZE_in2-1:0] in2;
  // OUT
  output signed [BITSIZE_out1-1:0] out1;
  `ifndef _SIM_HAVE_CLOG2
    function integer log2;
       input integer value;
       integer temp_value;
      begin
        temp_value = value-1;
        for (log2=0; temp_value>0; log2=log2+1)
          temp_value = temp_value>>1;
      end
    endfunction
  `endif
  `ifdef _SIM_HAVE_CLOG2
    localparam arg2_bitsize = $clog2(PRECISION);
  `else
    localparam arg2_bitsize = log2(PRECISION);
  `endif
  generate
    if(BITSIZE_in2 > arg2_bitsize)
      assign out1 = in1 >>> (in2[arg2_bitsize-1:0]);
    else
      assign out1 = in1 >>> in2;
  endgenerate
endmodule

// This component is part of the BAMBU/PANDA IP LIBRARY
// Copyright (C) 2004-2024 Politecnico di Milano
// Author(s): Fabrizio Ferrandi <fabrizio.ferrandi@polimi.it>
// License: PANDA_LGPLv3
`timescale 1ns / 1ps
module ui_bit_xor_expr_FU(in1,
  in2,
  out1);
  parameter BITSIZE_in1=1,
    BITSIZE_in2=1,
    BITSIZE_out1=1;
  // IN
  input [BITSIZE_in1-1:0] in1;
  input [BITSIZE_in2-1:0] in2;
  // OUT
  output [BITSIZE_out1-1:0] out1;
  assign out1 = in1 ^ in2;
endmodule

// This component is part of the BAMBU/PANDA IP LIBRARY
// Copyright (C) 2004-2024 Politecnico di Milano
// Author(s): Fabrizio Ferrandi <fabrizio.ferrandi@polimi.it>
// License: PANDA_LGPLv3
`timescale 1ns / 1ps
module ui_minus_expr_FU(in1,
  in2,
  out1);
  parameter BITSIZE_in1=1,
    BITSIZE_in2=1,
    BITSIZE_out1=1;
  // IN
  input [BITSIZE_in1-1:0] in1;
  input [BITSIZE_in2-1:0] in2;
  // OUT
  output [BITSIZE_out1-1:0] out1;
  assign out1 = in1 - in2;
endmodule

// This component is part of the BAMBU/PANDA IP LIBRARY
// Copyright (C) 2004-2024 Politecnico di Milano
// Author(s): Fabrizio Ferrandi <fabrizio.ferrandi@polimi.it>
// License: PANDA_LGPLv3
`timescale 1ns / 1ps
module ui_ternary_pm_expr_FU(in1,
  in2,
  in3,
  out1);
  parameter BITSIZE_in1=1,
    BITSIZE_in2=1,
    BITSIZE_in3=1,
    BITSIZE_out1=1;
  // IN
  input [BITSIZE_in1-1:0] in1;
  input [BITSIZE_in2-1:0] in2;
  input [BITSIZE_in3-1:0] in3;
  // OUT
  output [BITSIZE_out1-1:0] out1;
  assign out1 = in1 + in2 - in3;
endmodule

// Datapath RTL description for __float_adde8m23b_127nih
// This component has been derived from the input source code and so it does not fall under the copyright of PandA framework, but it follows the input source code copyright, and may be aggregated with components of the BAMBU/PANDA IP LIBRARY.
// Author(s): Component automatically generated by bambu
// License: THIS COMPONENT IS PROVIDED "AS IS" AND WITHOUT ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, WITHOUT LIMITATION, THE IMPLIED WARRANTIES OF MERCHANTIBILITY AND FITNESS FOR A PARTICULAR PURPOSE.
`timescale 1ns / 1ps
module datapath___float_adde8m23b_127nih(clock,
  reset,
  in_port_a,
  in_port_b,
  return_port,
  wrenable_reg_0,
  wrenable_reg_1,
  wrenable_reg_10,
  wrenable_reg_11,
  wrenable_reg_12,
  wrenable_reg_13,
  wrenable_reg_14,
  wrenable_reg_15,
  wrenable_reg_16,
  wrenable_reg_17,
  wrenable_reg_18,
  wrenable_reg_19,
  wrenable_reg_2,
  wrenable_reg_20,
  wrenable_reg_21,
  wrenable_reg_22,
  wrenable_reg_23,
  wrenable_reg_24,
  wrenable_reg_25,
  wrenable_reg_26,
  wrenable_reg_27,
  wrenable_reg_28,
  wrenable_reg_29,
  wrenable_reg_3,
  wrenable_reg_30,
  wrenable_reg_31,
  wrenable_reg_32,
  wrenable_reg_33,
  wrenable_reg_34,
  wrenable_reg_35,
  wrenable_reg_36,
  wrenable_reg_37,
  wrenable_reg_38,
  wrenable_reg_39,
  wrenable_reg_4,
  wrenable_reg_40,
  wrenable_reg_41,
  wrenable_reg_42,
  wrenable_reg_43,
  wrenable_reg_44,
  wrenable_reg_45,
  wrenable_reg_46,
  wrenable_reg_47,
  wrenable_reg_48,
  wrenable_reg_49,
  wrenable_reg_5,
  wrenable_reg_50,
  wrenable_reg_51,
  wrenable_reg_52,
  wrenable_reg_53,
  wrenable_reg_54,
  wrenable_reg_55,
  wrenable_reg_56,
  wrenable_reg_57,
  wrenable_reg_58,
  wrenable_reg_59,
  wrenable_reg_6,
  wrenable_reg_60,
  wrenable_reg_61,
  wrenable_reg_7,
  wrenable_reg_8,
  wrenable_reg_9);
  // IN
  input clock;
  input reset;
  input [63:0] in_port_a;
  input [63:0] in_port_b;
  input wrenable_reg_0;
  input wrenable_reg_1;
  input wrenable_reg_10;
  input wrenable_reg_11;
  input wrenable_reg_12;
  input wrenable_reg_13;
  input wrenable_reg_14;
  input wrenable_reg_15;
  input wrenable_reg_16;
  input wrenable_reg_17;
  input wrenable_reg_18;
  input wrenable_reg_19;
  input wrenable_reg_2;
  input wrenable_reg_20;
  input wrenable_reg_21;
  input wrenable_reg_22;
  input wrenable_reg_23;
  input wrenable_reg_24;
  input wrenable_reg_25;
  input wrenable_reg_26;
  input wrenable_reg_27;
  input wrenable_reg_28;
  input wrenable_reg_29;
  input wrenable_reg_3;
  input wrenable_reg_30;
  input wrenable_reg_31;
  input wrenable_reg_32;
  input wrenable_reg_33;
  input wrenable_reg_34;
  input wrenable_reg_35;
  input wrenable_reg_36;
  input wrenable_reg_37;
  input wrenable_reg_38;
  input wrenable_reg_39;
  input wrenable_reg_4;
  input wrenable_reg_40;
  input wrenable_reg_41;
  input wrenable_reg_42;
  input wrenable_reg_43;
  input wrenable_reg_44;
  input wrenable_reg_45;
  input wrenable_reg_46;
  input wrenable_reg_47;
  input wrenable_reg_48;
  input wrenable_reg_49;
  input wrenable_reg_5;
  input wrenable_reg_50;
  input wrenable_reg_51;
  input wrenable_reg_52;
  input wrenable_reg_53;
  input wrenable_reg_54;
  input wrenable_reg_55;
  input wrenable_reg_56;
  input wrenable_reg_57;
  input wrenable_reg_58;
  input wrenable_reg_59;
  input wrenable_reg_6;
  input wrenable_reg_60;
  input wrenable_reg_61;
  input wrenable_reg_7;
  input wrenable_reg_8;
  input wrenable_reg_9;
  // OUT
  output [63:0] return_port;
  // Component and signal declarations
  wire [7:0] out_ASSIGN_UNSIGNED_FU_7_i0_fu___float_adde8m23b_127nih_501195_503973;
  wire [31:0] out_IUdata_converter_FU_4_i0_fu___float_adde8m23b_127nih_501195_502496;
  wire [4:0] out_IUdata_converter_FU_66_i0_fu___float_adde8m23b_127nih_501195_502576;
  wire [26:0] out_IUdata_converter_FU_69_i0_fu___float_adde8m23b_127nih_501195_502586;
  wire signed [1:0] out_UIdata_converter_FU_3_i0_fu___float_adde8m23b_127nih_501195_502553;
  wire signed [1:0] out_UIdata_converter_FU_65_i0_fu___float_adde8m23b_127nih_501195_502599;
  wire signed [1:0] out_UIdata_converter_FU_68_i0_fu___float_adde8m23b_127nih_501195_502602;
  wire out_UUdata_converter_FU_114_i0_fu___float_adde8m23b_127nih_501195_501796;
  wire out_UUdata_converter_FU_115_i0_fu___float_adde8m23b_127nih_501195_501799;
  wire out_UUdata_converter_FU_116_i0_fu___float_adde8m23b_127nih_501195_501886;
  wire out_UUdata_converter_FU_117_i0_fu___float_adde8m23b_127nih_501195_503690;
  wire out_UUdata_converter_FU_118_i0_fu___float_adde8m23b_127nih_501195_503699;
  wire out_UUdata_converter_FU_119_i0_fu___float_adde8m23b_127nih_501195_503708;
  wire out_UUdata_converter_FU_120_i0_fu___float_adde8m23b_127nih_501195_503717;
  wire [4:0] out_UUdata_converter_FU_121_i0_fu___float_adde8m23b_127nih_501195_501937;
  wire out_UUdata_converter_FU_133_i0_fu___float_adde8m23b_127nih_501195_502101;
  wire out_UUdata_converter_FU_134_i0_fu___float_adde8m23b_127nih_501195_502104;
  wire out_UUdata_converter_FU_146_i0_fu___float_adde8m23b_127nih_501195_502143;
  wire out_UUdata_converter_FU_149_i0_fu___float_adde8m23b_127nih_501195_502158;
  wire out_UUdata_converter_FU_150_i0_fu___float_adde8m23b_127nih_501195_502161;
  wire out_UUdata_converter_FU_151_i0_fu___float_adde8m23b_127nih_501195_502216;
  wire out_UUdata_converter_FU_2_i0_fu___float_adde8m23b_127nih_501195_501259;
  wire out_UUdata_converter_FU_50_i0_fu___float_adde8m23b_127nih_501195_501391;
  wire out_UUdata_converter_FU_55_i0_fu___float_adde8m23b_127nih_501195_501405;
  wire out_UUdata_converter_FU_57_i0_fu___float_adde8m23b_127nih_501195_501408;
  wire out_UUdata_converter_FU_58_i0_fu___float_adde8m23b_127nih_501195_501444;
  wire out_UUdata_converter_FU_59_i0_fu___float_adde8m23b_127nih_501195_501459;
  wire out_UUdata_converter_FU_64_i0_fu___float_adde8m23b_127nih_501195_501493;
  wire [4:0] out_UUdata_converter_FU_67_i0_fu___float_adde8m23b_127nih_501195_501502;
  wire out_UUdata_converter_FU_71_i0_fu___float_adde8m23b_127nih_501195_501576;
  wire out_UUdata_converter_FU_72_i0_fu___float_adde8m23b_127nih_501195_501579;
  wire out_const_0;
  wire out_const_1;
  wire [53:0] out_const_10;
  wire [28:0] out_const_11;
  wire [4:0] out_const_12;
  wire [4:0] out_const_13;
  wire [2:0] out_const_14;
  wire [3:0] out_const_15;
  wire [4:0] out_const_16;
  wire [54:0] out_const_17;
  wire [11:0] out_const_18;
  wire [43:0] out_const_19;
  wire [1:0] out_const_2;
  wire [4:0] out_const_20;
  wire [30:0] out_const_21;
  wire [3:0] out_const_22;
  wire [4:0] out_const_23;
  wire [27:0] out_const_24;
  wire [4:0] out_const_25;
  wire [1:0] out_const_26;
  wire [2:0] out_const_27;
  wire [3:0] out_const_28;
  wire [4:0] out_const_29;
  wire [2:0] out_const_3;
  wire [4:0] out_const_30;
  wire [57:0] out_const_31;
  wire [3:0] out_const_32;
  wire [4:0] out_const_33;
  wire [4:0] out_const_34;
  wire [2:0] out_const_35;
  wire [3:0] out_const_36;
  wire [4:0] out_const_37;
  wire [63:0] out_const_38;
  wire [7:0] out_const_39;
  wire [3:0] out_const_4;
  wire [4:0] out_const_40;
  wire [31:0] out_const_41;
  wire [31:0] out_const_42;
  wire [3:0] out_const_43;
  wire [4:0] out_const_44;
  wire [7:0] out_const_45;
  wire [47:0] out_const_46;
  wire [31:0] out_const_47;
  wire [63:0] out_const_48;
  wire [31:0] out_const_49;
  wire [4:0] out_const_5;
  wire [63:0] out_const_50;
  wire [4:0] out_const_51;
  wire [5:0] out_const_52;
  wire [7:0] out_const_53;
  wire [7:0] out_const_54;
  wire [63:0] out_const_55;
  wire [31:0] out_const_56;
  wire [15:0] out_const_57;
  wire [31:0] out_const_58;
  wire [63:0] out_const_59;
  wire [16:0] out_const_6;
  wire [22:0] out_const_60;
  wire [63:0] out_const_61;
  wire [25:0] out_const_62;
  wire [26:0] out_const_63;
  wire [30:0] out_const_64;
  wire [63:0] out_const_65;
  wire [61:0] out_const_66;
  wire [63:0] out_const_67;
  wire [63:0] out_const_7;
  wire [4:0] out_const_8;
  wire [21:0] out_const_9;
  wire [31:0] out_conv_in_port_a_64_32;
  wire [31:0] out_conv_in_port_b_64_32;
  wire [63:0] out_conv_out_ui_bit_ior_expr_FU_0_32_32_171_i0_fu___float_adde8m23b_127nih_501195_502228_32_64;
  wire signed [31:0] out_lshift_expr_FU_32_0_32_153_i0_fu___float_adde8m23b_127nih_501195_502594;
  wire signed [63:0] out_lshift_expr_FU_64_0_64_154_i0_fu___float_adde8m23b_127nih_501195_502550;
  wire signed [63:0] out_lshift_expr_FU_64_0_64_154_i1_fu___float_adde8m23b_127nih_501195_502596;
  wire out_lut_expr_FU_103_i0_fu___float_adde8m23b_127nih_501195_510617;
  wire out_lut_expr_FU_104_i0_fu___float_adde8m23b_127nih_501195_510621;
  wire out_lut_expr_FU_105_i0_fu___float_adde8m23b_127nih_501195_510624;
  wire out_lut_expr_FU_106_i0_fu___float_adde8m23b_127nih_501195_510627;
  wire out_lut_expr_FU_107_i0_fu___float_adde8m23b_127nih_501195_502650;
  wire out_lut_expr_FU_108_i0_fu___float_adde8m23b_127nih_501195_510632;
  wire out_lut_expr_FU_109_i0_fu___float_adde8m23b_127nih_501195_510635;
  wire out_lut_expr_FU_110_i0_fu___float_adde8m23b_127nih_501195_510644;
  wire out_lut_expr_FU_111_i0_fu___float_adde8m23b_127nih_501195_510639;
  wire out_lut_expr_FU_112_i0_fu___float_adde8m23b_127nih_501195_502659;
  wire out_lut_expr_FU_113_i0_fu___float_adde8m23b_127nih_501195_502664;
  wire out_lut_expr_FU_122_i0_fu___float_adde8m23b_127nih_501195_510650;
  wire out_lut_expr_FU_123_i0_fu___float_adde8m23b_127nih_501195_510653;
  wire out_lut_expr_FU_124_i0_fu___float_adde8m23b_127nih_501195_510657;
  wire out_lut_expr_FU_125_i0_fu___float_adde8m23b_127nih_501195_510661;
  wire out_lut_expr_FU_126_i0_fu___float_adde8m23b_127nih_501195_510664;
  wire out_lut_expr_FU_127_i0_fu___float_adde8m23b_127nih_501195_502758;
  wire out_lut_expr_FU_132_i0_fu___float_adde8m23b_127nih_501195_506322;
  wire out_lut_expr_FU_135_i0_fu___float_adde8m23b_127nih_501195_510672;
  wire out_lut_expr_FU_136_i0_fu___float_adde8m23b_127nih_501195_510675;
  wire out_lut_expr_FU_137_i0_fu___float_adde8m23b_127nih_501195_510679;
  wire out_lut_expr_FU_138_i0_fu___float_adde8m23b_127nih_501195_510683;
  wire out_lut_expr_FU_139_i0_fu___float_adde8m23b_127nih_501195_510686;
  wire out_lut_expr_FU_140_i0_fu___float_adde8m23b_127nih_501195_510689;
  wire out_lut_expr_FU_141_i0_fu___float_adde8m23b_127nih_501195_502776;
  wire out_lut_expr_FU_142_i0_fu___float_adde8m23b_127nih_501195_510694;
  wire out_lut_expr_FU_143_i0_fu___float_adde8m23b_127nih_501195_510698;
  wire out_lut_expr_FU_144_i0_fu___float_adde8m23b_127nih_501195_502788;
  wire out_lut_expr_FU_145_i0_fu___float_adde8m23b_127nih_501195_506377;
  wire out_lut_expr_FU_147_i0_fu___float_adde8m23b_127nih_501195_510706;
  wire out_lut_expr_FU_148_i0_fu___float_adde8m23b_127nih_501195_506397;
  wire out_lut_expr_FU_42_i0_fu___float_adde8m23b_127nih_501195_510563;
  wire out_lut_expr_FU_43_i0_fu___float_adde8m23b_127nih_501195_510566;
  wire out_lut_expr_FU_44_i0_fu___float_adde8m23b_127nih_501195_510569;
  wire out_lut_expr_FU_45_i0_fu___float_adde8m23b_127nih_501195_510572;
  wire out_lut_expr_FU_46_i0_fu___float_adde8m23b_127nih_501195_510575;
  wire out_lut_expr_FU_47_i0_fu___float_adde8m23b_127nih_501195_510578;
  wire out_lut_expr_FU_48_i0_fu___float_adde8m23b_127nih_501195_510581;
  wire out_lut_expr_FU_49_i0_fu___float_adde8m23b_127nih_501195_506085;
  wire out_lut_expr_FU_51_i0_fu___float_adde8m23b_127nih_501195_510587;
  wire out_lut_expr_FU_52_i0_fu___float_adde8m23b_127nih_501195_510591;
  wire out_lut_expr_FU_53_i0_fu___float_adde8m23b_127nih_501195_510594;
  wire out_lut_expr_FU_54_i0_fu___float_adde8m23b_127nih_501195_506102;
  wire out_lut_expr_FU_56_i0_fu___float_adde8m23b_127nih_501195_506112;
  wire out_lut_expr_FU_63_i0_fu___float_adde8m23b_127nih_501195_502570;
  wire out_lut_expr_FU_70_i0_fu___float_adde8m23b_127nih_501195_506136;
  wire out_lut_expr_FU_89_i0_fu___float_adde8m23b_127nih_501195_510603;
  wire out_lut_expr_FU_90_i0_fu___float_adde8m23b_127nih_501195_510607;
  wire out_lut_expr_FU_91_i0_fu___float_adde8m23b_127nih_501195_510611;
  wire out_lut_expr_FU_92_i0_fu___float_adde8m23b_127nih_501195_502641;
  wire [26:0] out_reg_0_reg_0;
  wire out_reg_10_reg_10;
  wire out_reg_11_reg_11;
  wire out_reg_12_reg_12;
  wire out_reg_13_reg_13;
  wire out_reg_14_reg_14;
  wire out_reg_15_reg_15;
  wire out_reg_16_reg_16;
  wire out_reg_17_reg_17;
  wire out_reg_18_reg_18;
  wire out_reg_19_reg_19;
  wire [22:0] out_reg_1_reg_1;
  wire out_reg_20_reg_20;
  wire out_reg_21_reg_21;
  wire out_reg_22_reg_22;
  wire out_reg_23_reg_23;
  wire out_reg_24_reg_24;
  wire out_reg_25_reg_25;
  wire [26:0] out_reg_26_reg_26;
  wire [42:0] out_reg_27_reg_27;
  wire out_reg_28_reg_28;
  wire out_reg_29_reg_29;
  wire out_reg_2_reg_2;
  wire out_reg_30_reg_30;
  wire out_reg_31_reg_31;
  wire out_reg_32_reg_32;
  wire out_reg_33_reg_33;
  wire out_reg_34_reg_34;
  wire out_reg_35_reg_35;
  wire out_reg_36_reg_36;
  wire out_reg_37_reg_37;
  wire out_reg_38_reg_38;
  wire out_reg_39_reg_39;
  wire out_reg_3_reg_3;
  wire out_reg_40_reg_40;
  wire out_reg_41_reg_41;
  wire out_reg_42_reg_42;
  wire out_reg_43_reg_43;
  wire out_reg_44_reg_44;
  wire out_reg_45_reg_45;
  wire out_reg_46_reg_46;
  wire out_reg_47_reg_47;
  wire out_reg_48_reg_48;
  wire out_reg_49_reg_49;
  wire [23:0] out_reg_4_reg_4;
  wire out_reg_50_reg_50;
  wire out_reg_51_reg_51;
  wire out_reg_52_reg_52;
  wire out_reg_53_reg_53;
  wire out_reg_54_reg_54;
  wire out_reg_55_reg_55;
  wire out_reg_56_reg_56;
  wire out_reg_57_reg_57;
  wire [30:0] out_reg_58_reg_58;
  wire out_reg_59_reg_59;
  wire [23:0] out_reg_5_reg_5;
  wire [31:0] out_reg_60_reg_60;
  wire out_reg_61_reg_61;
  wire [7:0] out_reg_6_reg_6;
  wire out_reg_7_reg_7;
  wire out_reg_8_reg_8;
  wire out_reg_9_reg_9;
  wire signed [0:0] out_rshift_expr_FU_32_0_32_155_i0_fu___float_adde8m23b_127nih_501195_502573;
  wire signed [0:0] out_rshift_expr_FU_64_0_64_156_i0_fu___float_adde8m23b_127nih_501195_502493;
  wire signed [0:0] out_rshift_expr_FU_64_0_64_156_i1_fu___float_adde8m23b_127nih_501195_502584;
  wire [30:0] out_ui_bit_and_expr_FU_0_32_32_157_i0_fu___float_adde8m23b_127nih_501195_501249;
  wire [30:0] out_ui_bit_and_expr_FU_0_32_32_157_i1_fu___float_adde8m23b_127nih_501195_501254;
  wire [15:0] out_ui_bit_and_expr_FU_16_0_16_158_i0_fu___float_adde8m23b_127nih_501195_501647;
  wire [22:0] out_ui_bit_and_expr_FU_32_0_32_159_i0_fu___float_adde8m23b_127nih_501195_501316;
  wire [22:0] out_ui_bit_and_expr_FU_32_0_32_159_i1_fu___float_adde8m23b_127nih_501195_501344;
  wire [22:0] out_ui_bit_and_expr_FU_32_0_32_159_i2_fu___float_adde8m23b_127nih_501195_502061;
  wire [22:0] out_ui_bit_and_expr_FU_32_0_32_159_i3_fu___float_adde8m23b_127nih_501195_502128;
  wire [25:0] out_ui_bit_and_expr_FU_32_0_32_160_i0_fu___float_adde8m23b_127nih_501195_501545;
  wire [26:0] out_ui_bit_and_expr_FU_32_0_32_161_i0_fu___float_adde8m23b_127nih_501195_501570;
  wire [26:0] out_ui_bit_and_expr_FU_32_0_32_161_i1_fu___float_adde8m23b_127nih_501195_501588;
  wire [31:0] out_ui_bit_and_expr_FU_32_32_32_162_i0_fu___float_adde8m23b_127nih_501195_501268;
  wire [31:0] out_ui_bit_and_expr_FU_32_32_32_162_i1_fu___float_adde8m23b_127nih_501195_501278;
  wire [23:0] out_ui_bit_and_expr_FU_32_32_32_162_i2_fu___float_adde8m23b_127nih_501195_501524;
  wire [7:0] out_ui_bit_and_expr_FU_8_0_8_163_i0_fu___float_adde8m23b_127nih_501195_501331;
  wire [7:0] out_ui_bit_and_expr_FU_8_0_8_163_i1_fu___float_adde8m23b_127nih_501195_501350;
  wire [4:0] out_ui_bit_and_expr_FU_8_0_8_163_i2_fu___float_adde8m23b_127nih_501195_501441;
  wire [7:0] out_ui_bit_and_expr_FU_8_0_8_163_i3_fu___float_adde8m23b_127nih_501195_502049;
  wire [7:0] out_ui_bit_and_expr_FU_8_0_8_163_i4_fu___float_adde8m23b_127nih_501195_502213;
  wire [4:0] out_ui_bit_and_expr_FU_8_0_8_164_i0_fu___float_adde8m23b_127nih_501195_501515;
  wire [1:0] out_ui_bit_and_expr_FU_8_0_8_165_i0_fu___float_adde8m23b_127nih_501195_503550;
  wire [26:0] out_ui_bit_ior_concat_expr_FU_166_i0_fu___float_adde8m23b_127nih_501195_501585;
  wire [23:0] out_ui_bit_ior_expr_FU_0_32_32_167_i0_fu___float_adde8m23b_127nih_501195_501450;
  wire [23:0] out_ui_bit_ior_expr_FU_0_32_32_168_i0_fu___float_adde8m23b_127nih_501195_501465;
  wire [30:0] out_ui_bit_ior_expr_FU_0_32_32_169_i0_fu___float_adde8m23b_127nih_501195_502067;
  wire [31:0] out_ui_bit_ior_expr_FU_0_32_32_170_i0_fu___float_adde8m23b_127nih_501195_502225;
  wire [31:0] out_ui_bit_ior_expr_FU_0_32_32_171_i0_fu___float_adde8m23b_127nih_501195_502228;
  wire [4:0] out_ui_bit_ior_expr_FU_0_8_8_172_i0_fu___float_adde8m23b_127nih_501195_501901;
  wire [4:0] out_ui_bit_ior_expr_FU_0_8_8_173_i0_fu___float_adde8m23b_127nih_501195_501904;
  wire [4:0] out_ui_bit_ior_expr_FU_0_8_8_174_i0_fu___float_adde8m23b_127nih_501195_501907;
  wire [4:0] out_ui_bit_ior_expr_FU_0_8_8_175_i0_fu___float_adde8m23b_127nih_501195_501910;
  wire [30:0] out_ui_bit_ior_expr_FU_32_32_32_176_i0_fu___float_adde8m23b_127nih_501195_501275;
  wire [30:0] out_ui_bit_ior_expr_FU_32_32_32_176_i1_fu___float_adde8m23b_127nih_501195_501285;
  wire [22:0] out_ui_bit_ior_expr_FU_32_32_32_176_i2_fu___float_adde8m23b_127nih_501195_502173;
  wire [4:0] out_ui_bit_ior_expr_FU_8_8_8_177_i0_fu___float_adde8m23b_127nih_501195_501506;
  wire [23:0] out_ui_bit_xor_expr_FU_32_0_32_178_i0_fu___float_adde8m23b_127nih_501195_501521;
  wire [26:0] out_ui_bit_xor_expr_FU_32_32_32_179_i0_fu___float_adde8m23b_127nih_501195_501554;
  wire [30:0] out_ui_cond_expr_FU_32_32_32_32_180_i0_fu___float_adde8m23b_127nih_501195_501272;
  wire [30:0] out_ui_cond_expr_FU_32_32_32_32_180_i1_fu___float_adde8m23b_127nih_501195_501282;
  wire [22:0] out_ui_cond_expr_FU_32_32_32_32_180_i2_fu___float_adde8m23b_127nih_501195_502134;
  wire [42:0] out_ui_cond_expr_FU_64_64_64_64_181_i0_fu___float_adde8m23b_127nih_501195_501658;
  wire [50:0] out_ui_cond_expr_FU_64_64_64_64_181_i1_fu___float_adde8m23b_127nih_501195_501691;
  wire [54:0] out_ui_cond_expr_FU_64_64_64_64_181_i2_fu___float_adde8m23b_127nih_501195_501726;
  wire [56:0] out_ui_cond_expr_FU_64_64_64_64_181_i3_fu___float_adde8m23b_127nih_501195_501763;
  wire [7:0] out_ui_cond_expr_FU_8_8_8_8_182_i0_fu___float_adde8m23b_127nih_501195_502009;
  wire [7:0] out_ui_cond_expr_FU_8_8_8_8_182_i1_fu___float_adde8m23b_127nih_501195_502119;
  wire out_ui_eq_expr_FU_16_0_16_183_i0_fu___float_adde8m23b_127nih_501195_502628;
  wire out_ui_extract_bit_expr_FU_100_i0_fu___float_adde8m23b_127nih_501195_510515;
  wire out_ui_extract_bit_expr_FU_101_i0_fu___float_adde8m23b_127nih_501195_510527;
  wire out_ui_extract_bit_expr_FU_102_i0_fu___float_adde8m23b_127nih_501195_510442;
  wire out_ui_extract_bit_expr_FU_10_i0_fu___float_adde8m23b_127nih_501195_507336;
  wire out_ui_extract_bit_expr_FU_11_i0_fu___float_adde8m23b_127nih_501195_507899;
  wire out_ui_extract_bit_expr_FU_128_i0_fu___float_adde8m23b_127nih_501195_506764;
  wire out_ui_extract_bit_expr_FU_129_i0_fu___float_adde8m23b_127nih_501195_508668;
  wire out_ui_extract_bit_expr_FU_12_i0_fu___float_adde8m23b_127nih_501195_507343;
  wire out_ui_extract_bit_expr_FU_130_i0_fu___float_adde8m23b_127nih_501195_508672;
  wire out_ui_extract_bit_expr_FU_131_i0_fu___float_adde8m23b_127nih_501195_507242;
  wire out_ui_extract_bit_expr_FU_13_i0_fu___float_adde8m23b_127nih_501195_507906;
  wire out_ui_extract_bit_expr_FU_14_i0_fu___float_adde8m23b_127nih_501195_507350;
  wire out_ui_extract_bit_expr_FU_15_i0_fu___float_adde8m23b_127nih_501195_507913;
  wire out_ui_extract_bit_expr_FU_16_i0_fu___float_adde8m23b_127nih_501195_507357;
  wire out_ui_extract_bit_expr_FU_17_i0_fu___float_adde8m23b_127nih_501195_507920;
  wire out_ui_extract_bit_expr_FU_18_i0_fu___float_adde8m23b_127nih_501195_507364;
  wire out_ui_extract_bit_expr_FU_19_i0_fu___float_adde8m23b_127nih_501195_507927;
  wire out_ui_extract_bit_expr_FU_20_i0_fu___float_adde8m23b_127nih_501195_507371;
  wire out_ui_extract_bit_expr_FU_21_i0_fu___float_adde8m23b_127nih_501195_507934;
  wire out_ui_extract_bit_expr_FU_22_i0_fu___float_adde8m23b_127nih_501195_507378;
  wire out_ui_extract_bit_expr_FU_23_i0_fu___float_adde8m23b_127nih_501195_507941;
  wire out_ui_extract_bit_expr_FU_24_i0_fu___float_adde8m23b_127nih_501195_507385;
  wire out_ui_extract_bit_expr_FU_25_i0_fu___float_adde8m23b_127nih_501195_507948;
  wire out_ui_extract_bit_expr_FU_26_i0_fu___float_adde8m23b_127nih_501195_507392;
  wire out_ui_extract_bit_expr_FU_27_i0_fu___float_adde8m23b_127nih_501195_507955;
  wire out_ui_extract_bit_expr_FU_28_i0_fu___float_adde8m23b_127nih_501195_507399;
  wire out_ui_extract_bit_expr_FU_29_i0_fu___float_adde8m23b_127nih_501195_507962;
  wire out_ui_extract_bit_expr_FU_30_i0_fu___float_adde8m23b_127nih_501195_507406;
  wire out_ui_extract_bit_expr_FU_31_i0_fu___float_adde8m23b_127nih_501195_507969;
  wire out_ui_extract_bit_expr_FU_32_i0_fu___float_adde8m23b_127nih_501195_507413;
  wire out_ui_extract_bit_expr_FU_33_i0_fu___float_adde8m23b_127nih_501195_507976;
  wire out_ui_extract_bit_expr_FU_34_i0_fu___float_adde8m23b_127nih_501195_507420;
  wire out_ui_extract_bit_expr_FU_35_i0_fu___float_adde8m23b_127nih_501195_507983;
  wire out_ui_extract_bit_expr_FU_36_i0_fu___float_adde8m23b_127nih_501195_507427;
  wire out_ui_extract_bit_expr_FU_37_i0_fu___float_adde8m23b_127nih_501195_507990;
  wire out_ui_extract_bit_expr_FU_38_i0_fu___float_adde8m23b_127nih_501195_507434;
  wire out_ui_extract_bit_expr_FU_39_i0_fu___float_adde8m23b_127nih_501195_507997;
  wire out_ui_extract_bit_expr_FU_40_i0_fu___float_adde8m23b_127nih_501195_507441;
  wire out_ui_extract_bit_expr_FU_41_i0_fu___float_adde8m23b_127nih_501195_508004;
  wire out_ui_extract_bit_expr_FU_5_i0_fu___float_adde8m23b_127nih_501195_506850;
  wire out_ui_extract_bit_expr_FU_60_i0_fu___float_adde8m23b_127nih_501195_506992;
  wire out_ui_extract_bit_expr_FU_61_i0_fu___float_adde8m23b_127nih_501195_506996;
  wire out_ui_extract_bit_expr_FU_62_i0_fu___float_adde8m23b_127nih_501195_507000;
  wire out_ui_extract_bit_expr_FU_6_i0_fu___float_adde8m23b_127nih_501195_507325;
  wire out_ui_extract_bit_expr_FU_73_i0_fu___float_adde8m23b_127nih_501195_509799;
  wire out_ui_extract_bit_expr_FU_74_i0_fu___float_adde8m23b_127nih_501195_509408;
  wire out_ui_extract_bit_expr_FU_75_i0_fu___float_adde8m23b_127nih_501195_509803;
  wire out_ui_extract_bit_expr_FU_76_i0_fu___float_adde8m23b_127nih_501195_509416;
  wire out_ui_extract_bit_expr_FU_77_i0_fu___float_adde8m23b_127nih_501195_509807;
  wire out_ui_extract_bit_expr_FU_78_i0_fu___float_adde8m23b_127nih_501195_509424;
  wire out_ui_extract_bit_expr_FU_79_i0_fu___float_adde8m23b_127nih_501195_509811;
  wire out_ui_extract_bit_expr_FU_80_i0_fu___float_adde8m23b_127nih_501195_509432;
  wire out_ui_extract_bit_expr_FU_81_i0_fu___float_adde8m23b_127nih_501195_509815;
  wire out_ui_extract_bit_expr_FU_82_i0_fu___float_adde8m23b_127nih_501195_509440;
  wire out_ui_extract_bit_expr_FU_83_i0_fu___float_adde8m23b_127nih_501195_509819;
  wire out_ui_extract_bit_expr_FU_84_i0_fu___float_adde8m23b_127nih_501195_509448;
  wire out_ui_extract_bit_expr_FU_85_i0_fu___float_adde8m23b_127nih_501195_509823;
  wire out_ui_extract_bit_expr_FU_86_i0_fu___float_adde8m23b_127nih_501195_509456;
  wire out_ui_extract_bit_expr_FU_87_i0_fu___float_adde8m23b_127nih_501195_509827;
  wire out_ui_extract_bit_expr_FU_88_i0_fu___float_adde8m23b_127nih_501195_509464;
  wire out_ui_extract_bit_expr_FU_8_i0_fu___float_adde8m23b_127nih_501195_506857;
  wire out_ui_extract_bit_expr_FU_93_i0_fu___float_adde8m23b_127nih_501195_510146;
  wire out_ui_extract_bit_expr_FU_94_i0_fu___float_adde8m23b_127nih_501195_510382;
  wire out_ui_extract_bit_expr_FU_95_i0_fu___float_adde8m23b_127nih_501195_510158;
  wire out_ui_extract_bit_expr_FU_96_i0_fu___float_adde8m23b_127nih_501195_510386;
  wire out_ui_extract_bit_expr_FU_97_i0_fu___float_adde8m23b_127nih_501195_510170;
  wire out_ui_extract_bit_expr_FU_98_i0_fu___float_adde8m23b_127nih_501195_510390;
  wire out_ui_extract_bit_expr_FU_99_i0_fu___float_adde8m23b_127nih_501195_510182;
  wire out_ui_extract_bit_expr_FU_9_i0_fu___float_adde8m23b_127nih_501195_507332;
  wire [25:0] out_ui_lshift_expr_FU_0_64_64_184_i0_fu___float_adde8m23b_127nih_501195_501518;
  wire [15:0] out_ui_lshift_expr_FU_16_0_16_185_i0_fu___float_adde8m23b_127nih_501195_503693;
  wire [15:0] out_ui_lshift_expr_FU_16_0_16_185_i1_fu___float_adde8m23b_127nih_501195_503702;
  wire [15:0] out_ui_lshift_expr_FU_16_0_16_185_i2_fu___float_adde8m23b_127nih_501195_503711;
  wire [15:0] out_ui_lshift_expr_FU_16_0_16_185_i3_fu___float_adde8m23b_127nih_501195_503720;
  wire [23:0] out_ui_lshift_expr_FU_32_0_32_186_i0_fu___float_adde8m23b_127nih_501195_501447;
  wire [23:0] out_ui_lshift_expr_FU_32_0_32_186_i1_fu___float_adde8m23b_127nih_501195_501462;
  wire [30:0] out_ui_lshift_expr_FU_32_0_32_186_i2_fu___float_adde8m23b_127nih_501195_502064;
  wire [30:0] out_ui_lshift_expr_FU_32_0_32_186_i3_fu___float_adde8m23b_127nih_501195_502222;
  wire [25:0] out_ui_lshift_expr_FU_32_0_32_187_i0_fu___float_adde8m23b_127nih_501195_501456;
  wire [25:0] out_ui_lshift_expr_FU_32_0_32_187_i1_fu___float_adde8m23b_127nih_501195_501468;
  wire [25:0] out_ui_lshift_expr_FU_32_0_32_187_i2_fu___float_adde8m23b_127nih_501195_503511;
  wire [25:0] out_ui_lshift_expr_FU_32_0_32_187_i3_fu___float_adde8m23b_127nih_501195_503521;
  wire [26:0] out_ui_lshift_expr_FU_32_0_32_187_i4_fu___float_adde8m23b_127nih_501195_503546;
  wire [22:0] out_ui_lshift_expr_FU_32_0_32_188_i0_fu___float_adde8m23b_127nih_501195_502170;
  wire [31:0] out_ui_lshift_expr_FU_32_0_32_189_i0_fu___float_adde8m23b_127nih_501195_502219;
  wire [26:0] out_ui_lshift_expr_FU_32_0_32_190_i0_fu___float_adde8m23b_127nih_501195_503562;
  wire [42:0] out_ui_lshift_expr_FU_64_0_64_191_i0_fu___float_adde8m23b_127nih_501195_501655;
  wire [50:0] out_ui_lshift_expr_FU_64_0_64_192_i0_fu___float_adde8m23b_127nih_501195_501688;
  wire [54:0] out_ui_lshift_expr_FU_64_0_64_193_i0_fu___float_adde8m23b_127nih_501195_501723;
  wire [56:0] out_ui_lshift_expr_FU_64_0_64_194_i0_fu___float_adde8m23b_127nih_501195_501760;
  wire [25:0] out_ui_lshift_expr_FU_64_64_64_195_i0_fu___float_adde8m23b_127nih_501195_501802;
  wire [1:0] out_ui_lshift_expr_FU_8_0_8_196_i0_fu___float_adde8m23b_127nih_501195_503378;
  wire [2:0] out_ui_lshift_expr_FU_8_0_8_197_i0_fu___float_adde8m23b_127nih_501195_503386;
  wire [3:0] out_ui_lshift_expr_FU_8_0_8_198_i0_fu___float_adde8m23b_127nih_501195_503394;
  wire [4:0] out_ui_lshift_expr_FU_8_0_8_199_i0_fu___float_adde8m23b_127nih_501195_503403;
  wire out_ui_lt_expr_FU_32_32_32_200_i0_fu___float_adde8m23b_127nih_501195_502490;
  wire [7:0] out_ui_minus_expr_FU_8_8_8_201_i0_fu___float_adde8m23b_127nih_501195_501436;
  wire out_ui_ne_expr_FU_32_0_32_202_i0_fu___float_adde8m23b_127nih_501195_502535;
  wire out_ui_ne_expr_FU_32_0_32_202_i1_fu___float_adde8m23b_127nih_501195_502538;
  wire out_ui_ne_expr_FU_32_0_32_203_i0_fu___float_adde8m23b_127nih_501195_502578;
  wire [26:0] out_ui_plus_expr_FU_32_32_32_204_i0_fu___float_adde8m23b_127nih_501195_501582;
  wire [30:0] out_ui_plus_expr_FU_32_32_32_204_i1_fu___float_adde8m23b_127nih_501195_502107;
  wire [24:0] out_ui_plus_expr_FU_32_32_32_204_i2_fu___float_adde8m23b_127nih_501195_503543;
  wire [0:0] out_ui_rshift_expr_FU_16_0_16_205_i0_fu___float_adde8m23b_127nih_501195_503696;
  wire [0:0] out_ui_rshift_expr_FU_16_0_16_205_i1_fu___float_adde8m23b_127nih_501195_503705;
  wire [0:0] out_ui_rshift_expr_FU_16_0_16_205_i2_fu___float_adde8m23b_127nih_501195_503714;
  wire [0:0] out_ui_rshift_expr_FU_16_0_16_205_i3_fu___float_adde8m23b_127nih_501195_503723;
  wire [7:0] out_ui_rshift_expr_FU_32_0_32_206_i0_fu___float_adde8m23b_127nih_501195_501319;
  wire [7:0] out_ui_rshift_expr_FU_32_0_32_206_i1_fu___float_adde8m23b_127nih_501195_501347;
  wire [7:0] out_ui_rshift_expr_FU_32_0_32_206_i2_fu___float_adde8m23b_127nih_501195_502116;
  wire [22:0] out_ui_rshift_expr_FU_32_0_32_207_i0_fu___float_adde8m23b_127nih_501195_502058;
  wire [23:0] out_ui_rshift_expr_FU_32_0_32_208_i0_fu___float_adde8m23b_127nih_501195_503506;
  wire [23:0] out_ui_rshift_expr_FU_32_0_32_208_i1_fu___float_adde8m23b_127nih_501195_503514;
  wire [23:0] out_ui_rshift_expr_FU_32_0_32_208_i2_fu___float_adde8m23b_127nih_501195_503517;
  wire [23:0] out_ui_rshift_expr_FU_32_0_32_208_i3_fu___float_adde8m23b_127nih_501195_503524;
  wire [23:0] out_ui_rshift_expr_FU_32_0_32_208_i4_fu___float_adde8m23b_127nih_501195_503538;
  wire [24:0] out_ui_rshift_expr_FU_32_0_32_208_i5_fu___float_adde8m23b_127nih_501195_503541;
  wire [15:0] out_ui_rshift_expr_FU_32_0_32_209_i0_fu___float_adde8m23b_127nih_501195_503557;
  wire [15:0] out_ui_rshift_expr_FU_32_0_32_209_i1_fu___float_adde8m23b_127nih_501195_503565;
  wire [25:0] out_ui_rshift_expr_FU_32_32_32_210_i0_fu___float_adde8m23b_127nih_501195_501533;
  wire [7:0] out_ui_ternary_pm_expr_FU_8_0_8_8_211_i0_fu___float_adde8m23b_127nih_501195_502006;
  
  constant_value #(.BITSIZE_out1(1),
    .value(1'b0)) const_0 (.out1(out_const_0));
  constant_value #(.BITSIZE_out1(1),
    .value(1'b1)) const_1 (.out1(out_const_1));
  constant_value #(.BITSIZE_out1(54),
    .value(54'b100010000001010010011100000000000000000000000000000000)) const_10 (.out1(out_const_10));
  constant_value #(.BITSIZE_out1(29),
    .value(29'b10001000011111101110100001111)) const_11 (.out1(out_const_11));
  constant_value #(.BITSIZE_out1(5),
    .value(5'b10010)) const_12 (.out1(out_const_12));
  constant_value #(.BITSIZE_out1(5),
    .value(5'b10011)) const_13 (.out1(out_const_13));
  constant_value #(.BITSIZE_out1(3),
    .value(3'b101)) const_14 (.out1(out_const_14));
  constant_value #(.BITSIZE_out1(4),
    .value(4'b1010)) const_15 (.out1(out_const_15));
  constant_value #(.BITSIZE_out1(5),
    .value(5'b10100)) const_16 (.out1(out_const_16));
  constant_value #(.BITSIZE_out1(55),
    .value(55'b1010000000000110101001100000000000000000000000000000000)) const_17 (.out1(out_const_17));
  constant_value #(.BITSIZE_out1(12),
    .value(12'b101000001011)) const_18 (.out1(out_const_18));
  constant_value #(.BITSIZE_out1(44),
    .value(44'b10100000101100000000000000000000000000000000)) const_19 (.out1(out_const_19));
  constant_value #(.BITSIZE_out1(2),
    .value(2'b10)) const_2 (.out1(out_const_2));
  constant_value #(.BITSIZE_out1(5),
    .value(5'b10101)) const_20 (.out1(out_const_20));
  constant_value #(.BITSIZE_out1(31),
    .value(31'b1010101000000001101100011011000)) const_21 (.out1(out_const_21));
  constant_value #(.BITSIZE_out1(4),
    .value(4'b1011)) const_22 (.out1(out_const_22));
  constant_value #(.BITSIZE_out1(5),
    .value(5'b10110)) const_23 (.out1(out_const_23));
  constant_value #(.BITSIZE_out1(28),
    .value(28'b1011000010111010000111110100)) const_24 (.out1(out_const_24));
  constant_value #(.BITSIZE_out1(5),
    .value(5'b10111)) const_25 (.out1(out_const_25));
  constant_value #(.BITSIZE_out1(2),
    .value(2'b11)) const_26 (.out1(out_const_26));
  constant_value #(.BITSIZE_out1(3),
    .value(3'b110)) const_27 (.out1(out_const_27));
  constant_value #(.BITSIZE_out1(4),
    .value(4'b1100)) const_28 (.out1(out_const_28));
  constant_value #(.BITSIZE_out1(5),
    .value(5'b11000)) const_29 (.out1(out_const_29));
  constant_value #(.BITSIZE_out1(3),
    .value(3'b100)) const_3 (.out1(out_const_3));
  constant_value #(.BITSIZE_out1(5),
    .value(5'b11001)) const_30 (.out1(out_const_30));
  constant_value #(.BITSIZE_out1(58),
    .value(58'b1100111111000011111111111100000001000111110000011101111111)) const_31 (.out1(out_const_31));
  constant_value #(.BITSIZE_out1(4),
    .value(4'b1101)) const_32 (.out1(out_const_32));
  constant_value #(.BITSIZE_out1(5),
    .value(5'b11010)) const_33 (.out1(out_const_33));
  constant_value #(.BITSIZE_out1(5),
    .value(5'b11011)) const_34 (.out1(out_const_34));
  constant_value #(.BITSIZE_out1(3),
    .value(3'b111)) const_35 (.out1(out_const_35));
  constant_value #(.BITSIZE_out1(4),
    .value(4'b1110)) const_36 (.out1(out_const_36));
  constant_value #(.BITSIZE_out1(5),
    .value(5'b11100)) const_37 (.out1(out_const_37));
  constant_value #(.BITSIZE_out1(64),
    .value(64'b1110000010000000100000001000000011100000111000001110000010000000)) const_38 (.out1(out_const_38));
  constant_value #(.BITSIZE_out1(8),
    .value(8'b11100010)) const_39 (.out1(out_const_39));
  constant_value #(.BITSIZE_out1(4),
    .value(4'b1000)) const_4 (.out1(out_const_4));
  constant_value #(.BITSIZE_out1(5),
    .value(5'b11101)) const_40 (.out1(out_const_40));
  constant_value #(.BITSIZE_out1(32),
    .value(32'b11101110111100000010001011110000)) const_41 (.out1(out_const_41));
  constant_value #(.BITSIZE_out1(32),
    .value(32'b11101111110011001010101000000000)) const_42 (.out1(out_const_42));
  constant_value #(.BITSIZE_out1(4),
    .value(4'b1111)) const_43 (.out1(out_const_43));
  constant_value #(.BITSIZE_out1(5),
    .value(5'b11110)) const_44 (.out1(out_const_44));
  constant_value #(.BITSIZE_out1(8),
    .value(8'b11110100)) const_45 (.out1(out_const_45));
  constant_value #(.BITSIZE_out1(48),
    .value(48'b111101000000000000000000000000000000000000000000)) const_46 (.out1(out_const_46));
  constant_value #(.BITSIZE_out1(32),
    .value(32'b11110100111101000101010000000000)) const_47 (.out1(out_const_47));
  constant_value #(.BITSIZE_out1(64),
    .value(64'b1111010011110100010101000000000000000000000000000000000000000000)) const_48 (.out1(out_const_48));
  constant_value #(.BITSIZE_out1(32),
    .value(32'b11110100111101000101111000001011)) const_49 (.out1(out_const_49));
  constant_value #(.BITSIZE_out1(5),
    .value(5'b10000)) const_5 (.out1(out_const_5));
  constant_value #(.BITSIZE_out1(64),
    .value(64'b1111010011110100111101001111010011110100111101000101010000000000)) const_50 (.out1(out_const_50));
  constant_value #(.BITSIZE_out1(5),
    .value(5'b11111)) const_51 (.out1(out_const_51));
  constant_value #(.BITSIZE_out1(6),
    .value(6'b111111)) const_52 (.out1(out_const_52));
  constant_value #(.BITSIZE_out1(8),
    .value(8'b11111110)) const_53 (.out1(out_const_53));
  constant_value #(.BITSIZE_out1(8),
    .value(8'b11111111)) const_54 (.out1(out_const_54));
  constant_value #(.BITSIZE_out1(64),
    .value(64'b1111111101010101101010100000000011011000110110001101100011011000)) const_55 (.out1(out_const_55));
  constant_value #(.BITSIZE_out1(32),
    .value(32'b11111111111111100000000000000000)) const_56 (.out1(out_const_56));
  constant_value #(.BITSIZE_out1(16),
    .value(16'b1111111111111111)) const_57 (.out1(out_const_57));
  constant_value #(.BITSIZE_out1(32),
    .value(32'b11111111111111110111111111111111)) const_58 (.out1(out_const_58));
  constant_value #(.BITSIZE_out1(64),
    .value(64'b1111111111111111111101011111010011111111111111111111111111111111)) const_59 (.out1(out_const_59));
  constant_value #(.BITSIZE_out1(17),
    .value(17'b10000000000000000)) const_6 (.out1(out_const_6));
  constant_value #(.BITSIZE_out1(23),
    .value(23'b11111111111111111111111)) const_60 (.out1(out_const_60));
  constant_value #(.BITSIZE_out1(64),
    .value(64'b1111111111111111111111110010111111111111111111111111111100001111)) const_61 (.out1(out_const_61));
  constant_value #(.BITSIZE_out1(26),
    .value(26'b11111111111111111111111111)) const_62 (.out1(out_const_62));
  constant_value #(.BITSIZE_out1(27),
    .value(27'b111111111111111111111111111)) const_63 (.out1(out_const_63));
  constant_value #(.BITSIZE_out1(31),
    .value(31'b1111111111111111111111111111111)) const_64 (.out1(out_const_64));
  constant_value #(.BITSIZE_out1(64),
    .value(64'b1111111111111111111111111111111100000000000000001000000000000000)) const_65 (.out1(out_const_65));
  constant_value #(.BITSIZE_out1(62),
    .value(62'b11111111111111111111111111111111111111111111111111111111111111)) const_66 (.out1(out_const_66));
  constant_value #(.BITSIZE_out1(64),
    .value(64'b1111111111111111111111111111111111111111111111111111111111111111)) const_67 (.out1(out_const_67));
  constant_value #(.BITSIZE_out1(64),
    .value(64'b1000000000000000000000000000000000000000000000000000000000000000)) const_7 (.out1(out_const_7));
  constant_value #(.BITSIZE_out1(5),
    .value(5'b10001)) const_8 (.out1(out_const_8));
  constant_value #(.BITSIZE_out1(22),
    .value(22'b1000100000010100100111)) const_9 (.out1(out_const_9));
  UUdata_converter_FU #(.BITSIZE_in1(64),
    .BITSIZE_out1(32)) conv_in_port_a_64_32 (.out1(out_conv_in_port_a_64_32),
    .in1(in_port_a));
  UUdata_converter_FU #(.BITSIZE_in1(64),
    .BITSIZE_out1(32)) conv_in_port_b_64_32 (.out1(out_conv_in_port_b_64_32),
    .in1(in_port_b));
  UUdata_converter_FU #(.BITSIZE_in1(32),
    .BITSIZE_out1(64)) conv_out_ui_bit_ior_expr_FU_0_32_32_171_i0_fu___float_adde8m23b_127nih_501195_502228_32_64 (.out1(out_conv_out_ui_bit_ior_expr_FU_0_32_32_171_i0_fu___float_adde8m23b_127nih_501195_502228_32_64),
    .in1(out_ui_bit_ior_expr_FU_0_32_32_171_i0_fu___float_adde8m23b_127nih_501195_502228));
  ui_bit_and_expr_FU #(.BITSIZE_in1(31),
    .BITSIZE_in2(32),
    .BITSIZE_out1(31)) fu___float_adde8m23b_127nih_501195_501249 (.out1(out_ui_bit_and_expr_FU_0_32_32_157_i0_fu___float_adde8m23b_127nih_501195_501249),
    .in1(out_const_64),
    .in2(out_conv_in_port_a_64_32));
  ui_bit_and_expr_FU #(.BITSIZE_in1(31),
    .BITSIZE_in2(32),
    .BITSIZE_out1(31)) fu___float_adde8m23b_127nih_501195_501254 (.out1(out_ui_bit_and_expr_FU_0_32_32_157_i1_fu___float_adde8m23b_127nih_501195_501254),
    .in1(out_const_64),
    .in2(out_conv_in_port_b_64_32));
  UUdata_converter_FU #(.BITSIZE_in1(1),
    .BITSIZE_out1(1)) fu___float_adde8m23b_127nih_501195_501259 (.out1(out_UUdata_converter_FU_2_i0_fu___float_adde8m23b_127nih_501195_501259),
    .in1(out_ui_lt_expr_FU_32_32_32_200_i0_fu___float_adde8m23b_127nih_501195_502490));
  ui_bit_and_expr_FU #(.BITSIZE_in1(32),
    .BITSIZE_in2(32),
    .BITSIZE_out1(32)) fu___float_adde8m23b_127nih_501195_501268 (.out1(out_ui_bit_and_expr_FU_32_32_32_162_i0_fu___float_adde8m23b_127nih_501195_501268),
    .in1(out_IUdata_converter_FU_4_i0_fu___float_adde8m23b_127nih_501195_502496),
    .in2(out_conv_in_port_b_64_32));
  ui_cond_expr_FU #(.BITSIZE_in1(1),
    .BITSIZE_in2(1),
    .BITSIZE_in3(32),
    .BITSIZE_out1(31)) fu___float_adde8m23b_127nih_501195_501272 (.out1(out_ui_cond_expr_FU_32_32_32_32_180_i0_fu___float_adde8m23b_127nih_501195_501272),
    .in1(out_ui_lt_expr_FU_32_32_32_200_i0_fu___float_adde8m23b_127nih_501195_502490),
    .in2(out_const_0),
    .in3(out_conv_in_port_a_64_32));
  ui_bit_ior_expr_FU #(.BITSIZE_in1(32),
    .BITSIZE_in2(31),
    .BITSIZE_out1(31)) fu___float_adde8m23b_127nih_501195_501275 (.out1(out_ui_bit_ior_expr_FU_32_32_32_176_i0_fu___float_adde8m23b_127nih_501195_501275),
    .in1(out_ui_bit_and_expr_FU_32_32_32_162_i0_fu___float_adde8m23b_127nih_501195_501268),
    .in2(out_ui_cond_expr_FU_32_32_32_32_180_i0_fu___float_adde8m23b_127nih_501195_501272));
  ui_bit_and_expr_FU #(.BITSIZE_in1(32),
    .BITSIZE_in2(32),
    .BITSIZE_out1(32)) fu___float_adde8m23b_127nih_501195_501278 (.out1(out_ui_bit_and_expr_FU_32_32_32_162_i1_fu___float_adde8m23b_127nih_501195_501278),
    .in1(out_IUdata_converter_FU_4_i0_fu___float_adde8m23b_127nih_501195_502496),
    .in2(out_conv_in_port_a_64_32));
  ui_cond_expr_FU #(.BITSIZE_in1(1),
    .BITSIZE_in2(1),
    .BITSIZE_in3(32),
    .BITSIZE_out1(31)) fu___float_adde8m23b_127nih_501195_501282 (.out1(out_ui_cond_expr_FU_32_32_32_32_180_i1_fu___float_adde8m23b_127nih_501195_501282),
    .in1(out_ui_lt_expr_FU_32_32_32_200_i0_fu___float_adde8m23b_127nih_501195_502490),
    .in2(out_const_0),
    .in3(out_conv_in_port_b_64_32));
  ui_bit_ior_expr_FU #(.BITSIZE_in1(32),
    .BITSIZE_in2(31),
    .BITSIZE_out1(31)) fu___float_adde8m23b_127nih_501195_501285 (.out1(out_ui_bit_ior_expr_FU_32_32_32_176_i1_fu___float_adde8m23b_127nih_501195_501285),
    .in1(out_ui_bit_and_expr_FU_32_32_32_162_i1_fu___float_adde8m23b_127nih_501195_501278),
    .in2(out_ui_cond_expr_FU_32_32_32_32_180_i1_fu___float_adde8m23b_127nih_501195_501282));
  ui_bit_and_expr_FU #(.BITSIZE_in1(31),
    .BITSIZE_in2(23),
    .BITSIZE_out1(23)) fu___float_adde8m23b_127nih_501195_501316 (.out1(out_ui_bit_and_expr_FU_32_0_32_159_i0_fu___float_adde8m23b_127nih_501195_501316),
    .in1(out_ui_bit_ior_expr_FU_32_32_32_176_i0_fu___float_adde8m23b_127nih_501195_501275),
    .in2(out_const_60));
  ui_rshift_expr_FU #(.BITSIZE_in1(31),
    .BITSIZE_in2(5),
    .BITSIZE_out1(8),
    .PRECISION(64)) fu___float_adde8m23b_127nih_501195_501319 (.out1(out_ui_rshift_expr_FU_32_0_32_206_i0_fu___float_adde8m23b_127nih_501195_501319),
    .in1(out_ui_bit_ior_expr_FU_32_32_32_176_i0_fu___float_adde8m23b_127nih_501195_501275),
    .in2(out_const_25));
  ui_bit_and_expr_FU #(.BITSIZE_in1(8),
    .BITSIZE_in2(8),
    .BITSIZE_out1(8)) fu___float_adde8m23b_127nih_501195_501331 (.out1(out_ui_bit_and_expr_FU_8_0_8_163_i0_fu___float_adde8m23b_127nih_501195_501331),
    .in1(out_ui_rshift_expr_FU_32_0_32_206_i0_fu___float_adde8m23b_127nih_501195_501319),
    .in2(out_const_54));
  ui_bit_and_expr_FU #(.BITSIZE_in1(31),
    .BITSIZE_in2(23),
    .BITSIZE_out1(23)) fu___float_adde8m23b_127nih_501195_501344 (.out1(out_ui_bit_and_expr_FU_32_0_32_159_i1_fu___float_adde8m23b_127nih_501195_501344),
    .in1(out_ui_bit_ior_expr_FU_32_32_32_176_i1_fu___float_adde8m23b_127nih_501195_501285),
    .in2(out_const_60));
  ui_rshift_expr_FU #(.BITSIZE_in1(31),
    .BITSIZE_in2(5),
    .BITSIZE_out1(8),
    .PRECISION(64)) fu___float_adde8m23b_127nih_501195_501347 (.out1(out_ui_rshift_expr_FU_32_0_32_206_i1_fu___float_adde8m23b_127nih_501195_501347),
    .in1(out_ui_bit_ior_expr_FU_32_32_32_176_i1_fu___float_adde8m23b_127nih_501195_501285),
    .in2(out_const_25));
  ui_bit_and_expr_FU #(.BITSIZE_in1(8),
    .BITSIZE_in2(8),
    .BITSIZE_out1(8)) fu___float_adde8m23b_127nih_501195_501350 (.out1(out_ui_bit_and_expr_FU_8_0_8_163_i1_fu___float_adde8m23b_127nih_501195_501350),
    .in1(out_ui_rshift_expr_FU_32_0_32_206_i1_fu___float_adde8m23b_127nih_501195_501347),
    .in2(out_const_54));
  UUdata_converter_FU #(.BITSIZE_in1(1),
    .BITSIZE_out1(1)) fu___float_adde8m23b_127nih_501195_501391 (.out1(out_UUdata_converter_FU_50_i0_fu___float_adde8m23b_127nih_501195_501391),
    .in1(out_lut_expr_FU_49_i0_fu___float_adde8m23b_127nih_501195_506085));
  UUdata_converter_FU #(.BITSIZE_in1(1),
    .BITSIZE_out1(1)) fu___float_adde8m23b_127nih_501195_501405 (.out1(out_UUdata_converter_FU_55_i0_fu___float_adde8m23b_127nih_501195_501405),
    .in1(out_lut_expr_FU_54_i0_fu___float_adde8m23b_127nih_501195_506102));
  UUdata_converter_FU #(.BITSIZE_in1(1),
    .BITSIZE_out1(1)) fu___float_adde8m23b_127nih_501195_501408 (.out1(out_UUdata_converter_FU_57_i0_fu___float_adde8m23b_127nih_501195_501408),
    .in1(out_lut_expr_FU_56_i0_fu___float_adde8m23b_127nih_501195_506112));
  ui_minus_expr_FU #(.BITSIZE_in1(8),
    .BITSIZE_in2(8),
    .BITSIZE_out1(8)) fu___float_adde8m23b_127nih_501195_501436 (.out1(out_ui_minus_expr_FU_8_8_8_201_i0_fu___float_adde8m23b_127nih_501195_501436),
    .in1(out_ui_bit_and_expr_FU_8_0_8_163_i0_fu___float_adde8m23b_127nih_501195_501331),
    .in2(out_ui_bit_and_expr_FU_8_0_8_163_i1_fu___float_adde8m23b_127nih_501195_501350));
  ui_bit_and_expr_FU #(.BITSIZE_in1(8),
    .BITSIZE_in2(8),
    .BITSIZE_out1(5)) fu___float_adde8m23b_127nih_501195_501441 (.out1(out_ui_bit_and_expr_FU_8_0_8_163_i2_fu___float_adde8m23b_127nih_501195_501441),
    .in1(out_ui_minus_expr_FU_8_8_8_201_i0_fu___float_adde8m23b_127nih_501195_501436),
    .in2(out_const_54));
  UUdata_converter_FU #(.BITSIZE_in1(1),
    .BITSIZE_out1(1)) fu___float_adde8m23b_127nih_501195_501444 (.out1(out_UUdata_converter_FU_58_i0_fu___float_adde8m23b_127nih_501195_501444),
    .in1(out_UUdata_converter_FU_50_i0_fu___float_adde8m23b_127nih_501195_501391));
  ui_lshift_expr_FU #(.BITSIZE_in1(1),
    .BITSIZE_in2(5),
    .BITSIZE_out1(24),
    .PRECISION(64)) fu___float_adde8m23b_127nih_501195_501447 (.out1(out_ui_lshift_expr_FU_32_0_32_186_i0_fu___float_adde8m23b_127nih_501195_501447),
    .in1(out_UUdata_converter_FU_58_i0_fu___float_adde8m23b_127nih_501195_501444),
    .in2(out_const_25));
  ui_bit_ior_expr_FU #(.BITSIZE_in1(24),
    .BITSIZE_in2(23),
    .BITSIZE_out1(24)) fu___float_adde8m23b_127nih_501195_501450 (.out1(out_ui_bit_ior_expr_FU_0_32_32_167_i0_fu___float_adde8m23b_127nih_501195_501450),
    .in1(out_ui_lshift_expr_FU_32_0_32_186_i0_fu___float_adde8m23b_127nih_501195_501447),
    .in2(out_ui_bit_and_expr_FU_32_0_32_159_i0_fu___float_adde8m23b_127nih_501195_501316));
  ui_lshift_expr_FU #(.BITSIZE_in1(24),
    .BITSIZE_in2(2),
    .BITSIZE_out1(26),
    .PRECISION(64)) fu___float_adde8m23b_127nih_501195_501456 (.out1(out_ui_lshift_expr_FU_32_0_32_187_i0_fu___float_adde8m23b_127nih_501195_501456),
    .in1(out_ui_bit_ior_expr_FU_0_32_32_167_i0_fu___float_adde8m23b_127nih_501195_501450),
    .in2(out_const_2));
  UUdata_converter_FU #(.BITSIZE_in1(1),
    .BITSIZE_out1(1)) fu___float_adde8m23b_127nih_501195_501459 (.out1(out_UUdata_converter_FU_59_i0_fu___float_adde8m23b_127nih_501195_501459),
    .in1(out_UUdata_converter_FU_55_i0_fu___float_adde8m23b_127nih_501195_501405));
  ui_lshift_expr_FU #(.BITSIZE_in1(1),
    .BITSIZE_in2(5),
    .BITSIZE_out1(24),
    .PRECISION(64)) fu___float_adde8m23b_127nih_501195_501462 (.out1(out_ui_lshift_expr_FU_32_0_32_186_i1_fu___float_adde8m23b_127nih_501195_501462),
    .in1(out_UUdata_converter_FU_59_i0_fu___float_adde8m23b_127nih_501195_501459),
    .in2(out_const_25));
  ui_bit_ior_expr_FU #(.BITSIZE_in1(24),
    .BITSIZE_in2(23),
    .BITSIZE_out1(24)) fu___float_adde8m23b_127nih_501195_501465 (.out1(out_ui_bit_ior_expr_FU_0_32_32_168_i0_fu___float_adde8m23b_127nih_501195_501465),
    .in1(out_ui_lshift_expr_FU_32_0_32_186_i1_fu___float_adde8m23b_127nih_501195_501462),
    .in2(out_ui_bit_and_expr_FU_32_0_32_159_i1_fu___float_adde8m23b_127nih_501195_501344));
  ui_lshift_expr_FU #(.BITSIZE_in1(24),
    .BITSIZE_in2(2),
    .BITSIZE_out1(26),
    .PRECISION(64)) fu___float_adde8m23b_127nih_501195_501468 (.out1(out_ui_lshift_expr_FU_32_0_32_187_i1_fu___float_adde8m23b_127nih_501195_501468),
    .in1(out_ui_bit_ior_expr_FU_0_32_32_168_i0_fu___float_adde8m23b_127nih_501195_501465),
    .in2(out_const_2));
  UUdata_converter_FU #(.BITSIZE_in1(1),
    .BITSIZE_out1(1)) fu___float_adde8m23b_127nih_501195_501493 (.out1(out_UUdata_converter_FU_64_i0_fu___float_adde8m23b_127nih_501195_501493),
    .in1(out_lut_expr_FU_63_i0_fu___float_adde8m23b_127nih_501195_502570));
  UUdata_converter_FU #(.BITSIZE_in1(5),
    .BITSIZE_out1(5)) fu___float_adde8m23b_127nih_501195_501502 (.out1(out_UUdata_converter_FU_67_i0_fu___float_adde8m23b_127nih_501195_501502),
    .in1(out_IUdata_converter_FU_66_i0_fu___float_adde8m23b_127nih_501195_502576));
  ui_bit_ior_expr_FU #(.BITSIZE_in1(5),
    .BITSIZE_in2(5),
    .BITSIZE_out1(5)) fu___float_adde8m23b_127nih_501195_501506 (.out1(out_ui_bit_ior_expr_FU_8_8_8_177_i0_fu___float_adde8m23b_127nih_501195_501506),
    .in1(out_ui_bit_and_expr_FU_8_0_8_163_i2_fu___float_adde8m23b_127nih_501195_501441),
    .in2(out_UUdata_converter_FU_67_i0_fu___float_adde8m23b_127nih_501195_501502));
  ui_bit_and_expr_FU #(.BITSIZE_in1(5),
    .BITSIZE_in2(5),
    .BITSIZE_out1(5)) fu___float_adde8m23b_127nih_501195_501515 (.out1(out_ui_bit_and_expr_FU_8_0_8_164_i0_fu___float_adde8m23b_127nih_501195_501515),
    .in1(out_ui_bit_ior_expr_FU_8_8_8_177_i0_fu___float_adde8m23b_127nih_501195_501506),
    .in2(out_const_51));
  ui_lshift_expr_FU #(.BITSIZE_in1(64),
    .BITSIZE_in2(5),
    .BITSIZE_out1(26),
    .PRECISION(64)) fu___float_adde8m23b_127nih_501195_501518 (.out1(out_ui_lshift_expr_FU_0_64_64_184_i0_fu___float_adde8m23b_127nih_501195_501518),
    .in1(out_const_67),
    .in2(out_ui_bit_and_expr_FU_8_0_8_164_i0_fu___float_adde8m23b_127nih_501195_501515));
  ui_bit_xor_expr_FU #(.BITSIZE_in1(24),
    .BITSIZE_in2(62),
    .BITSIZE_out1(24)) fu___float_adde8m23b_127nih_501195_501521 (.out1(out_ui_bit_xor_expr_FU_32_0_32_178_i0_fu___float_adde8m23b_127nih_501195_501521),
    .in1(out_ui_rshift_expr_FU_32_0_32_208_i0_fu___float_adde8m23b_127nih_501195_503506),
    .in2(out_const_66));
  ui_bit_and_expr_FU #(.BITSIZE_in1(24),
    .BITSIZE_in2(24),
    .BITSIZE_out1(24)) fu___float_adde8m23b_127nih_501195_501524 (.out1(out_ui_bit_and_expr_FU_32_32_32_162_i2_fu___float_adde8m23b_127nih_501195_501524),
    .in1(out_ui_rshift_expr_FU_32_0_32_208_i1_fu___float_adde8m23b_127nih_501195_503514),
    .in2(out_ui_rshift_expr_FU_32_0_32_208_i2_fu___float_adde8m23b_127nih_501195_503517));
  ui_rshift_expr_FU #(.BITSIZE_in1(26),
    .BITSIZE_in2(5),
    .BITSIZE_out1(26),
    .PRECISION(64)) fu___float_adde8m23b_127nih_501195_501533 (.out1(out_ui_rshift_expr_FU_32_32_32_210_i0_fu___float_adde8m23b_127nih_501195_501533),
    .in1(out_ui_lshift_expr_FU_32_0_32_187_i1_fu___float_adde8m23b_127nih_501195_501468),
    .in2(out_ui_bit_and_expr_FU_8_0_8_164_i0_fu___float_adde8m23b_127nih_501195_501515));
  ui_bit_and_expr_FU #(.BITSIZE_in1(26),
    .BITSIZE_in2(26),
    .BITSIZE_out1(26)) fu___float_adde8m23b_127nih_501195_501545 (.out1(out_ui_bit_and_expr_FU_32_0_32_160_i0_fu___float_adde8m23b_127nih_501195_501545),
    .in1(out_ui_rshift_expr_FU_32_32_32_210_i0_fu___float_adde8m23b_127nih_501195_501533),
    .in2(out_const_62));
  ui_bit_xor_expr_FU #(.BITSIZE_in1(26),
    .BITSIZE_in2(27),
    .BITSIZE_out1(27)) fu___float_adde8m23b_127nih_501195_501554 (.out1(out_ui_bit_xor_expr_FU_32_32_32_179_i0_fu___float_adde8m23b_127nih_501195_501554),
    .in1(out_ui_bit_and_expr_FU_32_0_32_160_i0_fu___float_adde8m23b_127nih_501195_501545),
    .in2(out_IUdata_converter_FU_69_i0_fu___float_adde8m23b_127nih_501195_502586));
  ui_bit_and_expr_FU #(.BITSIZE_in1(27),
    .BITSIZE_in2(27),
    .BITSIZE_out1(27)) fu___float_adde8m23b_127nih_501195_501570 (.out1(out_ui_bit_and_expr_FU_32_0_32_161_i0_fu___float_adde8m23b_127nih_501195_501570),
    .in1(out_ui_bit_xor_expr_FU_32_32_32_179_i0_fu___float_adde8m23b_127nih_501195_501554),
    .in2(out_const_63));
  UUdata_converter_FU #(.BITSIZE_in1(1),
    .BITSIZE_out1(1)) fu___float_adde8m23b_127nih_501195_501576 (.out1(out_UUdata_converter_FU_71_i0_fu___float_adde8m23b_127nih_501195_501576),
    .in1(out_lut_expr_FU_70_i0_fu___float_adde8m23b_127nih_501195_506136));
  UUdata_converter_FU #(.BITSIZE_in1(1),
    .BITSIZE_out1(1)) fu___float_adde8m23b_127nih_501195_501579 (.out1(out_UUdata_converter_FU_72_i0_fu___float_adde8m23b_127nih_501195_501579),
    .in1(out_UUdata_converter_FU_71_i0_fu___float_adde8m23b_127nih_501195_501576));
  ui_plus_expr_FU #(.BITSIZE_in1(1),
    .BITSIZE_in2(27),
    .BITSIZE_out1(27)) fu___float_adde8m23b_127nih_501195_501582 (.out1(out_ui_plus_expr_FU_32_32_32_204_i0_fu___float_adde8m23b_127nih_501195_501582),
    .in1(out_UUdata_converter_FU_72_i0_fu___float_adde8m23b_127nih_501195_501579),
    .in2(out_reg_0_reg_0));
  ui_bit_ior_concat_expr_FU #(.BITSIZE_in1(27),
    .BITSIZE_in2(2),
    .BITSIZE_in3(2),
    .BITSIZE_out1(27),
    .OFFSET_PARAMETER(2)) fu___float_adde8m23b_127nih_501195_501585 (.out1(out_ui_bit_ior_concat_expr_FU_166_i0_fu___float_adde8m23b_127nih_501195_501585),
    .in1(out_ui_lshift_expr_FU_32_0_32_187_i4_fu___float_adde8m23b_127nih_501195_503546),
    .in2(out_ui_bit_and_expr_FU_8_0_8_165_i0_fu___float_adde8m23b_127nih_501195_503550),
    .in3(out_const_2));
  ui_bit_and_expr_FU #(.BITSIZE_in1(27),
    .BITSIZE_in2(27),
    .BITSIZE_out1(27)) fu___float_adde8m23b_127nih_501195_501588 (.out1(out_ui_bit_and_expr_FU_32_0_32_161_i1_fu___float_adde8m23b_127nih_501195_501588),
    .in1(out_ui_bit_ior_concat_expr_FU_166_i0_fu___float_adde8m23b_127nih_501195_501585),
    .in2(out_const_63));
  ui_bit_and_expr_FU #(.BITSIZE_in1(16),
    .BITSIZE_in2(16),
    .BITSIZE_out1(16)) fu___float_adde8m23b_127nih_501195_501647 (.out1(out_ui_bit_and_expr_FU_16_0_16_158_i0_fu___float_adde8m23b_127nih_501195_501647),
    .in1(out_ui_rshift_expr_FU_32_0_32_209_i0_fu___float_adde8m23b_127nih_501195_503557),
    .in2(out_const_57));
  ui_lshift_expr_FU #(.BITSIZE_in1(27),
    .BITSIZE_in2(5),
    .BITSIZE_out1(43),
    .PRECISION(64)) fu___float_adde8m23b_127nih_501195_501655 (.out1(out_ui_lshift_expr_FU_64_0_64_191_i0_fu___float_adde8m23b_127nih_501195_501655),
    .in1(out_ui_bit_and_expr_FU_32_0_32_161_i1_fu___float_adde8m23b_127nih_501195_501588),
    .in2(out_const_5));
  ui_cond_expr_FU #(.BITSIZE_in1(1),
    .BITSIZE_in2(43),
    .BITSIZE_in3(27),
    .BITSIZE_out1(43)) fu___float_adde8m23b_127nih_501195_501658 (.out1(out_ui_cond_expr_FU_64_64_64_64_181_i0_fu___float_adde8m23b_127nih_501195_501658),
    .in1(out_reg_29_reg_29),
    .in2(out_reg_27_reg_27),
    .in3(out_reg_26_reg_26));
  ui_lshift_expr_FU #(.BITSIZE_in1(43),
    .BITSIZE_in2(4),
    .BITSIZE_out1(51),
    .PRECISION(64)) fu___float_adde8m23b_127nih_501195_501688 (.out1(out_ui_lshift_expr_FU_64_0_64_192_i0_fu___float_adde8m23b_127nih_501195_501688),
    .in1(out_ui_cond_expr_FU_64_64_64_64_181_i0_fu___float_adde8m23b_127nih_501195_501658),
    .in2(out_const_4));
  ui_cond_expr_FU #(.BITSIZE_in1(1),
    .BITSIZE_in2(51),
    .BITSIZE_in3(43),
    .BITSIZE_out1(51)) fu___float_adde8m23b_127nih_501195_501691 (.out1(out_ui_cond_expr_FU_64_64_64_64_181_i1_fu___float_adde8m23b_127nih_501195_501691),
    .in1(out_lut_expr_FU_92_i0_fu___float_adde8m23b_127nih_501195_502641),
    .in2(out_ui_lshift_expr_FU_64_0_64_192_i0_fu___float_adde8m23b_127nih_501195_501688),
    .in3(out_ui_cond_expr_FU_64_64_64_64_181_i0_fu___float_adde8m23b_127nih_501195_501658));
  ui_lshift_expr_FU #(.BITSIZE_in1(51),
    .BITSIZE_in2(3),
    .BITSIZE_out1(55),
    .PRECISION(64)) fu___float_adde8m23b_127nih_501195_501723 (.out1(out_ui_lshift_expr_FU_64_0_64_193_i0_fu___float_adde8m23b_127nih_501195_501723),
    .in1(out_ui_cond_expr_FU_64_64_64_64_181_i1_fu___float_adde8m23b_127nih_501195_501691),
    .in2(out_const_3));
  ui_cond_expr_FU #(.BITSIZE_in1(1),
    .BITSIZE_in2(55),
    .BITSIZE_in3(51),
    .BITSIZE_out1(55)) fu___float_adde8m23b_127nih_501195_501726 (.out1(out_ui_cond_expr_FU_64_64_64_64_181_i2_fu___float_adde8m23b_127nih_501195_501726),
    .in1(out_lut_expr_FU_107_i0_fu___float_adde8m23b_127nih_501195_502650),
    .in2(out_ui_lshift_expr_FU_64_0_64_193_i0_fu___float_adde8m23b_127nih_501195_501723),
    .in3(out_ui_cond_expr_FU_64_64_64_64_181_i1_fu___float_adde8m23b_127nih_501195_501691));
  ui_lshift_expr_FU #(.BITSIZE_in1(55),
    .BITSIZE_in2(2),
    .BITSIZE_out1(57),
    .PRECISION(64)) fu___float_adde8m23b_127nih_501195_501760 (.out1(out_ui_lshift_expr_FU_64_0_64_194_i0_fu___float_adde8m23b_127nih_501195_501760),
    .in1(out_ui_cond_expr_FU_64_64_64_64_181_i2_fu___float_adde8m23b_127nih_501195_501726),
    .in2(out_const_2));
  ui_cond_expr_FU #(.BITSIZE_in1(1),
    .BITSIZE_in2(57),
    .BITSIZE_in3(55),
    .BITSIZE_out1(57)) fu___float_adde8m23b_127nih_501195_501763 (.out1(out_ui_cond_expr_FU_64_64_64_64_181_i3_fu___float_adde8m23b_127nih_501195_501763),
    .in1(out_lut_expr_FU_112_i0_fu___float_adde8m23b_127nih_501195_502659),
    .in2(out_ui_lshift_expr_FU_64_0_64_194_i0_fu___float_adde8m23b_127nih_501195_501760),
    .in3(out_ui_cond_expr_FU_64_64_64_64_181_i2_fu___float_adde8m23b_127nih_501195_501726));
  UUdata_converter_FU #(.BITSIZE_in1(1),
    .BITSIZE_out1(1)) fu___float_adde8m23b_127nih_501195_501796 (.out1(out_UUdata_converter_FU_114_i0_fu___float_adde8m23b_127nih_501195_501796),
    .in1(out_lut_expr_FU_113_i0_fu___float_adde8m23b_127nih_501195_502664));
  UUdata_converter_FU #(.BITSIZE_in1(1),
    .BITSIZE_out1(1)) fu___float_adde8m23b_127nih_501195_501799 (.out1(out_UUdata_converter_FU_115_i0_fu___float_adde8m23b_127nih_501195_501799),
    .in1(out_UUdata_converter_FU_114_i0_fu___float_adde8m23b_127nih_501195_501796));
  ui_lshift_expr_FU #(.BITSIZE_in1(57),
    .BITSIZE_in2(1),
    .BITSIZE_out1(26),
    .PRECISION(64)) fu___float_adde8m23b_127nih_501195_501802 (.out1(out_ui_lshift_expr_FU_64_64_64_195_i0_fu___float_adde8m23b_127nih_501195_501802),
    .in1(out_ui_cond_expr_FU_64_64_64_64_181_i3_fu___float_adde8m23b_127nih_501195_501763),
    .in2(out_UUdata_converter_FU_115_i0_fu___float_adde8m23b_127nih_501195_501799));
  UUdata_converter_FU #(.BITSIZE_in1(1),
    .BITSIZE_out1(1)) fu___float_adde8m23b_127nih_501195_501886 (.out1(out_UUdata_converter_FU_116_i0_fu___float_adde8m23b_127nih_501195_501886),
    .in1(out_UUdata_converter_FU_114_i0_fu___float_adde8m23b_127nih_501195_501796));
  ui_bit_ior_expr_FU #(.BITSIZE_in1(5),
    .BITSIZE_in2(2),
    .BITSIZE_out1(5)) fu___float_adde8m23b_127nih_501195_501901 (.out1(out_ui_bit_ior_expr_FU_0_8_8_172_i0_fu___float_adde8m23b_127nih_501195_501901),
    .in1(out_ui_bit_ior_expr_FU_0_8_8_173_i0_fu___float_adde8m23b_127nih_501195_501904),
    .in2(out_ui_lshift_expr_FU_8_0_8_196_i0_fu___float_adde8m23b_127nih_501195_503378));
  ui_bit_ior_expr_FU #(.BITSIZE_in1(5),
    .BITSIZE_in2(3),
    .BITSIZE_out1(5)) fu___float_adde8m23b_127nih_501195_501904 (.out1(out_ui_bit_ior_expr_FU_0_8_8_173_i0_fu___float_adde8m23b_127nih_501195_501904),
    .in1(out_ui_bit_ior_expr_FU_0_8_8_174_i0_fu___float_adde8m23b_127nih_501195_501907),
    .in2(out_ui_lshift_expr_FU_8_0_8_197_i0_fu___float_adde8m23b_127nih_501195_503386));
  ui_bit_ior_expr_FU #(.BITSIZE_in1(5),
    .BITSIZE_in2(4),
    .BITSIZE_out1(5)) fu___float_adde8m23b_127nih_501195_501907 (.out1(out_ui_bit_ior_expr_FU_0_8_8_174_i0_fu___float_adde8m23b_127nih_501195_501907),
    .in1(out_ui_bit_ior_expr_FU_0_8_8_175_i0_fu___float_adde8m23b_127nih_501195_501910),
    .in2(out_ui_lshift_expr_FU_8_0_8_198_i0_fu___float_adde8m23b_127nih_501195_503394));
  ui_bit_ior_expr_FU #(.BITSIZE_in1(5),
    .BITSIZE_in2(1),
    .BITSIZE_out1(5)) fu___float_adde8m23b_127nih_501195_501910 (.out1(out_ui_bit_ior_expr_FU_0_8_8_175_i0_fu___float_adde8m23b_127nih_501195_501910),
    .in1(out_ui_lshift_expr_FU_8_0_8_199_i0_fu___float_adde8m23b_127nih_501195_503403),
    .in2(out_UUdata_converter_FU_116_i0_fu___float_adde8m23b_127nih_501195_501886));
  UUdata_converter_FU #(.BITSIZE_in1(5),
    .BITSIZE_out1(5)) fu___float_adde8m23b_127nih_501195_501937 (.out1(out_UUdata_converter_FU_121_i0_fu___float_adde8m23b_127nih_501195_501937),
    .in1(out_ui_bit_ior_expr_FU_0_8_8_172_i0_fu___float_adde8m23b_127nih_501195_501901));
  ui_ternary_pm_expr_FU #(.BITSIZE_in1(8),
    .BITSIZE_in2(1),
    .BITSIZE_in3(5),
    .BITSIZE_out1(8)) fu___float_adde8m23b_127nih_501195_502006 (.out1(out_ui_ternary_pm_expr_FU_8_0_8_8_211_i0_fu___float_adde8m23b_127nih_501195_502006),
    .in1(out_reg_6_reg_6),
    .in2(out_const_1),
    .in3(out_UUdata_converter_FU_121_i0_fu___float_adde8m23b_127nih_501195_501937));
  ui_cond_expr_FU #(.BITSIZE_in1(1),
    .BITSIZE_in2(1),
    .BITSIZE_in3(8),
    .BITSIZE_out1(8)) fu___float_adde8m23b_127nih_501195_502009 (.out1(out_ui_cond_expr_FU_8_8_8_8_182_i0_fu___float_adde8m23b_127nih_501195_502009),
    .in1(out_lut_expr_FU_127_i0_fu___float_adde8m23b_127nih_501195_502758),
    .in2(out_const_0),
    .in3(out_ui_ternary_pm_expr_FU_8_0_8_8_211_i0_fu___float_adde8m23b_127nih_501195_502006));
  ui_bit_and_expr_FU #(.BITSIZE_in1(8),
    .BITSIZE_in2(8),
    .BITSIZE_out1(8)) fu___float_adde8m23b_127nih_501195_502049 (.out1(out_ui_bit_and_expr_FU_8_0_8_163_i3_fu___float_adde8m23b_127nih_501195_502049),
    .in1(out_ui_cond_expr_FU_8_8_8_8_182_i0_fu___float_adde8m23b_127nih_501195_502009),
    .in2(out_const_54));
  ui_rshift_expr_FU #(.BITSIZE_in1(26),
    .BITSIZE_in2(2),
    .BITSIZE_out1(23),
    .PRECISION(64)) fu___float_adde8m23b_127nih_501195_502058 (.out1(out_ui_rshift_expr_FU_32_0_32_207_i0_fu___float_adde8m23b_127nih_501195_502058),
    .in1(out_ui_lshift_expr_FU_64_64_64_195_i0_fu___float_adde8m23b_127nih_501195_501802),
    .in2(out_const_26));
  ui_bit_and_expr_FU #(.BITSIZE_in1(23),
    .BITSIZE_in2(23),
    .BITSIZE_out1(23)) fu___float_adde8m23b_127nih_501195_502061 (.out1(out_ui_bit_and_expr_FU_32_0_32_159_i2_fu___float_adde8m23b_127nih_501195_502061),
    .in1(out_ui_rshift_expr_FU_32_0_32_207_i0_fu___float_adde8m23b_127nih_501195_502058),
    .in2(out_const_60));
  ui_lshift_expr_FU #(.BITSIZE_in1(8),
    .BITSIZE_in2(5),
    .BITSIZE_out1(31),
    .PRECISION(64)) fu___float_adde8m23b_127nih_501195_502064 (.out1(out_ui_lshift_expr_FU_32_0_32_186_i2_fu___float_adde8m23b_127nih_501195_502064),
    .in1(out_ui_bit_and_expr_FU_8_0_8_163_i3_fu___float_adde8m23b_127nih_501195_502049),
    .in2(out_const_25));
  ui_bit_ior_expr_FU #(.BITSIZE_in1(31),
    .BITSIZE_in2(23),
    .BITSIZE_out1(31)) fu___float_adde8m23b_127nih_501195_502067 (.out1(out_ui_bit_ior_expr_FU_0_32_32_169_i0_fu___float_adde8m23b_127nih_501195_502067),
    .in1(out_ui_lshift_expr_FU_32_0_32_186_i2_fu___float_adde8m23b_127nih_501195_502064),
    .in2(out_ui_bit_and_expr_FU_32_0_32_159_i2_fu___float_adde8m23b_127nih_501195_502061));
  UUdata_converter_FU #(.BITSIZE_in1(1),
    .BITSIZE_out1(1)) fu___float_adde8m23b_127nih_501195_502101 (.out1(out_UUdata_converter_FU_133_i0_fu___float_adde8m23b_127nih_501195_502101),
    .in1(out_lut_expr_FU_132_i0_fu___float_adde8m23b_127nih_501195_506322));
  UUdata_converter_FU #(.BITSIZE_in1(1),
    .BITSIZE_out1(1)) fu___float_adde8m23b_127nih_501195_502104 (.out1(out_UUdata_converter_FU_134_i0_fu___float_adde8m23b_127nih_501195_502104),
    .in1(out_UUdata_converter_FU_133_i0_fu___float_adde8m23b_127nih_501195_502101));
  ui_plus_expr_FU #(.BITSIZE_in1(31),
    .BITSIZE_in2(1),
    .BITSIZE_out1(31)) fu___float_adde8m23b_127nih_501195_502107 (.out1(out_ui_plus_expr_FU_32_32_32_204_i1_fu___float_adde8m23b_127nih_501195_502107),
    .in1(out_reg_58_reg_58),
    .in2(out_reg_59_reg_59));
  ui_rshift_expr_FU #(.BITSIZE_in1(31),
    .BITSIZE_in2(5),
    .BITSIZE_out1(8),
    .PRECISION(64)) fu___float_adde8m23b_127nih_501195_502116 (.out1(out_ui_rshift_expr_FU_32_0_32_206_i2_fu___float_adde8m23b_127nih_501195_502116),
    .in1(out_ui_plus_expr_FU_32_32_32_204_i1_fu___float_adde8m23b_127nih_501195_502107),
    .in2(out_const_25));
  ui_cond_expr_FU #(.BITSIZE_in1(1),
    .BITSIZE_in2(64),
    .BITSIZE_in3(8),
    .BITSIZE_out1(8)) fu___float_adde8m23b_127nih_501195_502119 (.out1(out_ui_cond_expr_FU_8_8_8_8_182_i1_fu___float_adde8m23b_127nih_501195_502119),
    .in1(out_reg_3_reg_3),
    .in2(out_const_67),
    .in3(out_ui_rshift_expr_FU_32_0_32_206_i2_fu___float_adde8m23b_127nih_501195_502116));
  ui_bit_and_expr_FU #(.BITSIZE_in1(31),
    .BITSIZE_in2(23),
    .BITSIZE_out1(23)) fu___float_adde8m23b_127nih_501195_502128 (.out1(out_ui_bit_and_expr_FU_32_0_32_159_i3_fu___float_adde8m23b_127nih_501195_502128),
    .in1(out_ui_plus_expr_FU_32_32_32_204_i1_fu___float_adde8m23b_127nih_501195_502107),
    .in2(out_const_60));
  ui_cond_expr_FU #(.BITSIZE_in1(1),
    .BITSIZE_in2(1),
    .BITSIZE_in3(23),
    .BITSIZE_out1(23)) fu___float_adde8m23b_127nih_501195_502134 (.out1(out_ui_cond_expr_FU_32_32_32_32_180_i2_fu___float_adde8m23b_127nih_501195_502134),
    .in1(out_reg_61_reg_61),
    .in2(out_const_0),
    .in3(out_ui_bit_and_expr_FU_32_0_32_159_i3_fu___float_adde8m23b_127nih_501195_502128));
  UUdata_converter_FU #(.BITSIZE_in1(1),
    .BITSIZE_out1(1)) fu___float_adde8m23b_127nih_501195_502143 (.out1(out_UUdata_converter_FU_146_i0_fu___float_adde8m23b_127nih_501195_502143),
    .in1(out_lut_expr_FU_145_i0_fu___float_adde8m23b_127nih_501195_506377));
  UUdata_converter_FU #(.BITSIZE_in1(1),
    .BITSIZE_out1(1)) fu___float_adde8m23b_127nih_501195_502158 (.out1(out_UUdata_converter_FU_149_i0_fu___float_adde8m23b_127nih_501195_502158),
    .in1(out_lut_expr_FU_148_i0_fu___float_adde8m23b_127nih_501195_506397));
  UUdata_converter_FU #(.BITSIZE_in1(1),
    .BITSIZE_out1(1)) fu___float_adde8m23b_127nih_501195_502161 (.out1(out_UUdata_converter_FU_150_i0_fu___float_adde8m23b_127nih_501195_502161),
    .in1(out_UUdata_converter_FU_149_i0_fu___float_adde8m23b_127nih_501195_502158));
  ui_lshift_expr_FU #(.BITSIZE_in1(1),
    .BITSIZE_in2(5),
    .BITSIZE_out1(23),
    .PRECISION(64)) fu___float_adde8m23b_127nih_501195_502170 (.out1(out_ui_lshift_expr_FU_32_0_32_188_i0_fu___float_adde8m23b_127nih_501195_502170),
    .in1(out_UUdata_converter_FU_150_i0_fu___float_adde8m23b_127nih_501195_502161),
    .in2(out_const_23));
  ui_bit_ior_expr_FU #(.BITSIZE_in1(23),
    .BITSIZE_in2(23),
    .BITSIZE_out1(23)) fu___float_adde8m23b_127nih_501195_502173 (.out1(out_ui_bit_ior_expr_FU_32_32_32_176_i2_fu___float_adde8m23b_127nih_501195_502173),
    .in1(out_ui_cond_expr_FU_32_32_32_32_180_i2_fu___float_adde8m23b_127nih_501195_502134),
    .in2(out_reg_1_reg_1));
  ui_bit_and_expr_FU #(.BITSIZE_in1(8),
    .BITSIZE_in2(8),
    .BITSIZE_out1(8)) fu___float_adde8m23b_127nih_501195_502213 (.out1(out_ui_bit_and_expr_FU_8_0_8_163_i4_fu___float_adde8m23b_127nih_501195_502213),
    .in1(out_ui_cond_expr_FU_8_8_8_8_182_i1_fu___float_adde8m23b_127nih_501195_502119),
    .in2(out_const_54));
  UUdata_converter_FU #(.BITSIZE_in1(1),
    .BITSIZE_out1(1)) fu___float_adde8m23b_127nih_501195_502216 (.out1(out_UUdata_converter_FU_151_i0_fu___float_adde8m23b_127nih_501195_502216),
    .in1(out_UUdata_converter_FU_146_i0_fu___float_adde8m23b_127nih_501195_502143));
  ui_lshift_expr_FU #(.BITSIZE_in1(1),
    .BITSIZE_in2(5),
    .BITSIZE_out1(32),
    .PRECISION(64)) fu___float_adde8m23b_127nih_501195_502219 (.out1(out_ui_lshift_expr_FU_32_0_32_189_i0_fu___float_adde8m23b_127nih_501195_502219),
    .in1(out_UUdata_converter_FU_151_i0_fu___float_adde8m23b_127nih_501195_502216),
    .in2(out_const_51));
  ui_lshift_expr_FU #(.BITSIZE_in1(8),
    .BITSIZE_in2(5),
    .BITSIZE_out1(31),
    .PRECISION(64)) fu___float_adde8m23b_127nih_501195_502222 (.out1(out_ui_lshift_expr_FU_32_0_32_186_i3_fu___float_adde8m23b_127nih_501195_502222),
    .in1(out_ui_bit_and_expr_FU_8_0_8_163_i4_fu___float_adde8m23b_127nih_501195_502213),
    .in2(out_const_25));
  ui_bit_ior_expr_FU #(.BITSIZE_in1(23),
    .BITSIZE_in2(32),
    .BITSIZE_out1(32)) fu___float_adde8m23b_127nih_501195_502225 (.out1(out_ui_bit_ior_expr_FU_0_32_32_170_i0_fu___float_adde8m23b_127nih_501195_502225),
    .in1(out_ui_bit_ior_expr_FU_32_32_32_176_i2_fu___float_adde8m23b_127nih_501195_502173),
    .in2(out_reg_60_reg_60));
  ui_bit_ior_expr_FU #(.BITSIZE_in1(32),
    .BITSIZE_in2(31),
    .BITSIZE_out1(32)) fu___float_adde8m23b_127nih_501195_502228 (.out1(out_ui_bit_ior_expr_FU_0_32_32_171_i0_fu___float_adde8m23b_127nih_501195_502228),
    .in1(out_ui_bit_ior_expr_FU_0_32_32_170_i0_fu___float_adde8m23b_127nih_501195_502225),
    .in2(out_ui_lshift_expr_FU_32_0_32_186_i3_fu___float_adde8m23b_127nih_501195_502222));
  ui_lt_expr_FU #(.BITSIZE_in1(31),
    .BITSIZE_in2(31),
    .BITSIZE_out1(1)) fu___float_adde8m23b_127nih_501195_502490 (.out1(out_ui_lt_expr_FU_32_32_32_200_i0_fu___float_adde8m23b_127nih_501195_502490),
    .in1(out_ui_bit_and_expr_FU_0_32_32_157_i0_fu___float_adde8m23b_127nih_501195_501249),
    .in2(out_ui_bit_and_expr_FU_0_32_32_157_i1_fu___float_adde8m23b_127nih_501195_501254));
  rshift_expr_FU #(.BITSIZE_in1(64),
    .BITSIZE_in2(6),
    .BITSIZE_out1(1),
    .PRECISION(64)) fu___float_adde8m23b_127nih_501195_502493 (.out1(out_rshift_expr_FU_64_0_64_156_i0_fu___float_adde8m23b_127nih_501195_502493),
    .in1(out_lshift_expr_FU_64_0_64_154_i0_fu___float_adde8m23b_127nih_501195_502550),
    .in2(out_const_52));
  IUdata_converter_FU #(.BITSIZE_in1(1),
    .BITSIZE_out1(32)) fu___float_adde8m23b_127nih_501195_502496 (.out1(out_IUdata_converter_FU_4_i0_fu___float_adde8m23b_127nih_501195_502496),
    .in1(out_rshift_expr_FU_64_0_64_156_i0_fu___float_adde8m23b_127nih_501195_502493));
  ui_ne_expr_FU #(.BITSIZE_in1(23),
    .BITSIZE_in2(1),
    .BITSIZE_out1(1)) fu___float_adde8m23b_127nih_501195_502535 (.out1(out_ui_ne_expr_FU_32_0_32_202_i0_fu___float_adde8m23b_127nih_501195_502535),
    .in1(out_ui_bit_and_expr_FU_32_0_32_159_i0_fu___float_adde8m23b_127nih_501195_501316),
    .in2(out_const_0));
  ui_ne_expr_FU #(.BITSIZE_in1(23),
    .BITSIZE_in2(1),
    .BITSIZE_out1(1)) fu___float_adde8m23b_127nih_501195_502538 (.out1(out_ui_ne_expr_FU_32_0_32_202_i1_fu___float_adde8m23b_127nih_501195_502538),
    .in1(out_ui_bit_and_expr_FU_32_0_32_159_i1_fu___float_adde8m23b_127nih_501195_501344),
    .in2(out_const_0));
  lshift_expr_FU #(.BITSIZE_in1(2),
    .BITSIZE_in2(6),
    .BITSIZE_out1(64),
    .PRECISION(64)) fu___float_adde8m23b_127nih_501195_502550 (.out1(out_lshift_expr_FU_64_0_64_154_i0_fu___float_adde8m23b_127nih_501195_502550),
    .in1(out_UIdata_converter_FU_3_i0_fu___float_adde8m23b_127nih_501195_502553),
    .in2(out_const_52));
  UIdata_converter_FU #(.BITSIZE_in1(1),
    .BITSIZE_out1(2)) fu___float_adde8m23b_127nih_501195_502553 (.out1(out_UIdata_converter_FU_3_i0_fu___float_adde8m23b_127nih_501195_502553),
    .in1(out_UUdata_converter_FU_2_i0_fu___float_adde8m23b_127nih_501195_501259));
  lut_expr_FU #(.BITSIZE_in1(8),
    .BITSIZE_out1(1)) fu___float_adde8m23b_127nih_501195_502570 (.out1(out_lut_expr_FU_63_i0_fu___float_adde8m23b_127nih_501195_502570),
    .in1(out_const_53),
    .in2(out_ui_extract_bit_expr_FU_60_i0_fu___float_adde8m23b_127nih_501195_506992),
    .in3(out_ui_extract_bit_expr_FU_61_i0_fu___float_adde8m23b_127nih_501195_506996),
    .in4(out_ui_extract_bit_expr_FU_62_i0_fu___float_adde8m23b_127nih_501195_507000),
    .in5(1'b0),
    .in6(1'b0),
    .in7(1'b0),
    .in8(1'b0),
    .in9(1'b0));
  rshift_expr_FU #(.BITSIZE_in1(32),
    .BITSIZE_in2(5),
    .BITSIZE_out1(1),
    .PRECISION(32)) fu___float_adde8m23b_127nih_501195_502573 (.out1(out_rshift_expr_FU_32_0_32_155_i0_fu___float_adde8m23b_127nih_501195_502573),
    .in1(out_lshift_expr_FU_32_0_32_153_i0_fu___float_adde8m23b_127nih_501195_502594),
    .in2(out_const_51));
  IUdata_converter_FU #(.BITSIZE_in1(1),
    .BITSIZE_out1(5)) fu___float_adde8m23b_127nih_501195_502576 (.out1(out_IUdata_converter_FU_66_i0_fu___float_adde8m23b_127nih_501195_502576),
    .in1(out_rshift_expr_FU_32_0_32_155_i0_fu___float_adde8m23b_127nih_501195_502573));
  ui_ne_expr_FU #(.BITSIZE_in1(24),
    .BITSIZE_in2(1),
    .BITSIZE_out1(1)) fu___float_adde8m23b_127nih_501195_502578 (.out1(out_ui_ne_expr_FU_32_0_32_203_i0_fu___float_adde8m23b_127nih_501195_502578),
    .in1(out_reg_4_reg_4),
    .in2(out_const_0));
  rshift_expr_FU #(.BITSIZE_in1(64),
    .BITSIZE_in2(6),
    .BITSIZE_out1(1),
    .PRECISION(64)) fu___float_adde8m23b_127nih_501195_502584 (.out1(out_rshift_expr_FU_64_0_64_156_i1_fu___float_adde8m23b_127nih_501195_502584),
    .in1(out_lshift_expr_FU_64_0_64_154_i1_fu___float_adde8m23b_127nih_501195_502596),
    .in2(out_const_52));
  IUdata_converter_FU #(.BITSIZE_in1(1),
    .BITSIZE_out1(27)) fu___float_adde8m23b_127nih_501195_502586 (.out1(out_IUdata_converter_FU_69_i0_fu___float_adde8m23b_127nih_501195_502586),
    .in1(out_rshift_expr_FU_64_0_64_156_i1_fu___float_adde8m23b_127nih_501195_502584));
  lshift_expr_FU #(.BITSIZE_in1(2),
    .BITSIZE_in2(5),
    .BITSIZE_out1(32),
    .PRECISION(32)) fu___float_adde8m23b_127nih_501195_502594 (.out1(out_lshift_expr_FU_32_0_32_153_i0_fu___float_adde8m23b_127nih_501195_502594),
    .in1(out_UIdata_converter_FU_65_i0_fu___float_adde8m23b_127nih_501195_502599),
    .in2(out_const_51));
  lshift_expr_FU #(.BITSIZE_in1(2),
    .BITSIZE_in2(6),
    .BITSIZE_out1(64),
    .PRECISION(64)) fu___float_adde8m23b_127nih_501195_502596 (.out1(out_lshift_expr_FU_64_0_64_154_i1_fu___float_adde8m23b_127nih_501195_502596),
    .in1(out_UIdata_converter_FU_68_i0_fu___float_adde8m23b_127nih_501195_502602),
    .in2(out_const_52));
  UIdata_converter_FU #(.BITSIZE_in1(1),
    .BITSIZE_out1(2)) fu___float_adde8m23b_127nih_501195_502599 (.out1(out_UIdata_converter_FU_65_i0_fu___float_adde8m23b_127nih_501195_502599),
    .in1(out_UUdata_converter_FU_64_i0_fu___float_adde8m23b_127nih_501195_501493));
  UIdata_converter_FU #(.BITSIZE_in1(1),
    .BITSIZE_out1(2)) fu___float_adde8m23b_127nih_501195_502602 (.out1(out_UIdata_converter_FU_68_i0_fu___float_adde8m23b_127nih_501195_502602),
    .in1(out_UUdata_converter_FU_57_i0_fu___float_adde8m23b_127nih_501195_501408));
  ui_eq_expr_FU #(.BITSIZE_in1(16),
    .BITSIZE_in2(1),
    .BITSIZE_out1(1)) fu___float_adde8m23b_127nih_501195_502628 (.out1(out_ui_eq_expr_FU_16_0_16_183_i0_fu___float_adde8m23b_127nih_501195_502628),
    .in1(out_ui_rshift_expr_FU_32_0_32_209_i1_fu___float_adde8m23b_127nih_501195_503565),
    .in2(out_const_0));
  lut_expr_FU #(.BITSIZE_in1(54),
    .BITSIZE_out1(1)) fu___float_adde8m23b_127nih_501195_502641 (.out1(out_lut_expr_FU_92_i0_fu___float_adde8m23b_127nih_501195_502641),
    .in1(out_const_10),
    .in2(out_reg_29_reg_29),
    .in3(out_reg_42_reg_42),
    .in4(out_reg_34_reg_34),
    .in5(out_reg_43_reg_43),
    .in6(out_reg_35_reg_35),
    .in7(out_lut_expr_FU_91_i0_fu___float_adde8m23b_127nih_501195_510611),
    .in8(1'b0),
    .in9(1'b0));
  lut_expr_FU #(.BITSIZE_in1(1),
    .BITSIZE_out1(1)) fu___float_adde8m23b_127nih_501195_502650 (.out1(out_lut_expr_FU_107_i0_fu___float_adde8m23b_127nih_501195_502650),
    .in1(out_const_1),
    .in2(out_lut_expr_FU_103_i0_fu___float_adde8m23b_127nih_501195_510617),
    .in3(out_lut_expr_FU_104_i0_fu___float_adde8m23b_127nih_501195_510621),
    .in4(out_lut_expr_FU_105_i0_fu___float_adde8m23b_127nih_501195_510624),
    .in5(out_lut_expr_FU_106_i0_fu___float_adde8m23b_127nih_501195_510627),
    .in6(1'b0),
    .in7(1'b0),
    .in8(1'b0),
    .in9(1'b0));
  lut_expr_FU #(.BITSIZE_in1(5),
    .BITSIZE_out1(1)) fu___float_adde8m23b_127nih_501195_502659 (.out1(out_lut_expr_FU_112_i0_fu___float_adde8m23b_127nih_501195_502659),
    .in1(out_const_40),
    .in2(out_lut_expr_FU_105_i0_fu___float_adde8m23b_127nih_501195_510624),
    .in3(out_lut_expr_FU_107_i0_fu___float_adde8m23b_127nih_501195_502650),
    .in4(out_lut_expr_FU_108_i0_fu___float_adde8m23b_127nih_501195_510632),
    .in5(out_lut_expr_FU_111_i0_fu___float_adde8m23b_127nih_501195_510639),
    .in6(1'b0),
    .in7(1'b0),
    .in8(1'b0),
    .in9(1'b0));
  lut_expr_FU #(.BITSIZE_in1(29),
    .BITSIZE_out1(1)) fu___float_adde8m23b_127nih_501195_502664 (.out1(out_lut_expr_FU_113_i0_fu___float_adde8m23b_127nih_501195_502664),
    .in1(out_const_11),
    .in2(out_lut_expr_FU_104_i0_fu___float_adde8m23b_127nih_501195_510621),
    .in3(out_lut_expr_FU_107_i0_fu___float_adde8m23b_127nih_501195_502650),
    .in4(out_lut_expr_FU_111_i0_fu___float_adde8m23b_127nih_501195_510639),
    .in5(out_lut_expr_FU_112_i0_fu___float_adde8m23b_127nih_501195_502659),
    .in6(out_lut_expr_FU_110_i0_fu___float_adde8m23b_127nih_501195_510644),
    .in7(1'b0),
    .in8(1'b0),
    .in9(1'b0));
  lut_expr_FU #(.BITSIZE_in1(64),
    .BITSIZE_out1(1)) fu___float_adde8m23b_127nih_501195_502758 (.out1(out_lut_expr_FU_127_i0_fu___float_adde8m23b_127nih_501195_502758),
    .in1(out_const_65),
    .in2(out_reg_29_reg_29),
    .in3(out_lut_expr_FU_92_i0_fu___float_adde8m23b_127nih_501195_502641),
    .in4(out_lut_expr_FU_107_i0_fu___float_adde8m23b_127nih_501195_502650),
    .in5(out_lut_expr_FU_112_i0_fu___float_adde8m23b_127nih_501195_502659),
    .in6(out_lut_expr_FU_122_i0_fu___float_adde8m23b_127nih_501195_510650),
    .in7(out_lut_expr_FU_126_i0_fu___float_adde8m23b_127nih_501195_510664),
    .in8(1'b0),
    .in9(1'b0));
  lut_expr_FU #(.BITSIZE_in1(4),
    .BITSIZE_out1(1)) fu___float_adde8m23b_127nih_501195_502776 (.out1(out_lut_expr_FU_141_i0_fu___float_adde8m23b_127nih_501195_502776),
    .in1(out_const_36),
    .in2(out_lut_expr_FU_136_i0_fu___float_adde8m23b_127nih_501195_510675),
    .in3(out_lut_expr_FU_140_i0_fu___float_adde8m23b_127nih_501195_510689),
    .in4(1'b0),
    .in5(1'b0),
    .in6(1'b0),
    .in7(1'b0),
    .in8(1'b0),
    .in9(1'b0));
  lut_expr_FU #(.BITSIZE_in1(64),
    .BITSIZE_out1(1)) fu___float_adde8m23b_127nih_501195_502788 (.out1(out_lut_expr_FU_144_i0_fu___float_adde8m23b_127nih_501195_502788),
    .in1(out_const_61),
    .in2(out_reg_18_reg_18),
    .in3(out_reg_19_reg_19),
    .in4(out_lut_expr_FU_142_i0_fu___float_adde8m23b_127nih_501195_510694),
    .in5(out_reg_24_reg_24),
    .in6(out_reg_25_reg_25),
    .in7(out_reg_57_reg_57),
    .in8(1'b0),
    .in9(1'b0));
  ui_lshift_expr_FU #(.BITSIZE_in1(1),
    .BITSIZE_in2(1),
    .BITSIZE_out1(2),
    .PRECISION(16)) fu___float_adde8m23b_127nih_501195_503378 (.out1(out_ui_lshift_expr_FU_8_0_8_196_i0_fu___float_adde8m23b_127nih_501195_503378),
    .in1(out_ui_rshift_expr_FU_16_0_16_205_i0_fu___float_adde8m23b_127nih_501195_503696),
    .in2(out_const_1));
  ui_lshift_expr_FU #(.BITSIZE_in1(1),
    .BITSIZE_in2(2),
    .BITSIZE_out1(3),
    .PRECISION(16)) fu___float_adde8m23b_127nih_501195_503386 (.out1(out_ui_lshift_expr_FU_8_0_8_197_i0_fu___float_adde8m23b_127nih_501195_503386),
    .in1(out_ui_rshift_expr_FU_16_0_16_205_i1_fu___float_adde8m23b_127nih_501195_503705),
    .in2(out_const_2));
  ui_lshift_expr_FU #(.BITSIZE_in1(1),
    .BITSIZE_in2(2),
    .BITSIZE_out1(4),
    .PRECISION(16)) fu___float_adde8m23b_127nih_501195_503394 (.out1(out_ui_lshift_expr_FU_8_0_8_198_i0_fu___float_adde8m23b_127nih_501195_503394),
    .in1(out_ui_rshift_expr_FU_16_0_16_205_i2_fu___float_adde8m23b_127nih_501195_503714),
    .in2(out_const_26));
  ui_lshift_expr_FU #(.BITSIZE_in1(1),
    .BITSIZE_in2(3),
    .BITSIZE_out1(5),
    .PRECISION(16)) fu___float_adde8m23b_127nih_501195_503403 (.out1(out_ui_lshift_expr_FU_8_0_8_199_i0_fu___float_adde8m23b_127nih_501195_503403),
    .in1(out_ui_rshift_expr_FU_16_0_16_205_i3_fu___float_adde8m23b_127nih_501195_503723),
    .in2(out_const_3));
  ui_rshift_expr_FU #(.BITSIZE_in1(26),
    .BITSIZE_in2(2),
    .BITSIZE_out1(24),
    .PRECISION(64)) fu___float_adde8m23b_127nih_501195_503506 (.out1(out_ui_rshift_expr_FU_32_0_32_208_i0_fu___float_adde8m23b_127nih_501195_503506),
    .in1(out_ui_lshift_expr_FU_0_64_64_184_i0_fu___float_adde8m23b_127nih_501195_501518),
    .in2(out_const_2));
  ui_lshift_expr_FU #(.BITSIZE_in1(24),
    .BITSIZE_in2(2),
    .BITSIZE_out1(26),
    .PRECISION(64)) fu___float_adde8m23b_127nih_501195_503511 (.out1(out_ui_lshift_expr_FU_32_0_32_187_i2_fu___float_adde8m23b_127nih_501195_503511),
    .in1(out_ui_bit_xor_expr_FU_32_0_32_178_i0_fu___float_adde8m23b_127nih_501195_501521),
    .in2(out_const_2));
  ui_rshift_expr_FU #(.BITSIZE_in1(26),
    .BITSIZE_in2(2),
    .BITSIZE_out1(24),
    .PRECISION(64)) fu___float_adde8m23b_127nih_501195_503514 (.out1(out_ui_rshift_expr_FU_32_0_32_208_i1_fu___float_adde8m23b_127nih_501195_503514),
    .in1(out_ui_lshift_expr_FU_32_0_32_187_i1_fu___float_adde8m23b_127nih_501195_501468),
    .in2(out_const_2));
  ui_rshift_expr_FU #(.BITSIZE_in1(26),
    .BITSIZE_in2(2),
    .BITSIZE_out1(24),
    .PRECISION(64)) fu___float_adde8m23b_127nih_501195_503517 (.out1(out_ui_rshift_expr_FU_32_0_32_208_i2_fu___float_adde8m23b_127nih_501195_503517),
    .in1(out_ui_lshift_expr_FU_32_0_32_187_i2_fu___float_adde8m23b_127nih_501195_503511),
    .in2(out_const_2));
  ui_lshift_expr_FU #(.BITSIZE_in1(24),
    .BITSIZE_in2(2),
    .BITSIZE_out1(26),
    .PRECISION(64)) fu___float_adde8m23b_127nih_501195_503521 (.out1(out_ui_lshift_expr_FU_32_0_32_187_i3_fu___float_adde8m23b_127nih_501195_503521),
    .in1(out_ui_bit_and_expr_FU_32_32_32_162_i2_fu___float_adde8m23b_127nih_501195_501524),
    .in2(out_const_2));
  ui_rshift_expr_FU #(.BITSIZE_in1(26),
    .BITSIZE_in2(2),
    .BITSIZE_out1(24),
    .PRECISION(64)) fu___float_adde8m23b_127nih_501195_503524 (.out1(out_ui_rshift_expr_FU_32_0_32_208_i3_fu___float_adde8m23b_127nih_501195_503524),
    .in1(out_ui_lshift_expr_FU_32_0_32_187_i3_fu___float_adde8m23b_127nih_501195_503521),
    .in2(out_const_2));
  ui_rshift_expr_FU #(.BITSIZE_in1(26),
    .BITSIZE_in2(2),
    .BITSIZE_out1(24),
    .PRECISION(64)) fu___float_adde8m23b_127nih_501195_503538 (.out1(out_ui_rshift_expr_FU_32_0_32_208_i4_fu___float_adde8m23b_127nih_501195_503538),
    .in1(out_ui_lshift_expr_FU_32_0_32_187_i0_fu___float_adde8m23b_127nih_501195_501456),
    .in2(out_const_2));
  ui_rshift_expr_FU #(.BITSIZE_in1(27),
    .BITSIZE_in2(2),
    .BITSIZE_out1(25),
    .PRECISION(64)) fu___float_adde8m23b_127nih_501195_503541 (.out1(out_ui_rshift_expr_FU_32_0_32_208_i5_fu___float_adde8m23b_127nih_501195_503541),
    .in1(out_ui_plus_expr_FU_32_32_32_204_i0_fu___float_adde8m23b_127nih_501195_501582),
    .in2(out_const_2));
  ui_plus_expr_FU #(.BITSIZE_in1(24),
    .BITSIZE_in2(25),
    .BITSIZE_out1(25)) fu___float_adde8m23b_127nih_501195_503543 (.out1(out_ui_plus_expr_FU_32_32_32_204_i2_fu___float_adde8m23b_127nih_501195_503543),
    .in1(out_reg_5_reg_5),
    .in2(out_ui_rshift_expr_FU_32_0_32_208_i5_fu___float_adde8m23b_127nih_501195_503541));
  ui_lshift_expr_FU #(.BITSIZE_in1(25),
    .BITSIZE_in2(2),
    .BITSIZE_out1(27),
    .PRECISION(64)) fu___float_adde8m23b_127nih_501195_503546 (.out1(out_ui_lshift_expr_FU_32_0_32_187_i4_fu___float_adde8m23b_127nih_501195_503546),
    .in1(out_ui_plus_expr_FU_32_32_32_204_i2_fu___float_adde8m23b_127nih_501195_503543),
    .in2(out_const_2));
  ui_bit_and_expr_FU #(.BITSIZE_in1(27),
    .BITSIZE_in2(2),
    .BITSIZE_out1(2)) fu___float_adde8m23b_127nih_501195_503550 (.out1(out_ui_bit_and_expr_FU_8_0_8_165_i0_fu___float_adde8m23b_127nih_501195_503550),
    .in1(out_ui_plus_expr_FU_32_32_32_204_i0_fu___float_adde8m23b_127nih_501195_501582),
    .in2(out_const_26));
  ui_rshift_expr_FU #(.BITSIZE_in1(27),
    .BITSIZE_in2(4),
    .BITSIZE_out1(16),
    .PRECISION(64)) fu___float_adde8m23b_127nih_501195_503557 (.out1(out_ui_rshift_expr_FU_32_0_32_209_i0_fu___float_adde8m23b_127nih_501195_503557),
    .in1(out_ui_bit_and_expr_FU_32_0_32_161_i1_fu___float_adde8m23b_127nih_501195_501588),
    .in2(out_const_22));
  ui_lshift_expr_FU #(.BITSIZE_in1(16),
    .BITSIZE_in2(4),
    .BITSIZE_out1(27),
    .PRECISION(64)) fu___float_adde8m23b_127nih_501195_503562 (.out1(out_ui_lshift_expr_FU_32_0_32_190_i0_fu___float_adde8m23b_127nih_501195_503562),
    .in1(out_ui_bit_and_expr_FU_16_0_16_158_i0_fu___float_adde8m23b_127nih_501195_501647),
    .in2(out_const_22));
  ui_rshift_expr_FU #(.BITSIZE_in1(27),
    .BITSIZE_in2(4),
    .BITSIZE_out1(16),
    .PRECISION(64)) fu___float_adde8m23b_127nih_501195_503565 (.out1(out_ui_rshift_expr_FU_32_0_32_209_i1_fu___float_adde8m23b_127nih_501195_503565),
    .in1(out_ui_lshift_expr_FU_32_0_32_190_i0_fu___float_adde8m23b_127nih_501195_503562),
    .in2(out_const_22));
  UUdata_converter_FU #(.BITSIZE_in1(1),
    .BITSIZE_out1(1)) fu___float_adde8m23b_127nih_501195_503690 (.out1(out_UUdata_converter_FU_117_i0_fu___float_adde8m23b_127nih_501195_503690),
    .in1(out_lut_expr_FU_112_i0_fu___float_adde8m23b_127nih_501195_502659));
  ui_lshift_expr_FU #(.BITSIZE_in1(1),
    .BITSIZE_in2(4),
    .BITSIZE_out1(16),
    .PRECISION(16)) fu___float_adde8m23b_127nih_501195_503693 (.out1(out_ui_lshift_expr_FU_16_0_16_185_i0_fu___float_adde8m23b_127nih_501195_503693),
    .in1(out_UUdata_converter_FU_117_i0_fu___float_adde8m23b_127nih_501195_503690),
    .in2(out_const_43));
  ui_rshift_expr_FU #(.BITSIZE_in1(16),
    .BITSIZE_in2(4),
    .BITSIZE_out1(1),
    .PRECISION(16)) fu___float_adde8m23b_127nih_501195_503696 (.out1(out_ui_rshift_expr_FU_16_0_16_205_i0_fu___float_adde8m23b_127nih_501195_503696),
    .in1(out_ui_lshift_expr_FU_16_0_16_185_i0_fu___float_adde8m23b_127nih_501195_503693),
    .in2(out_const_43));
  UUdata_converter_FU #(.BITSIZE_in1(1),
    .BITSIZE_out1(1)) fu___float_adde8m23b_127nih_501195_503699 (.out1(out_UUdata_converter_FU_118_i0_fu___float_adde8m23b_127nih_501195_503699),
    .in1(out_lut_expr_FU_107_i0_fu___float_adde8m23b_127nih_501195_502650));
  ui_lshift_expr_FU #(.BITSIZE_in1(1),
    .BITSIZE_in2(4),
    .BITSIZE_out1(16),
    .PRECISION(16)) fu___float_adde8m23b_127nih_501195_503702 (.out1(out_ui_lshift_expr_FU_16_0_16_185_i1_fu___float_adde8m23b_127nih_501195_503702),
    .in1(out_UUdata_converter_FU_118_i0_fu___float_adde8m23b_127nih_501195_503699),
    .in2(out_const_43));
  ui_rshift_expr_FU #(.BITSIZE_in1(16),
    .BITSIZE_in2(4),
    .BITSIZE_out1(1),
    .PRECISION(16)) fu___float_adde8m23b_127nih_501195_503705 (.out1(out_ui_rshift_expr_FU_16_0_16_205_i1_fu___float_adde8m23b_127nih_501195_503705),
    .in1(out_ui_lshift_expr_FU_16_0_16_185_i1_fu___float_adde8m23b_127nih_501195_503702),
    .in2(out_const_43));
  UUdata_converter_FU #(.BITSIZE_in1(1),
    .BITSIZE_out1(1)) fu___float_adde8m23b_127nih_501195_503708 (.out1(out_UUdata_converter_FU_119_i0_fu___float_adde8m23b_127nih_501195_503708),
    .in1(out_lut_expr_FU_92_i0_fu___float_adde8m23b_127nih_501195_502641));
  ui_lshift_expr_FU #(.BITSIZE_in1(1),
    .BITSIZE_in2(4),
    .BITSIZE_out1(16),
    .PRECISION(16)) fu___float_adde8m23b_127nih_501195_503711 (.out1(out_ui_lshift_expr_FU_16_0_16_185_i2_fu___float_adde8m23b_127nih_501195_503711),
    .in1(out_UUdata_converter_FU_119_i0_fu___float_adde8m23b_127nih_501195_503708),
    .in2(out_const_43));
  ui_rshift_expr_FU #(.BITSIZE_in1(16),
    .BITSIZE_in2(4),
    .BITSIZE_out1(1),
    .PRECISION(16)) fu___float_adde8m23b_127nih_501195_503714 (.out1(out_ui_rshift_expr_FU_16_0_16_205_i2_fu___float_adde8m23b_127nih_501195_503714),
    .in1(out_ui_lshift_expr_FU_16_0_16_185_i2_fu___float_adde8m23b_127nih_501195_503711),
    .in2(out_const_43));
  UUdata_converter_FU #(.BITSIZE_in1(1),
    .BITSIZE_out1(1)) fu___float_adde8m23b_127nih_501195_503717 (.out1(out_UUdata_converter_FU_120_i0_fu___float_adde8m23b_127nih_501195_503717),
    .in1(out_reg_29_reg_29));
  ui_lshift_expr_FU #(.BITSIZE_in1(1),
    .BITSIZE_in2(4),
    .BITSIZE_out1(16),
    .PRECISION(16)) fu___float_adde8m23b_127nih_501195_503720 (.out1(out_ui_lshift_expr_FU_16_0_16_185_i3_fu___float_adde8m23b_127nih_501195_503720),
    .in1(out_UUdata_converter_FU_120_i0_fu___float_adde8m23b_127nih_501195_503717),
    .in2(out_const_43));
  ui_rshift_expr_FU #(.BITSIZE_in1(16),
    .BITSIZE_in2(4),
    .BITSIZE_out1(1),
    .PRECISION(16)) fu___float_adde8m23b_127nih_501195_503723 (.out1(out_ui_rshift_expr_FU_16_0_16_205_i3_fu___float_adde8m23b_127nih_501195_503723),
    .in1(out_ui_lshift_expr_FU_16_0_16_185_i3_fu___float_adde8m23b_127nih_501195_503720),
    .in2(out_const_43));
  ASSIGN_UNSIGNED_FU #(.BITSIZE_in1(8),
    .BITSIZE_out1(8)) fu___float_adde8m23b_127nih_501195_503973 (.out1(out_ASSIGN_UNSIGNED_FU_7_i0_fu___float_adde8m23b_127nih_501195_503973),
    .in1(out_ui_bit_and_expr_FU_8_0_8_163_i0_fu___float_adde8m23b_127nih_501195_501331));
  lut_expr_FU #(.BITSIZE_in1(64),
    .BITSIZE_out1(1)) fu___float_adde8m23b_127nih_501195_506085 (.out1(out_lut_expr_FU_49_i0_fu___float_adde8m23b_127nih_501195_506085),
    .in1(out_const_59),
    .in2(out_ui_lt_expr_FU_32_32_32_200_i0_fu___float_adde8m23b_127nih_501195_502490),
    .in3(out_ui_extract_bit_expr_FU_19_i0_fu___float_adde8m23b_127nih_501195_507927),
    .in4(out_ui_extract_bit_expr_FU_18_i0_fu___float_adde8m23b_127nih_501195_507364),
    .in5(out_ui_extract_bit_expr_FU_21_i0_fu___float_adde8m23b_127nih_501195_507934),
    .in6(out_ui_extract_bit_expr_FU_20_i0_fu___float_adde8m23b_127nih_501195_507371),
    .in7(out_lut_expr_FU_48_i0_fu___float_adde8m23b_127nih_501195_510581),
    .in8(1'b0),
    .in9(1'b0));
  lut_expr_FU #(.BITSIZE_in1(64),
    .BITSIZE_out1(1)) fu___float_adde8m23b_127nih_501195_506102 (.out1(out_lut_expr_FU_54_i0_fu___float_adde8m23b_127nih_501195_506102),
    .in1(out_const_59),
    .in2(out_ui_lt_expr_FU_32_32_32_200_i0_fu___float_adde8m23b_127nih_501195_502490),
    .in3(out_ui_extract_bit_expr_FU_35_i0_fu___float_adde8m23b_127nih_501195_507983),
    .in4(out_ui_extract_bit_expr_FU_34_i0_fu___float_adde8m23b_127nih_501195_507420),
    .in5(out_ui_extract_bit_expr_FU_37_i0_fu___float_adde8m23b_127nih_501195_507990),
    .in6(out_ui_extract_bit_expr_FU_36_i0_fu___float_adde8m23b_127nih_501195_507427),
    .in7(out_lut_expr_FU_53_i0_fu___float_adde8m23b_127nih_501195_510594),
    .in8(1'b0),
    .in9(1'b0));
  lut_expr_FU #(.BITSIZE_in1(28),
    .BITSIZE_out1(1)) fu___float_adde8m23b_127nih_501195_506112 (.out1(out_lut_expr_FU_56_i0_fu___float_adde8m23b_127nih_501195_506112),
    .in1(out_const_24),
    .in2(out_ui_lt_expr_FU_32_32_32_200_i0_fu___float_adde8m23b_127nih_501195_502490),
    .in3(out_ui_extract_bit_expr_FU_6_i0_fu___float_adde8m23b_127nih_501195_507325),
    .in4(out_ui_extract_bit_expr_FU_5_i0_fu___float_adde8m23b_127nih_501195_506850),
    .in5(out_ui_extract_bit_expr_FU_9_i0_fu___float_adde8m23b_127nih_501195_507332),
    .in6(out_ui_extract_bit_expr_FU_8_i0_fu___float_adde8m23b_127nih_501195_506857),
    .in7(1'b0),
    .in8(1'b0),
    .in9(1'b0));
  lut_expr_FU #(.BITSIZE_in1(28),
    .BITSIZE_out1(1)) fu___float_adde8m23b_127nih_501195_506136 (.out1(out_lut_expr_FU_70_i0_fu___float_adde8m23b_127nih_501195_506136),
    .in1(out_const_24),
    .in2(out_reg_2_reg_2),
    .in3(out_reg_9_reg_9),
    .in4(out_reg_7_reg_7),
    .in5(out_reg_10_reg_10),
    .in6(out_reg_8_reg_8),
    .in7(out_ui_ne_expr_FU_32_0_32_203_i0_fu___float_adde8m23b_127nih_501195_502578),
    .in8(1'b0),
    .in9(1'b0));
  lut_expr_FU #(.BITSIZE_in1(32),
    .BITSIZE_out1(1)) fu___float_adde8m23b_127nih_501195_506322 (.out1(out_lut_expr_FU_132_i0_fu___float_adde8m23b_127nih_501195_506322),
    .in1(out_const_56),
    .in2(out_reg_28_reg_28),
    .in3(out_ui_extract_bit_expr_FU_128_i0_fu___float_adde8m23b_127nih_501195_506764),
    .in4(out_ui_extract_bit_expr_FU_129_i0_fu___float_adde8m23b_127nih_501195_508668),
    .in5(out_ui_extract_bit_expr_FU_130_i0_fu___float_adde8m23b_127nih_501195_508672),
    .in6(out_ui_extract_bit_expr_FU_131_i0_fu___float_adde8m23b_127nih_501195_507242),
    .in7(1'b0),
    .in8(1'b0),
    .in9(1'b0));
  lut_expr_FU #(.BITSIZE_in1(64),
    .BITSIZE_out1(1)) fu___float_adde8m23b_127nih_501195_506377 (.out1(out_lut_expr_FU_145_i0_fu___float_adde8m23b_127nih_501195_506377),
    .in1(out_const_50),
    .in2(out_reg_2_reg_2),
    .in3(out_reg_9_reg_9),
    .in4(out_reg_7_reg_7),
    .in5(out_reg_10_reg_10),
    .in6(out_reg_8_reg_8),
    .in7(out_lut_expr_FU_142_i0_fu___float_adde8m23b_127nih_501195_510694),
    .in8(1'b0),
    .in9(1'b0));
  lut_expr_FU #(.BITSIZE_in1(32),
    .BITSIZE_out1(1)) fu___float_adde8m23b_127nih_501195_506397 (.out1(out_lut_expr_FU_148_i0_fu___float_adde8m23b_127nih_501195_506397),
    .in1(out_const_42),
    .in2(out_ui_ne_expr_FU_32_0_32_202_i0_fu___float_adde8m23b_127nih_501195_502535),
    .in3(out_ui_ne_expr_FU_32_0_32_202_i1_fu___float_adde8m23b_127nih_501195_502538),
    .in4(out_lut_expr_FU_147_i0_fu___float_adde8m23b_127nih_501195_510706),
    .in5(out_lut_expr_FU_136_i0_fu___float_adde8m23b_127nih_501195_510675),
    .in6(out_lut_expr_FU_140_i0_fu___float_adde8m23b_127nih_501195_510689),
    .in7(1'b0),
    .in8(1'b0),
    .in9(1'b0));
  ui_extract_bit_expr_FU #(.BITSIZE_in1(26),
    .BITSIZE_in2(1)) fu___float_adde8m23b_127nih_501195_506764 (.out1(out_ui_extract_bit_expr_FU_128_i0_fu___float_adde8m23b_127nih_501195_506764),
    .in1(out_ui_lshift_expr_FU_64_64_64_195_i0_fu___float_adde8m23b_127nih_501195_501802),
    .in2(out_const_0));
  ui_extract_bit_expr_FU #(.BITSIZE_in1(32),
    .BITSIZE_in2(5)) fu___float_adde8m23b_127nih_501195_506850 (.out1(out_ui_extract_bit_expr_FU_5_i0_fu___float_adde8m23b_127nih_501195_506850),
    .in1(out_ui_bit_and_expr_FU_32_32_32_162_i0_fu___float_adde8m23b_127nih_501195_501268),
    .in2(out_const_51));
  ui_extract_bit_expr_FU #(.BITSIZE_in1(32),
    .BITSIZE_in2(5)) fu___float_adde8m23b_127nih_501195_506857 (.out1(out_ui_extract_bit_expr_FU_8_i0_fu___float_adde8m23b_127nih_501195_506857),
    .in1(out_ui_bit_and_expr_FU_32_32_32_162_i1_fu___float_adde8m23b_127nih_501195_501278),
    .in2(out_const_51));
  ui_extract_bit_expr_FU #(.BITSIZE_in1(8),
    .BITSIZE_in2(3)) fu___float_adde8m23b_127nih_501195_506992 (.out1(out_ui_extract_bit_expr_FU_60_i0_fu___float_adde8m23b_127nih_501195_506992),
    .in1(out_ui_minus_expr_FU_8_8_8_201_i0_fu___float_adde8m23b_127nih_501195_501436),
    .in2(out_const_14));
  ui_extract_bit_expr_FU #(.BITSIZE_in1(8),
    .BITSIZE_in2(3)) fu___float_adde8m23b_127nih_501195_506996 (.out1(out_ui_extract_bit_expr_FU_61_i0_fu___float_adde8m23b_127nih_501195_506996),
    .in1(out_ui_minus_expr_FU_8_8_8_201_i0_fu___float_adde8m23b_127nih_501195_501436),
    .in2(out_const_27));
  ui_extract_bit_expr_FU #(.BITSIZE_in1(8),
    .BITSIZE_in2(3)) fu___float_adde8m23b_127nih_501195_507000 (.out1(out_ui_extract_bit_expr_FU_62_i0_fu___float_adde8m23b_127nih_501195_507000),
    .in1(out_ui_minus_expr_FU_8_8_8_201_i0_fu___float_adde8m23b_127nih_501195_501436),
    .in2(out_const_35));
  ui_extract_bit_expr_FU #(.BITSIZE_in1(26),
    .BITSIZE_in2(2)) fu___float_adde8m23b_127nih_501195_507242 (.out1(out_ui_extract_bit_expr_FU_131_i0_fu___float_adde8m23b_127nih_501195_507242),
    .in1(out_ui_lshift_expr_FU_64_64_64_195_i0_fu___float_adde8m23b_127nih_501195_501802),
    .in2(out_const_2));
  ui_extract_bit_expr_FU #(.BITSIZE_in1(32),
    .BITSIZE_in2(5)) fu___float_adde8m23b_127nih_501195_507325 (.out1(out_ui_extract_bit_expr_FU_6_i0_fu___float_adde8m23b_127nih_501195_507325),
    .in1(out_conv_in_port_a_64_32),
    .in2(out_const_51));
  ui_extract_bit_expr_FU #(.BITSIZE_in1(32),
    .BITSIZE_in2(5)) fu___float_adde8m23b_127nih_501195_507332 (.out1(out_ui_extract_bit_expr_FU_9_i0_fu___float_adde8m23b_127nih_501195_507332),
    .in1(out_conv_in_port_b_64_32),
    .in2(out_const_51));
  ui_extract_bit_expr_FU #(.BITSIZE_in1(32),
    .BITSIZE_in2(5)) fu___float_adde8m23b_127nih_501195_507336 (.out1(out_ui_extract_bit_expr_FU_10_i0_fu___float_adde8m23b_127nih_501195_507336),
    .in1(out_ui_bit_and_expr_FU_32_32_32_162_i0_fu___float_adde8m23b_127nih_501195_501268),
    .in2(out_const_25));
  ui_extract_bit_expr_FU #(.BITSIZE_in1(32),
    .BITSIZE_in2(5)) fu___float_adde8m23b_127nih_501195_507343 (.out1(out_ui_extract_bit_expr_FU_12_i0_fu___float_adde8m23b_127nih_501195_507343),
    .in1(out_ui_bit_and_expr_FU_32_32_32_162_i0_fu___float_adde8m23b_127nih_501195_501268),
    .in2(out_const_29));
  ui_extract_bit_expr_FU #(.BITSIZE_in1(32),
    .BITSIZE_in2(5)) fu___float_adde8m23b_127nih_501195_507350 (.out1(out_ui_extract_bit_expr_FU_14_i0_fu___float_adde8m23b_127nih_501195_507350),
    .in1(out_ui_bit_and_expr_FU_32_32_32_162_i0_fu___float_adde8m23b_127nih_501195_501268),
    .in2(out_const_30));
  ui_extract_bit_expr_FU #(.BITSIZE_in1(32),
    .BITSIZE_in2(5)) fu___float_adde8m23b_127nih_501195_507357 (.out1(out_ui_extract_bit_expr_FU_16_i0_fu___float_adde8m23b_127nih_501195_507357),
    .in1(out_ui_bit_and_expr_FU_32_32_32_162_i0_fu___float_adde8m23b_127nih_501195_501268),
    .in2(out_const_33));
  ui_extract_bit_expr_FU #(.BITSIZE_in1(32),
    .BITSIZE_in2(5)) fu___float_adde8m23b_127nih_501195_507364 (.out1(out_ui_extract_bit_expr_FU_18_i0_fu___float_adde8m23b_127nih_501195_507364),
    .in1(out_ui_bit_and_expr_FU_32_32_32_162_i0_fu___float_adde8m23b_127nih_501195_501268),
    .in2(out_const_34));
  ui_extract_bit_expr_FU #(.BITSIZE_in1(32),
    .BITSIZE_in2(5)) fu___float_adde8m23b_127nih_501195_507371 (.out1(out_ui_extract_bit_expr_FU_20_i0_fu___float_adde8m23b_127nih_501195_507371),
    .in1(out_ui_bit_and_expr_FU_32_32_32_162_i0_fu___float_adde8m23b_127nih_501195_501268),
    .in2(out_const_37));
  ui_extract_bit_expr_FU #(.BITSIZE_in1(32),
    .BITSIZE_in2(5)) fu___float_adde8m23b_127nih_501195_507378 (.out1(out_ui_extract_bit_expr_FU_22_i0_fu___float_adde8m23b_127nih_501195_507378),
    .in1(out_ui_bit_and_expr_FU_32_32_32_162_i0_fu___float_adde8m23b_127nih_501195_501268),
    .in2(out_const_40));
  ui_extract_bit_expr_FU #(.BITSIZE_in1(32),
    .BITSIZE_in2(5)) fu___float_adde8m23b_127nih_501195_507385 (.out1(out_ui_extract_bit_expr_FU_24_i0_fu___float_adde8m23b_127nih_501195_507385),
    .in1(out_ui_bit_and_expr_FU_32_32_32_162_i0_fu___float_adde8m23b_127nih_501195_501268),
    .in2(out_const_44));
  ui_extract_bit_expr_FU #(.BITSIZE_in1(32),
    .BITSIZE_in2(5)) fu___float_adde8m23b_127nih_501195_507392 (.out1(out_ui_extract_bit_expr_FU_26_i0_fu___float_adde8m23b_127nih_501195_507392),
    .in1(out_ui_bit_and_expr_FU_32_32_32_162_i1_fu___float_adde8m23b_127nih_501195_501278),
    .in2(out_const_25));
  ui_extract_bit_expr_FU #(.BITSIZE_in1(32),
    .BITSIZE_in2(5)) fu___float_adde8m23b_127nih_501195_507399 (.out1(out_ui_extract_bit_expr_FU_28_i0_fu___float_adde8m23b_127nih_501195_507399),
    .in1(out_ui_bit_and_expr_FU_32_32_32_162_i1_fu___float_adde8m23b_127nih_501195_501278),
    .in2(out_const_29));
  ui_extract_bit_expr_FU #(.BITSIZE_in1(32),
    .BITSIZE_in2(5)) fu___float_adde8m23b_127nih_501195_507406 (.out1(out_ui_extract_bit_expr_FU_30_i0_fu___float_adde8m23b_127nih_501195_507406),
    .in1(out_ui_bit_and_expr_FU_32_32_32_162_i1_fu___float_adde8m23b_127nih_501195_501278),
    .in2(out_const_30));
  ui_extract_bit_expr_FU #(.BITSIZE_in1(32),
    .BITSIZE_in2(5)) fu___float_adde8m23b_127nih_501195_507413 (.out1(out_ui_extract_bit_expr_FU_32_i0_fu___float_adde8m23b_127nih_501195_507413),
    .in1(out_ui_bit_and_expr_FU_32_32_32_162_i1_fu___float_adde8m23b_127nih_501195_501278),
    .in2(out_const_33));
  ui_extract_bit_expr_FU #(.BITSIZE_in1(32),
    .BITSIZE_in2(5)) fu___float_adde8m23b_127nih_501195_507420 (.out1(out_ui_extract_bit_expr_FU_34_i0_fu___float_adde8m23b_127nih_501195_507420),
    .in1(out_ui_bit_and_expr_FU_32_32_32_162_i1_fu___float_adde8m23b_127nih_501195_501278),
    .in2(out_const_34));
  ui_extract_bit_expr_FU #(.BITSIZE_in1(32),
    .BITSIZE_in2(5)) fu___float_adde8m23b_127nih_501195_507427 (.out1(out_ui_extract_bit_expr_FU_36_i0_fu___float_adde8m23b_127nih_501195_507427),
    .in1(out_ui_bit_and_expr_FU_32_32_32_162_i1_fu___float_adde8m23b_127nih_501195_501278),
    .in2(out_const_37));
  ui_extract_bit_expr_FU #(.BITSIZE_in1(32),
    .BITSIZE_in2(5)) fu___float_adde8m23b_127nih_501195_507434 (.out1(out_ui_extract_bit_expr_FU_38_i0_fu___float_adde8m23b_127nih_501195_507434),
    .in1(out_ui_bit_and_expr_FU_32_32_32_162_i1_fu___float_adde8m23b_127nih_501195_501278),
    .in2(out_const_40));
  ui_extract_bit_expr_FU #(.BITSIZE_in1(32),
    .BITSIZE_in2(5)) fu___float_adde8m23b_127nih_501195_507441 (.out1(out_ui_extract_bit_expr_FU_40_i0_fu___float_adde8m23b_127nih_501195_507441),
    .in1(out_ui_bit_and_expr_FU_32_32_32_162_i1_fu___float_adde8m23b_127nih_501195_501278),
    .in2(out_const_44));
  ui_extract_bit_expr_FU #(.BITSIZE_in1(32),
    .BITSIZE_in2(5)) fu___float_adde8m23b_127nih_501195_507899 (.out1(out_ui_extract_bit_expr_FU_11_i0_fu___float_adde8m23b_127nih_501195_507899),
    .in1(out_conv_in_port_a_64_32),
    .in2(out_const_25));
  ui_extract_bit_expr_FU #(.BITSIZE_in1(32),
    .BITSIZE_in2(5)) fu___float_adde8m23b_127nih_501195_507906 (.out1(out_ui_extract_bit_expr_FU_13_i0_fu___float_adde8m23b_127nih_501195_507906),
    .in1(out_conv_in_port_a_64_32),
    .in2(out_const_29));
  ui_extract_bit_expr_FU #(.BITSIZE_in1(32),
    .BITSIZE_in2(5)) fu___float_adde8m23b_127nih_501195_507913 (.out1(out_ui_extract_bit_expr_FU_15_i0_fu___float_adde8m23b_127nih_501195_507913),
    .in1(out_conv_in_port_a_64_32),
    .in2(out_const_30));
  ui_extract_bit_expr_FU #(.BITSIZE_in1(32),
    .BITSIZE_in2(5)) fu___float_adde8m23b_127nih_501195_507920 (.out1(out_ui_extract_bit_expr_FU_17_i0_fu___float_adde8m23b_127nih_501195_507920),
    .in1(out_conv_in_port_a_64_32),
    .in2(out_const_33));
  ui_extract_bit_expr_FU #(.BITSIZE_in1(32),
    .BITSIZE_in2(5)) fu___float_adde8m23b_127nih_501195_507927 (.out1(out_ui_extract_bit_expr_FU_19_i0_fu___float_adde8m23b_127nih_501195_507927),
    .in1(out_conv_in_port_a_64_32),
    .in2(out_const_34));
  ui_extract_bit_expr_FU #(.BITSIZE_in1(32),
    .BITSIZE_in2(5)) fu___float_adde8m23b_127nih_501195_507934 (.out1(out_ui_extract_bit_expr_FU_21_i0_fu___float_adde8m23b_127nih_501195_507934),
    .in1(out_conv_in_port_a_64_32),
    .in2(out_const_37));
  ui_extract_bit_expr_FU #(.BITSIZE_in1(32),
    .BITSIZE_in2(5)) fu___float_adde8m23b_127nih_501195_507941 (.out1(out_ui_extract_bit_expr_FU_23_i0_fu___float_adde8m23b_127nih_501195_507941),
    .in1(out_conv_in_port_a_64_32),
    .in2(out_const_40));
  ui_extract_bit_expr_FU #(.BITSIZE_in1(32),
    .BITSIZE_in2(5)) fu___float_adde8m23b_127nih_501195_507948 (.out1(out_ui_extract_bit_expr_FU_25_i0_fu___float_adde8m23b_127nih_501195_507948),
    .in1(out_conv_in_port_a_64_32),
    .in2(out_const_44));
  ui_extract_bit_expr_FU #(.BITSIZE_in1(32),
    .BITSIZE_in2(5)) fu___float_adde8m23b_127nih_501195_507955 (.out1(out_ui_extract_bit_expr_FU_27_i0_fu___float_adde8m23b_127nih_501195_507955),
    .in1(out_conv_in_port_b_64_32),
    .in2(out_const_25));
  ui_extract_bit_expr_FU #(.BITSIZE_in1(32),
    .BITSIZE_in2(5)) fu___float_adde8m23b_127nih_501195_507962 (.out1(out_ui_extract_bit_expr_FU_29_i0_fu___float_adde8m23b_127nih_501195_507962),
    .in1(out_conv_in_port_b_64_32),
    .in2(out_const_29));
  ui_extract_bit_expr_FU #(.BITSIZE_in1(32),
    .BITSIZE_in2(5)) fu___float_adde8m23b_127nih_501195_507969 (.out1(out_ui_extract_bit_expr_FU_31_i0_fu___float_adde8m23b_127nih_501195_507969),
    .in1(out_conv_in_port_b_64_32),
    .in2(out_const_30));
  ui_extract_bit_expr_FU #(.BITSIZE_in1(32),
    .BITSIZE_in2(5)) fu___float_adde8m23b_127nih_501195_507976 (.out1(out_ui_extract_bit_expr_FU_33_i0_fu___float_adde8m23b_127nih_501195_507976),
    .in1(out_conv_in_port_b_64_32),
    .in2(out_const_33));
  ui_extract_bit_expr_FU #(.BITSIZE_in1(32),
    .BITSIZE_in2(5)) fu___float_adde8m23b_127nih_501195_507983 (.out1(out_ui_extract_bit_expr_FU_35_i0_fu___float_adde8m23b_127nih_501195_507983),
    .in1(out_conv_in_port_b_64_32),
    .in2(out_const_34));
  ui_extract_bit_expr_FU #(.BITSIZE_in1(32),
    .BITSIZE_in2(5)) fu___float_adde8m23b_127nih_501195_507990 (.out1(out_ui_extract_bit_expr_FU_37_i0_fu___float_adde8m23b_127nih_501195_507990),
    .in1(out_conv_in_port_b_64_32),
    .in2(out_const_37));
  ui_extract_bit_expr_FU #(.BITSIZE_in1(32),
    .BITSIZE_in2(5)) fu___float_adde8m23b_127nih_501195_507997 (.out1(out_ui_extract_bit_expr_FU_39_i0_fu___float_adde8m23b_127nih_501195_507997),
    .in1(out_conv_in_port_b_64_32),
    .in2(out_const_40));
  ui_extract_bit_expr_FU #(.BITSIZE_in1(32),
    .BITSIZE_in2(5)) fu___float_adde8m23b_127nih_501195_508004 (.out1(out_ui_extract_bit_expr_FU_41_i0_fu___float_adde8m23b_127nih_501195_508004),
    .in1(out_conv_in_port_b_64_32),
    .in2(out_const_44));
  ui_extract_bit_expr_FU #(.BITSIZE_in1(26),
    .BITSIZE_in2(1)) fu___float_adde8m23b_127nih_501195_508668 (.out1(out_ui_extract_bit_expr_FU_129_i0_fu___float_adde8m23b_127nih_501195_508668),
    .in1(out_ui_lshift_expr_FU_64_64_64_195_i0_fu___float_adde8m23b_127nih_501195_501802),
    .in2(out_const_1));
  ui_extract_bit_expr_FU #(.BITSIZE_in1(26),
    .BITSIZE_in2(2)) fu___float_adde8m23b_127nih_501195_508672 (.out1(out_ui_extract_bit_expr_FU_130_i0_fu___float_adde8m23b_127nih_501195_508672),
    .in1(out_ui_lshift_expr_FU_64_64_64_195_i0_fu___float_adde8m23b_127nih_501195_501802),
    .in2(out_const_26));
  ui_extract_bit_expr_FU #(.BITSIZE_in1(25),
    .BITSIZE_in2(5)) fu___float_adde8m23b_127nih_501195_509408 (.out1(out_ui_extract_bit_expr_FU_74_i0_fu___float_adde8m23b_127nih_501195_509408),
    .in1(out_ui_plus_expr_FU_32_32_32_204_i2_fu___float_adde8m23b_127nih_501195_503543),
    .in2(out_const_8));
  ui_extract_bit_expr_FU #(.BITSIZE_in1(25),
    .BITSIZE_in2(5)) fu___float_adde8m23b_127nih_501195_509416 (.out1(out_ui_extract_bit_expr_FU_76_i0_fu___float_adde8m23b_127nih_501195_509416),
    .in1(out_ui_plus_expr_FU_32_32_32_204_i2_fu___float_adde8m23b_127nih_501195_503543),
    .in2(out_const_12));
  ui_extract_bit_expr_FU #(.BITSIZE_in1(25),
    .BITSIZE_in2(5)) fu___float_adde8m23b_127nih_501195_509424 (.out1(out_ui_extract_bit_expr_FU_78_i0_fu___float_adde8m23b_127nih_501195_509424),
    .in1(out_ui_plus_expr_FU_32_32_32_204_i2_fu___float_adde8m23b_127nih_501195_503543),
    .in2(out_const_13));
  ui_extract_bit_expr_FU #(.BITSIZE_in1(25),
    .BITSIZE_in2(5)) fu___float_adde8m23b_127nih_501195_509432 (.out1(out_ui_extract_bit_expr_FU_80_i0_fu___float_adde8m23b_127nih_501195_509432),
    .in1(out_ui_plus_expr_FU_32_32_32_204_i2_fu___float_adde8m23b_127nih_501195_503543),
    .in2(out_const_16));
  ui_extract_bit_expr_FU #(.BITSIZE_in1(25),
    .BITSIZE_in2(5)) fu___float_adde8m23b_127nih_501195_509440 (.out1(out_ui_extract_bit_expr_FU_82_i0_fu___float_adde8m23b_127nih_501195_509440),
    .in1(out_ui_plus_expr_FU_32_32_32_204_i2_fu___float_adde8m23b_127nih_501195_503543),
    .in2(out_const_20));
  ui_extract_bit_expr_FU #(.BITSIZE_in1(25),
    .BITSIZE_in2(5)) fu___float_adde8m23b_127nih_501195_509448 (.out1(out_ui_extract_bit_expr_FU_84_i0_fu___float_adde8m23b_127nih_501195_509448),
    .in1(out_ui_plus_expr_FU_32_32_32_204_i2_fu___float_adde8m23b_127nih_501195_503543),
    .in2(out_const_23));
  ui_extract_bit_expr_FU #(.BITSIZE_in1(25),
    .BITSIZE_in2(5)) fu___float_adde8m23b_127nih_501195_509456 (.out1(out_ui_extract_bit_expr_FU_86_i0_fu___float_adde8m23b_127nih_501195_509456),
    .in1(out_ui_plus_expr_FU_32_32_32_204_i2_fu___float_adde8m23b_127nih_501195_503543),
    .in2(out_const_25));
  ui_extract_bit_expr_FU #(.BITSIZE_in1(25),
    .BITSIZE_in2(5)) fu___float_adde8m23b_127nih_501195_509464 (.out1(out_ui_extract_bit_expr_FU_88_i0_fu___float_adde8m23b_127nih_501195_509464),
    .in1(out_ui_plus_expr_FU_32_32_32_204_i2_fu___float_adde8m23b_127nih_501195_503543),
    .in2(out_const_29));
  ui_extract_bit_expr_FU #(.BITSIZE_in1(25),
    .BITSIZE_in2(1)) fu___float_adde8m23b_127nih_501195_509799 (.out1(out_ui_extract_bit_expr_FU_73_i0_fu___float_adde8m23b_127nih_501195_509799),
    .in1(out_ui_plus_expr_FU_32_32_32_204_i2_fu___float_adde8m23b_127nih_501195_503543),
    .in2(out_const_1));
  ui_extract_bit_expr_FU #(.BITSIZE_in1(25),
    .BITSIZE_in2(2)) fu___float_adde8m23b_127nih_501195_509803 (.out1(out_ui_extract_bit_expr_FU_75_i0_fu___float_adde8m23b_127nih_501195_509803),
    .in1(out_ui_plus_expr_FU_32_32_32_204_i2_fu___float_adde8m23b_127nih_501195_503543),
    .in2(out_const_2));
  ui_extract_bit_expr_FU #(.BITSIZE_in1(25),
    .BITSIZE_in2(2)) fu___float_adde8m23b_127nih_501195_509807 (.out1(out_ui_extract_bit_expr_FU_77_i0_fu___float_adde8m23b_127nih_501195_509807),
    .in1(out_ui_plus_expr_FU_32_32_32_204_i2_fu___float_adde8m23b_127nih_501195_503543),
    .in2(out_const_26));
  ui_extract_bit_expr_FU #(.BITSIZE_in1(25),
    .BITSIZE_in2(3)) fu___float_adde8m23b_127nih_501195_509811 (.out1(out_ui_extract_bit_expr_FU_79_i0_fu___float_adde8m23b_127nih_501195_509811),
    .in1(out_ui_plus_expr_FU_32_32_32_204_i2_fu___float_adde8m23b_127nih_501195_503543),
    .in2(out_const_3));
  ui_extract_bit_expr_FU #(.BITSIZE_in1(25),
    .BITSIZE_in2(3)) fu___float_adde8m23b_127nih_501195_509815 (.out1(out_ui_extract_bit_expr_FU_81_i0_fu___float_adde8m23b_127nih_501195_509815),
    .in1(out_ui_plus_expr_FU_32_32_32_204_i2_fu___float_adde8m23b_127nih_501195_503543),
    .in2(out_const_14));
  ui_extract_bit_expr_FU #(.BITSIZE_in1(25),
    .BITSIZE_in2(3)) fu___float_adde8m23b_127nih_501195_509819 (.out1(out_ui_extract_bit_expr_FU_83_i0_fu___float_adde8m23b_127nih_501195_509819),
    .in1(out_ui_plus_expr_FU_32_32_32_204_i2_fu___float_adde8m23b_127nih_501195_503543),
    .in2(out_const_27));
  ui_extract_bit_expr_FU #(.BITSIZE_in1(25),
    .BITSIZE_in2(3)) fu___float_adde8m23b_127nih_501195_509823 (.out1(out_ui_extract_bit_expr_FU_85_i0_fu___float_adde8m23b_127nih_501195_509823),
    .in1(out_ui_plus_expr_FU_32_32_32_204_i2_fu___float_adde8m23b_127nih_501195_503543),
    .in2(out_const_35));
  ui_extract_bit_expr_FU #(.BITSIZE_in1(25),
    .BITSIZE_in2(4)) fu___float_adde8m23b_127nih_501195_509827 (.out1(out_ui_extract_bit_expr_FU_87_i0_fu___float_adde8m23b_127nih_501195_509827),
    .in1(out_ui_plus_expr_FU_32_32_32_204_i2_fu___float_adde8m23b_127nih_501195_503543),
    .in2(out_const_4));
  ui_extract_bit_expr_FU #(.BITSIZE_in1(25),
    .BITSIZE_in2(4)) fu___float_adde8m23b_127nih_501195_510146 (.out1(out_ui_extract_bit_expr_FU_93_i0_fu___float_adde8m23b_127nih_501195_510146),
    .in1(out_ui_plus_expr_FU_32_32_32_204_i2_fu___float_adde8m23b_127nih_501195_503543),
    .in2(out_const_32));
  ui_extract_bit_expr_FU #(.BITSIZE_in1(25),
    .BITSIZE_in2(4)) fu___float_adde8m23b_127nih_501195_510158 (.out1(out_ui_extract_bit_expr_FU_95_i0_fu___float_adde8m23b_127nih_501195_510158),
    .in1(out_ui_plus_expr_FU_32_32_32_204_i2_fu___float_adde8m23b_127nih_501195_503543),
    .in2(out_const_36));
  ui_extract_bit_expr_FU #(.BITSIZE_in1(25),
    .BITSIZE_in2(4)) fu___float_adde8m23b_127nih_501195_510170 (.out1(out_ui_extract_bit_expr_FU_97_i0_fu___float_adde8m23b_127nih_501195_510170),
    .in1(out_ui_plus_expr_FU_32_32_32_204_i2_fu___float_adde8m23b_127nih_501195_503543),
    .in2(out_const_43));
  ui_extract_bit_expr_FU #(.BITSIZE_in1(25),
    .BITSIZE_in2(5)) fu___float_adde8m23b_127nih_501195_510182 (.out1(out_ui_extract_bit_expr_FU_99_i0_fu___float_adde8m23b_127nih_501195_510182),
    .in1(out_ui_plus_expr_FU_32_32_32_204_i2_fu___float_adde8m23b_127nih_501195_503543),
    .in2(out_const_5));
  ui_extract_bit_expr_FU #(.BITSIZE_in1(27),
    .BITSIZE_in2(1)) fu___float_adde8m23b_127nih_501195_510382 (.out1(out_ui_extract_bit_expr_FU_94_i0_fu___float_adde8m23b_127nih_501195_510382),
    .in1(out_ui_plus_expr_FU_32_32_32_204_i0_fu___float_adde8m23b_127nih_501195_501582),
    .in2(out_const_0));
  ui_extract_bit_expr_FU #(.BITSIZE_in1(27),
    .BITSIZE_in2(1)) fu___float_adde8m23b_127nih_501195_510386 (.out1(out_ui_extract_bit_expr_FU_96_i0_fu___float_adde8m23b_127nih_501195_510386),
    .in1(out_ui_plus_expr_FU_32_32_32_204_i0_fu___float_adde8m23b_127nih_501195_501582),
    .in2(out_const_1));
  ui_extract_bit_expr_FU #(.BITSIZE_in1(25),
    .BITSIZE_in2(1)) fu___float_adde8m23b_127nih_501195_510390 (.out1(out_ui_extract_bit_expr_FU_98_i0_fu___float_adde8m23b_127nih_501195_510390),
    .in1(out_ui_plus_expr_FU_32_32_32_204_i2_fu___float_adde8m23b_127nih_501195_503543),
    .in2(out_const_0));
  ui_extract_bit_expr_FU #(.BITSIZE_in1(25),
    .BITSIZE_in2(4)) fu___float_adde8m23b_127nih_501195_510442 (.out1(out_ui_extract_bit_expr_FU_102_i0_fu___float_adde8m23b_127nih_501195_510442),
    .in1(out_ui_plus_expr_FU_32_32_32_204_i2_fu___float_adde8m23b_127nih_501195_503543),
    .in2(out_const_15));
  ui_extract_bit_expr_FU #(.BITSIZE_in1(25),
    .BITSIZE_in2(4)) fu___float_adde8m23b_127nih_501195_510515 (.out1(out_ui_extract_bit_expr_FU_100_i0_fu___float_adde8m23b_127nih_501195_510515),
    .in1(out_ui_plus_expr_FU_32_32_32_204_i2_fu___float_adde8m23b_127nih_501195_503543),
    .in2(out_const_22));
  ui_extract_bit_expr_FU #(.BITSIZE_in1(25),
    .BITSIZE_in2(4)) fu___float_adde8m23b_127nih_501195_510527 (.out1(out_ui_extract_bit_expr_FU_101_i0_fu___float_adde8m23b_127nih_501195_510527),
    .in1(out_ui_plus_expr_FU_32_32_32_204_i2_fu___float_adde8m23b_127nih_501195_503543),
    .in2(out_const_28));
  lut_expr_FU #(.BITSIZE_in1(4),
    .BITSIZE_out1(1)) fu___float_adde8m23b_127nih_501195_510563 (.out1(out_lut_expr_FU_42_i0_fu___float_adde8m23b_127nih_501195_510563),
    .in1(out_const_22),
    .in2(out_ui_lt_expr_FU_32_32_32_200_i0_fu___float_adde8m23b_127nih_501195_502490),
    .in3(out_ui_extract_bit_expr_FU_23_i0_fu___float_adde8m23b_127nih_501195_507941),
    .in4(out_ui_extract_bit_expr_FU_22_i0_fu___float_adde8m23b_127nih_501195_507378),
    .in5(1'b0),
    .in6(1'b0),
    .in7(1'b0),
    .in8(1'b0),
    .in9(1'b0));
  lut_expr_FU #(.BITSIZE_in1(4),
    .BITSIZE_out1(1)) fu___float_adde8m23b_127nih_501195_510566 (.out1(out_lut_expr_FU_43_i0_fu___float_adde8m23b_127nih_501195_510566),
    .in1(out_const_22),
    .in2(out_ui_lt_expr_FU_32_32_32_200_i0_fu___float_adde8m23b_127nih_501195_502490),
    .in3(out_ui_extract_bit_expr_FU_25_i0_fu___float_adde8m23b_127nih_501195_507948),
    .in4(out_ui_extract_bit_expr_FU_24_i0_fu___float_adde8m23b_127nih_501195_507385),
    .in5(1'b0),
    .in6(1'b0),
    .in7(1'b0),
    .in8(1'b0),
    .in9(1'b0));
  lut_expr_FU #(.BITSIZE_in1(4),
    .BITSIZE_out1(1)) fu___float_adde8m23b_127nih_501195_510569 (.out1(out_lut_expr_FU_44_i0_fu___float_adde8m23b_127nih_501195_510569),
    .in1(out_const_22),
    .in2(out_ui_lt_expr_FU_32_32_32_200_i0_fu___float_adde8m23b_127nih_501195_502490),
    .in3(out_ui_extract_bit_expr_FU_11_i0_fu___float_adde8m23b_127nih_501195_507899),
    .in4(out_ui_extract_bit_expr_FU_10_i0_fu___float_adde8m23b_127nih_501195_507336),
    .in5(1'b0),
    .in6(1'b0),
    .in7(1'b0),
    .in8(1'b0),
    .in9(1'b0));
  lut_expr_FU #(.BITSIZE_in1(4),
    .BITSIZE_out1(1)) fu___float_adde8m23b_127nih_501195_510572 (.out1(out_lut_expr_FU_45_i0_fu___float_adde8m23b_127nih_501195_510572),
    .in1(out_const_22),
    .in2(out_ui_lt_expr_FU_32_32_32_200_i0_fu___float_adde8m23b_127nih_501195_502490),
    .in3(out_ui_extract_bit_expr_FU_13_i0_fu___float_adde8m23b_127nih_501195_507906),
    .in4(out_ui_extract_bit_expr_FU_12_i0_fu___float_adde8m23b_127nih_501195_507343),
    .in5(1'b0),
    .in6(1'b0),
    .in7(1'b0),
    .in8(1'b0),
    .in9(1'b0));
  lut_expr_FU #(.BITSIZE_in1(4),
    .BITSIZE_out1(1)) fu___float_adde8m23b_127nih_501195_510575 (.out1(out_lut_expr_FU_46_i0_fu___float_adde8m23b_127nih_501195_510575),
    .in1(out_const_22),
    .in2(out_ui_lt_expr_FU_32_32_32_200_i0_fu___float_adde8m23b_127nih_501195_502490),
    .in3(out_ui_extract_bit_expr_FU_15_i0_fu___float_adde8m23b_127nih_501195_507913),
    .in4(out_ui_extract_bit_expr_FU_14_i0_fu___float_adde8m23b_127nih_501195_507350),
    .in5(1'b0),
    .in6(1'b0),
    .in7(1'b0),
    .in8(1'b0),
    .in9(1'b0));
  lut_expr_FU #(.BITSIZE_in1(4),
    .BITSIZE_out1(1)) fu___float_adde8m23b_127nih_501195_510578 (.out1(out_lut_expr_FU_47_i0_fu___float_adde8m23b_127nih_501195_510578),
    .in1(out_const_22),
    .in2(out_ui_lt_expr_FU_32_32_32_200_i0_fu___float_adde8m23b_127nih_501195_502490),
    .in3(out_ui_extract_bit_expr_FU_17_i0_fu___float_adde8m23b_127nih_501195_507920),
    .in4(out_ui_extract_bit_expr_FU_16_i0_fu___float_adde8m23b_127nih_501195_507357),
    .in5(1'b0),
    .in6(1'b0),
    .in7(1'b0),
    .in8(1'b0),
    .in9(1'b0));
  lut_expr_FU #(.BITSIZE_in1(64),
    .BITSIZE_out1(1)) fu___float_adde8m23b_127nih_501195_510581 (.out1(out_lut_expr_FU_48_i0_fu___float_adde8m23b_127nih_501195_510581),
    .in1(out_const_7),
    .in2(out_lut_expr_FU_42_i0_fu___float_adde8m23b_127nih_501195_510563),
    .in3(out_lut_expr_FU_43_i0_fu___float_adde8m23b_127nih_501195_510566),
    .in4(out_lut_expr_FU_44_i0_fu___float_adde8m23b_127nih_501195_510569),
    .in5(out_lut_expr_FU_45_i0_fu___float_adde8m23b_127nih_501195_510572),
    .in6(out_lut_expr_FU_46_i0_fu___float_adde8m23b_127nih_501195_510575),
    .in7(out_lut_expr_FU_47_i0_fu___float_adde8m23b_127nih_501195_510578),
    .in8(1'b0),
    .in9(1'b0));
  lut_expr_FU #(.BITSIZE_in1(12),
    .BITSIZE_out1(1)) fu___float_adde8m23b_127nih_501195_510587 (.out1(out_lut_expr_FU_51_i0_fu___float_adde8m23b_127nih_501195_510587),
    .in1(out_const_18),
    .in2(out_ui_lt_expr_FU_32_32_32_200_i0_fu___float_adde8m23b_127nih_501195_502490),
    .in3(out_ui_extract_bit_expr_FU_31_i0_fu___float_adde8m23b_127nih_501195_507969),
    .in4(out_ui_extract_bit_expr_FU_30_i0_fu___float_adde8m23b_127nih_501195_507406),
    .in5(out_ui_extract_bit_expr_FU_33_i0_fu___float_adde8m23b_127nih_501195_507976),
    .in6(out_ui_extract_bit_expr_FU_32_i0_fu___float_adde8m23b_127nih_501195_507413),
    .in7(1'b0),
    .in8(1'b0),
    .in9(1'b0));
  lut_expr_FU #(.BITSIZE_in1(44),
    .BITSIZE_out1(1)) fu___float_adde8m23b_127nih_501195_510591 (.out1(out_lut_expr_FU_52_i0_fu___float_adde8m23b_127nih_501195_510591),
    .in1(out_const_19),
    .in2(out_ui_lt_expr_FU_32_32_32_200_i0_fu___float_adde8m23b_127nih_501195_502490),
    .in3(out_ui_extract_bit_expr_FU_27_i0_fu___float_adde8m23b_127nih_501195_507955),
    .in4(out_ui_extract_bit_expr_FU_26_i0_fu___float_adde8m23b_127nih_501195_507392),
    .in5(out_ui_extract_bit_expr_FU_29_i0_fu___float_adde8m23b_127nih_501195_507962),
    .in6(out_ui_extract_bit_expr_FU_28_i0_fu___float_adde8m23b_127nih_501195_507399),
    .in7(out_lut_expr_FU_51_i0_fu___float_adde8m23b_127nih_501195_510587),
    .in8(1'b0),
    .in9(1'b0));
  lut_expr_FU #(.BITSIZE_in1(44),
    .BITSIZE_out1(1)) fu___float_adde8m23b_127nih_501195_510594 (.out1(out_lut_expr_FU_53_i0_fu___float_adde8m23b_127nih_501195_510594),
    .in1(out_const_19),
    .in2(out_ui_lt_expr_FU_32_32_32_200_i0_fu___float_adde8m23b_127nih_501195_502490),
    .in3(out_ui_extract_bit_expr_FU_39_i0_fu___float_adde8m23b_127nih_501195_507997),
    .in4(out_ui_extract_bit_expr_FU_38_i0_fu___float_adde8m23b_127nih_501195_507434),
    .in5(out_ui_extract_bit_expr_FU_41_i0_fu___float_adde8m23b_127nih_501195_508004),
    .in6(out_ui_extract_bit_expr_FU_40_i0_fu___float_adde8m23b_127nih_501195_507441),
    .in7(out_lut_expr_FU_52_i0_fu___float_adde8m23b_127nih_501195_510591),
    .in8(1'b0),
    .in9(1'b0));
  lut_expr_FU #(.BITSIZE_in1(22),
    .BITSIZE_out1(1)) fu___float_adde8m23b_127nih_501195_510603 (.out1(out_lut_expr_FU_89_i0_fu___float_adde8m23b_127nih_501195_510603),
    .in1(out_const_9),
    .in2(out_ui_eq_expr_FU_16_0_16_183_i0_fu___float_adde8m23b_127nih_501195_502628),
    .in3(out_ui_extract_bit_expr_FU_77_i0_fu___float_adde8m23b_127nih_501195_509807),
    .in4(out_ui_extract_bit_expr_FU_78_i0_fu___float_adde8m23b_127nih_501195_509424),
    .in5(out_ui_extract_bit_expr_FU_79_i0_fu___float_adde8m23b_127nih_501195_509811),
    .in6(out_ui_extract_bit_expr_FU_80_i0_fu___float_adde8m23b_127nih_501195_509432),
    .in7(1'b0),
    .in8(1'b0),
    .in9(1'b0));
  lut_expr_FU #(.BITSIZE_in1(55),
    .BITSIZE_out1(1)) fu___float_adde8m23b_127nih_501195_510607 (.out1(out_lut_expr_FU_90_i0_fu___float_adde8m23b_127nih_501195_510607),
    .in1(out_const_17),
    .in2(out_reg_38_reg_38),
    .in3(out_reg_30_reg_30),
    .in4(out_reg_29_reg_29),
    .in5(out_reg_39_reg_39),
    .in6(out_reg_31_reg_31),
    .in7(out_reg_56_reg_56),
    .in8(1'b0),
    .in9(1'b0));
  lut_expr_FU #(.BITSIZE_in1(54),
    .BITSIZE_out1(1)) fu___float_adde8m23b_127nih_501195_510611 (.out1(out_lut_expr_FU_91_i0_fu___float_adde8m23b_127nih_501195_510611),
    .in1(out_const_10),
    .in2(out_reg_29_reg_29),
    .in3(out_reg_44_reg_44),
    .in4(out_reg_36_reg_36),
    .in5(out_reg_45_reg_45),
    .in6(out_reg_37_reg_37),
    .in7(out_lut_expr_FU_90_i0_fu___float_adde8m23b_127nih_501195_510607),
    .in8(1'b0),
    .in9(1'b0));
  lut_expr_FU #(.BITSIZE_in1(31),
    .BITSIZE_out1(1)) fu___float_adde8m23b_127nih_501195_510617 (.out1(out_lut_expr_FU_103_i0_fu___float_adde8m23b_127nih_501195_510617),
    .in1(out_const_21),
    .in2(out_reg_29_reg_29),
    .in3(out_reg_42_reg_42),
    .in4(out_reg_34_reg_34),
    .in5(out_reg_46_reg_46),
    .in6(out_lut_expr_FU_92_i0_fu___float_adde8m23b_127nih_501195_502641),
    .in7(1'b0),
    .in8(1'b0),
    .in9(1'b0));
  lut_expr_FU #(.BITSIZE_in1(64),
    .BITSIZE_out1(1)) fu___float_adde8m23b_127nih_501195_510621 (.out1(out_lut_expr_FU_104_i0_fu___float_adde8m23b_127nih_501195_510621),
    .in1(out_const_55),
    .in2(out_reg_29_reg_29),
    .in3(out_reg_43_reg_43),
    .in4(out_reg_35_reg_35),
    .in5(out_reg_50_reg_50),
    .in6(out_reg_47_reg_47),
    .in7(out_lut_expr_FU_92_i0_fu___float_adde8m23b_127nih_501195_502641),
    .in8(1'b0),
    .in9(1'b0));
  lut_expr_FU #(.BITSIZE_in1(64),
    .BITSIZE_out1(1)) fu___float_adde8m23b_127nih_501195_510624 (.out1(out_lut_expr_FU_105_i0_fu___float_adde8m23b_127nih_501195_510624),
    .in1(out_const_55),
    .in2(out_reg_29_reg_29),
    .in3(out_reg_44_reg_44),
    .in4(out_reg_36_reg_36),
    .in5(out_reg_51_reg_51),
    .in6(out_reg_48_reg_48),
    .in7(out_lut_expr_FU_92_i0_fu___float_adde8m23b_127nih_501195_502641),
    .in8(1'b0),
    .in9(1'b0));
  lut_expr_FU #(.BITSIZE_in1(64),
    .BITSIZE_out1(1)) fu___float_adde8m23b_127nih_501195_510627 (.out1(out_lut_expr_FU_106_i0_fu___float_adde8m23b_127nih_501195_510627),
    .in1(out_const_55),
    .in2(out_reg_29_reg_29),
    .in3(out_reg_45_reg_45),
    .in4(out_reg_37_reg_37),
    .in5(out_reg_52_reg_52),
    .in6(out_reg_49_reg_49),
    .in7(out_lut_expr_FU_92_i0_fu___float_adde8m23b_127nih_501195_502641),
    .in8(1'b0),
    .in9(1'b0));
  lut_expr_FU #(.BITSIZE_in1(31),
    .BITSIZE_out1(1)) fu___float_adde8m23b_127nih_501195_510632 (.out1(out_lut_expr_FU_108_i0_fu___float_adde8m23b_127nih_501195_510632),
    .in1(out_const_21),
    .in2(out_reg_29_reg_29),
    .in3(out_reg_40_reg_40),
    .in4(out_reg_32_reg_32),
    .in5(out_reg_54_reg_54),
    .in6(out_lut_expr_FU_92_i0_fu___float_adde8m23b_127nih_501195_502641),
    .in7(1'b0),
    .in8(1'b0),
    .in9(1'b0));
  lut_expr_FU #(.BITSIZE_in1(31),
    .BITSIZE_out1(1)) fu___float_adde8m23b_127nih_501195_510635 (.out1(out_lut_expr_FU_109_i0_fu___float_adde8m23b_127nih_501195_510635),
    .in1(out_const_21),
    .in2(out_reg_29_reg_29),
    .in3(out_reg_41_reg_41),
    .in4(out_reg_33_reg_33),
    .in5(out_reg_55_reg_55),
    .in6(out_lut_expr_FU_92_i0_fu___float_adde8m23b_127nih_501195_502641),
    .in7(1'b0),
    .in8(1'b0),
    .in9(1'b0));
  lut_expr_FU #(.BITSIZE_in1(8),
    .BITSIZE_out1(1)) fu___float_adde8m23b_127nih_501195_510639 (.out1(out_lut_expr_FU_111_i0_fu___float_adde8m23b_127nih_501195_510639),
    .in1(out_const_39),
    .in2(out_lut_expr_FU_106_i0_fu___float_adde8m23b_127nih_501195_510627),
    .in3(out_lut_expr_FU_107_i0_fu___float_adde8m23b_127nih_501195_502650),
    .in4(out_lut_expr_FU_109_i0_fu___float_adde8m23b_127nih_501195_510635),
    .in5(1'b0),
    .in6(1'b0),
    .in7(1'b0),
    .in8(1'b0),
    .in9(1'b0));
  lut_expr_FU #(.BITSIZE_in1(31),
    .BITSIZE_out1(1)) fu___float_adde8m23b_127nih_501195_510644 (.out1(out_lut_expr_FU_110_i0_fu___float_adde8m23b_127nih_501195_510644),
    .in1(out_const_21),
    .in2(out_reg_29_reg_29),
    .in3(out_reg_39_reg_39),
    .in4(out_reg_31_reg_31),
    .in5(out_reg_53_reg_53),
    .in6(out_lut_expr_FU_92_i0_fu___float_adde8m23b_127nih_501195_502641),
    .in7(1'b0),
    .in8(1'b0),
    .in9(1'b0));
  lut_expr_FU #(.BITSIZE_in1(32),
    .BITSIZE_out1(1)) fu___float_adde8m23b_127nih_501195_510650 (.out1(out_lut_expr_FU_122_i0_fu___float_adde8m23b_127nih_501195_510650),
    .in1(out_const_41),
    .in2(out_lut_expr_FU_104_i0_fu___float_adde8m23b_127nih_501195_510621),
    .in3(out_lut_expr_FU_107_i0_fu___float_adde8m23b_127nih_501195_502650),
    .in4(out_lut_expr_FU_111_i0_fu___float_adde8m23b_127nih_501195_510639),
    .in5(out_lut_expr_FU_112_i0_fu___float_adde8m23b_127nih_501195_502659),
    .in6(out_lut_expr_FU_110_i0_fu___float_adde8m23b_127nih_501195_510644),
    .in7(1'b0),
    .in8(1'b0),
    .in9(1'b0));
  lut_expr_FU #(.BITSIZE_in1(4),
    .BITSIZE_out1(1)) fu___float_adde8m23b_127nih_501195_510653 (.out1(out_lut_expr_FU_123_i0_fu___float_adde8m23b_127nih_501195_510653),
    .in1(out_const_22),
    .in2(out_ui_lt_expr_FU_32_32_32_200_i0_fu___float_adde8m23b_127nih_501195_502490),
    .in3(out_ui_extract_bit_expr_FU_19_i0_fu___float_adde8m23b_127nih_501195_507927),
    .in4(out_ui_extract_bit_expr_FU_18_i0_fu___float_adde8m23b_127nih_501195_507364),
    .in5(1'b0),
    .in6(1'b0),
    .in7(1'b0),
    .in8(1'b0),
    .in9(1'b0));
  lut_expr_FU #(.BITSIZE_in1(58),
    .BITSIZE_out1(1)) fu___float_adde8m23b_127nih_501195_510657 (.out1(out_lut_expr_FU_124_i0_fu___float_adde8m23b_127nih_501195_510657),
    .in1(out_const_31),
    .in2(out_reg_18_reg_18),
    .in3(out_reg_19_reg_19),
    .in4(out_reg_20_reg_20),
    .in5(out_lut_expr_FU_107_i0_fu___float_adde8m23b_127nih_501195_502650),
    .in6(out_lut_expr_FU_112_i0_fu___float_adde8m23b_127nih_501195_502659),
    .in7(out_lut_expr_FU_122_i0_fu___float_adde8m23b_127nih_501195_510650),
    .in8(1'b0),
    .in9(1'b0));
  lut_expr_FU #(.BITSIZE_in1(64),
    .BITSIZE_out1(1)) fu___float_adde8m23b_127nih_501195_510661 (.out1(out_lut_expr_FU_125_i0_fu___float_adde8m23b_127nih_501195_510661),
    .in1(out_const_38),
    .in2(out_reg_29_reg_29),
    .in3(out_reg_22_reg_22),
    .in4(out_reg_17_reg_17),
    .in5(out_reg_21_reg_21),
    .in6(out_lut_expr_FU_92_i0_fu___float_adde8m23b_127nih_501195_502641),
    .in7(out_lut_expr_FU_124_i0_fu___float_adde8m23b_127nih_501195_510657),
    .in8(1'b0),
    .in9(1'b0));
  lut_expr_FU #(.BITSIZE_in1(44),
    .BITSIZE_out1(1)) fu___float_adde8m23b_127nih_501195_510664 (.out1(out_lut_expr_FU_126_i0_fu___float_adde8m23b_127nih_501195_510664),
    .in1(out_const_19),
    .in2(out_reg_2_reg_2),
    .in3(out_reg_15_reg_15),
    .in4(out_reg_12_reg_12),
    .in5(out_reg_16_reg_16),
    .in6(out_reg_13_reg_13),
    .in7(out_lut_expr_FU_125_i0_fu___float_adde8m23b_127nih_501195_510661),
    .in8(1'b0),
    .in9(1'b0));
  lut_expr_FU #(.BITSIZE_in1(8),
    .BITSIZE_out1(1)) fu___float_adde8m23b_127nih_501195_510672 (.out1(out_lut_expr_FU_135_i0_fu___float_adde8m23b_127nih_501195_510672),
    .in1(out_const_45),
    .in2(out_ui_lt_expr_FU_32_32_32_200_i0_fu___float_adde8m23b_127nih_501195_502490),
    .in3(out_ui_extract_bit_expr_FU_21_i0_fu___float_adde8m23b_127nih_501195_507934),
    .in4(out_ui_extract_bit_expr_FU_20_i0_fu___float_adde8m23b_127nih_501195_507371),
    .in5(out_lut_expr_FU_123_i0_fu___float_adde8m23b_127nih_501195_510653),
    .in6(out_lut_expr_FU_42_i0_fu___float_adde8m23b_127nih_501195_510563),
    .in7(out_lut_expr_FU_43_i0_fu___float_adde8m23b_127nih_501195_510566),
    .in8(1'b0),
    .in9(1'b0));
  lut_expr_FU #(.BITSIZE_in1(17),
    .BITSIZE_out1(1)) fu___float_adde8m23b_127nih_501195_510675 (.out1(out_lut_expr_FU_136_i0_fu___float_adde8m23b_127nih_501195_510675),
    .in1(out_const_6),
    .in2(out_lut_expr_FU_44_i0_fu___float_adde8m23b_127nih_501195_510569),
    .in3(out_lut_expr_FU_45_i0_fu___float_adde8m23b_127nih_501195_510572),
    .in4(out_lut_expr_FU_46_i0_fu___float_adde8m23b_127nih_501195_510575),
    .in5(out_lut_expr_FU_47_i0_fu___float_adde8m23b_127nih_501195_510578),
    .in6(out_lut_expr_FU_135_i0_fu___float_adde8m23b_127nih_501195_510672),
    .in7(1'b0),
    .in8(1'b0),
    .in9(1'b0));
  lut_expr_FU #(.BITSIZE_in1(32),
    .BITSIZE_out1(1)) fu___float_adde8m23b_127nih_501195_510679 (.out1(out_lut_expr_FU_137_i0_fu___float_adde8m23b_127nih_501195_510679),
    .in1(out_const_47),
    .in2(out_ui_lt_expr_FU_32_32_32_200_i0_fu___float_adde8m23b_127nih_501195_502490),
    .in3(out_ui_extract_bit_expr_FU_31_i0_fu___float_adde8m23b_127nih_501195_507969),
    .in4(out_ui_extract_bit_expr_FU_30_i0_fu___float_adde8m23b_127nih_501195_507406),
    .in5(out_ui_extract_bit_expr_FU_33_i0_fu___float_adde8m23b_127nih_501195_507976),
    .in6(out_ui_extract_bit_expr_FU_32_i0_fu___float_adde8m23b_127nih_501195_507413),
    .in7(1'b0),
    .in8(1'b0),
    .in9(1'b0));
  lut_expr_FU #(.BITSIZE_in1(64),
    .BITSIZE_out1(1)) fu___float_adde8m23b_127nih_501195_510683 (.out1(out_lut_expr_FU_138_i0_fu___float_adde8m23b_127nih_501195_510683),
    .in1(out_const_48),
    .in2(out_ui_lt_expr_FU_32_32_32_200_i0_fu___float_adde8m23b_127nih_501195_502490),
    .in3(out_ui_extract_bit_expr_FU_27_i0_fu___float_adde8m23b_127nih_501195_507955),
    .in4(out_ui_extract_bit_expr_FU_26_i0_fu___float_adde8m23b_127nih_501195_507392),
    .in5(out_ui_extract_bit_expr_FU_29_i0_fu___float_adde8m23b_127nih_501195_507962),
    .in6(out_ui_extract_bit_expr_FU_28_i0_fu___float_adde8m23b_127nih_501195_507399),
    .in7(out_lut_expr_FU_137_i0_fu___float_adde8m23b_127nih_501195_510679),
    .in8(1'b0),
    .in9(1'b0));
  lut_expr_FU #(.BITSIZE_in1(64),
    .BITSIZE_out1(1)) fu___float_adde8m23b_127nih_501195_510686 (.out1(out_lut_expr_FU_139_i0_fu___float_adde8m23b_127nih_501195_510686),
    .in1(out_const_48),
    .in2(out_ui_lt_expr_FU_32_32_32_200_i0_fu___float_adde8m23b_127nih_501195_502490),
    .in3(out_ui_extract_bit_expr_FU_39_i0_fu___float_adde8m23b_127nih_501195_507997),
    .in4(out_ui_extract_bit_expr_FU_38_i0_fu___float_adde8m23b_127nih_501195_507434),
    .in5(out_ui_extract_bit_expr_FU_41_i0_fu___float_adde8m23b_127nih_501195_508004),
    .in6(out_ui_extract_bit_expr_FU_40_i0_fu___float_adde8m23b_127nih_501195_507441),
    .in7(out_lut_expr_FU_138_i0_fu___float_adde8m23b_127nih_501195_510683),
    .in8(1'b0),
    .in9(1'b0));
  lut_expr_FU #(.BITSIZE_in1(64),
    .BITSIZE_out1(1)) fu___float_adde8m23b_127nih_501195_510689 (.out1(out_lut_expr_FU_140_i0_fu___float_adde8m23b_127nih_501195_510689),
    .in1(out_const_48),
    .in2(out_ui_lt_expr_FU_32_32_32_200_i0_fu___float_adde8m23b_127nih_501195_502490),
    .in3(out_ui_extract_bit_expr_FU_35_i0_fu___float_adde8m23b_127nih_501195_507983),
    .in4(out_ui_extract_bit_expr_FU_34_i0_fu___float_adde8m23b_127nih_501195_507420),
    .in5(out_ui_extract_bit_expr_FU_37_i0_fu___float_adde8m23b_127nih_501195_507990),
    .in6(out_ui_extract_bit_expr_FU_36_i0_fu___float_adde8m23b_127nih_501195_507427),
    .in7(out_lut_expr_FU_139_i0_fu___float_adde8m23b_127nih_501195_510686),
    .in8(1'b0),
    .in9(1'b0));
  lut_expr_FU #(.BITSIZE_in1(32),
    .BITSIZE_out1(1)) fu___float_adde8m23b_127nih_501195_510694 (.out1(out_lut_expr_FU_142_i0_fu___float_adde8m23b_127nih_501195_510694),
    .in1(out_const_58),
    .in2(out_reg_29_reg_29),
    .in3(out_lut_expr_FU_92_i0_fu___float_adde8m23b_127nih_501195_502641),
    .in4(out_lut_expr_FU_107_i0_fu___float_adde8m23b_127nih_501195_502650),
    .in5(out_lut_expr_FU_112_i0_fu___float_adde8m23b_127nih_501195_502659),
    .in6(out_lut_expr_FU_122_i0_fu___float_adde8m23b_127nih_501195_510650),
    .in7(out_lut_expr_FU_126_i0_fu___float_adde8m23b_127nih_501195_510664),
    .in8(1'b0),
    .in9(1'b0));
  lut_expr_FU #(.BITSIZE_in1(48),
    .BITSIZE_out1(1)) fu___float_adde8m23b_127nih_501195_510698 (.out1(out_lut_expr_FU_143_i0_fu___float_adde8m23b_127nih_501195_510698),
    .in1(out_const_46),
    .in2(out_reg_2_reg_2),
    .in3(out_reg_14_reg_14),
    .in4(out_reg_11_reg_11),
    .in5(out_ui_extract_bit_expr_FU_88_i0_fu___float_adde8m23b_127nih_501195_509464),
    .in6(out_reg_20_reg_20),
    .in7(out_reg_23_reg_23),
    .in8(1'b0),
    .in9(1'b0));
  lut_expr_FU #(.BITSIZE_in1(32),
    .BITSIZE_out1(1)) fu___float_adde8m23b_127nih_501195_510706 (.out1(out_lut_expr_FU_147_i0_fu___float_adde8m23b_127nih_501195_510706),
    .in1(out_const_49),
    .in2(out_ui_lt_expr_FU_32_32_32_200_i0_fu___float_adde8m23b_127nih_501195_502490),
    .in3(out_ui_extract_bit_expr_FU_6_i0_fu___float_adde8m23b_127nih_501195_507325),
    .in4(out_ui_extract_bit_expr_FU_5_i0_fu___float_adde8m23b_127nih_501195_506850),
    .in5(out_ui_extract_bit_expr_FU_9_i0_fu___float_adde8m23b_127nih_501195_507332),
    .in6(out_ui_extract_bit_expr_FU_8_i0_fu___float_adde8m23b_127nih_501195_506857),
    .in7(1'b0),
    .in8(1'b0),
    .in9(1'b0));
  register_STD #(.BITSIZE_in1(27),
    .BITSIZE_out1(27)) reg_0 (.out1(out_reg_0_reg_0),
    .clock(clock),
    .reset(reset),
    .in1(out_ui_bit_and_expr_FU_32_0_32_161_i0_fu___float_adde8m23b_127nih_501195_501570),
    .wenable(wrenable_reg_0));
  register_SE #(.BITSIZE_in1(23),
    .BITSIZE_out1(23)) reg_1 (.out1(out_reg_1_reg_1),
    .clock(clock),
    .reset(reset),
    .in1(out_ui_lshift_expr_FU_32_0_32_188_i0_fu___float_adde8m23b_127nih_501195_502170),
    .wenable(wrenable_reg_1));
  register_SE #(.BITSIZE_in1(1),
    .BITSIZE_out1(1)) reg_10 (.out1(out_reg_10_reg_10),
    .clock(clock),
    .reset(reset),
    .in1(out_ui_extract_bit_expr_FU_9_i0_fu___float_adde8m23b_127nih_501195_507332),
    .wenable(wrenable_reg_10));
  register_STD #(.BITSIZE_in1(1),
    .BITSIZE_out1(1)) reg_11 (.out1(out_reg_11_reg_11),
    .clock(clock),
    .reset(reset),
    .in1(out_ui_extract_bit_expr_FU_16_i0_fu___float_adde8m23b_127nih_501195_507357),
    .wenable(wrenable_reg_11));
  register_SE #(.BITSIZE_in1(1),
    .BITSIZE_out1(1)) reg_12 (.out1(out_reg_12_reg_12),
    .clock(clock),
    .reset(reset),
    .in1(out_ui_extract_bit_expr_FU_20_i0_fu___float_adde8m23b_127nih_501195_507371),
    .wenable(wrenable_reg_12));
  register_SE #(.BITSIZE_in1(1),
    .BITSIZE_out1(1)) reg_13 (.out1(out_reg_13_reg_13),
    .clock(clock),
    .reset(reset),
    .in1(out_ui_extract_bit_expr_FU_22_i0_fu___float_adde8m23b_127nih_501195_507378),
    .wenable(wrenable_reg_13));
  register_STD #(.BITSIZE_in1(1),
    .BITSIZE_out1(1)) reg_14 (.out1(out_reg_14_reg_14),
    .clock(clock),
    .reset(reset),
    .in1(out_ui_extract_bit_expr_FU_17_i0_fu___float_adde8m23b_127nih_501195_507920),
    .wenable(wrenable_reg_14));
  register_SE #(.BITSIZE_in1(1),
    .BITSIZE_out1(1)) reg_15 (.out1(out_reg_15_reg_15),
    .clock(clock),
    .reset(reset),
    .in1(out_ui_extract_bit_expr_FU_21_i0_fu___float_adde8m23b_127nih_501195_507934),
    .wenable(wrenable_reg_15));
  register_SE #(.BITSIZE_in1(1),
    .BITSIZE_out1(1)) reg_16 (.out1(out_reg_16_reg_16),
    .clock(clock),
    .reset(reset),
    .in1(out_ui_extract_bit_expr_FU_23_i0_fu___float_adde8m23b_127nih_501195_507941),
    .wenable(wrenable_reg_16));
  register_SE #(.BITSIZE_in1(1),
    .BITSIZE_out1(1)) reg_17 (.out1(out_reg_17_reg_17),
    .clock(clock),
    .reset(reset),
    .in1(out_lut_expr_FU_43_i0_fu___float_adde8m23b_127nih_501195_510566),
    .wenable(wrenable_reg_17));
  register_SE #(.BITSIZE_in1(1),
    .BITSIZE_out1(1)) reg_18 (.out1(out_reg_18_reg_18),
    .clock(clock),
    .reset(reset),
    .in1(out_lut_expr_FU_44_i0_fu___float_adde8m23b_127nih_501195_510569),
    .wenable(wrenable_reg_18));
  register_SE #(.BITSIZE_in1(1),
    .BITSIZE_out1(1)) reg_19 (.out1(out_reg_19_reg_19),
    .clock(clock),
    .reset(reset),
    .in1(out_lut_expr_FU_45_i0_fu___float_adde8m23b_127nih_501195_510572),
    .wenable(wrenable_reg_19));
  register_SE #(.BITSIZE_in1(1),
    .BITSIZE_out1(1)) reg_2 (.out1(out_reg_2_reg_2),
    .clock(clock),
    .reset(reset),
    .in1(out_ui_lt_expr_FU_32_32_32_200_i0_fu___float_adde8m23b_127nih_501195_502490),
    .wenable(wrenable_reg_2));
  register_SE #(.BITSIZE_in1(1),
    .BITSIZE_out1(1)) reg_20 (.out1(out_reg_20_reg_20),
    .clock(clock),
    .reset(reset),
    .in1(out_lut_expr_FU_46_i0_fu___float_adde8m23b_127nih_501195_510575),
    .wenable(wrenable_reg_20));
  register_SE #(.BITSIZE_in1(1),
    .BITSIZE_out1(1)) reg_21 (.out1(out_reg_21_reg_21),
    .clock(clock),
    .reset(reset),
    .in1(out_lut_expr_FU_47_i0_fu___float_adde8m23b_127nih_501195_510578),
    .wenable(wrenable_reg_21));
  register_SE #(.BITSIZE_in1(1),
    .BITSIZE_out1(1)) reg_22 (.out1(out_reg_22_reg_22),
    .clock(clock),
    .reset(reset),
    .in1(out_lut_expr_FU_123_i0_fu___float_adde8m23b_127nih_501195_510653),
    .wenable(wrenable_reg_22));
  register_STD #(.BITSIZE_in1(1),
    .BITSIZE_out1(1)) reg_23 (.out1(out_reg_23_reg_23),
    .clock(clock),
    .reset(reset),
    .in1(out_lut_expr_FU_135_i0_fu___float_adde8m23b_127nih_501195_510672),
    .wenable(wrenable_reg_23));
  register_SE #(.BITSIZE_in1(1),
    .BITSIZE_out1(1)) reg_24 (.out1(out_reg_24_reg_24),
    .clock(clock),
    .reset(reset),
    .in1(out_lut_expr_FU_136_i0_fu___float_adde8m23b_127nih_501195_510675),
    .wenable(wrenable_reg_24));
  register_SE #(.BITSIZE_in1(1),
    .BITSIZE_out1(1)) reg_25 (.out1(out_reg_25_reg_25),
    .clock(clock),
    .reset(reset),
    .in1(out_lut_expr_FU_140_i0_fu___float_adde8m23b_127nih_501195_510689),
    .wenable(wrenable_reg_25));
  register_STD #(.BITSIZE_in1(27),
    .BITSIZE_out1(27)) reg_26 (.out1(out_reg_26_reg_26),
    .clock(clock),
    .reset(reset),
    .in1(out_ui_bit_and_expr_FU_32_0_32_161_i1_fu___float_adde8m23b_127nih_501195_501588),
    .wenable(wrenable_reg_26));
  register_STD #(.BITSIZE_in1(43),
    .BITSIZE_out1(43)) reg_27 (.out1(out_reg_27_reg_27),
    .clock(clock),
    .reset(reset),
    .in1(out_ui_lshift_expr_FU_64_0_64_191_i0_fu___float_adde8m23b_127nih_501195_501655),
    .wenable(wrenable_reg_27));
  register_STD #(.BITSIZE_in1(1),
    .BITSIZE_out1(1)) reg_28 (.out1(out_reg_28_reg_28),
    .clock(clock),
    .reset(reset),
    .in1(out_ui_ne_expr_FU_32_0_32_203_i0_fu___float_adde8m23b_127nih_501195_502578),
    .wenable(wrenable_reg_28));
  register_STD #(.BITSIZE_in1(1),
    .BITSIZE_out1(1)) reg_29 (.out1(out_reg_29_reg_29),
    .clock(clock),
    .reset(reset),
    .in1(out_ui_eq_expr_FU_16_0_16_183_i0_fu___float_adde8m23b_127nih_501195_502628),
    .wenable(wrenable_reg_29));
  register_SE #(.BITSIZE_in1(1),
    .BITSIZE_out1(1)) reg_3 (.out1(out_reg_3_reg_3),
    .clock(clock),
    .reset(reset),
    .in1(out_lut_expr_FU_141_i0_fu___float_adde8m23b_127nih_501195_502776),
    .wenable(wrenable_reg_3));
  register_STD #(.BITSIZE_in1(1),
    .BITSIZE_out1(1)) reg_30 (.out1(out_reg_30_reg_30),
    .clock(clock),
    .reset(reset),
    .in1(out_ui_extract_bit_expr_FU_74_i0_fu___float_adde8m23b_127nih_501195_509408),
    .wenable(wrenable_reg_30));
  register_STD #(.BITSIZE_in1(1),
    .BITSIZE_out1(1)) reg_31 (.out1(out_reg_31_reg_31),
    .clock(clock),
    .reset(reset),
    .in1(out_ui_extract_bit_expr_FU_76_i0_fu___float_adde8m23b_127nih_501195_509416),
    .wenable(wrenable_reg_31));
  register_STD #(.BITSIZE_in1(1),
    .BITSIZE_out1(1)) reg_32 (.out1(out_reg_32_reg_32),
    .clock(clock),
    .reset(reset),
    .in1(out_ui_extract_bit_expr_FU_78_i0_fu___float_adde8m23b_127nih_501195_509424),
    .wenable(wrenable_reg_32));
  register_STD #(.BITSIZE_in1(1),
    .BITSIZE_out1(1)) reg_33 (.out1(out_reg_33_reg_33),
    .clock(clock),
    .reset(reset),
    .in1(out_ui_extract_bit_expr_FU_80_i0_fu___float_adde8m23b_127nih_501195_509432),
    .wenable(wrenable_reg_33));
  register_STD #(.BITSIZE_in1(1),
    .BITSIZE_out1(1)) reg_34 (.out1(out_reg_34_reg_34),
    .clock(clock),
    .reset(reset),
    .in1(out_ui_extract_bit_expr_FU_82_i0_fu___float_adde8m23b_127nih_501195_509440),
    .wenable(wrenable_reg_34));
  register_STD #(.BITSIZE_in1(1),
    .BITSIZE_out1(1)) reg_35 (.out1(out_reg_35_reg_35),
    .clock(clock),
    .reset(reset),
    .in1(out_ui_extract_bit_expr_FU_84_i0_fu___float_adde8m23b_127nih_501195_509448),
    .wenable(wrenable_reg_35));
  register_STD #(.BITSIZE_in1(1),
    .BITSIZE_out1(1)) reg_36 (.out1(out_reg_36_reg_36),
    .clock(clock),
    .reset(reset),
    .in1(out_ui_extract_bit_expr_FU_86_i0_fu___float_adde8m23b_127nih_501195_509456),
    .wenable(wrenable_reg_36));
  register_STD #(.BITSIZE_in1(1),
    .BITSIZE_out1(1)) reg_37 (.out1(out_reg_37_reg_37),
    .clock(clock),
    .reset(reset),
    .in1(out_ui_extract_bit_expr_FU_88_i0_fu___float_adde8m23b_127nih_501195_509464),
    .wenable(wrenable_reg_37));
  register_STD #(.BITSIZE_in1(1),
    .BITSIZE_out1(1)) reg_38 (.out1(out_reg_38_reg_38),
    .clock(clock),
    .reset(reset),
    .in1(out_ui_extract_bit_expr_FU_73_i0_fu___float_adde8m23b_127nih_501195_509799),
    .wenable(wrenable_reg_38));
  register_STD #(.BITSIZE_in1(1),
    .BITSIZE_out1(1)) reg_39 (.out1(out_reg_39_reg_39),
    .clock(clock),
    .reset(reset),
    .in1(out_ui_extract_bit_expr_FU_75_i0_fu___float_adde8m23b_127nih_501195_509803),
    .wenable(wrenable_reg_39));
  register_STD #(.BITSIZE_in1(24),
    .BITSIZE_out1(24)) reg_4 (.out1(out_reg_4_reg_4),
    .clock(clock),
    .reset(reset),
    .in1(out_ui_rshift_expr_FU_32_0_32_208_i3_fu___float_adde8m23b_127nih_501195_503524),
    .wenable(wrenable_reg_4));
  register_STD #(.BITSIZE_in1(1),
    .BITSIZE_out1(1)) reg_40 (.out1(out_reg_40_reg_40),
    .clock(clock),
    .reset(reset),
    .in1(out_ui_extract_bit_expr_FU_77_i0_fu___float_adde8m23b_127nih_501195_509807),
    .wenable(wrenable_reg_40));
  register_STD #(.BITSIZE_in1(1),
    .BITSIZE_out1(1)) reg_41 (.out1(out_reg_41_reg_41),
    .clock(clock),
    .reset(reset),
    .in1(out_ui_extract_bit_expr_FU_79_i0_fu___float_adde8m23b_127nih_501195_509811),
    .wenable(wrenable_reg_41));
  register_STD #(.BITSIZE_in1(1),
    .BITSIZE_out1(1)) reg_42 (.out1(out_reg_42_reg_42),
    .clock(clock),
    .reset(reset),
    .in1(out_ui_extract_bit_expr_FU_81_i0_fu___float_adde8m23b_127nih_501195_509815),
    .wenable(wrenable_reg_42));
  register_STD #(.BITSIZE_in1(1),
    .BITSIZE_out1(1)) reg_43 (.out1(out_reg_43_reg_43),
    .clock(clock),
    .reset(reset),
    .in1(out_ui_extract_bit_expr_FU_83_i0_fu___float_adde8m23b_127nih_501195_509819),
    .wenable(wrenable_reg_43));
  register_STD #(.BITSIZE_in1(1),
    .BITSIZE_out1(1)) reg_44 (.out1(out_reg_44_reg_44),
    .clock(clock),
    .reset(reset),
    .in1(out_ui_extract_bit_expr_FU_85_i0_fu___float_adde8m23b_127nih_501195_509823),
    .wenable(wrenable_reg_44));
  register_STD #(.BITSIZE_in1(1),
    .BITSIZE_out1(1)) reg_45 (.out1(out_reg_45_reg_45),
    .clock(clock),
    .reset(reset),
    .in1(out_ui_extract_bit_expr_FU_87_i0_fu___float_adde8m23b_127nih_501195_509827),
    .wenable(wrenable_reg_45));
  register_STD #(.BITSIZE_in1(1),
    .BITSIZE_out1(1)) reg_46 (.out1(out_reg_46_reg_46),
    .clock(clock),
    .reset(reset),
    .in1(out_ui_extract_bit_expr_FU_93_i0_fu___float_adde8m23b_127nih_501195_510146),
    .wenable(wrenable_reg_46));
  register_STD #(.BITSIZE_in1(1),
    .BITSIZE_out1(1)) reg_47 (.out1(out_reg_47_reg_47),
    .clock(clock),
    .reset(reset),
    .in1(out_ui_extract_bit_expr_FU_95_i0_fu___float_adde8m23b_127nih_501195_510158),
    .wenable(wrenable_reg_47));
  register_STD #(.BITSIZE_in1(1),
    .BITSIZE_out1(1)) reg_48 (.out1(out_reg_48_reg_48),
    .clock(clock),
    .reset(reset),
    .in1(out_ui_extract_bit_expr_FU_97_i0_fu___float_adde8m23b_127nih_501195_510170),
    .wenable(wrenable_reg_48));
  register_STD #(.BITSIZE_in1(1),
    .BITSIZE_out1(1)) reg_49 (.out1(out_reg_49_reg_49),
    .clock(clock),
    .reset(reset),
    .in1(out_ui_extract_bit_expr_FU_99_i0_fu___float_adde8m23b_127nih_501195_510182),
    .wenable(wrenable_reg_49));
  register_STD #(.BITSIZE_in1(24),
    .BITSIZE_out1(24)) reg_5 (.out1(out_reg_5_reg_5),
    .clock(clock),
    .reset(reset),
    .in1(out_ui_rshift_expr_FU_32_0_32_208_i4_fu___float_adde8m23b_127nih_501195_503538),
    .wenable(wrenable_reg_5));
  register_STD #(.BITSIZE_in1(1),
    .BITSIZE_out1(1)) reg_50 (.out1(out_reg_50_reg_50),
    .clock(clock),
    .reset(reset),
    .in1(out_ui_extract_bit_expr_FU_94_i0_fu___float_adde8m23b_127nih_501195_510382),
    .wenable(wrenable_reg_50));
  register_STD #(.BITSIZE_in1(1),
    .BITSIZE_out1(1)) reg_51 (.out1(out_reg_51_reg_51),
    .clock(clock),
    .reset(reset),
    .in1(out_ui_extract_bit_expr_FU_96_i0_fu___float_adde8m23b_127nih_501195_510386),
    .wenable(wrenable_reg_51));
  register_STD #(.BITSIZE_in1(1),
    .BITSIZE_out1(1)) reg_52 (.out1(out_reg_52_reg_52),
    .clock(clock),
    .reset(reset),
    .in1(out_ui_extract_bit_expr_FU_98_i0_fu___float_adde8m23b_127nih_501195_510390),
    .wenable(wrenable_reg_52));
  register_STD #(.BITSIZE_in1(1),
    .BITSIZE_out1(1)) reg_53 (.out1(out_reg_53_reg_53),
    .clock(clock),
    .reset(reset),
    .in1(out_ui_extract_bit_expr_FU_102_i0_fu___float_adde8m23b_127nih_501195_510442),
    .wenable(wrenable_reg_53));
  register_STD #(.BITSIZE_in1(1),
    .BITSIZE_out1(1)) reg_54 (.out1(out_reg_54_reg_54),
    .clock(clock),
    .reset(reset),
    .in1(out_ui_extract_bit_expr_FU_100_i0_fu___float_adde8m23b_127nih_501195_510515),
    .wenable(wrenable_reg_54));
  register_STD #(.BITSIZE_in1(1),
    .BITSIZE_out1(1)) reg_55 (.out1(out_reg_55_reg_55),
    .clock(clock),
    .reset(reset),
    .in1(out_ui_extract_bit_expr_FU_101_i0_fu___float_adde8m23b_127nih_501195_510527),
    .wenable(wrenable_reg_55));
  register_STD #(.BITSIZE_in1(1),
    .BITSIZE_out1(1)) reg_56 (.out1(out_reg_56_reg_56),
    .clock(clock),
    .reset(reset),
    .in1(out_lut_expr_FU_89_i0_fu___float_adde8m23b_127nih_501195_510603),
    .wenable(wrenable_reg_56));
  register_STD #(.BITSIZE_in1(1),
    .BITSIZE_out1(1)) reg_57 (.out1(out_reg_57_reg_57),
    .clock(clock),
    .reset(reset),
    .in1(out_lut_expr_FU_143_i0_fu___float_adde8m23b_127nih_501195_510698),
    .wenable(wrenable_reg_57));
  register_STD #(.BITSIZE_in1(31),
    .BITSIZE_out1(31)) reg_58 (.out1(out_reg_58_reg_58),
    .clock(clock),
    .reset(reset),
    .in1(out_ui_bit_ior_expr_FU_0_32_32_169_i0_fu___float_adde8m23b_127nih_501195_502067),
    .wenable(wrenable_reg_58));
  register_STD #(.BITSIZE_in1(1),
    .BITSIZE_out1(1)) reg_59 (.out1(out_reg_59_reg_59),
    .clock(clock),
    .reset(reset),
    .in1(out_UUdata_converter_FU_134_i0_fu___float_adde8m23b_127nih_501195_502104),
    .wenable(wrenable_reg_59));
  register_SE #(.BITSIZE_in1(8),
    .BITSIZE_out1(8)) reg_6 (.out1(out_reg_6_reg_6),
    .clock(clock),
    .reset(reset),
    .in1(out_ASSIGN_UNSIGNED_FU_7_i0_fu___float_adde8m23b_127nih_501195_503973),
    .wenable(wrenable_reg_6));
  register_STD #(.BITSIZE_in1(32),
    .BITSIZE_out1(32)) reg_60 (.out1(out_reg_60_reg_60),
    .clock(clock),
    .reset(reset),
    .in1(out_ui_lshift_expr_FU_32_0_32_189_i0_fu___float_adde8m23b_127nih_501195_502219),
    .wenable(wrenable_reg_60));
  register_STD #(.BITSIZE_in1(1),
    .BITSIZE_out1(1)) reg_61 (.out1(out_reg_61_reg_61),
    .clock(clock),
    .reset(reset),
    .in1(out_lut_expr_FU_144_i0_fu___float_adde8m23b_127nih_501195_502788),
    .wenable(wrenable_reg_61));
  register_SE #(.BITSIZE_in1(1),
    .BITSIZE_out1(1)) reg_7 (.out1(out_reg_7_reg_7),
    .clock(clock),
    .reset(reset),
    .in1(out_ui_extract_bit_expr_FU_5_i0_fu___float_adde8m23b_127nih_501195_506850),
    .wenable(wrenable_reg_7));
  register_SE #(.BITSIZE_in1(1),
    .BITSIZE_out1(1)) reg_8 (.out1(out_reg_8_reg_8),
    .clock(clock),
    .reset(reset),
    .in1(out_ui_extract_bit_expr_FU_8_i0_fu___float_adde8m23b_127nih_501195_506857),
    .wenable(wrenable_reg_8));
  register_SE #(.BITSIZE_in1(1),
    .BITSIZE_out1(1)) reg_9 (.out1(out_reg_9_reg_9),
    .clock(clock),
    .reset(reset),
    .in1(out_ui_extract_bit_expr_FU_6_i0_fu___float_adde8m23b_127nih_501195_507325),
    .wenable(wrenable_reg_9));
  // io-signal post fix
  assign return_port = out_conv_out_ui_bit_ior_expr_FU_0_32_32_171_i0_fu___float_adde8m23b_127nih_501195_502228_32_64;

endmodule

// FSM based controller description for __float_adde8m23b_127nih
// This component has been derived from the input source code and so it does not fall under the copyright of PandA framework, but it follows the input source code copyright, and may be aggregated with components of the BAMBU/PANDA IP LIBRARY.
// Author(s): Component automatically generated by bambu
// License: THIS COMPONENT IS PROVIDED "AS IS" AND WITHOUT ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, WITHOUT LIMITATION, THE IMPLIED WARRANTIES OF MERCHANTIBILITY AND FITNESS FOR A PARTICULAR PURPOSE.
`timescale 1ns / 1ps
module controller___float_adde8m23b_127nih(done_port,
  wrenable_reg_0,
  wrenable_reg_1,
  wrenable_reg_10,
  wrenable_reg_11,
  wrenable_reg_12,
  wrenable_reg_13,
  wrenable_reg_14,
  wrenable_reg_15,
  wrenable_reg_16,
  wrenable_reg_17,
  wrenable_reg_18,
  wrenable_reg_19,
  wrenable_reg_2,
  wrenable_reg_20,
  wrenable_reg_21,
  wrenable_reg_22,
  wrenable_reg_23,
  wrenable_reg_24,
  wrenable_reg_25,
  wrenable_reg_26,
  wrenable_reg_27,
  wrenable_reg_28,
  wrenable_reg_29,
  wrenable_reg_3,
  wrenable_reg_30,
  wrenable_reg_31,
  wrenable_reg_32,
  wrenable_reg_33,
  wrenable_reg_34,
  wrenable_reg_35,
  wrenable_reg_36,
  wrenable_reg_37,
  wrenable_reg_38,
  wrenable_reg_39,
  wrenable_reg_4,
  wrenable_reg_40,
  wrenable_reg_41,
  wrenable_reg_42,
  wrenable_reg_43,
  wrenable_reg_44,
  wrenable_reg_45,
  wrenable_reg_46,
  wrenable_reg_47,
  wrenable_reg_48,
  wrenable_reg_49,
  wrenable_reg_5,
  wrenable_reg_50,
  wrenable_reg_51,
  wrenable_reg_52,
  wrenable_reg_53,
  wrenable_reg_54,
  wrenable_reg_55,
  wrenable_reg_56,
  wrenable_reg_57,
  wrenable_reg_58,
  wrenable_reg_59,
  wrenable_reg_6,
  wrenable_reg_60,
  wrenable_reg_61,
  wrenable_reg_7,
  wrenable_reg_8,
  wrenable_reg_9,
  clock,
  reset,
  start_port);
  // IN
  input clock;
  input reset;
  input start_port;
  // OUT
  output done_port;
  output wrenable_reg_0;
  output wrenable_reg_1;
  output wrenable_reg_10;
  output wrenable_reg_11;
  output wrenable_reg_12;
  output wrenable_reg_13;
  output wrenable_reg_14;
  output wrenable_reg_15;
  output wrenable_reg_16;
  output wrenable_reg_17;
  output wrenable_reg_18;
  output wrenable_reg_19;
  output wrenable_reg_2;
  output wrenable_reg_20;
  output wrenable_reg_21;
  output wrenable_reg_22;
  output wrenable_reg_23;
  output wrenable_reg_24;
  output wrenable_reg_25;
  output wrenable_reg_26;
  output wrenable_reg_27;
  output wrenable_reg_28;
  output wrenable_reg_29;
  output wrenable_reg_3;
  output wrenable_reg_30;
  output wrenable_reg_31;
  output wrenable_reg_32;
  output wrenable_reg_33;
  output wrenable_reg_34;
  output wrenable_reg_35;
  output wrenable_reg_36;
  output wrenable_reg_37;
  output wrenable_reg_38;
  output wrenable_reg_39;
  output wrenable_reg_4;
  output wrenable_reg_40;
  output wrenable_reg_41;
  output wrenable_reg_42;
  output wrenable_reg_43;
  output wrenable_reg_44;
  output wrenable_reg_45;
  output wrenable_reg_46;
  output wrenable_reg_47;
  output wrenable_reg_48;
  output wrenable_reg_49;
  output wrenable_reg_5;
  output wrenable_reg_50;
  output wrenable_reg_51;
  output wrenable_reg_52;
  output wrenable_reg_53;
  output wrenable_reg_54;
  output wrenable_reg_55;
  output wrenable_reg_56;
  output wrenable_reg_57;
  output wrenable_reg_58;
  output wrenable_reg_59;
  output wrenable_reg_6;
  output wrenable_reg_60;
  output wrenable_reg_61;
  output wrenable_reg_7;
  output wrenable_reg_8;
  output wrenable_reg_9;
  parameter [3:0] S_0 = 4'b0001,
    S_1 = 4'b0010,
    S_2 = 4'b0100,
    S_3 = 4'b1000;
  reg [3:0] _present_state=S_0, _next_state;
  reg done_port;
  reg wrenable_reg_0;
  reg wrenable_reg_1;
  reg wrenable_reg_10;
  reg wrenable_reg_11;
  reg wrenable_reg_12;
  reg wrenable_reg_13;
  reg wrenable_reg_14;
  reg wrenable_reg_15;
  reg wrenable_reg_16;
  reg wrenable_reg_17;
  reg wrenable_reg_18;
  reg wrenable_reg_19;
  reg wrenable_reg_2;
  reg wrenable_reg_20;
  reg wrenable_reg_21;
  reg wrenable_reg_22;
  reg wrenable_reg_23;
  reg wrenable_reg_24;
  reg wrenable_reg_25;
  reg wrenable_reg_26;
  reg wrenable_reg_27;
  reg wrenable_reg_28;
  reg wrenable_reg_29;
  reg wrenable_reg_3;
  reg wrenable_reg_30;
  reg wrenable_reg_31;
  reg wrenable_reg_32;
  reg wrenable_reg_33;
  reg wrenable_reg_34;
  reg wrenable_reg_35;
  reg wrenable_reg_36;
  reg wrenable_reg_37;
  reg wrenable_reg_38;
  reg wrenable_reg_39;
  reg wrenable_reg_4;
  reg wrenable_reg_40;
  reg wrenable_reg_41;
  reg wrenable_reg_42;
  reg wrenable_reg_43;
  reg wrenable_reg_44;
  reg wrenable_reg_45;
  reg wrenable_reg_46;
  reg wrenable_reg_47;
  reg wrenable_reg_48;
  reg wrenable_reg_49;
  reg wrenable_reg_5;
  reg wrenable_reg_50;
  reg wrenable_reg_51;
  reg wrenable_reg_52;
  reg wrenable_reg_53;
  reg wrenable_reg_54;
  reg wrenable_reg_55;
  reg wrenable_reg_56;
  reg wrenable_reg_57;
  reg wrenable_reg_58;
  reg wrenable_reg_59;
  reg wrenable_reg_6;
  reg wrenable_reg_60;
  reg wrenable_reg_61;
  reg wrenable_reg_7;
  reg wrenable_reg_8;
  reg wrenable_reg_9;
  
  always @(posedge clock)
    if (reset == 1'b0) _present_state <= S_0;
    else _present_state <= _next_state;
  
  always @(*)
  begin
    done_port = 1'b0;
    wrenable_reg_0 = 1'b0;
    wrenable_reg_1 = 1'b0;
    wrenable_reg_10 = 1'b0;
    wrenable_reg_11 = 1'b0;
    wrenable_reg_12 = 1'b0;
    wrenable_reg_13 = 1'b0;
    wrenable_reg_14 = 1'b0;
    wrenable_reg_15 = 1'b0;
    wrenable_reg_16 = 1'b0;
    wrenable_reg_17 = 1'b0;
    wrenable_reg_18 = 1'b0;
    wrenable_reg_19 = 1'b0;
    wrenable_reg_2 = 1'b0;
    wrenable_reg_20 = 1'b0;
    wrenable_reg_21 = 1'b0;
    wrenable_reg_22 = 1'b0;
    wrenable_reg_23 = 1'b0;
    wrenable_reg_24 = 1'b0;
    wrenable_reg_25 = 1'b0;
    wrenable_reg_26 = 1'b0;
    wrenable_reg_27 = 1'b0;
    wrenable_reg_28 = 1'b0;
    wrenable_reg_29 = 1'b0;
    wrenable_reg_3 = 1'b0;
    wrenable_reg_30 = 1'b0;
    wrenable_reg_31 = 1'b0;
    wrenable_reg_32 = 1'b0;
    wrenable_reg_33 = 1'b0;
    wrenable_reg_34 = 1'b0;
    wrenable_reg_35 = 1'b0;
    wrenable_reg_36 = 1'b0;
    wrenable_reg_37 = 1'b0;
    wrenable_reg_38 = 1'b0;
    wrenable_reg_39 = 1'b0;
    wrenable_reg_4 = 1'b0;
    wrenable_reg_40 = 1'b0;
    wrenable_reg_41 = 1'b0;
    wrenable_reg_42 = 1'b0;
    wrenable_reg_43 = 1'b0;
    wrenable_reg_44 = 1'b0;
    wrenable_reg_45 = 1'b0;
    wrenable_reg_46 = 1'b0;
    wrenable_reg_47 = 1'b0;
    wrenable_reg_48 = 1'b0;
    wrenable_reg_49 = 1'b0;
    wrenable_reg_5 = 1'b0;
    wrenable_reg_50 = 1'b0;
    wrenable_reg_51 = 1'b0;
    wrenable_reg_52 = 1'b0;
    wrenable_reg_53 = 1'b0;
    wrenable_reg_54 = 1'b0;
    wrenable_reg_55 = 1'b0;
    wrenable_reg_56 = 1'b0;
    wrenable_reg_57 = 1'b0;
    wrenable_reg_58 = 1'b0;
    wrenable_reg_59 = 1'b0;
    wrenable_reg_6 = 1'b0;
    wrenable_reg_60 = 1'b0;
    wrenable_reg_61 = 1'b0;
    wrenable_reg_7 = 1'b0;
    wrenable_reg_8 = 1'b0;
    wrenable_reg_9 = 1'b0;
    case (_present_state)
      S_0 :
        if(start_port == 1'b1)
        begin
          wrenable_reg_0 = 1'b1;
          wrenable_reg_1 = 1'b1;
          wrenable_reg_10 = 1'b1;
          wrenable_reg_11 = 1'b1;
          wrenable_reg_12 = 1'b1;
          wrenable_reg_13 = 1'b1;
          wrenable_reg_14 = 1'b1;
          wrenable_reg_15 = 1'b1;
          wrenable_reg_16 = 1'b1;
          wrenable_reg_17 = 1'b1;
          wrenable_reg_18 = 1'b1;
          wrenable_reg_19 = 1'b1;
          wrenable_reg_2 = 1'b1;
          wrenable_reg_20 = 1'b1;
          wrenable_reg_21 = 1'b1;
          wrenable_reg_22 = 1'b1;
          wrenable_reg_23 = 1'b1;
          wrenable_reg_24 = 1'b1;
          wrenable_reg_25 = 1'b1;
          wrenable_reg_3 = 1'b1;
          wrenable_reg_4 = 1'b1;
          wrenable_reg_5 = 1'b1;
          wrenable_reg_6 = 1'b1;
          wrenable_reg_7 = 1'b1;
          wrenable_reg_8 = 1'b1;
          wrenable_reg_9 = 1'b1;
          _next_state = S_1;
        end
        else
        begin
          _next_state = S_0;
        end
      S_1 :
        begin
          wrenable_reg_26 = 1'b1;
          wrenable_reg_27 = 1'b1;
          wrenable_reg_28 = 1'b1;
          wrenable_reg_29 = 1'b1;
          wrenable_reg_30 = 1'b1;
          wrenable_reg_31 = 1'b1;
          wrenable_reg_32 = 1'b1;
          wrenable_reg_33 = 1'b1;
          wrenable_reg_34 = 1'b1;
          wrenable_reg_35 = 1'b1;
          wrenable_reg_36 = 1'b1;
          wrenable_reg_37 = 1'b1;
          wrenable_reg_38 = 1'b1;
          wrenable_reg_39 = 1'b1;
          wrenable_reg_40 = 1'b1;
          wrenable_reg_41 = 1'b1;
          wrenable_reg_42 = 1'b1;
          wrenable_reg_43 = 1'b1;
          wrenable_reg_44 = 1'b1;
          wrenable_reg_45 = 1'b1;
          wrenable_reg_46 = 1'b1;
          wrenable_reg_47 = 1'b1;
          wrenable_reg_48 = 1'b1;
          wrenable_reg_49 = 1'b1;
          wrenable_reg_50 = 1'b1;
          wrenable_reg_51 = 1'b1;
          wrenable_reg_52 = 1'b1;
          wrenable_reg_53 = 1'b1;
          wrenable_reg_54 = 1'b1;
          wrenable_reg_55 = 1'b1;
          wrenable_reg_56 = 1'b1;
          wrenable_reg_57 = 1'b1;
          _next_state = S_2;
        end
      S_2 :
        begin
          wrenable_reg_58 = 1'b1;
          wrenable_reg_59 = 1'b1;
          wrenable_reg_60 = 1'b1;
          wrenable_reg_61 = 1'b1;
          _next_state = S_3;
          done_port = 1'b1;
        end
      S_3 :
        begin
          _next_state = S_0;
        end
      default :
        begin
          _next_state = S_0;
        end
    endcase
  end
endmodule

// This component is part of the BAMBU/PANDA IP LIBRARY
// Copyright (C) 2004-2024 Politecnico di Milano
// Author(s): Marco Lattuada <marco.lattuada@polimi.it>
// License: PANDA_LGPLv3
`timescale 1ns / 1ps
module flipflop_AR(clock,
  reset,
  in1,
  out1);
  parameter BITSIZE_in1=1,
    BITSIZE_out1=1;
  // IN
  input clock;
  input reset;
  input in1;
  // OUT
  output out1;
  
  reg reg_out1 =0;
  assign out1 = reg_out1;
  always @(posedge clock or negedge reset)
    if (reset == 1'b0)
      reg_out1 <= {BITSIZE_out1{1'b0}};
    else
      reg_out1 <= in1;
endmodule

// Top component for __float_adde8m23b_127nih
// This component has been derived from the input source code and so it does not fall under the copyright of PandA framework, but it follows the input source code copyright, and may be aggregated with components of the BAMBU/PANDA IP LIBRARY.
// Author(s): Component automatically generated by bambu
// License: THIS COMPONENT IS PROVIDED "AS IS" AND WITHOUT ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, WITHOUT LIMITATION, THE IMPLIED WARRANTIES OF MERCHANTIBILITY AND FITNESS FOR A PARTICULAR PURPOSE.
`timescale 1ns / 1ps
module __float_adde8m23b_127nih(clock,
  reset,
  start_port,
  done_port,
  a,
  b,
  return_port);
  // IN
  input clock;
  input reset;
  input start_port;
  input [63:0] a;
  input [63:0] b;
  // OUT
  output done_port;
  output [63:0] return_port;
  // Component and signal declarations
  wire done_delayed_REG_signal_in;
  wire done_delayed_REG_signal_out;
  wire wrenable_reg_0;
  wire wrenable_reg_1;
  wire wrenable_reg_10;
  wire wrenable_reg_11;
  wire wrenable_reg_12;
  wire wrenable_reg_13;
  wire wrenable_reg_14;
  wire wrenable_reg_15;
  wire wrenable_reg_16;
  wire wrenable_reg_17;
  wire wrenable_reg_18;
  wire wrenable_reg_19;
  wire wrenable_reg_2;
  wire wrenable_reg_20;
  wire wrenable_reg_21;
  wire wrenable_reg_22;
  wire wrenable_reg_23;
  wire wrenable_reg_24;
  wire wrenable_reg_25;
  wire wrenable_reg_26;
  wire wrenable_reg_27;
  wire wrenable_reg_28;
  wire wrenable_reg_29;
  wire wrenable_reg_3;
  wire wrenable_reg_30;
  wire wrenable_reg_31;
  wire wrenable_reg_32;
  wire wrenable_reg_33;
  wire wrenable_reg_34;
  wire wrenable_reg_35;
  wire wrenable_reg_36;
  wire wrenable_reg_37;
  wire wrenable_reg_38;
  wire wrenable_reg_39;
  wire wrenable_reg_4;
  wire wrenable_reg_40;
  wire wrenable_reg_41;
  wire wrenable_reg_42;
  wire wrenable_reg_43;
  wire wrenable_reg_44;
  wire wrenable_reg_45;
  wire wrenable_reg_46;
  wire wrenable_reg_47;
  wire wrenable_reg_48;
  wire wrenable_reg_49;
  wire wrenable_reg_5;
  wire wrenable_reg_50;
  wire wrenable_reg_51;
  wire wrenable_reg_52;
  wire wrenable_reg_53;
  wire wrenable_reg_54;
  wire wrenable_reg_55;
  wire wrenable_reg_56;
  wire wrenable_reg_57;
  wire wrenable_reg_58;
  wire wrenable_reg_59;
  wire wrenable_reg_6;
  wire wrenable_reg_60;
  wire wrenable_reg_61;
  wire wrenable_reg_7;
  wire wrenable_reg_8;
  wire wrenable_reg_9;
  
  controller___float_adde8m23b_127nih Controller_i (.done_port(done_delayed_REG_signal_in),
    .wrenable_reg_0(wrenable_reg_0),
    .wrenable_reg_1(wrenable_reg_1),
    .wrenable_reg_10(wrenable_reg_10),
    .wrenable_reg_11(wrenable_reg_11),
    .wrenable_reg_12(wrenable_reg_12),
    .wrenable_reg_13(wrenable_reg_13),
    .wrenable_reg_14(wrenable_reg_14),
    .wrenable_reg_15(wrenable_reg_15),
    .wrenable_reg_16(wrenable_reg_16),
    .wrenable_reg_17(wrenable_reg_17),
    .wrenable_reg_18(wrenable_reg_18),
    .wrenable_reg_19(wrenable_reg_19),
    .wrenable_reg_2(wrenable_reg_2),
    .wrenable_reg_20(wrenable_reg_20),
    .wrenable_reg_21(wrenable_reg_21),
    .wrenable_reg_22(wrenable_reg_22),
    .wrenable_reg_23(wrenable_reg_23),
    .wrenable_reg_24(wrenable_reg_24),
    .wrenable_reg_25(wrenable_reg_25),
    .wrenable_reg_26(wrenable_reg_26),
    .wrenable_reg_27(wrenable_reg_27),
    .wrenable_reg_28(wrenable_reg_28),
    .wrenable_reg_29(wrenable_reg_29),
    .wrenable_reg_3(wrenable_reg_3),
    .wrenable_reg_30(wrenable_reg_30),
    .wrenable_reg_31(wrenable_reg_31),
    .wrenable_reg_32(wrenable_reg_32),
    .wrenable_reg_33(wrenable_reg_33),
    .wrenable_reg_34(wrenable_reg_34),
    .wrenable_reg_35(wrenable_reg_35),
    .wrenable_reg_36(wrenable_reg_36),
    .wrenable_reg_37(wrenable_reg_37),
    .wrenable_reg_38(wrenable_reg_38),
    .wrenable_reg_39(wrenable_reg_39),
    .wrenable_reg_4(wrenable_reg_4),
    .wrenable_reg_40(wrenable_reg_40),
    .wrenable_reg_41(wrenable_reg_41),
    .wrenable_reg_42(wrenable_reg_42),
    .wrenable_reg_43(wrenable_reg_43),
    .wrenable_reg_44(wrenable_reg_44),
    .wrenable_reg_45(wrenable_reg_45),
    .wrenable_reg_46(wrenable_reg_46),
    .wrenable_reg_47(wrenable_reg_47),
    .wrenable_reg_48(wrenable_reg_48),
    .wrenable_reg_49(wrenable_reg_49),
    .wrenable_reg_5(wrenable_reg_5),
    .wrenable_reg_50(wrenable_reg_50),
    .wrenable_reg_51(wrenable_reg_51),
    .wrenable_reg_52(wrenable_reg_52),
    .wrenable_reg_53(wrenable_reg_53),
    .wrenable_reg_54(wrenable_reg_54),
    .wrenable_reg_55(wrenable_reg_55),
    .wrenable_reg_56(wrenable_reg_56),
    .wrenable_reg_57(wrenable_reg_57),
    .wrenable_reg_58(wrenable_reg_58),
    .wrenable_reg_59(wrenable_reg_59),
    .wrenable_reg_6(wrenable_reg_6),
    .wrenable_reg_60(wrenable_reg_60),
    .wrenable_reg_61(wrenable_reg_61),
    .wrenable_reg_7(wrenable_reg_7),
    .wrenable_reg_8(wrenable_reg_8),
    .wrenable_reg_9(wrenable_reg_9),
    .clock(clock),
    .reset(reset),
    .start_port(start_port));
  datapath___float_adde8m23b_127nih Datapath_i (.return_port(return_port),
    .clock(clock),
    .reset(reset),
    .in_port_a(a),
    .in_port_b(b),
    .wrenable_reg_0(wrenable_reg_0),
    .wrenable_reg_1(wrenable_reg_1),
    .wrenable_reg_10(wrenable_reg_10),
    .wrenable_reg_11(wrenable_reg_11),
    .wrenable_reg_12(wrenable_reg_12),
    .wrenable_reg_13(wrenable_reg_13),
    .wrenable_reg_14(wrenable_reg_14),
    .wrenable_reg_15(wrenable_reg_15),
    .wrenable_reg_16(wrenable_reg_16),
    .wrenable_reg_17(wrenable_reg_17),
    .wrenable_reg_18(wrenable_reg_18),
    .wrenable_reg_19(wrenable_reg_19),
    .wrenable_reg_2(wrenable_reg_2),
    .wrenable_reg_20(wrenable_reg_20),
    .wrenable_reg_21(wrenable_reg_21),
    .wrenable_reg_22(wrenable_reg_22),
    .wrenable_reg_23(wrenable_reg_23),
    .wrenable_reg_24(wrenable_reg_24),
    .wrenable_reg_25(wrenable_reg_25),
    .wrenable_reg_26(wrenable_reg_26),
    .wrenable_reg_27(wrenable_reg_27),
    .wrenable_reg_28(wrenable_reg_28),
    .wrenable_reg_29(wrenable_reg_29),
    .wrenable_reg_3(wrenable_reg_3),
    .wrenable_reg_30(wrenable_reg_30),
    .wrenable_reg_31(wrenable_reg_31),
    .wrenable_reg_32(wrenable_reg_32),
    .wrenable_reg_33(wrenable_reg_33),
    .wrenable_reg_34(wrenable_reg_34),
    .wrenable_reg_35(wrenable_reg_35),
    .wrenable_reg_36(wrenable_reg_36),
    .wrenable_reg_37(wrenable_reg_37),
    .wrenable_reg_38(wrenable_reg_38),
    .wrenable_reg_39(wrenable_reg_39),
    .wrenable_reg_4(wrenable_reg_4),
    .wrenable_reg_40(wrenable_reg_40),
    .wrenable_reg_41(wrenable_reg_41),
    .wrenable_reg_42(wrenable_reg_42),
    .wrenable_reg_43(wrenable_reg_43),
    .wrenable_reg_44(wrenable_reg_44),
    .wrenable_reg_45(wrenable_reg_45),
    .wrenable_reg_46(wrenable_reg_46),
    .wrenable_reg_47(wrenable_reg_47),
    .wrenable_reg_48(wrenable_reg_48),
    .wrenable_reg_49(wrenable_reg_49),
    .wrenable_reg_5(wrenable_reg_5),
    .wrenable_reg_50(wrenable_reg_50),
    .wrenable_reg_51(wrenable_reg_51),
    .wrenable_reg_52(wrenable_reg_52),
    .wrenable_reg_53(wrenable_reg_53),
    .wrenable_reg_54(wrenable_reg_54),
    .wrenable_reg_55(wrenable_reg_55),
    .wrenable_reg_56(wrenable_reg_56),
    .wrenable_reg_57(wrenable_reg_57),
    .wrenable_reg_58(wrenable_reg_58),
    .wrenable_reg_59(wrenable_reg_59),
    .wrenable_reg_6(wrenable_reg_6),
    .wrenable_reg_60(wrenable_reg_60),
    .wrenable_reg_61(wrenable_reg_61),
    .wrenable_reg_7(wrenable_reg_7),
    .wrenable_reg_8(wrenable_reg_8),
    .wrenable_reg_9(wrenable_reg_9));
  flipflop_AR #(.BITSIZE_in1(1),
    .BITSIZE_out1(1)) done_delayed_REG (.out1(done_delayed_REG_signal_out),
    .clock(clock),
    .reset(reset),
    .in1(done_delayed_REG_signal_in));
  // io-signal post fix
  assign done_port = done_delayed_REG_signal_out;

endmodule

// This component is part of the BAMBU/PANDA IP LIBRARY
// Copyright (C) 2004-2024 Politecnico di Milano
// Author(s): Fabrizio Ferrandi <fabrizio.ferrandi@polimi.it>, Christian Pilato <christian.pilato@polimi.it>
// License: PANDA_LGPLv3
`timescale 1ns / 1ps
module MUX_GATE(sel,
  in1,
  in2,
  out1);
  parameter BITSIZE_in1=1,
    BITSIZE_in2=1,
    BITSIZE_out1=1;
  // IN
  input sel;
  input [BITSIZE_in1-1:0] in1;
  input [BITSIZE_in2-1:0] in2;
  // OUT
  output [BITSIZE_out1-1:0] out1;
  assign out1 = sel ? in1 : in2;
endmodule

// Datapath RTL description for forward_kernel
// This component has been derived from the input source code and so it does not fall under the copyright of PandA framework, but it follows the input source code copyright, and may be aggregated with components of the BAMBU/PANDA IP LIBRARY.
// Author(s): Component automatically generated by bambu
// License: THIS COMPONENT IS PROVIDED "AS IS" AND WITHOUT ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, WITHOUT LIMITATION, THE IMPLIED WARRANTIES OF MERCHANTIBILITY AND FITNESS FOR A PARTICULAR PURPOSE.
`timescale 1ns / 1ps
module datapath_forward_kernel(clock,
  reset,
  in_port_P0,
  in_port_P1,
  in_port_P2,
  M_Rdata_ram,
  M_DataRdy,
  Min_oe_ram,
  Min_we_ram,
  Min_addr_ram,
  Min_Wdata_ram,
  Min_data_ram_size,
  Mout_oe_ram,
  Mout_we_ram,
  Mout_addr_ram,
  Mout_Wdata_ram,
  Mout_data_ram_size,
  fuselector_BMEMORY_CTRLN_83_i0_LOAD,
  fuselector_BMEMORY_CTRLN_83_i0_STORE,
  selector_IN_UNBOUNDED_forward_kernel_500073_500104,
  selector_MUX_136_reg_0_0_0_0,
  selector_MUX_168_reg_5_0_0_0,
  selector_MUX_169_reg_6_0_0_0,
  selector_MUX_1_BMEMORY_CTRLN_83_i0_1_0_0,
  selector_MUX_1_BMEMORY_CTRLN_83_i0_1_0_1,
  selector_MUX_1_BMEMORY_CTRLN_83_i0_1_1_0,
  wrenable_reg_0,
  wrenable_reg_1,
  wrenable_reg_10,
  wrenable_reg_11,
  wrenable_reg_12,
  wrenable_reg_13,
  wrenable_reg_14,
  wrenable_reg_15,
  wrenable_reg_16,
  wrenable_reg_17,
  wrenable_reg_18,
  wrenable_reg_19,
  wrenable_reg_2,
  wrenable_reg_20,
  wrenable_reg_21,
  wrenable_reg_22,
  wrenable_reg_23,
  wrenable_reg_24,
  wrenable_reg_25,
  wrenable_reg_26,
  wrenable_reg_27,
  wrenable_reg_28,
  wrenable_reg_29,
  wrenable_reg_3,
  wrenable_reg_30,
  wrenable_reg_31,
  wrenable_reg_32,
  wrenable_reg_33,
  wrenable_reg_34,
  wrenable_reg_35,
  wrenable_reg_36,
  wrenable_reg_4,
  wrenable_reg_5,
  wrenable_reg_6,
  wrenable_reg_7,
  wrenable_reg_8,
  wrenable_reg_9,
  OUT_MULTIIF_forward_kernel_500073_503980,
  OUT_UNBOUNDED_forward_kernel_500073_500104);
  // IN
  input clock;
  input reset;
  input [31:0] in_port_P0;
  input [31:0] in_port_P1;
  input [31:0] in_port_P2;
  input [63:0] M_Rdata_ram;
  input [1:0] M_DataRdy;
  input [1:0] Min_oe_ram;
  input [1:0] Min_we_ram;
  input [63:0] Min_addr_ram;
  input [63:0] Min_Wdata_ram;
  input [11:0] Min_data_ram_size;
  input fuselector_BMEMORY_CTRLN_83_i0_LOAD;
  input fuselector_BMEMORY_CTRLN_83_i0_STORE;
  input selector_IN_UNBOUNDED_forward_kernel_500073_500104;
  input selector_MUX_136_reg_0_0_0_0;
  input selector_MUX_168_reg_5_0_0_0;
  input selector_MUX_169_reg_6_0_0_0;
  input selector_MUX_1_BMEMORY_CTRLN_83_i0_1_0_0;
  input selector_MUX_1_BMEMORY_CTRLN_83_i0_1_0_1;
  input selector_MUX_1_BMEMORY_CTRLN_83_i0_1_1_0;
  input wrenable_reg_0;
  input wrenable_reg_1;
  input wrenable_reg_10;
  input wrenable_reg_11;
  input wrenable_reg_12;
  input wrenable_reg_13;
  input wrenable_reg_14;
  input wrenable_reg_15;
  input wrenable_reg_16;
  input wrenable_reg_17;
  input wrenable_reg_18;
  input wrenable_reg_19;
  input wrenable_reg_2;
  input wrenable_reg_20;
  input wrenable_reg_21;
  input wrenable_reg_22;
  input wrenable_reg_23;
  input wrenable_reg_24;
  input wrenable_reg_25;
  input wrenable_reg_26;
  input wrenable_reg_27;
  input wrenable_reg_28;
  input wrenable_reg_29;
  input wrenable_reg_3;
  input wrenable_reg_30;
  input wrenable_reg_31;
  input wrenable_reg_32;
  input wrenable_reg_33;
  input wrenable_reg_34;
  input wrenable_reg_35;
  input wrenable_reg_36;
  input wrenable_reg_4;
  input wrenable_reg_5;
  input wrenable_reg_6;
  input wrenable_reg_7;
  input wrenable_reg_8;
  input wrenable_reg_9;
  // OUT
  output [1:0] Mout_oe_ram;
  output [1:0] Mout_we_ram;
  output [63:0] Mout_addr_ram;
  output [63:0] Mout_Wdata_ram;
  output [11:0] Mout_data_ram_size;
  output [1:0] OUT_MULTIIF_forward_kernel_500073_503980;
  output OUT_UNBOUNDED_forward_kernel_500073_500104;
  // Component and signal declarations
  wire [31:0] null_out_signal_BMEMORY_CTRLN_83_i0_out1_1;
  wire [31:0] out_BMEMORY_CTRLN_83_i0_BMEMORY_CTRLN_83_i0;
  wire [63:0] out_MUX_136_reg_0_0_0_0;
  wire [63:0] out_MUX_168_reg_5_0_0_0;
  wire [31:0] out_MUX_169_reg_6_0_0_0;
  wire [31:0] out_MUX_1_BMEMORY_CTRLN_83_i0_1_0_0;
  wire [31:0] out_MUX_1_BMEMORY_CTRLN_83_i0_1_0_1;
  wire [31:0] out_MUX_1_BMEMORY_CTRLN_83_i0_1_1_0;
  wire [7:0] out_UUdata_converter_FU_10_i0_fu_forward_kernel_500073_510721;
  wire [7:0] out_UUdata_converter_FU_12_i0_fu_forward_kernel_500073_510735;
  wire out_UUdata_converter_FU_15_i0_fu_forward_kernel_500073_510747;
  wire out_UUdata_converter_FU_33_i0_fu_forward_kernel_500073_510831;
  wire out_UUdata_converter_FU_34_i0_fu_forward_kernel_500073_510834;
  wire out_UUdata_converter_FU_36_i0_fu_forward_kernel_500073_510843;
  wire out_UUdata_converter_FU_37_i0_fu_forward_kernel_500073_510846;
  wire [9:0] out_UUdata_converter_FU_38_i0_fu_forward_kernel_500073_510858;
  wire out_UUdata_converter_FU_43_i0_fu_forward_kernel_500073_510903;
  wire out_UUdata_converter_FU_44_i0_fu_forward_kernel_500073_510906;
  wire out_UUdata_converter_FU_46_i0_fu_forward_kernel_500073_510915;
  wire [29:0] out_UUdata_converter_FU_6_i0_fu_forward_kernel_500073_500095;
  wire [31:0] out_UUdata_converter_FU_73_i0_fu_forward_kernel_500073_502249;
  wire [31:0] out_UUdata_converter_FU_74_i0_fu_forward_kernel_500073_502286;
  wire [31:0] out_UUdata_converter_FU_75_i0_fu_forward_kernel_500073_502289;
  wire [31:0] out_UUdata_converter_FU_76_i0_fu_forward_kernel_500073_502283;
  wire [29:0] out_UUdata_converter_FU_7_i0_fu_forward_kernel_500073_500100;
  wire [29:0] out_UUdata_converter_FU_82_i0_fu_forward_kernel_500073_500136;
  wire [30:0] out_UUdata_converter_FU_8_i0_fu_forward_kernel_500073_502252;
  wire [30:0] out_UUdata_converter_FU_9_i0_fu_forward_kernel_500073_502255;
  wire [63:0] out___float_adde8m23b_127nih_123_i0_fu_forward_kernel_500073_500104;
  wire out_const_0;
  wire [6:0] out_const_1;
  wire [8:0] out_const_10;
  wire [3:0] out_const_11;
  wire [7:0] out_const_12;
  wire [15:0] out_const_13;
  wire [12:0] out_const_14;
  wire [4:0] out_const_15;
  wire [5:0] out_const_16;
  wire [2:0] out_const_17;
  wire [4:0] out_const_18;
  wire [4:0] out_const_19;
  wire out_const_2;
  wire [31:0] out_const_20;
  wire [4:0] out_const_21;
  wire [4:0] out_const_22;
  wire [4:0] out_const_23;
  wire [7:0] out_const_24;
  wire [11:0] out_const_25;
  wire [4:0] out_const_26;
  wire [63:0] out_const_27;
  wire [9:0] out_const_28;
  wire [3:0] out_const_29;
  wire [1:0] out_const_3;
  wire [4:0] out_const_30;
  wire [27:0] out_const_31;
  wire [4:0] out_const_32;
  wire [7:0] out_const_33;
  wire [30:0] out_const_34;
  wire [31:0] out_const_35;
  wire [22:0] out_const_36;
  wire [31:0] out_const_37;
  wire [30:0] out_const_38;
  wire [31:0] out_const_39;
  wire [2:0] out_const_4;
  wire [32:0] out_const_40;
  wire [46:0] out_const_41;
  wire [5:0] out_const_5;
  wire [7:0] out_const_6;
  wire [14:0] out_const_7;
  wire [23:0] out_const_8;
  wire [63:0] out_const_9;
  wire [31:0] out_conv_out___float_adde8m23b_127nih_123_i0_fu_forward_kernel_500073_500104_64_32;
  wire [63:0] out_conv_out_const_0_1_64;
  wire [5:0] out_conv_out_const_1_7_6;
  wire [63:0] out_conv_out_reg_35_reg_35_32_64;
  wire [63:0] out_conv_out_reg_9_reg_9_32_64;
  wire out_lut_expr_FU_14_i0_fu_forward_kernel_500073_510744;
  wire out_lut_expr_FU_35_i0_fu_forward_kernel_500073_510840;
  wire out_lut_expr_FU_42_i0_fu_forward_kernel_500073_510900;
  wire out_lut_expr_FU_56_i0_fu_forward_kernel_500073_511097;
  wire out_lut_expr_FU_57_i0_fu_forward_kernel_500073_511100;
  wire out_lut_expr_FU_58_i0_fu_forward_kernel_500073_511103;
  wire out_lut_expr_FU_59_i0_fu_forward_kernel_500073_511106;
  wire out_lut_expr_FU_60_i0_fu_forward_kernel_500073_511109;
  wire out_lut_expr_FU_61_i0_fu_forward_kernel_500073_511112;
  wire out_lut_expr_FU_62_i0_fu_forward_kernel_500073_511115;
  wire out_lut_expr_FU_63_i0_fu_forward_kernel_500073_511118;
  wire out_lut_expr_FU_64_i0_fu_forward_kernel_500073_511121;
  wire out_lut_expr_FU_65_i0_fu_forward_kernel_500073_511124;
  wire out_lut_expr_FU_66_i0_fu_forward_kernel_500073_511127;
  wire out_lut_expr_FU_67_i0_fu_forward_kernel_500073_511130;
  wire out_lut_expr_FU_68_i0_fu_forward_kernel_500073_511134;
  wire out_lut_expr_FU_69_i0_fu_forward_kernel_500073_511138;
  wire out_lut_expr_FU_70_i0_fu_forward_kernel_500073_510996;
  wire out_lut_expr_FU_71_i0_fu_forward_kernel_500073_511002;
  wire out_lut_expr_FU_72_i0_fu_forward_kernel_500073_511008;
  wire out_lut_expr_FU_77_i0_fu_forward_kernel_500073_503986;
  wire [1:0] out_multi_read_cond_FU_78_i0_fu_forward_kernel_500073_503980;
  wire [63:0] out_reg_0_reg_0;
  wire out_reg_10_reg_10;
  wire [7:0] out_reg_11_reg_11;
  wire out_reg_12_reg_12;
  wire out_reg_13_reg_13;
  wire [23:0] out_reg_14_reg_14;
  wire out_reg_15_reg_15;
  wire out_reg_16_reg_16;
  wire out_reg_17_reg_17;
  wire [9:0] out_reg_18_reg_18;
  wire [23:0] out_reg_19_reg_19;
  wire [31:0] out_reg_1_reg_1;
  wire [31:0] out_reg_20_reg_20;
  wire [31:0] out_reg_21_reg_21;
  wire out_reg_22_reg_22;
  wire out_reg_23_reg_23;
  wire out_reg_24_reg_24;
  wire [47:0] out_reg_25_reg_25;
  wire out_reg_26_reg_26;
  wire out_reg_27_reg_27;
  wire out_reg_28_reg_28;
  wire [31:0] out_reg_29_reg_29;
  wire out_reg_2_reg_2;
  wire out_reg_30_reg_30;
  wire out_reg_31_reg_31;
  wire out_reg_32_reg_32;
  wire out_reg_33_reg_33;
  wire out_reg_34_reg_34;
  wire [31:0] out_reg_35_reg_35;
  wire [31:0] out_reg_36_reg_36;
  wire [25:0] out_reg_3_reg_3;
  wire [3:0] out_reg_4_reg_4;
  wire [63:0] out_reg_5_reg_5;
  wire [31:0] out_reg_6_reg_6;
  wire [31:0] out_reg_7_reg_7;
  wire out_reg_8_reg_8;
  wire [31:0] out_reg_9_reg_9;
  wire [22:0] out_ui_bit_and_expr_FU_0_32_32_84_i0_fu_forward_kernel_500073_510710;
  wire [22:0] out_ui_bit_and_expr_FU_0_32_32_84_i1_fu_forward_kernel_500073_510738;
  wire [23:0] out_ui_bit_and_expr_FU_32_0_32_85_i0_fu_forward_kernel_500073_510819;
  wire [23:0] out_ui_bit_and_expr_FU_32_0_32_85_i1_fu_forward_kernel_500073_510822;
  wire [22:0] out_ui_bit_and_expr_FU_32_0_32_86_i0_fu_forward_kernel_500073_510867;
  wire [22:0] out_ui_bit_and_expr_FU_32_0_32_86_i1_fu_forward_kernel_500073_510882;
  wire [30:0] out_ui_bit_and_expr_FU_32_0_32_87_i0_fu_forward_kernel_500073_510921;
  wire [46:0] out_ui_bit_and_expr_FU_64_0_64_88_i0_fu_forward_kernel_500073_510852;
  wire [32:0] out_ui_bit_and_expr_FU_64_0_64_89_i0_fu_forward_kernel_500073_510873;
  wire [3:0] out_ui_bit_and_expr_FU_8_0_8_90_i0_fu_forward_kernel_500073_503873;
  wire [7:0] out_ui_bit_and_expr_FU_8_0_8_91_i0_fu_forward_kernel_500073_510718;
  wire [7:0] out_ui_bit_and_expr_FU_8_0_8_91_i1_fu_forward_kernel_500073_510732;
  wire [29:0] out_ui_bit_ior_concat_expr_FU_92_i0_fu_forward_kernel_500073_500099;
  wire [23:0] out_ui_bit_ior_expr_FU_0_32_32_93_i0_fu_forward_kernel_500073_510813;
  wire [23:0] out_ui_bit_ior_expr_FU_0_32_32_93_i1_fu_forward_kernel_500073_510816;
  wire [31:0] out_ui_bit_ior_expr_FU_0_32_32_94_i0_fu_forward_kernel_500073_510924;
  wire [31:0] out_ui_bit_ior_expr_FU_0_32_32_95_i0_fu_forward_kernel_500073_510954;
  wire [32:0] out_ui_bit_ior_expr_FU_0_64_64_96_i0_fu_forward_kernel_500073_510870;
  wire [31:0] out_ui_cond_expr_FU_32_32_32_32_97_i0_fu_forward_kernel_500073_511005;
  wire [31:0] out_ui_cond_expr_FU_32_32_32_32_97_i1_fu_forward_kernel_500073_511011;
  wire [31:0] out_ui_cond_expr_FU_32_32_32_32_97_i2_fu_forward_kernel_500073_511014;
  wire out_ui_eq_expr_FU_32_0_32_98_i0_fu_forward_kernel_500073_510774;
  wire out_ui_eq_expr_FU_32_0_32_98_i1_fu_forward_kernel_500073_510804;
  wire out_ui_extract_bit_expr_FU_11_i0_fu_forward_kernel_500073_511022;
  wire out_ui_extract_bit_expr_FU_13_i0_fu_forward_kernel_500073_511026;
  wire out_ui_extract_bit_expr_FU_16_i0_fu_forward_kernel_500073_511030;
  wire out_ui_extract_bit_expr_FU_17_i0_fu_forward_kernel_500073_511034;
  wire out_ui_extract_bit_expr_FU_18_i0_fu_forward_kernel_500073_511038;
  wire out_ui_extract_bit_expr_FU_19_i0_fu_forward_kernel_500073_511042;
  wire out_ui_extract_bit_expr_FU_20_i0_fu_forward_kernel_500073_511046;
  wire out_ui_extract_bit_expr_FU_21_i0_fu_forward_kernel_500073_511050;
  wire out_ui_extract_bit_expr_FU_22_i0_fu_forward_kernel_500073_511054;
  wire out_ui_extract_bit_expr_FU_23_i0_fu_forward_kernel_500073_511058;
  wire out_ui_extract_bit_expr_FU_24_i0_fu_forward_kernel_500073_511062;
  wire out_ui_extract_bit_expr_FU_25_i0_fu_forward_kernel_500073_511066;
  wire out_ui_extract_bit_expr_FU_26_i0_fu_forward_kernel_500073_511070;
  wire out_ui_extract_bit_expr_FU_27_i0_fu_forward_kernel_500073_511074;
  wire out_ui_extract_bit_expr_FU_28_i0_fu_forward_kernel_500073_511078;
  wire out_ui_extract_bit_expr_FU_29_i0_fu_forward_kernel_500073_511082;
  wire out_ui_extract_bit_expr_FU_30_i0_fu_forward_kernel_500073_511086;
  wire out_ui_extract_bit_expr_FU_31_i0_fu_forward_kernel_500073_511090;
  wire out_ui_extract_bit_expr_FU_32_i0_fu_forward_kernel_500073_510828;
  wire out_ui_extract_bit_expr_FU_39_i0_fu_forward_kernel_500073_510876;
  wire out_ui_extract_bit_expr_FU_40_i0_fu_forward_kernel_500073_510894;
  wire out_ui_extract_bit_expr_FU_41_i0_fu_forward_kernel_500073_510897;
  wire out_ui_extract_bit_expr_FU_45_i0_fu_forward_kernel_500073_510912;
  wire out_ui_extract_bit_expr_FU_47_i0_fu_forward_kernel_500073_510927;
  wire out_ui_extract_bit_expr_FU_48_i0_fu_forward_kernel_500073_510930;
  wire out_ui_extract_bit_expr_FU_49_i0_fu_forward_kernel_500073_510933;
  wire out_ui_extract_bit_expr_FU_50_i0_fu_forward_kernel_500073_510936;
  wire out_ui_extract_bit_expr_FU_51_i0_fu_forward_kernel_500073_510939;
  wire out_ui_extract_bit_expr_FU_52_i0_fu_forward_kernel_500073_510942;
  wire out_ui_extract_bit_expr_FU_53_i0_fu_forward_kernel_500073_510945;
  wire out_ui_extract_bit_expr_FU_54_i0_fu_forward_kernel_500073_510948;
  wire out_ui_extract_bit_expr_FU_55_i0_fu_forward_kernel_500073_510951;
  wire [29:0] out_ui_lshift_expr_FU_32_0_32_100_i0_fu_forward_kernel_500073_503868;
  wire [23:0] out_ui_lshift_expr_FU_32_0_32_101_i0_fu_forward_kernel_500073_510885;
  wire [31:0] out_ui_lshift_expr_FU_32_0_32_102_i0_fu_forward_kernel_500073_510918;
  wire [31:0] out_ui_lshift_expr_FU_32_0_32_99_i0_fu_forward_kernel_500073_500199;
  wire [31:0] out_ui_lshift_expr_FU_32_0_32_99_i1_fu_forward_kernel_500073_500201;
  wire [31:0] out_ui_lshift_expr_FU_32_0_32_99_i2_fu_forward_kernel_500073_500213;
  wire [29:0] out_ui_lshift_expr_FU_64_0_64_103_i0_fu_forward_kernel_500073_500098;
  wire [47:0] out_ui_lshift_expr_FU_64_0_64_104_i0_fu_forward_kernel_500073_510855;
  wire [32:0] out_ui_lshift_expr_FU_64_0_64_105_i0_fu_forward_kernel_500073_510861;
  wire [46:0] out_ui_lshift_expr_FU_64_64_64_106_i0_fu_forward_kernel_500073_510849;
  wire out_ui_lt_expr_FU_64_0_64_107_i0_fu_forward_kernel_500073_500207;
  wire out_ui_lt_expr_FU_64_0_64_108_i0_fu_forward_kernel_500073_500216;
  wire [47:0] out_ui_mult_expr_FU_32_32_32_0_109_i0_fu_forward_kernel_500073_510825;
  wire out_ui_ne_expr_FU_32_0_32_110_i0_fu_forward_kernel_500073_510777;
  wire out_ui_ne_expr_FU_32_0_32_110_i1_fu_forward_kernel_500073_510807;
  wire out_ui_ne_expr_FU_32_0_32_111_i0_fu_forward_kernel_500073_510891;
  wire [9:0] out_ui_plus_expr_FU_16_16_16_112_i0_fu_forward_kernel_500073_510837;
  wire [25:0] out_ui_plus_expr_FU_32_32_32_113_i0_fu_forward_kernel_500073_503864;
  wire [32:0] out_ui_plus_expr_FU_32_32_32_113_i1_fu_forward_kernel_500073_510909;
  wire [63:0] out_ui_plus_expr_FU_64_0_64_114_i0_fu_forward_kernel_500073_500106;
  wire [63:0] out_ui_plus_expr_FU_64_0_64_114_i1_fu_forward_kernel_500073_500143;
  wire [31:0] out_ui_pointer_plus_expr_FU_32_32_32_115_i0_fu_forward_kernel_500073_500096;
  wire [31:0] out_ui_pointer_plus_expr_FU_32_32_32_115_i1_fu_forward_kernel_500073_500101;
  wire [31:0] out_ui_pointer_plus_expr_FU_32_32_32_115_i2_fu_forward_kernel_500073_500127;
  wire [25:0] out_ui_rshift_expr_FU_32_0_32_116_i0_fu_forward_kernel_500073_503856;
  wire [7:0] out_ui_rshift_expr_FU_32_0_32_117_i0_fu_forward_kernel_500073_510715;
  wire [7:0] out_ui_rshift_expr_FU_32_0_32_117_i1_fu_forward_kernel_500073_510727;
  wire [22:0] out_ui_rshift_expr_FU_32_0_32_118_i0_fu_forward_kernel_500073_510888;
  wire [25:0] out_ui_rshift_expr_FU_64_0_64_119_i0_fu_forward_kernel_500073_503861;
  wire [22:0] out_ui_rshift_expr_FU_64_0_64_120_i0_fu_forward_kernel_500073_510864;
  wire [22:0] out_ui_rshift_expr_FU_64_0_64_121_i0_fu_forward_kernel_500073_510879;
  wire [9:0] out_ui_ternary_plus_expr_FU_16_0_16_16_122_i0_fu_forward_kernel_500073_510810;
  wire [63:0] out_uu_conv_conn_obj_0_UUdata_converter_FU_uu_conv_0;
  wire [31:0] out_uu_conv_conn_obj_1_UUdata_converter_FU_uu_conv_1;
  wire s_done_fu_forward_kernel_500073_500104;
  
  BMEMORY_CTRLN #(.BITSIZE_in1(32),
    .PORTSIZE_in1(2),
    .BITSIZE_in2(32),
    .PORTSIZE_in2(2),
    .BITSIZE_in3(6),
    .PORTSIZE_in3(2),
    .BITSIZE_in4(1),
    .PORTSIZE_in4(2),
    .BITSIZE_sel_LOAD(1),
    .PORTSIZE_sel_LOAD(2),
    .BITSIZE_sel_STORE(1),
    .PORTSIZE_sel_STORE(2),
    .BITSIZE_out1(32),
    .PORTSIZE_out1(2),
    .BITSIZE_Min_oe_ram(1),
    .PORTSIZE_Min_oe_ram(2),
    .BITSIZE_Min_we_ram(1),
    .PORTSIZE_Min_we_ram(2),
    .BITSIZE_Mout_oe_ram(1),
    .PORTSIZE_Mout_oe_ram(2),
    .BITSIZE_Mout_we_ram(1),
    .PORTSIZE_Mout_we_ram(2),
    .BITSIZE_M_DataRdy(1),
    .PORTSIZE_M_DataRdy(2),
    .BITSIZE_Min_addr_ram(32),
    .PORTSIZE_Min_addr_ram(2),
    .BITSIZE_Mout_addr_ram(32),
    .PORTSIZE_Mout_addr_ram(2),
    .BITSIZE_M_Rdata_ram(32),
    .PORTSIZE_M_Rdata_ram(2),
    .BITSIZE_Min_Wdata_ram(32),
    .PORTSIZE_Min_Wdata_ram(2),
    .BITSIZE_Mout_Wdata_ram(32),
    .PORTSIZE_Mout_Wdata_ram(2),
    .BITSIZE_Min_data_ram_size(6),
    .PORTSIZE_Min_data_ram_size(2),
    .BITSIZE_Mout_data_ram_size(6),
    .PORTSIZE_Mout_data_ram_size(2)) BMEMORY_CTRLN_83_i0 (.out1({null_out_signal_BMEMORY_CTRLN_83_i0_out1_1,
      out_BMEMORY_CTRLN_83_i0_BMEMORY_CTRLN_83_i0}),
    .Mout_oe_ram(Mout_oe_ram),
    .Mout_we_ram(Mout_we_ram),
    .Mout_addr_ram(Mout_addr_ram),
    .Mout_Wdata_ram(Mout_Wdata_ram),
    .Mout_data_ram_size(Mout_data_ram_size),
    .clock(clock),
    .in1({32'b00000000000000000000000000000000,
      out_uu_conv_conn_obj_1_UUdata_converter_FU_uu_conv_1}),
    .in2({32'b00000000000000000000000000000000,
      out_MUX_1_BMEMORY_CTRLN_83_i0_1_1_0}),
    .in3({6'b000000,
      out_conv_out_const_1_7_6}),
    .in4({1'b0,
      out_const_2}),
    .sel_LOAD({1'b0,
      fuselector_BMEMORY_CTRLN_83_i0_LOAD}),
    .sel_STORE({1'b0,
      fuselector_BMEMORY_CTRLN_83_i0_STORE}),
    .Min_oe_ram(Min_oe_ram),
    .Min_we_ram(Min_we_ram),
    .Min_addr_ram(Min_addr_ram),
    .M_Rdata_ram(M_Rdata_ram),
    .Min_Wdata_ram(Min_Wdata_ram),
    .Min_data_ram_size(Min_data_ram_size),
    .M_DataRdy(M_DataRdy));
  MUX_GATE #(.BITSIZE_in1(64),
    .BITSIZE_in2(64),
    .BITSIZE_out1(64)) MUX_136_reg_0_0_0_0 (.out1(out_MUX_136_reg_0_0_0_0),
    .sel(selector_MUX_136_reg_0_0_0_0),
    .in1(out_ui_plus_expr_FU_64_0_64_114_i1_fu_forward_kernel_500073_500143),
    .in2(out_uu_conv_conn_obj_0_UUdata_converter_FU_uu_conv_0));
  MUX_GATE #(.BITSIZE_in1(64),
    .BITSIZE_in2(64),
    .BITSIZE_out1(64)) MUX_168_reg_5_0_0_0 (.out1(out_MUX_168_reg_5_0_0_0),
    .sel(selector_MUX_168_reg_5_0_0_0),
    .in1(out_ui_plus_expr_FU_64_0_64_114_i0_fu_forward_kernel_500073_500106),
    .in2(out_uu_conv_conn_obj_0_UUdata_converter_FU_uu_conv_0));
  MUX_GATE #(.BITSIZE_in1(32),
    .BITSIZE_in2(32),
    .BITSIZE_out1(32)) MUX_169_reg_6_0_0_0 (.out1(out_MUX_169_reg_6_0_0_0),
    .sel(selector_MUX_169_reg_6_0_0_0),
    .in1(out_BMEMORY_CTRLN_83_i0_BMEMORY_CTRLN_83_i0),
    .in2(out_UUdata_converter_FU_76_i0_fu_forward_kernel_500073_502283));
  MUX_GATE #(.BITSIZE_in1(32),
    .BITSIZE_in2(32),
    .BITSIZE_out1(32)) MUX_1_BMEMORY_CTRLN_83_i0_1_0_0 (.out1(out_MUX_1_BMEMORY_CTRLN_83_i0_1_0_0),
    .sel(selector_MUX_1_BMEMORY_CTRLN_83_i0_1_0_0),
    .in1(out_reg_7_reg_7),
    .in2(out_reg_1_reg_1));
  MUX_GATE #(.BITSIZE_in1(32),
    .BITSIZE_in2(32),
    .BITSIZE_out1(32)) MUX_1_BMEMORY_CTRLN_83_i0_1_0_1 (.out1(out_MUX_1_BMEMORY_CTRLN_83_i0_1_0_1),
    .sel(selector_MUX_1_BMEMORY_CTRLN_83_i0_1_0_1),
    .in1(out_ui_pointer_plus_expr_FU_32_32_32_115_i0_fu_forward_kernel_500073_500096),
    .in2(out_ui_pointer_plus_expr_FU_32_32_32_115_i2_fu_forward_kernel_500073_500127));
  MUX_GATE #(.BITSIZE_in1(32),
    .BITSIZE_in2(32),
    .BITSIZE_out1(32)) MUX_1_BMEMORY_CTRLN_83_i0_1_1_0 (.out1(out_MUX_1_BMEMORY_CTRLN_83_i0_1_1_0),
    .sel(selector_MUX_1_BMEMORY_CTRLN_83_i0_1_1_0),
    .in1(out_MUX_1_BMEMORY_CTRLN_83_i0_1_0_0),
    .in2(out_MUX_1_BMEMORY_CTRLN_83_i0_1_0_1));
  UUdata_converter_FU #(.BITSIZE_in1(64),
    .BITSIZE_out1(64)) UUdata_converter_FU_uu_conv_0 (.out1(out_uu_conv_conn_obj_0_UUdata_converter_FU_uu_conv_0),
    .in1(out_conv_out_const_0_1_64));
  UUdata_converter_FU #(.BITSIZE_in1(32),
    .BITSIZE_out1(32)) UUdata_converter_FU_uu_conv_1 (.out1(out_uu_conv_conn_obj_1_UUdata_converter_FU_uu_conv_1),
    .in1(out_UUdata_converter_FU_76_i0_fu_forward_kernel_500073_502283));
  constant_value #(.BITSIZE_out1(1),
    .value(1'b0)) const_0 (.out1(out_const_0));
  constant_value #(.BITSIZE_out1(7),
    .value(7'b0100000)) const_1 (.out1(out_const_1));
  constant_value #(.BITSIZE_out1(9),
    .value(9'b100001111)) const_10 (.out1(out_const_10));
  constant_value #(.BITSIZE_out1(4),
    .value(4'b1001)) const_11 (.out1(out_const_11));
  constant_value #(.BITSIZE_out1(8),
    .value(8'b10101000)) const_12 (.out1(out_const_12));
  constant_value #(.BITSIZE_out1(16),
    .value(16'b1010100000000000)) const_13 (.out1(out_const_13));
  constant_value #(.BITSIZE_out1(13),
    .value(13'b1010101010101)) const_14 (.out1(out_const_14));
  constant_value #(.BITSIZE_out1(5),
    .value(5'b10111)) const_15 (.out1(out_const_15));
  constant_value #(.BITSIZE_out1(6),
    .value(6'b101111)) const_16 (.out1(out_const_16));
  constant_value #(.BITSIZE_out1(3),
    .value(3'b110)) const_17 (.out1(out_const_17));
  constant_value #(.BITSIZE_out1(5),
    .value(5'b11000)) const_18 (.out1(out_const_18));
  constant_value #(.BITSIZE_out1(5),
    .value(5'b11001)) const_19 (.out1(out_const_19));
  constant_value #(.BITSIZE_out1(1),
    .value(1'b1)) const_2 (.out1(out_const_2));
  constant_value #(.BITSIZE_out1(32),
    .value(32'b11001100110011001100100011001100)) const_20 (.out1(out_const_20));
  constant_value #(.BITSIZE_out1(5),
    .value(5'b11010)) const_21 (.out1(out_const_21));
  constant_value #(.BITSIZE_out1(5),
    .value(5'b11011)) const_22 (.out1(out_const_22));
  constant_value #(.BITSIZE_out1(5),
    .value(5'b11100)) const_23 (.out1(out_const_23));
  constant_value #(.BITSIZE_out1(8),
    .value(8'b11100000)) const_24 (.out1(out_const_24));
  constant_value #(.BITSIZE_out1(12),
    .value(12'b111000001111)) const_25 (.out1(out_const_25));
  constant_value #(.BITSIZE_out1(5),
    .value(5'b11101)) const_26 (.out1(out_const_26));
  constant_value #(.BITSIZE_out1(64),
    .value(64'b1110111000000000101111101111000011111111111111111111101011110000)) const_27 (.out1(out_const_27));
  constant_value #(.BITSIZE_out1(10),
    .value(10'b1110111111)) const_28 (.out1(out_const_28));
  constant_value #(.BITSIZE_out1(4),
    .value(4'b1111)) const_29 (.out1(out_const_29));
  constant_value #(.BITSIZE_out1(2),
    .value(2'b10)) const_3 (.out1(out_const_3));
  constant_value #(.BITSIZE_out1(5),
    .value(5'b11110)) const_30 (.out1(out_const_30));
  constant_value #(.BITSIZE_out1(28),
    .value(28'b1111000100010000111100000000)) const_31 (.out1(out_const_31));
  constant_value #(.BITSIZE_out1(5),
    .value(5'b11111)) const_32 (.out1(out_const_32));
  constant_value #(.BITSIZE_out1(8),
    .value(8'b11111111)) const_33 (.out1(out_const_33));
  constant_value #(.BITSIZE_out1(31),
    .value(31'b1111111100000000000000000000000)) const_34 (.out1(out_const_34));
  constant_value #(.BITSIZE_out1(32),
    .value(32'b11111111110000000000000000000000)) const_35 (.out1(out_const_35));
  constant_value #(.BITSIZE_out1(23),
    .value(23'b11111111111111111111111)) const_36 (.out1(out_const_36));
  constant_value #(.BITSIZE_out1(32),
    .value(32'b11111111111111111111111110000001)) const_37 (.out1(out_const_37));
  constant_value #(.BITSIZE_out1(31),
    .value(31'b1111111111111111111111111111111)) const_38 (.out1(out_const_38));
  constant_value #(.BITSIZE_out1(32),
    .value(32'b11111111111111111111111111111111)) const_39 (.out1(out_const_39));
  constant_value #(.BITSIZE_out1(3),
    .value(3'b100)) const_4 (.out1(out_const_4));
  constant_value #(.BITSIZE_out1(33),
    .value(33'b111111111111111111111111111111111)) const_40 (.out1(out_const_40));
  constant_value #(.BITSIZE_out1(47),
    .value(47'b11111111111111111111111111111111111111111111111)) const_41 (.out1(out_const_41));
  constant_value #(.BITSIZE_out1(6),
    .value(6'b100000)) const_5 (.out1(out_const_5));
  constant_value #(.BITSIZE_out1(8),
    .value(8'b10000000)) const_6 (.out1(out_const_6));
  constant_value #(.BITSIZE_out1(15),
    .value(15'b100000000000000)) const_7 (.out1(out_const_7));
  constant_value #(.BITSIZE_out1(24),
    .value(24'b100000000000000000000000)) const_8 (.out1(out_const_8));
  constant_value #(.BITSIZE_out1(64),
    .value(64'b1000000000000000000000000000000000000000000000000000000000000000)) const_9 (.out1(out_const_9));
  UUdata_converter_FU #(.BITSIZE_in1(64),
    .BITSIZE_out1(32)) conv_out___float_adde8m23b_127nih_123_i0_fu_forward_kernel_500073_500104_64_32 (.out1(out_conv_out___float_adde8m23b_127nih_123_i0_fu_forward_kernel_500073_500104_64_32),
    .in1(out___float_adde8m23b_127nih_123_i0_fu_forward_kernel_500073_500104));
  UUdata_converter_FU #(.BITSIZE_in1(1),
    .BITSIZE_out1(64)) conv_out_const_0_1_64 (.out1(out_conv_out_const_0_1_64),
    .in1(out_const_0));
  UUdata_converter_FU #(.BITSIZE_in1(7),
    .BITSIZE_out1(6)) conv_out_const_1_7_6 (.out1(out_conv_out_const_1_7_6),
    .in1(out_const_1));
  UUdata_converter_FU #(.BITSIZE_in1(32),
    .BITSIZE_out1(64)) conv_out_reg_35_reg_35_32_64 (.out1(out_conv_out_reg_35_reg_35_32_64),
    .in1(out_reg_35_reg_35));
  UUdata_converter_FU #(.BITSIZE_in1(32),
    .BITSIZE_out1(64)) conv_out_reg_9_reg_9_32_64 (.out1(out_conv_out_reg_9_reg_9_32_64),
    .in1(out_reg_9_reg_9));
  UUdata_converter_FU #(.BITSIZE_in1(64),
    .BITSIZE_out1(30)) fu_forward_kernel_500073_500095 (.out1(out_UUdata_converter_FU_6_i0_fu_forward_kernel_500073_500095),
    .in1(out_reg_5_reg_5));
  ui_pointer_plus_expr_FU #(.BITSIZE_in1(32),
    .BITSIZE_in2(32),
    .BITSIZE_out1(32),
    .LSB_PARAMETER(0)) fu_forward_kernel_500073_500096 (.out1(out_ui_pointer_plus_expr_FU_32_32_32_115_i0_fu_forward_kernel_500073_500096),
    .in1(in_port_P0),
    .in2(out_ui_lshift_expr_FU_32_0_32_99_i0_fu_forward_kernel_500073_500199));
  ui_lshift_expr_FU #(.BITSIZE_in1(64),
    .BITSIZE_in2(3),
    .BITSIZE_out1(30),
    .PRECISION(64)) fu_forward_kernel_500073_500098 (.out1(out_ui_lshift_expr_FU_64_0_64_103_i0_fu_forward_kernel_500073_500098),
    .in1(out_reg_5_reg_5),
    .in2(out_const_4));
  ui_bit_ior_concat_expr_FU #(.BITSIZE_in1(30),
    .BITSIZE_in2(4),
    .BITSIZE_in3(3),
    .BITSIZE_out1(30),
    .OFFSET_PARAMETER(4)) fu_forward_kernel_500073_500099 (.out1(out_ui_bit_ior_concat_expr_FU_92_i0_fu_forward_kernel_500073_500099),
    .in1(out_ui_lshift_expr_FU_32_0_32_100_i0_fu_forward_kernel_500073_503868),
    .in2(out_reg_4_reg_4),
    .in3(out_const_4));
  UUdata_converter_FU #(.BITSIZE_in1(30),
    .BITSIZE_out1(30)) fu_forward_kernel_500073_500100 (.out1(out_UUdata_converter_FU_7_i0_fu_forward_kernel_500073_500100),
    .in1(out_ui_bit_ior_concat_expr_FU_92_i0_fu_forward_kernel_500073_500099));
  ui_pointer_plus_expr_FU #(.BITSIZE_in1(32),
    .BITSIZE_in2(32),
    .BITSIZE_out1(32),
    .LSB_PARAMETER(0)) fu_forward_kernel_500073_500101 (.out1(out_ui_pointer_plus_expr_FU_32_32_32_115_i1_fu_forward_kernel_500073_500101),
    .in1(in_port_P1),
    .in2(out_ui_lshift_expr_FU_32_0_32_99_i1_fu_forward_kernel_500073_500201));
  __float_adde8m23b_127nih fu_forward_kernel_500073_500104 (.done_port(s_done_fu_forward_kernel_500073_500104),
    .return_port(out___float_adde8m23b_127nih_123_i0_fu_forward_kernel_500073_500104),
    .clock(clock),
    .reset(reset),
    .start_port(selector_IN_UNBOUNDED_forward_kernel_500073_500104),
    .a(out_conv_out_reg_9_reg_9_32_64),
    .b(out_conv_out_reg_35_reg_35_32_64));
  ui_plus_expr_FU #(.BITSIZE_in1(64),
    .BITSIZE_in2(1),
    .BITSIZE_out1(64)) fu_forward_kernel_500073_500106 (.out1(out_ui_plus_expr_FU_64_0_64_114_i0_fu_forward_kernel_500073_500106),
    .in1(out_reg_5_reg_5),
    .in2(out_const_2));
  ui_pointer_plus_expr_FU #(.BITSIZE_in1(32),
    .BITSIZE_in2(32),
    .BITSIZE_out1(32),
    .LSB_PARAMETER(0)) fu_forward_kernel_500073_500127 (.out1(out_ui_pointer_plus_expr_FU_32_32_32_115_i2_fu_forward_kernel_500073_500127),
    .in1(in_port_P2),
    .in2(out_ui_lshift_expr_FU_32_0_32_99_i2_fu_forward_kernel_500073_500213));
  UUdata_converter_FU #(.BITSIZE_in1(64),
    .BITSIZE_out1(30)) fu_forward_kernel_500073_500136 (.out1(out_UUdata_converter_FU_82_i0_fu_forward_kernel_500073_500136),
    .in1(out_reg_0_reg_0));
  ui_plus_expr_FU #(.BITSIZE_in1(64),
    .BITSIZE_in2(1),
    .BITSIZE_out1(64)) fu_forward_kernel_500073_500143 (.out1(out_ui_plus_expr_FU_64_0_64_114_i1_fu_forward_kernel_500073_500143),
    .in1(out_reg_0_reg_0),
    .in2(out_const_2));
  ui_lshift_expr_FU #(.BITSIZE_in1(30),
    .BITSIZE_in2(2),
    .BITSIZE_out1(32),
    .PRECISION(32)) fu_forward_kernel_500073_500199 (.out1(out_ui_lshift_expr_FU_32_0_32_99_i0_fu_forward_kernel_500073_500199),
    .in1(out_UUdata_converter_FU_6_i0_fu_forward_kernel_500073_500095),
    .in2(out_const_3));
  ui_lshift_expr_FU #(.BITSIZE_in1(30),
    .BITSIZE_in2(2),
    .BITSIZE_out1(32),
    .PRECISION(32)) fu_forward_kernel_500073_500201 (.out1(out_ui_lshift_expr_FU_32_0_32_99_i1_fu_forward_kernel_500073_500201),
    .in1(out_UUdata_converter_FU_7_i0_fu_forward_kernel_500073_500100),
    .in2(out_const_3));
  ui_lt_expr_FU #(.BITSIZE_in1(64),
    .BITSIZE_in2(10),
    .BITSIZE_out1(1)) fu_forward_kernel_500073_500207 (.out1(out_ui_lt_expr_FU_64_0_64_107_i0_fu_forward_kernel_500073_500207),
    .in1(out_reg_5_reg_5),
    .in2(out_const_28));
  ui_lshift_expr_FU #(.BITSIZE_in1(30),
    .BITSIZE_in2(2),
    .BITSIZE_out1(32),
    .PRECISION(32)) fu_forward_kernel_500073_500213 (.out1(out_ui_lshift_expr_FU_32_0_32_99_i2_fu_forward_kernel_500073_500213),
    .in1(out_UUdata_converter_FU_82_i0_fu_forward_kernel_500073_500136),
    .in2(out_const_3));
  ui_lt_expr_FU #(.BITSIZE_in1(64),
    .BITSIZE_in2(4),
    .BITSIZE_out1(1)) fu_forward_kernel_500073_500216 (.out1(out_ui_lt_expr_FU_64_0_64_108_i0_fu_forward_kernel_500073_500216),
    .in1(out_reg_0_reg_0),
    .in2(out_const_29));
  UUdata_converter_FU #(.BITSIZE_in1(32),
    .BITSIZE_out1(32)) fu_forward_kernel_500073_502249 (.out1(out_UUdata_converter_FU_73_i0_fu_forward_kernel_500073_502249),
    .in1(out_ui_cond_expr_FU_32_32_32_32_97_i2_fu_forward_kernel_500073_511014));
  UUdata_converter_FU #(.BITSIZE_in1(32),
    .BITSIZE_out1(31)) fu_forward_kernel_500073_502252 (.out1(out_UUdata_converter_FU_8_i0_fu_forward_kernel_500073_502252),
    .in1(out_BMEMORY_CTRLN_83_i0_BMEMORY_CTRLN_83_i0));
  UUdata_converter_FU #(.BITSIZE_in1(32),
    .BITSIZE_out1(31)) fu_forward_kernel_500073_502255 (.out1(out_UUdata_converter_FU_9_i0_fu_forward_kernel_500073_502255),
    .in1(out_BMEMORY_CTRLN_83_i0_BMEMORY_CTRLN_83_i0));
  UUdata_converter_FU #(.BITSIZE_in1(32),
    .BITSIZE_out1(32)) fu_forward_kernel_500073_502283 (.out1(out_UUdata_converter_FU_76_i0_fu_forward_kernel_500073_502283),
    .in1(out_reg_36_reg_36));
  UUdata_converter_FU #(.BITSIZE_in1(32),
    .BITSIZE_out1(32)) fu_forward_kernel_500073_502286 (.out1(out_UUdata_converter_FU_74_i0_fu_forward_kernel_500073_502286),
    .in1(out_reg_6_reg_6));
  UUdata_converter_FU #(.BITSIZE_in1(32),
    .BITSIZE_out1(32)) fu_forward_kernel_500073_502289 (.out1(out_UUdata_converter_FU_75_i0_fu_forward_kernel_500073_502289),
    .in1(out_UUdata_converter_FU_73_i0_fu_forward_kernel_500073_502249));
  ui_rshift_expr_FU #(.BITSIZE_in1(30),
    .BITSIZE_in2(3),
    .BITSIZE_out1(26),
    .PRECISION(64)) fu_forward_kernel_500073_503856 (.out1(out_ui_rshift_expr_FU_32_0_32_116_i0_fu_forward_kernel_500073_503856),
    .in1(out_ui_lshift_expr_FU_64_0_64_103_i0_fu_forward_kernel_500073_500098),
    .in2(out_const_4));
  ui_rshift_expr_FU #(.BITSIZE_in1(64),
    .BITSIZE_in2(3),
    .BITSIZE_out1(26),
    .PRECISION(64)) fu_forward_kernel_500073_503861 (.out1(out_ui_rshift_expr_FU_64_0_64_119_i0_fu_forward_kernel_500073_503861),
    .in1(out_reg_0_reg_0),
    .in2(out_const_4));
  ui_plus_expr_FU #(.BITSIZE_in1(26),
    .BITSIZE_in2(26),
    .BITSIZE_out1(26)) fu_forward_kernel_500073_503864 (.out1(out_ui_plus_expr_FU_32_32_32_113_i0_fu_forward_kernel_500073_503864),
    .in1(out_ui_rshift_expr_FU_32_0_32_116_i0_fu_forward_kernel_500073_503856),
    .in2(out_reg_3_reg_3));
  ui_lshift_expr_FU #(.BITSIZE_in1(26),
    .BITSIZE_in2(3),
    .BITSIZE_out1(30),
    .PRECISION(64)) fu_forward_kernel_500073_503868 (.out1(out_ui_lshift_expr_FU_32_0_32_100_i0_fu_forward_kernel_500073_503868),
    .in1(out_ui_plus_expr_FU_32_32_32_113_i0_fu_forward_kernel_500073_503864),
    .in2(out_const_4));
  ui_bit_and_expr_FU #(.BITSIZE_in1(64),
    .BITSIZE_in2(4),
    .BITSIZE_out1(4)) fu_forward_kernel_500073_503873 (.out1(out_ui_bit_and_expr_FU_8_0_8_90_i0_fu_forward_kernel_500073_503873),
    .in1(out_reg_0_reg_0),
    .in2(out_const_29));
  multi_read_cond_FU #(.BITSIZE_in1(1),
    .PORTSIZE_in1(2),
    .BITSIZE_out1(2)) fu_forward_kernel_500073_503980 (.out1(out_multi_read_cond_FU_78_i0_fu_forward_kernel_500073_503980),
    .in1({out_reg_10_reg_10,
      out_reg_8_reg_8}));
  lut_expr_FU #(.BITSIZE_in1(3),
    .BITSIZE_out1(1)) fu_forward_kernel_500073_503986 (.out1(out_lut_expr_FU_77_i0_fu_forward_kernel_500073_503986),
    .in1(out_const_4),
    .in2(out_ui_lt_expr_FU_64_0_64_107_i0_fu_forward_kernel_500073_500207),
    .in3(out_reg_2_reg_2),
    .in4(1'b0),
    .in5(1'b0),
    .in6(1'b0),
    .in7(1'b0),
    .in8(1'b0),
    .in9(1'b0));
  ui_bit_and_expr_FU #(.BITSIZE_in1(23),
    .BITSIZE_in2(31),
    .BITSIZE_out1(23)) fu_forward_kernel_500073_510710 (.out1(out_ui_bit_and_expr_FU_0_32_32_84_i0_fu_forward_kernel_500073_510710),
    .in1(out_const_36),
    .in2(out_UUdata_converter_FU_8_i0_fu_forward_kernel_500073_502252));
  ui_rshift_expr_FU #(.BITSIZE_in1(31),
    .BITSIZE_in2(5),
    .BITSIZE_out1(8),
    .PRECISION(64)) fu_forward_kernel_500073_510715 (.out1(out_ui_rshift_expr_FU_32_0_32_117_i0_fu_forward_kernel_500073_510715),
    .in1(out_UUdata_converter_FU_8_i0_fu_forward_kernel_500073_502252),
    .in2(out_const_15));
  ui_bit_and_expr_FU #(.BITSIZE_in1(8),
    .BITSIZE_in2(8),
    .BITSIZE_out1(8)) fu_forward_kernel_500073_510718 (.out1(out_ui_bit_and_expr_FU_8_0_8_91_i0_fu_forward_kernel_500073_510718),
    .in1(out_ui_rshift_expr_FU_32_0_32_117_i0_fu_forward_kernel_500073_510715),
    .in2(out_const_33));
  UUdata_converter_FU #(.BITSIZE_in1(8),
    .BITSIZE_out1(8)) fu_forward_kernel_500073_510721 (.out1(out_UUdata_converter_FU_10_i0_fu_forward_kernel_500073_510721),
    .in1(out_ui_bit_and_expr_FU_8_0_8_91_i0_fu_forward_kernel_500073_510718));
  ui_rshift_expr_FU #(.BITSIZE_in1(31),
    .BITSIZE_in2(5),
    .BITSIZE_out1(8),
    .PRECISION(64)) fu_forward_kernel_500073_510727 (.out1(out_ui_rshift_expr_FU_32_0_32_117_i1_fu_forward_kernel_500073_510727),
    .in1(out_UUdata_converter_FU_9_i0_fu_forward_kernel_500073_502255),
    .in2(out_const_15));
  ui_bit_and_expr_FU #(.BITSIZE_in1(8),
    .BITSIZE_in2(8),
    .BITSIZE_out1(8)) fu_forward_kernel_500073_510732 (.out1(out_ui_bit_and_expr_FU_8_0_8_91_i1_fu_forward_kernel_500073_510732),
    .in1(out_ui_rshift_expr_FU_32_0_32_117_i1_fu_forward_kernel_500073_510727),
    .in2(out_const_33));
  UUdata_converter_FU #(.BITSIZE_in1(8),
    .BITSIZE_out1(8)) fu_forward_kernel_500073_510735 (.out1(out_UUdata_converter_FU_12_i0_fu_forward_kernel_500073_510735),
    .in1(out_ui_bit_and_expr_FU_8_0_8_91_i1_fu_forward_kernel_500073_510732));
  ui_bit_and_expr_FU #(.BITSIZE_in1(23),
    .BITSIZE_in2(31),
    .BITSIZE_out1(23)) fu_forward_kernel_500073_510738 (.out1(out_ui_bit_and_expr_FU_0_32_32_84_i1_fu_forward_kernel_500073_510738),
    .in1(out_const_36),
    .in2(out_UUdata_converter_FU_9_i0_fu_forward_kernel_500073_502255));
  lut_expr_FU #(.BITSIZE_in1(3),
    .BITSIZE_out1(1)) fu_forward_kernel_500073_510744 (.out1(out_lut_expr_FU_14_i0_fu_forward_kernel_500073_510744),
    .in1(out_const_17),
    .in2(out_reg_15_reg_15),
    .in3(out_ui_extract_bit_expr_FU_13_i0_fu_forward_kernel_500073_511026),
    .in4(1'b0),
    .in5(1'b0),
    .in6(1'b0),
    .in7(1'b0),
    .in8(1'b0),
    .in9(1'b0));
  UUdata_converter_FU #(.BITSIZE_in1(1),
    .BITSIZE_out1(1)) fu_forward_kernel_500073_510747 (.out1(out_UUdata_converter_FU_15_i0_fu_forward_kernel_500073_510747),
    .in1(out_lut_expr_FU_14_i0_fu_forward_kernel_500073_510744));
  ui_eq_expr_FU #(.BITSIZE_in1(23),
    .BITSIZE_in2(1),
    .BITSIZE_out1(1)) fu_forward_kernel_500073_510774 (.out1(out_ui_eq_expr_FU_32_0_32_98_i0_fu_forward_kernel_500073_510774),
    .in1(out_ui_bit_and_expr_FU_0_32_32_84_i0_fu_forward_kernel_500073_510710),
    .in2(out_const_0));
  ui_ne_expr_FU #(.BITSIZE_in1(23),
    .BITSIZE_in2(1),
    .BITSIZE_out1(1)) fu_forward_kernel_500073_510777 (.out1(out_ui_ne_expr_FU_32_0_32_110_i0_fu_forward_kernel_500073_510777),
    .in1(out_ui_bit_and_expr_FU_0_32_32_84_i0_fu_forward_kernel_500073_510710),
    .in2(out_const_0));
  ui_eq_expr_FU #(.BITSIZE_in1(23),
    .BITSIZE_in2(1),
    .BITSIZE_out1(1)) fu_forward_kernel_500073_510804 (.out1(out_ui_eq_expr_FU_32_0_32_98_i1_fu_forward_kernel_500073_510804),
    .in1(out_ui_bit_and_expr_FU_0_32_32_84_i1_fu_forward_kernel_500073_510738),
    .in2(out_const_0));
  ui_ne_expr_FU #(.BITSIZE_in1(23),
    .BITSIZE_in2(1),
    .BITSIZE_out1(1)) fu_forward_kernel_500073_510807 (.out1(out_ui_ne_expr_FU_32_0_32_110_i1_fu_forward_kernel_500073_510807),
    .in1(out_ui_bit_and_expr_FU_0_32_32_84_i1_fu_forward_kernel_500073_510738),
    .in2(out_const_0));
  ui_ternary_plus_expr_FU #(.BITSIZE_in1(8),
    .BITSIZE_in2(32),
    .BITSIZE_in3(8),
    .BITSIZE_out1(10)) fu_forward_kernel_500073_510810 (.out1(out_ui_ternary_plus_expr_FU_16_0_16_16_122_i0_fu_forward_kernel_500073_510810),
    .in1(out_reg_11_reg_11),
    .in2(out_const_37),
    .in3(out_UUdata_converter_FU_12_i0_fu_forward_kernel_500073_510735));
  ui_bit_ior_expr_FU #(.BITSIZE_in1(24),
    .BITSIZE_in2(23),
    .BITSIZE_out1(24)) fu_forward_kernel_500073_510813 (.out1(out_ui_bit_ior_expr_FU_0_32_32_93_i0_fu_forward_kernel_500073_510813),
    .in1(out_const_8),
    .in2(out_ui_bit_and_expr_FU_0_32_32_84_i0_fu_forward_kernel_500073_510710));
  ui_bit_ior_expr_FU #(.BITSIZE_in1(24),
    .BITSIZE_in2(23),
    .BITSIZE_out1(24)) fu_forward_kernel_500073_510816 (.out1(out_ui_bit_ior_expr_FU_0_32_32_93_i1_fu_forward_kernel_500073_510816),
    .in1(out_const_8),
    .in2(out_ui_bit_and_expr_FU_0_32_32_84_i1_fu_forward_kernel_500073_510738));
  ui_bit_and_expr_FU #(.BITSIZE_in1(24),
    .BITSIZE_in2(32),
    .BITSIZE_out1(24)) fu_forward_kernel_500073_510819 (.out1(out_ui_bit_and_expr_FU_32_0_32_85_i0_fu_forward_kernel_500073_510819),
    .in1(out_ui_bit_ior_expr_FU_0_32_32_93_i0_fu_forward_kernel_500073_510813),
    .in2(out_const_39));
  ui_bit_and_expr_FU #(.BITSIZE_in1(24),
    .BITSIZE_in2(32),
    .BITSIZE_out1(24)) fu_forward_kernel_500073_510822 (.out1(out_ui_bit_and_expr_FU_32_0_32_85_i1_fu_forward_kernel_500073_510822),
    .in1(out_ui_bit_ior_expr_FU_0_32_32_93_i1_fu_forward_kernel_500073_510816),
    .in2(out_const_39));
  ui_mult_expr_FU #(.BITSIZE_in1(24),
    .BITSIZE_in2(24),
    .BITSIZE_out1(48),
    .PIPE_PARAMETER(0)) fu_forward_kernel_500073_510825 (.out1(out_ui_mult_expr_FU_32_32_32_0_109_i0_fu_forward_kernel_500073_510825),
    .clock(clock),
    .in1(out_reg_19_reg_19),
    .in2(out_reg_14_reg_14));
  ui_extract_bit_expr_FU #(.BITSIZE_in1(48),
    .BITSIZE_in2(6)) fu_forward_kernel_500073_510828 (.out1(out_ui_extract_bit_expr_FU_32_i0_fu_forward_kernel_500073_510828),
    .in1(out_ui_mult_expr_FU_32_32_32_0_109_i0_fu_forward_kernel_500073_510825),
    .in2(out_const_16));
  UUdata_converter_FU #(.BITSIZE_in1(1),
    .BITSIZE_out1(1)) fu_forward_kernel_500073_510831 (.out1(out_UUdata_converter_FU_33_i0_fu_forward_kernel_500073_510831),
    .in1(out_ui_extract_bit_expr_FU_32_i0_fu_forward_kernel_500073_510828));
  UUdata_converter_FU #(.BITSIZE_in1(1),
    .BITSIZE_out1(1)) fu_forward_kernel_500073_510834 (.out1(out_UUdata_converter_FU_34_i0_fu_forward_kernel_500073_510834),
    .in1(out_UUdata_converter_FU_33_i0_fu_forward_kernel_500073_510831));
  ui_plus_expr_FU #(.BITSIZE_in1(10),
    .BITSIZE_in2(1),
    .BITSIZE_out1(10)) fu_forward_kernel_500073_510837 (.out1(out_ui_plus_expr_FU_16_16_16_112_i0_fu_forward_kernel_500073_510837),
    .in1(out_reg_18_reg_18),
    .in2(out_reg_27_reg_27));
  lut_expr_FU #(.BITSIZE_in1(1),
    .BITSIZE_out1(1)) fu_forward_kernel_500073_510840 (.out1(out_lut_expr_FU_35_i0_fu_forward_kernel_500073_510840),
    .in1(out_const_2),
    .in2(out_reg_26_reg_26),
    .in3(1'b0),
    .in4(1'b0),
    .in5(1'b0),
    .in6(1'b0),
    .in7(1'b0),
    .in8(1'b0),
    .in9(1'b0));
  UUdata_converter_FU #(.BITSIZE_in1(1),
    .BITSIZE_out1(1)) fu_forward_kernel_500073_510843 (.out1(out_UUdata_converter_FU_36_i0_fu_forward_kernel_500073_510843),
    .in1(out_lut_expr_FU_35_i0_fu_forward_kernel_500073_510840));
  UUdata_converter_FU #(.BITSIZE_in1(1),
    .BITSIZE_out1(1)) fu_forward_kernel_500073_510846 (.out1(out_UUdata_converter_FU_37_i0_fu_forward_kernel_500073_510846),
    .in1(out_UUdata_converter_FU_36_i0_fu_forward_kernel_500073_510843));
  ui_lshift_expr_FU #(.BITSIZE_in1(48),
    .BITSIZE_in2(1),
    .BITSIZE_out1(47),
    .PRECISION(64)) fu_forward_kernel_500073_510849 (.out1(out_ui_lshift_expr_FU_64_64_64_106_i0_fu_forward_kernel_500073_510849),
    .in1(out_reg_25_reg_25),
    .in2(out_UUdata_converter_FU_37_i0_fu_forward_kernel_500073_510846));
  ui_bit_and_expr_FU #(.BITSIZE_in1(47),
    .BITSIZE_in2(47),
    .BITSIZE_out1(47)) fu_forward_kernel_500073_510852 (.out1(out_ui_bit_and_expr_FU_64_0_64_88_i0_fu_forward_kernel_500073_510852),
    .in1(out_ui_lshift_expr_FU_64_64_64_106_i0_fu_forward_kernel_500073_510849),
    .in2(out_const_41));
  ui_lshift_expr_FU #(.BITSIZE_in1(47),
    .BITSIZE_in2(1),
    .BITSIZE_out1(48),
    .PRECISION(64)) fu_forward_kernel_500073_510855 (.out1(out_ui_lshift_expr_FU_64_0_64_104_i0_fu_forward_kernel_500073_510855),
    .in1(out_ui_bit_and_expr_FU_64_0_64_88_i0_fu_forward_kernel_500073_510852),
    .in2(out_const_2));
  UUdata_converter_FU #(.BITSIZE_in1(10),
    .BITSIZE_out1(10)) fu_forward_kernel_500073_510858 (.out1(out_UUdata_converter_FU_38_i0_fu_forward_kernel_500073_510858),
    .in1(out_ui_plus_expr_FU_16_16_16_112_i0_fu_forward_kernel_500073_510837));
  ui_lshift_expr_FU #(.BITSIZE_in1(10),
    .BITSIZE_in2(5),
    .BITSIZE_out1(33),
    .PRECISION(64)) fu_forward_kernel_500073_510861 (.out1(out_ui_lshift_expr_FU_64_0_64_105_i0_fu_forward_kernel_500073_510861),
    .in1(out_UUdata_converter_FU_38_i0_fu_forward_kernel_500073_510858),
    .in2(out_const_15));
  ui_rshift_expr_FU #(.BITSIZE_in1(48),
    .BITSIZE_in2(5),
    .BITSIZE_out1(23),
    .PRECISION(64)) fu_forward_kernel_500073_510864 (.out1(out_ui_rshift_expr_FU_64_0_64_120_i0_fu_forward_kernel_500073_510864),
    .in1(out_ui_lshift_expr_FU_64_0_64_104_i0_fu_forward_kernel_500073_510855),
    .in2(out_const_19));
  ui_bit_and_expr_FU #(.BITSIZE_in1(23),
    .BITSIZE_in2(23),
    .BITSIZE_out1(23)) fu_forward_kernel_500073_510867 (.out1(out_ui_bit_and_expr_FU_32_0_32_86_i0_fu_forward_kernel_500073_510867),
    .in1(out_ui_rshift_expr_FU_64_0_64_120_i0_fu_forward_kernel_500073_510864),
    .in2(out_const_36));
  ui_bit_ior_expr_FU #(.BITSIZE_in1(23),
    .BITSIZE_in2(33),
    .BITSIZE_out1(33)) fu_forward_kernel_500073_510870 (.out1(out_ui_bit_ior_expr_FU_0_64_64_96_i0_fu_forward_kernel_500073_510870),
    .in1(out_ui_bit_and_expr_FU_32_0_32_86_i0_fu_forward_kernel_500073_510867),
    .in2(out_ui_lshift_expr_FU_64_0_64_105_i0_fu_forward_kernel_500073_510861));
  ui_bit_and_expr_FU #(.BITSIZE_in1(33),
    .BITSIZE_in2(33),
    .BITSIZE_out1(33)) fu_forward_kernel_500073_510873 (.out1(out_ui_bit_and_expr_FU_64_0_64_89_i0_fu_forward_kernel_500073_510873),
    .in1(out_ui_bit_ior_expr_FU_0_64_64_96_i0_fu_forward_kernel_500073_510870),
    .in2(out_const_40));
  ui_extract_bit_expr_FU #(.BITSIZE_in1(10),
    .BITSIZE_in2(4)) fu_forward_kernel_500073_510876 (.out1(out_ui_extract_bit_expr_FU_39_i0_fu_forward_kernel_500073_510876),
    .in1(out_ui_plus_expr_FU_16_16_16_112_i0_fu_forward_kernel_500073_510837),
    .in2(out_const_11));
  ui_rshift_expr_FU #(.BITSIZE_in1(48),
    .BITSIZE_in2(1),
    .BITSIZE_out1(23),
    .PRECISION(64)) fu_forward_kernel_500073_510879 (.out1(out_ui_rshift_expr_FU_64_0_64_121_i0_fu_forward_kernel_500073_510879),
    .in1(out_ui_lshift_expr_FU_64_0_64_104_i0_fu_forward_kernel_500073_510855),
    .in2(out_const_2));
  ui_bit_and_expr_FU #(.BITSIZE_in1(23),
    .BITSIZE_in2(23),
    .BITSIZE_out1(23)) fu_forward_kernel_500073_510882 (.out1(out_ui_bit_and_expr_FU_32_0_32_86_i1_fu_forward_kernel_500073_510882),
    .in1(out_ui_rshift_expr_FU_64_0_64_121_i0_fu_forward_kernel_500073_510879),
    .in2(out_const_36));
  ui_lshift_expr_FU #(.BITSIZE_in1(23),
    .BITSIZE_in2(1),
    .BITSIZE_out1(24),
    .PRECISION(64)) fu_forward_kernel_500073_510885 (.out1(out_ui_lshift_expr_FU_32_0_32_101_i0_fu_forward_kernel_500073_510885),
    .in1(out_ui_bit_and_expr_FU_32_0_32_86_i1_fu_forward_kernel_500073_510882),
    .in2(out_const_2));
  ui_rshift_expr_FU #(.BITSIZE_in1(24),
    .BITSIZE_in2(1),
    .BITSIZE_out1(23),
    .PRECISION(64)) fu_forward_kernel_500073_510888 (.out1(out_ui_rshift_expr_FU_32_0_32_118_i0_fu_forward_kernel_500073_510888),
    .in1(out_ui_lshift_expr_FU_32_0_32_101_i0_fu_forward_kernel_500073_510885),
    .in2(out_const_2));
  ui_ne_expr_FU #(.BITSIZE_in1(23),
    .BITSIZE_in2(1),
    .BITSIZE_out1(1)) fu_forward_kernel_500073_510891 (.out1(out_ui_ne_expr_FU_32_0_32_111_i0_fu_forward_kernel_500073_510891),
    .in1(out_ui_rshift_expr_FU_32_0_32_118_i0_fu_forward_kernel_500073_510888),
    .in2(out_const_0));
  ui_extract_bit_expr_FU #(.BITSIZE_in1(47),
    .BITSIZE_in2(5)) fu_forward_kernel_500073_510894 (.out1(out_ui_extract_bit_expr_FU_40_i0_fu_forward_kernel_500073_510894),
    .in1(out_ui_lshift_expr_FU_64_64_64_106_i0_fu_forward_kernel_500073_510849),
    .in2(out_const_15));
  ui_extract_bit_expr_FU #(.BITSIZE_in1(47),
    .BITSIZE_in2(5)) fu_forward_kernel_500073_510897 (.out1(out_ui_extract_bit_expr_FU_41_i0_fu_forward_kernel_500073_510897),
    .in1(out_ui_lshift_expr_FU_64_64_64_106_i0_fu_forward_kernel_500073_510849),
    .in2(out_const_18));
  lut_expr_FU #(.BITSIZE_in1(8),
    .BITSIZE_out1(1)) fu_forward_kernel_500073_510900 (.out1(out_lut_expr_FU_42_i0_fu_forward_kernel_500073_510900),
    .in1(out_const_12),
    .in2(out_ui_extract_bit_expr_FU_40_i0_fu_forward_kernel_500073_510894),
    .in3(out_ui_extract_bit_expr_FU_41_i0_fu_forward_kernel_500073_510897),
    .in4(out_ui_ne_expr_FU_32_0_32_111_i0_fu_forward_kernel_500073_510891),
    .in5(1'b0),
    .in6(1'b0),
    .in7(1'b0),
    .in8(1'b0),
    .in9(1'b0));
  UUdata_converter_FU #(.BITSIZE_in1(1),
    .BITSIZE_out1(1)) fu_forward_kernel_500073_510903 (.out1(out_UUdata_converter_FU_43_i0_fu_forward_kernel_500073_510903),
    .in1(out_lut_expr_FU_42_i0_fu_forward_kernel_500073_510900));
  UUdata_converter_FU #(.BITSIZE_in1(1),
    .BITSIZE_out1(1)) fu_forward_kernel_500073_510906 (.out1(out_UUdata_converter_FU_44_i0_fu_forward_kernel_500073_510906),
    .in1(out_UUdata_converter_FU_43_i0_fu_forward_kernel_500073_510903));
  ui_plus_expr_FU #(.BITSIZE_in1(33),
    .BITSIZE_in2(1),
    .BITSIZE_out1(33)) fu_forward_kernel_500073_510909 (.out1(out_ui_plus_expr_FU_32_32_32_113_i1_fu_forward_kernel_500073_510909),
    .in1(out_ui_bit_and_expr_FU_64_0_64_89_i0_fu_forward_kernel_500073_510873),
    .in2(out_UUdata_converter_FU_44_i0_fu_forward_kernel_500073_510906));
  ui_extract_bit_expr_FU #(.BITSIZE_in1(33),
    .BITSIZE_in2(6)) fu_forward_kernel_500073_510912 (.out1(out_ui_extract_bit_expr_FU_45_i0_fu_forward_kernel_500073_510912),
    .in1(out_ui_plus_expr_FU_32_32_32_113_i1_fu_forward_kernel_500073_510909),
    .in2(out_const_5));
  UUdata_converter_FU #(.BITSIZE_in1(1),
    .BITSIZE_out1(1)) fu_forward_kernel_500073_510915 (.out1(out_UUdata_converter_FU_46_i0_fu_forward_kernel_500073_510915),
    .in1(out_UUdata_converter_FU_15_i0_fu_forward_kernel_500073_510747));
  ui_lshift_expr_FU #(.BITSIZE_in1(1),
    .BITSIZE_in2(5),
    .BITSIZE_out1(32),
    .PRECISION(64)) fu_forward_kernel_500073_510918 (.out1(out_ui_lshift_expr_FU_32_0_32_102_i0_fu_forward_kernel_500073_510918),
    .in1(out_UUdata_converter_FU_46_i0_fu_forward_kernel_500073_510915),
    .in2(out_const_32));
  ui_bit_and_expr_FU #(.BITSIZE_in1(33),
    .BITSIZE_in2(31),
    .BITSIZE_out1(31)) fu_forward_kernel_500073_510921 (.out1(out_ui_bit_and_expr_FU_32_0_32_87_i0_fu_forward_kernel_500073_510921),
    .in1(out_ui_plus_expr_FU_32_32_32_113_i1_fu_forward_kernel_500073_510909),
    .in2(out_const_38));
  ui_bit_ior_expr_FU #(.BITSIZE_in1(31),
    .BITSIZE_in2(32),
    .BITSIZE_out1(32)) fu_forward_kernel_500073_510924 (.out1(out_ui_bit_ior_expr_FU_0_32_32_94_i0_fu_forward_kernel_500073_510924),
    .in1(out_ui_bit_and_expr_FU_32_0_32_87_i0_fu_forward_kernel_500073_510921),
    .in2(out_reg_20_reg_20));
  ui_extract_bit_expr_FU #(.BITSIZE_in1(33),
    .BITSIZE_in2(5)) fu_forward_kernel_500073_510927 (.out1(out_ui_extract_bit_expr_FU_47_i0_fu_forward_kernel_500073_510927),
    .in1(out_ui_plus_expr_FU_32_32_32_113_i1_fu_forward_kernel_500073_510909),
    .in2(out_const_32));
  ui_extract_bit_expr_FU #(.BITSIZE_in1(33),
    .BITSIZE_in2(5)) fu_forward_kernel_500073_510930 (.out1(out_ui_extract_bit_expr_FU_48_i0_fu_forward_kernel_500073_510930),
    .in1(out_ui_plus_expr_FU_32_32_32_113_i1_fu_forward_kernel_500073_510909),
    .in2(out_const_15));
  ui_extract_bit_expr_FU #(.BITSIZE_in1(33),
    .BITSIZE_in2(5)) fu_forward_kernel_500073_510933 (.out1(out_ui_extract_bit_expr_FU_49_i0_fu_forward_kernel_500073_510933),
    .in1(out_ui_plus_expr_FU_32_32_32_113_i1_fu_forward_kernel_500073_510909),
    .in2(out_const_18));
  ui_extract_bit_expr_FU #(.BITSIZE_in1(33),
    .BITSIZE_in2(5)) fu_forward_kernel_500073_510936 (.out1(out_ui_extract_bit_expr_FU_50_i0_fu_forward_kernel_500073_510936),
    .in1(out_ui_plus_expr_FU_32_32_32_113_i1_fu_forward_kernel_500073_510909),
    .in2(out_const_19));
  ui_extract_bit_expr_FU #(.BITSIZE_in1(33),
    .BITSIZE_in2(5)) fu_forward_kernel_500073_510939 (.out1(out_ui_extract_bit_expr_FU_51_i0_fu_forward_kernel_500073_510939),
    .in1(out_ui_plus_expr_FU_32_32_32_113_i1_fu_forward_kernel_500073_510909),
    .in2(out_const_21));
  ui_extract_bit_expr_FU #(.BITSIZE_in1(33),
    .BITSIZE_in2(5)) fu_forward_kernel_500073_510942 (.out1(out_ui_extract_bit_expr_FU_52_i0_fu_forward_kernel_500073_510942),
    .in1(out_ui_plus_expr_FU_32_32_32_113_i1_fu_forward_kernel_500073_510909),
    .in2(out_const_22));
  ui_extract_bit_expr_FU #(.BITSIZE_in1(33),
    .BITSIZE_in2(5)) fu_forward_kernel_500073_510945 (.out1(out_ui_extract_bit_expr_FU_53_i0_fu_forward_kernel_500073_510945),
    .in1(out_ui_plus_expr_FU_32_32_32_113_i1_fu_forward_kernel_500073_510909),
    .in2(out_const_23));
  ui_extract_bit_expr_FU #(.BITSIZE_in1(33),
    .BITSIZE_in2(5)) fu_forward_kernel_500073_510948 (.out1(out_ui_extract_bit_expr_FU_54_i0_fu_forward_kernel_500073_510948),
    .in1(out_ui_plus_expr_FU_32_32_32_113_i1_fu_forward_kernel_500073_510909),
    .in2(out_const_26));
  ui_extract_bit_expr_FU #(.BITSIZE_in1(33),
    .BITSIZE_in2(5)) fu_forward_kernel_500073_510951 (.out1(out_ui_extract_bit_expr_FU_55_i0_fu_forward_kernel_500073_510951),
    .in1(out_ui_plus_expr_FU_32_32_32_113_i1_fu_forward_kernel_500073_510909),
    .in2(out_const_30));
  ui_bit_ior_expr_FU #(.BITSIZE_in1(31),
    .BITSIZE_in2(32),
    .BITSIZE_out1(32)) fu_forward_kernel_500073_510954 (.out1(out_ui_bit_ior_expr_FU_0_32_32_95_i0_fu_forward_kernel_500073_510954),
    .in1(out_const_34),
    .in2(out_ui_lshift_expr_FU_32_0_32_102_i0_fu_forward_kernel_500073_510918));
  lut_expr_FU #(.BITSIZE_in1(32),
    .BITSIZE_out1(1)) fu_forward_kernel_500073_510996 (.out1(out_lut_expr_FU_70_i0_fu_forward_kernel_500073_510996),
    .in1(out_const_20),
    .in2(out_reg_28_reg_28),
    .in3(out_reg_23_reg_23),
    .in4(out_lut_expr_FU_63_i0_fu_forward_kernel_500073_511118),
    .in5(out_reg_24_reg_24),
    .in6(out_reg_34_reg_34),
    .in7(1'b0),
    .in8(1'b0),
    .in9(1'b0));
  lut_expr_FU #(.BITSIZE_in1(15),
    .BITSIZE_out1(1)) fu_forward_kernel_500073_511002 (.out1(out_lut_expr_FU_71_i0_fu_forward_kernel_500073_511002),
    .in1(out_const_7),
    .in2(out_reg_28_reg_28),
    .in3(out_reg_23_reg_23),
    .in4(out_lut_expr_FU_63_i0_fu_forward_kernel_500073_511118),
    .in5(out_reg_24_reg_24),
    .in6(out_reg_34_reg_34),
    .in7(1'b0),
    .in8(1'b0),
    .in9(1'b0));
  ui_cond_expr_FU #(.BITSIZE_in1(1),
    .BITSIZE_in2(32),
    .BITSIZE_in3(32),
    .BITSIZE_out1(32)) fu_forward_kernel_500073_511005 (.out1(out_ui_cond_expr_FU_32_32_32_32_97_i0_fu_forward_kernel_500073_511005),
    .in1(out_lut_expr_FU_71_i0_fu_forward_kernel_500073_511002),
    .in2(out_reg_29_reg_29),
    .in3(out_reg_20_reg_20));
  lut_expr_FU #(.BITSIZE_in1(3),
    .BITSIZE_out1(1)) fu_forward_kernel_500073_511008 (.out1(out_lut_expr_FU_72_i0_fu_forward_kernel_500073_511008),
    .in1(out_const_4),
    .in2(out_lut_expr_FU_61_i0_fu_forward_kernel_500073_511112),
    .in3(out_lut_expr_FU_68_i0_fu_forward_kernel_500073_511134),
    .in4(1'b0),
    .in5(1'b0),
    .in6(1'b0),
    .in7(1'b0),
    .in8(1'b0),
    .in9(1'b0));
  ui_cond_expr_FU #(.BITSIZE_in1(1),
    .BITSIZE_in2(32),
    .BITSIZE_in3(32),
    .BITSIZE_out1(32)) fu_forward_kernel_500073_511011 (.out1(out_ui_cond_expr_FU_32_32_32_32_97_i1_fu_forward_kernel_500073_511011),
    .in1(out_lut_expr_FU_70_i0_fu_forward_kernel_500073_510996),
    .in2(out_ui_cond_expr_FU_32_32_32_32_97_i0_fu_forward_kernel_500073_511005),
    .in3(out_reg_21_reg_21));
  ui_cond_expr_FU #(.BITSIZE_in1(1),
    .BITSIZE_in2(32),
    .BITSIZE_in3(32),
    .BITSIZE_out1(32)) fu_forward_kernel_500073_511014 (.out1(out_ui_cond_expr_FU_32_32_32_32_97_i2_fu_forward_kernel_500073_511014),
    .in1(out_reg_22_reg_22),
    .in2(out_const_35),
    .in3(out_ui_cond_expr_FU_32_32_32_32_97_i1_fu_forward_kernel_500073_511011));
  ui_extract_bit_expr_FU #(.BITSIZE_in1(32),
    .BITSIZE_in2(5)) fu_forward_kernel_500073_511022 (.out1(out_ui_extract_bit_expr_FU_11_i0_fu_forward_kernel_500073_511022),
    .in1(out_BMEMORY_CTRLN_83_i0_BMEMORY_CTRLN_83_i0),
    .in2(out_const_32));
  ui_extract_bit_expr_FU #(.BITSIZE_in1(32),
    .BITSIZE_in2(5)) fu_forward_kernel_500073_511026 (.out1(out_ui_extract_bit_expr_FU_13_i0_fu_forward_kernel_500073_511026),
    .in1(out_BMEMORY_CTRLN_83_i0_BMEMORY_CTRLN_83_i0),
    .in2(out_const_32));
  ui_extract_bit_expr_FU #(.BITSIZE_in1(32),
    .BITSIZE_in2(5)) fu_forward_kernel_500073_511030 (.out1(out_ui_extract_bit_expr_FU_16_i0_fu_forward_kernel_500073_511030),
    .in1(out_BMEMORY_CTRLN_83_i0_BMEMORY_CTRLN_83_i0),
    .in2(out_const_15));
  ui_extract_bit_expr_FU #(.BITSIZE_in1(32),
    .BITSIZE_in2(5)) fu_forward_kernel_500073_511034 (.out1(out_ui_extract_bit_expr_FU_17_i0_fu_forward_kernel_500073_511034),
    .in1(out_BMEMORY_CTRLN_83_i0_BMEMORY_CTRLN_83_i0),
    .in2(out_const_18));
  ui_extract_bit_expr_FU #(.BITSIZE_in1(32),
    .BITSIZE_in2(5)) fu_forward_kernel_500073_511038 (.out1(out_ui_extract_bit_expr_FU_18_i0_fu_forward_kernel_500073_511038),
    .in1(out_BMEMORY_CTRLN_83_i0_BMEMORY_CTRLN_83_i0),
    .in2(out_const_19));
  ui_extract_bit_expr_FU #(.BITSIZE_in1(32),
    .BITSIZE_in2(5)) fu_forward_kernel_500073_511042 (.out1(out_ui_extract_bit_expr_FU_19_i0_fu_forward_kernel_500073_511042),
    .in1(out_BMEMORY_CTRLN_83_i0_BMEMORY_CTRLN_83_i0),
    .in2(out_const_21));
  ui_extract_bit_expr_FU #(.BITSIZE_in1(32),
    .BITSIZE_in2(5)) fu_forward_kernel_500073_511046 (.out1(out_ui_extract_bit_expr_FU_20_i0_fu_forward_kernel_500073_511046),
    .in1(out_BMEMORY_CTRLN_83_i0_BMEMORY_CTRLN_83_i0),
    .in2(out_const_22));
  ui_extract_bit_expr_FU #(.BITSIZE_in1(32),
    .BITSIZE_in2(5)) fu_forward_kernel_500073_511050 (.out1(out_ui_extract_bit_expr_FU_21_i0_fu_forward_kernel_500073_511050),
    .in1(out_BMEMORY_CTRLN_83_i0_BMEMORY_CTRLN_83_i0),
    .in2(out_const_23));
  ui_extract_bit_expr_FU #(.BITSIZE_in1(32),
    .BITSIZE_in2(5)) fu_forward_kernel_500073_511054 (.out1(out_ui_extract_bit_expr_FU_22_i0_fu_forward_kernel_500073_511054),
    .in1(out_BMEMORY_CTRLN_83_i0_BMEMORY_CTRLN_83_i0),
    .in2(out_const_26));
  ui_extract_bit_expr_FU #(.BITSIZE_in1(32),
    .BITSIZE_in2(5)) fu_forward_kernel_500073_511058 (.out1(out_ui_extract_bit_expr_FU_23_i0_fu_forward_kernel_500073_511058),
    .in1(out_BMEMORY_CTRLN_83_i0_BMEMORY_CTRLN_83_i0),
    .in2(out_const_30));
  ui_extract_bit_expr_FU #(.BITSIZE_in1(32),
    .BITSIZE_in2(5)) fu_forward_kernel_500073_511062 (.out1(out_ui_extract_bit_expr_FU_24_i0_fu_forward_kernel_500073_511062),
    .in1(out_BMEMORY_CTRLN_83_i0_BMEMORY_CTRLN_83_i0),
    .in2(out_const_15));
  ui_extract_bit_expr_FU #(.BITSIZE_in1(32),
    .BITSIZE_in2(5)) fu_forward_kernel_500073_511066 (.out1(out_ui_extract_bit_expr_FU_25_i0_fu_forward_kernel_500073_511066),
    .in1(out_BMEMORY_CTRLN_83_i0_BMEMORY_CTRLN_83_i0),
    .in2(out_const_18));
  ui_extract_bit_expr_FU #(.BITSIZE_in1(32),
    .BITSIZE_in2(5)) fu_forward_kernel_500073_511070 (.out1(out_ui_extract_bit_expr_FU_26_i0_fu_forward_kernel_500073_511070),
    .in1(out_BMEMORY_CTRLN_83_i0_BMEMORY_CTRLN_83_i0),
    .in2(out_const_19));
  ui_extract_bit_expr_FU #(.BITSIZE_in1(32),
    .BITSIZE_in2(5)) fu_forward_kernel_500073_511074 (.out1(out_ui_extract_bit_expr_FU_27_i0_fu_forward_kernel_500073_511074),
    .in1(out_BMEMORY_CTRLN_83_i0_BMEMORY_CTRLN_83_i0),
    .in2(out_const_21));
  ui_extract_bit_expr_FU #(.BITSIZE_in1(32),
    .BITSIZE_in2(5)) fu_forward_kernel_500073_511078 (.out1(out_ui_extract_bit_expr_FU_28_i0_fu_forward_kernel_500073_511078),
    .in1(out_BMEMORY_CTRLN_83_i0_BMEMORY_CTRLN_83_i0),
    .in2(out_const_22));
  ui_extract_bit_expr_FU #(.BITSIZE_in1(32),
    .BITSIZE_in2(5)) fu_forward_kernel_500073_511082 (.out1(out_ui_extract_bit_expr_FU_29_i0_fu_forward_kernel_500073_511082),
    .in1(out_BMEMORY_CTRLN_83_i0_BMEMORY_CTRLN_83_i0),
    .in2(out_const_23));
  ui_extract_bit_expr_FU #(.BITSIZE_in1(32),
    .BITSIZE_in2(5)) fu_forward_kernel_500073_511086 (.out1(out_ui_extract_bit_expr_FU_30_i0_fu_forward_kernel_500073_511086),
    .in1(out_BMEMORY_CTRLN_83_i0_BMEMORY_CTRLN_83_i0),
    .in2(out_const_26));
  ui_extract_bit_expr_FU #(.BITSIZE_in1(32),
    .BITSIZE_in2(5)) fu_forward_kernel_500073_511090 (.out1(out_ui_extract_bit_expr_FU_31_i0_fu_forward_kernel_500073_511090),
    .in1(out_BMEMORY_CTRLN_83_i0_BMEMORY_CTRLN_83_i0),
    .in2(out_const_30));
  lut_expr_FU #(.BITSIZE_in1(64),
    .BITSIZE_out1(1)) fu_forward_kernel_500073_511097 (.out1(out_lut_expr_FU_56_i0_fu_forward_kernel_500073_511097),
    .in1(out_const_9),
    .in2(out_ui_extract_bit_expr_FU_24_i0_fu_forward_kernel_500073_511062),
    .in3(out_ui_extract_bit_expr_FU_25_i0_fu_forward_kernel_500073_511066),
    .in4(out_ui_extract_bit_expr_FU_26_i0_fu_forward_kernel_500073_511070),
    .in5(out_ui_extract_bit_expr_FU_27_i0_fu_forward_kernel_500073_511074),
    .in6(out_ui_extract_bit_expr_FU_30_i0_fu_forward_kernel_500073_511086),
    .in7(out_ui_extract_bit_expr_FU_31_i0_fu_forward_kernel_500073_511090),
    .in8(1'b0),
    .in9(1'b0));
  lut_expr_FU #(.BITSIZE_in1(8),
    .BITSIZE_out1(1)) fu_forward_kernel_500073_511100 (.out1(out_lut_expr_FU_57_i0_fu_forward_kernel_500073_511100),
    .in1(out_const_6),
    .in2(out_ui_extract_bit_expr_FU_28_i0_fu_forward_kernel_500073_511078),
    .in3(out_ui_extract_bit_expr_FU_29_i0_fu_forward_kernel_500073_511082),
    .in4(out_lut_expr_FU_56_i0_fu_forward_kernel_500073_511097),
    .in5(1'b0),
    .in6(1'b0),
    .in7(1'b0),
    .in8(1'b0),
    .in9(1'b0));
  lut_expr_FU #(.BITSIZE_in1(8),
    .BITSIZE_out1(1)) fu_forward_kernel_500073_511103 (.out1(out_lut_expr_FU_58_i0_fu_forward_kernel_500073_511103),
    .in1(out_const_24),
    .in2(out_ui_ne_expr_FU_32_0_32_110_i1_fu_forward_kernel_500073_510807),
    .in3(out_ui_eq_expr_FU_32_0_32_98_i1_fu_forward_kernel_500073_510804),
    .in4(out_lut_expr_FU_57_i0_fu_forward_kernel_500073_511100),
    .in5(1'b0),
    .in6(1'b0),
    .in7(1'b0),
    .in8(1'b0),
    .in9(1'b0));
  lut_expr_FU #(.BITSIZE_in1(64),
    .BITSIZE_out1(1)) fu_forward_kernel_500073_511106 (.out1(out_lut_expr_FU_59_i0_fu_forward_kernel_500073_511106),
    .in1(out_const_9),
    .in2(out_ui_extract_bit_expr_FU_16_i0_fu_forward_kernel_500073_511030),
    .in3(out_ui_extract_bit_expr_FU_17_i0_fu_forward_kernel_500073_511034),
    .in4(out_ui_extract_bit_expr_FU_18_i0_fu_forward_kernel_500073_511038),
    .in5(out_ui_extract_bit_expr_FU_19_i0_fu_forward_kernel_500073_511042),
    .in6(out_ui_extract_bit_expr_FU_22_i0_fu_forward_kernel_500073_511054),
    .in7(out_ui_extract_bit_expr_FU_23_i0_fu_forward_kernel_500073_511058),
    .in8(1'b0),
    .in9(1'b0));
  lut_expr_FU #(.BITSIZE_in1(8),
    .BITSIZE_out1(1)) fu_forward_kernel_500073_511109 (.out1(out_lut_expr_FU_60_i0_fu_forward_kernel_500073_511109),
    .in1(out_const_6),
    .in2(out_ui_extract_bit_expr_FU_20_i0_fu_forward_kernel_500073_511046),
    .in3(out_ui_extract_bit_expr_FU_21_i0_fu_forward_kernel_500073_511050),
    .in4(out_lut_expr_FU_59_i0_fu_forward_kernel_500073_511106),
    .in5(1'b0),
    .in6(1'b0),
    .in7(1'b0),
    .in8(1'b0),
    .in9(1'b0));
  lut_expr_FU #(.BITSIZE_in1(9),
    .BITSIZE_out1(1)) fu_forward_kernel_500073_511112 (.out1(out_lut_expr_FU_61_i0_fu_forward_kernel_500073_511112),
    .in1(out_const_10),
    .in2(out_reg_13_reg_13),
    .in3(out_reg_12_reg_12),
    .in4(out_lut_expr_FU_58_i0_fu_forward_kernel_500073_511103),
    .in5(out_reg_16_reg_16),
    .in6(1'b0),
    .in7(1'b0),
    .in8(1'b0),
    .in9(1'b0));
  lut_expr_FU #(.BITSIZE_in1(64),
    .BITSIZE_out1(1)) fu_forward_kernel_500073_511115 (.out1(out_lut_expr_FU_62_i0_fu_forward_kernel_500073_511115),
    .in1(out_const_9),
    .in2(out_ui_extract_bit_expr_FU_48_i0_fu_forward_kernel_500073_510930),
    .in3(out_ui_extract_bit_expr_FU_49_i0_fu_forward_kernel_500073_510933),
    .in4(out_ui_extract_bit_expr_FU_50_i0_fu_forward_kernel_500073_510936),
    .in5(out_ui_extract_bit_expr_FU_51_i0_fu_forward_kernel_500073_510939),
    .in6(out_ui_extract_bit_expr_FU_54_i0_fu_forward_kernel_500073_510948),
    .in7(out_ui_extract_bit_expr_FU_55_i0_fu_forward_kernel_500073_510951),
    .in8(1'b0),
    .in9(1'b0));
  lut_expr_FU #(.BITSIZE_in1(13),
    .BITSIZE_out1(1)) fu_forward_kernel_500073_511118 (.out1(out_lut_expr_FU_63_i0_fu_forward_kernel_500073_511118),
    .in1(out_const_14),
    .in2(out_reg_30_reg_30),
    .in3(out_reg_31_reg_31),
    .in4(out_reg_32_reg_32),
    .in5(out_reg_33_reg_33),
    .in6(1'b0),
    .in7(1'b0),
    .in8(1'b0),
    .in9(1'b0));
  lut_expr_FU #(.BITSIZE_in1(1),
    .BITSIZE_out1(1)) fu_forward_kernel_500073_511121 (.out1(out_lut_expr_FU_64_i0_fu_forward_kernel_500073_511121),
    .in1(out_const_2),
    .in2(out_ui_extract_bit_expr_FU_18_i0_fu_forward_kernel_500073_511038),
    .in3(out_ui_extract_bit_expr_FU_19_i0_fu_forward_kernel_500073_511042),
    .in4(out_ui_extract_bit_expr_FU_20_i0_fu_forward_kernel_500073_511046),
    .in5(out_ui_extract_bit_expr_FU_21_i0_fu_forward_kernel_500073_511050),
    .in6(out_ui_extract_bit_expr_FU_22_i0_fu_forward_kernel_500073_511054),
    .in7(out_ui_extract_bit_expr_FU_23_i0_fu_forward_kernel_500073_511058),
    .in8(1'b0),
    .in9(1'b0));
  lut_expr_FU #(.BITSIZE_in1(12),
    .BITSIZE_out1(1)) fu_forward_kernel_500073_511124 (.out1(out_lut_expr_FU_65_i0_fu_forward_kernel_500073_511124),
    .in1(out_const_25),
    .in2(out_ui_extract_bit_expr_FU_16_i0_fu_forward_kernel_500073_511030),
    .in3(out_ui_extract_bit_expr_FU_17_i0_fu_forward_kernel_500073_511034),
    .in4(out_lut_expr_FU_60_i0_fu_forward_kernel_500073_511109),
    .in5(out_lut_expr_FU_64_i0_fu_forward_kernel_500073_511121),
    .in6(1'b0),
    .in7(1'b0),
    .in8(1'b0),
    .in9(1'b0));
  lut_expr_FU #(.BITSIZE_in1(1),
    .BITSIZE_out1(1)) fu_forward_kernel_500073_511127 (.out1(out_lut_expr_FU_66_i0_fu_forward_kernel_500073_511127),
    .in1(out_const_2),
    .in2(out_ui_extract_bit_expr_FU_26_i0_fu_forward_kernel_500073_511070),
    .in3(out_ui_extract_bit_expr_FU_27_i0_fu_forward_kernel_500073_511074),
    .in4(out_ui_extract_bit_expr_FU_28_i0_fu_forward_kernel_500073_511078),
    .in5(out_ui_extract_bit_expr_FU_29_i0_fu_forward_kernel_500073_511082),
    .in6(out_ui_extract_bit_expr_FU_30_i0_fu_forward_kernel_500073_511086),
    .in7(out_ui_extract_bit_expr_FU_31_i0_fu_forward_kernel_500073_511090),
    .in8(1'b0),
    .in9(1'b0));
  lut_expr_FU #(.BITSIZE_in1(28),
    .BITSIZE_out1(1)) fu_forward_kernel_500073_511130 (.out1(out_lut_expr_FU_67_i0_fu_forward_kernel_500073_511130),
    .in1(out_const_31),
    .in2(out_ui_extract_bit_expr_FU_24_i0_fu_forward_kernel_500073_511062),
    .in3(out_ui_extract_bit_expr_FU_25_i0_fu_forward_kernel_500073_511066),
    .in4(out_ui_ne_expr_FU_32_0_32_110_i1_fu_forward_kernel_500073_510807),
    .in5(out_lut_expr_FU_57_i0_fu_forward_kernel_500073_511100),
    .in6(out_lut_expr_FU_66_i0_fu_forward_kernel_500073_511127),
    .in7(1'b0),
    .in8(1'b0),
    .in9(1'b0));
  lut_expr_FU #(.BITSIZE_in1(64),
    .BITSIZE_out1(1)) fu_forward_kernel_500073_511134 (.out1(out_lut_expr_FU_68_i0_fu_forward_kernel_500073_511134),
    .in1(out_const_27),
    .in2(out_reg_13_reg_13),
    .in3(out_reg_12_reg_12),
    .in4(out_lut_expr_FU_58_i0_fu_forward_kernel_500073_511103),
    .in5(out_reg_16_reg_16),
    .in6(out_reg_17_reg_17),
    .in7(out_lut_expr_FU_67_i0_fu_forward_kernel_500073_511130),
    .in8(1'b0),
    .in9(1'b0));
  lut_expr_FU #(.BITSIZE_in1(16),
    .BITSIZE_out1(1)) fu_forward_kernel_500073_511138 (.out1(out_lut_expr_FU_69_i0_fu_forward_kernel_500073_511138),
    .in1(out_const_13),
    .in2(out_ui_extract_bit_expr_FU_40_i0_fu_forward_kernel_500073_510894),
    .in3(out_ui_extract_bit_expr_FU_41_i0_fu_forward_kernel_500073_510897),
    .in4(out_ui_ne_expr_FU_32_0_32_111_i0_fu_forward_kernel_500073_510891),
    .in5(out_ui_extract_bit_expr_FU_45_i0_fu_forward_kernel_500073_510912),
    .in6(1'b0),
    .in7(1'b0),
    .in8(1'b0),
    .in9(1'b0));
  register_SE #(.BITSIZE_in1(64),
    .BITSIZE_out1(64)) reg_0 (.out1(out_reg_0_reg_0),
    .clock(clock),
    .reset(reset),
    .in1(out_MUX_136_reg_0_0_0_0),
    .wenable(wrenable_reg_0));
  register_SE #(.BITSIZE_in1(32),
    .BITSIZE_out1(32)) reg_1 (.out1(out_reg_1_reg_1),
    .clock(clock),
    .reset(reset),
    .in1(out_ui_pointer_plus_expr_FU_32_32_32_115_i2_fu_forward_kernel_500073_500127),
    .wenable(wrenable_reg_1));
  register_SE #(.BITSIZE_in1(1),
    .BITSIZE_out1(1)) reg_10 (.out1(out_reg_10_reg_10),
    .clock(clock),
    .reset(reset),
    .in1(out_lut_expr_FU_77_i0_fu_forward_kernel_500073_503986),
    .wenable(wrenable_reg_10));
  register_STD #(.BITSIZE_in1(8),
    .BITSIZE_out1(8)) reg_11 (.out1(out_reg_11_reg_11),
    .clock(clock),
    .reset(reset),
    .in1(out_UUdata_converter_FU_10_i0_fu_forward_kernel_500073_510721),
    .wenable(wrenable_reg_11));
  register_STD #(.BITSIZE_in1(1),
    .BITSIZE_out1(1)) reg_12 (.out1(out_reg_12_reg_12),
    .clock(clock),
    .reset(reset),
    .in1(out_ui_eq_expr_FU_32_0_32_98_i0_fu_forward_kernel_500073_510774),
    .wenable(wrenable_reg_12));
  register_STD #(.BITSIZE_in1(1),
    .BITSIZE_out1(1)) reg_13 (.out1(out_reg_13_reg_13),
    .clock(clock),
    .reset(reset),
    .in1(out_ui_ne_expr_FU_32_0_32_110_i0_fu_forward_kernel_500073_510777),
    .wenable(wrenable_reg_13));
  register_SE #(.BITSIZE_in1(24),
    .BITSIZE_out1(24)) reg_14 (.out1(out_reg_14_reg_14),
    .clock(clock),
    .reset(reset),
    .in1(out_ui_bit_and_expr_FU_32_0_32_85_i0_fu_forward_kernel_500073_510819),
    .wenable(wrenable_reg_14));
  register_STD #(.BITSIZE_in1(1),
    .BITSIZE_out1(1)) reg_15 (.out1(out_reg_15_reg_15),
    .clock(clock),
    .reset(reset),
    .in1(out_ui_extract_bit_expr_FU_11_i0_fu_forward_kernel_500073_511022),
    .wenable(wrenable_reg_15));
  register_STD #(.BITSIZE_in1(1),
    .BITSIZE_out1(1)) reg_16 (.out1(out_reg_16_reg_16),
    .clock(clock),
    .reset(reset),
    .in1(out_lut_expr_FU_60_i0_fu_forward_kernel_500073_511109),
    .wenable(wrenable_reg_16));
  register_STD #(.BITSIZE_in1(1),
    .BITSIZE_out1(1)) reg_17 (.out1(out_reg_17_reg_17),
    .clock(clock),
    .reset(reset),
    .in1(out_lut_expr_FU_65_i0_fu_forward_kernel_500073_511124),
    .wenable(wrenable_reg_17));
  register_SE #(.BITSIZE_in1(10),
    .BITSIZE_out1(10)) reg_18 (.out1(out_reg_18_reg_18),
    .clock(clock),
    .reset(reset),
    .in1(out_ui_ternary_plus_expr_FU_16_0_16_16_122_i0_fu_forward_kernel_500073_510810),
    .wenable(wrenable_reg_18));
  register_STD #(.BITSIZE_in1(24),
    .BITSIZE_out1(24)) reg_19 (.out1(out_reg_19_reg_19),
    .clock(clock),
    .reset(reset),
    .in1(out_ui_bit_and_expr_FU_32_0_32_85_i1_fu_forward_kernel_500073_510822),
    .wenable(wrenable_reg_19));
  register_SE #(.BITSIZE_in1(1),
    .BITSIZE_out1(1)) reg_2 (.out1(out_reg_2_reg_2),
    .clock(clock),
    .reset(reset),
    .in1(out_ui_lt_expr_FU_64_0_64_108_i0_fu_forward_kernel_500073_500216),
    .wenable(wrenable_reg_2));
  register_SE #(.BITSIZE_in1(32),
    .BITSIZE_out1(32)) reg_20 (.out1(out_reg_20_reg_20),
    .clock(clock),
    .reset(reset),
    .in1(out_ui_lshift_expr_FU_32_0_32_102_i0_fu_forward_kernel_500073_510918),
    .wenable(wrenable_reg_20));
  register_SE #(.BITSIZE_in1(32),
    .BITSIZE_out1(32)) reg_21 (.out1(out_reg_21_reg_21),
    .clock(clock),
    .reset(reset),
    .in1(out_ui_bit_ior_expr_FU_0_32_32_95_i0_fu_forward_kernel_500073_510954),
    .wenable(wrenable_reg_21));
  register_SE #(.BITSIZE_in1(1),
    .BITSIZE_out1(1)) reg_22 (.out1(out_reg_22_reg_22),
    .clock(clock),
    .reset(reset),
    .in1(out_lut_expr_FU_72_i0_fu_forward_kernel_500073_511008),
    .wenable(wrenable_reg_22));
  register_SE #(.BITSIZE_in1(1),
    .BITSIZE_out1(1)) reg_23 (.out1(out_reg_23_reg_23),
    .clock(clock),
    .reset(reset),
    .in1(out_lut_expr_FU_61_i0_fu_forward_kernel_500073_511112),
    .wenable(wrenable_reg_23));
  register_SE #(.BITSIZE_in1(1),
    .BITSIZE_out1(1)) reg_24 (.out1(out_reg_24_reg_24),
    .clock(clock),
    .reset(reset),
    .in1(out_lut_expr_FU_68_i0_fu_forward_kernel_500073_511134),
    .wenable(wrenable_reg_24));
  register_STD #(.BITSIZE_in1(48),
    .BITSIZE_out1(48)) reg_25 (.out1(out_reg_25_reg_25),
    .clock(clock),
    .reset(reset),
    .in1(out_ui_mult_expr_FU_32_32_32_0_109_i0_fu_forward_kernel_500073_510825),
    .wenable(wrenable_reg_25));
  register_STD #(.BITSIZE_in1(1),
    .BITSIZE_out1(1)) reg_26 (.out1(out_reg_26_reg_26),
    .clock(clock),
    .reset(reset),
    .in1(out_ui_extract_bit_expr_FU_32_i0_fu_forward_kernel_500073_510828),
    .wenable(wrenable_reg_26));
  register_STD #(.BITSIZE_in1(1),
    .BITSIZE_out1(1)) reg_27 (.out1(out_reg_27_reg_27),
    .clock(clock),
    .reset(reset),
    .in1(out_UUdata_converter_FU_34_i0_fu_forward_kernel_500073_510834),
    .wenable(wrenable_reg_27));
  register_STD #(.BITSIZE_in1(1),
    .BITSIZE_out1(1)) reg_28 (.out1(out_reg_28_reg_28),
    .clock(clock),
    .reset(reset),
    .in1(out_ui_extract_bit_expr_FU_39_i0_fu_forward_kernel_500073_510876),
    .wenable(wrenable_reg_28));
  register_STD #(.BITSIZE_in1(32),
    .BITSIZE_out1(32)) reg_29 (.out1(out_reg_29_reg_29),
    .clock(clock),
    .reset(reset),
    .in1(out_ui_bit_ior_expr_FU_0_32_32_94_i0_fu_forward_kernel_500073_510924),
    .wenable(wrenable_reg_29));
  register_SE #(.BITSIZE_in1(26),
    .BITSIZE_out1(26)) reg_3 (.out1(out_reg_3_reg_3),
    .clock(clock),
    .reset(reset),
    .in1(out_ui_rshift_expr_FU_64_0_64_119_i0_fu_forward_kernel_500073_503861),
    .wenable(wrenable_reg_3));
  register_STD #(.BITSIZE_in1(1),
    .BITSIZE_out1(1)) reg_30 (.out1(out_reg_30_reg_30),
    .clock(clock),
    .reset(reset),
    .in1(out_ui_extract_bit_expr_FU_47_i0_fu_forward_kernel_500073_510927),
    .wenable(wrenable_reg_30));
  register_STD #(.BITSIZE_in1(1),
    .BITSIZE_out1(1)) reg_31 (.out1(out_reg_31_reg_31),
    .clock(clock),
    .reset(reset),
    .in1(out_ui_extract_bit_expr_FU_52_i0_fu_forward_kernel_500073_510942),
    .wenable(wrenable_reg_31));
  register_STD #(.BITSIZE_in1(1),
    .BITSIZE_out1(1)) reg_32 (.out1(out_reg_32_reg_32),
    .clock(clock),
    .reset(reset),
    .in1(out_ui_extract_bit_expr_FU_53_i0_fu_forward_kernel_500073_510945),
    .wenable(wrenable_reg_32));
  register_STD #(.BITSIZE_in1(1),
    .BITSIZE_out1(1)) reg_33 (.out1(out_reg_33_reg_33),
    .clock(clock),
    .reset(reset),
    .in1(out_lut_expr_FU_62_i0_fu_forward_kernel_500073_511115),
    .wenable(wrenable_reg_33));
  register_STD #(.BITSIZE_in1(1),
    .BITSIZE_out1(1)) reg_34 (.out1(out_reg_34_reg_34),
    .clock(clock),
    .reset(reset),
    .in1(out_lut_expr_FU_69_i0_fu_forward_kernel_500073_511138),
    .wenable(wrenable_reg_34));
  register_SE #(.BITSIZE_in1(32),
    .BITSIZE_out1(32)) reg_35 (.out1(out_reg_35_reg_35),
    .clock(clock),
    .reset(reset),
    .in1(out_UUdata_converter_FU_75_i0_fu_forward_kernel_500073_502289),
    .wenable(wrenable_reg_35));
  register_STD #(.BITSIZE_in1(32),
    .BITSIZE_out1(32)) reg_36 (.out1(out_reg_36_reg_36),
    .clock(clock),
    .reset(reset),
    .in1(out_conv_out___float_adde8m23b_127nih_123_i0_fu_forward_kernel_500073_500104_64_32),
    .wenable(wrenable_reg_36));
  register_SE #(.BITSIZE_in1(4),
    .BITSIZE_out1(4)) reg_4 (.out1(out_reg_4_reg_4),
    .clock(clock),
    .reset(reset),
    .in1(out_ui_bit_and_expr_FU_8_0_8_90_i0_fu_forward_kernel_500073_503873),
    .wenable(wrenable_reg_4));
  register_SE #(.BITSIZE_in1(64),
    .BITSIZE_out1(64)) reg_5 (.out1(out_reg_5_reg_5),
    .clock(clock),
    .reset(reset),
    .in1(out_MUX_168_reg_5_0_0_0),
    .wenable(wrenable_reg_5));
  register_SE #(.BITSIZE_in1(32),
    .BITSIZE_out1(32)) reg_6 (.out1(out_reg_6_reg_6),
    .clock(clock),
    .reset(reset),
    .in1(out_MUX_169_reg_6_0_0_0),
    .wenable(wrenable_reg_6));
  register_STD #(.BITSIZE_in1(32),
    .BITSIZE_out1(32)) reg_7 (.out1(out_reg_7_reg_7),
    .clock(clock),
    .reset(reset),
    .in1(out_ui_pointer_plus_expr_FU_32_32_32_115_i1_fu_forward_kernel_500073_500101),
    .wenable(wrenable_reg_7));
  register_SE #(.BITSIZE_in1(1),
    .BITSIZE_out1(1)) reg_8 (.out1(out_reg_8_reg_8),
    .clock(clock),
    .reset(reset),
    .in1(out_ui_lt_expr_FU_64_0_64_107_i0_fu_forward_kernel_500073_500207),
    .wenable(wrenable_reg_8));
  register_SE #(.BITSIZE_in1(32),
    .BITSIZE_out1(32)) reg_9 (.out1(out_reg_9_reg_9),
    .clock(clock),
    .reset(reset),
    .in1(out_UUdata_converter_FU_74_i0_fu_forward_kernel_500073_502286),
    .wenable(wrenable_reg_9));
  // io-signal post fix
  assign OUT_MULTIIF_forward_kernel_500073_503980 = out_multi_read_cond_FU_78_i0_fu_forward_kernel_500073_503980;
  assign OUT_UNBOUNDED_forward_kernel_500073_500104 = s_done_fu_forward_kernel_500073_500104;

endmodule

// FSM based controller description for forward_kernel
// This component has been derived from the input source code and so it does not fall under the copyright of PandA framework, but it follows the input source code copyright, and may be aggregated with components of the BAMBU/PANDA IP LIBRARY.
// Author(s): Component automatically generated by bambu
// License: THIS COMPONENT IS PROVIDED "AS IS" AND WITHOUT ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, WITHOUT LIMITATION, THE IMPLIED WARRANTIES OF MERCHANTIBILITY AND FITNESS FOR A PARTICULAR PURPOSE.
`timescale 1ns / 1ps
module controller_forward_kernel(done_port,
  fuselector_BMEMORY_CTRLN_83_i0_LOAD,
  fuselector_BMEMORY_CTRLN_83_i0_STORE,
  selector_IN_UNBOUNDED_forward_kernel_500073_500104,
  selector_MUX_136_reg_0_0_0_0,
  selector_MUX_168_reg_5_0_0_0,
  selector_MUX_169_reg_6_0_0_0,
  selector_MUX_1_BMEMORY_CTRLN_83_i0_1_0_0,
  selector_MUX_1_BMEMORY_CTRLN_83_i0_1_0_1,
  selector_MUX_1_BMEMORY_CTRLN_83_i0_1_1_0,
  wrenable_reg_0,
  wrenable_reg_1,
  wrenable_reg_10,
  wrenable_reg_11,
  wrenable_reg_12,
  wrenable_reg_13,
  wrenable_reg_14,
  wrenable_reg_15,
  wrenable_reg_16,
  wrenable_reg_17,
  wrenable_reg_18,
  wrenable_reg_19,
  wrenable_reg_2,
  wrenable_reg_20,
  wrenable_reg_21,
  wrenable_reg_22,
  wrenable_reg_23,
  wrenable_reg_24,
  wrenable_reg_25,
  wrenable_reg_26,
  wrenable_reg_27,
  wrenable_reg_28,
  wrenable_reg_29,
  wrenable_reg_3,
  wrenable_reg_30,
  wrenable_reg_31,
  wrenable_reg_32,
  wrenable_reg_33,
  wrenable_reg_34,
  wrenable_reg_35,
  wrenable_reg_36,
  wrenable_reg_4,
  wrenable_reg_5,
  wrenable_reg_6,
  wrenable_reg_7,
  wrenable_reg_8,
  wrenable_reg_9,
  OUT_MULTIIF_forward_kernel_500073_503980,
  OUT_UNBOUNDED_forward_kernel_500073_500104,
  clock,
  reset,
  start_port);
  // IN
  input [1:0] OUT_MULTIIF_forward_kernel_500073_503980;
  input OUT_UNBOUNDED_forward_kernel_500073_500104;
  input clock;
  input reset;
  input start_port;
  // OUT
  output done_port;
  output fuselector_BMEMORY_CTRLN_83_i0_LOAD;
  output fuselector_BMEMORY_CTRLN_83_i0_STORE;
  output selector_IN_UNBOUNDED_forward_kernel_500073_500104;
  output selector_MUX_136_reg_0_0_0_0;
  output selector_MUX_168_reg_5_0_0_0;
  output selector_MUX_169_reg_6_0_0_0;
  output selector_MUX_1_BMEMORY_CTRLN_83_i0_1_0_0;
  output selector_MUX_1_BMEMORY_CTRLN_83_i0_1_0_1;
  output selector_MUX_1_BMEMORY_CTRLN_83_i0_1_1_0;
  output wrenable_reg_0;
  output wrenable_reg_1;
  output wrenable_reg_10;
  output wrenable_reg_11;
  output wrenable_reg_12;
  output wrenable_reg_13;
  output wrenable_reg_14;
  output wrenable_reg_15;
  output wrenable_reg_16;
  output wrenable_reg_17;
  output wrenable_reg_18;
  output wrenable_reg_19;
  output wrenable_reg_2;
  output wrenable_reg_20;
  output wrenable_reg_21;
  output wrenable_reg_22;
  output wrenable_reg_23;
  output wrenable_reg_24;
  output wrenable_reg_25;
  output wrenable_reg_26;
  output wrenable_reg_27;
  output wrenable_reg_28;
  output wrenable_reg_29;
  output wrenable_reg_3;
  output wrenable_reg_30;
  output wrenable_reg_31;
  output wrenable_reg_32;
  output wrenable_reg_33;
  output wrenable_reg_34;
  output wrenable_reg_35;
  output wrenable_reg_36;
  output wrenable_reg_4;
  output wrenable_reg_5;
  output wrenable_reg_6;
  output wrenable_reg_7;
  output wrenable_reg_8;
  output wrenable_reg_9;
  parameter [14:0] S_13 = 15'b010000000000000,
    S_11 = 15'b000100000000000,
    S_12 = 15'b001000000000000,
    S_0 = 15'b000000000000001,
    S_1 = 15'b000000000000010,
    S_2 = 15'b000000000000100,
    S_3 = 15'b000000000001000,
    S_4 = 15'b000000000010000,
    S_5 = 15'b000000000100000,
    S_6 = 15'b000000001000000,
    S_7 = 15'b000000010000000,
    S_8 = 15'b000000100000000,
    S_9 = 15'b000001000000000,
    S_10 = 15'b000010000000000,
    S_14 = 15'b100000000000000;
  reg [14:0] _present_state=S_13, _next_state;
  reg done_port;
  reg fuselector_BMEMORY_CTRLN_83_i0_LOAD;
  reg fuselector_BMEMORY_CTRLN_83_i0_STORE;
  reg selector_IN_UNBOUNDED_forward_kernel_500073_500104;
  reg selector_MUX_136_reg_0_0_0_0;
  reg selector_MUX_168_reg_5_0_0_0;
  reg selector_MUX_169_reg_6_0_0_0;
  reg selector_MUX_1_BMEMORY_CTRLN_83_i0_1_0_0;
  reg selector_MUX_1_BMEMORY_CTRLN_83_i0_1_0_1;
  reg selector_MUX_1_BMEMORY_CTRLN_83_i0_1_1_0;
  reg wrenable_reg_0;
  reg wrenable_reg_1;
  reg wrenable_reg_10;
  reg wrenable_reg_11;
  reg wrenable_reg_12;
  reg wrenable_reg_13;
  reg wrenable_reg_14;
  reg wrenable_reg_15;
  reg wrenable_reg_16;
  reg wrenable_reg_17;
  reg wrenable_reg_18;
  reg wrenable_reg_19;
  reg wrenable_reg_2;
  reg wrenable_reg_20;
  reg wrenable_reg_21;
  reg wrenable_reg_22;
  reg wrenable_reg_23;
  reg wrenable_reg_24;
  reg wrenable_reg_25;
  reg wrenable_reg_26;
  reg wrenable_reg_27;
  reg wrenable_reg_28;
  reg wrenable_reg_29;
  reg wrenable_reg_3;
  reg wrenable_reg_30;
  reg wrenable_reg_31;
  reg wrenable_reg_32;
  reg wrenable_reg_33;
  reg wrenable_reg_34;
  reg wrenable_reg_35;
  reg wrenable_reg_36;
  reg wrenable_reg_4;
  reg wrenable_reg_5;
  reg wrenable_reg_6;
  reg wrenable_reg_7;
  reg wrenable_reg_8;
  reg wrenable_reg_9;
  
  always @(posedge clock)
    if (reset == 1'b0) _present_state <= S_13;
    else _present_state <= _next_state;
  
  always @(*)
  begin
    done_port = 1'b0;
    fuselector_BMEMORY_CTRLN_83_i0_LOAD = 1'b0;
    fuselector_BMEMORY_CTRLN_83_i0_STORE = 1'b0;
    selector_IN_UNBOUNDED_forward_kernel_500073_500104 = 1'b0;
    selector_MUX_136_reg_0_0_0_0 = 1'b0;
    selector_MUX_168_reg_5_0_0_0 = 1'b0;
    selector_MUX_169_reg_6_0_0_0 = 1'b0;
    selector_MUX_1_BMEMORY_CTRLN_83_i0_1_0_0 = 1'b0;
    selector_MUX_1_BMEMORY_CTRLN_83_i0_1_0_1 = 1'b0;
    selector_MUX_1_BMEMORY_CTRLN_83_i0_1_1_0 = 1'b0;
    wrenable_reg_0 = 1'b0;
    wrenable_reg_1 = 1'b0;
    wrenable_reg_10 = 1'b0;
    wrenable_reg_11 = 1'b0;
    wrenable_reg_12 = 1'b0;
    wrenable_reg_13 = 1'b0;
    wrenable_reg_14 = 1'b0;
    wrenable_reg_15 = 1'b0;
    wrenable_reg_16 = 1'b0;
    wrenable_reg_17 = 1'b0;
    wrenable_reg_18 = 1'b0;
    wrenable_reg_19 = 1'b0;
    wrenable_reg_2 = 1'b0;
    wrenable_reg_20 = 1'b0;
    wrenable_reg_21 = 1'b0;
    wrenable_reg_22 = 1'b0;
    wrenable_reg_23 = 1'b0;
    wrenable_reg_24 = 1'b0;
    wrenable_reg_25 = 1'b0;
    wrenable_reg_26 = 1'b0;
    wrenable_reg_27 = 1'b0;
    wrenable_reg_28 = 1'b0;
    wrenable_reg_29 = 1'b0;
    wrenable_reg_3 = 1'b0;
    wrenable_reg_30 = 1'b0;
    wrenable_reg_31 = 1'b0;
    wrenable_reg_32 = 1'b0;
    wrenable_reg_33 = 1'b0;
    wrenable_reg_34 = 1'b0;
    wrenable_reg_35 = 1'b0;
    wrenable_reg_36 = 1'b0;
    wrenable_reg_4 = 1'b0;
    wrenable_reg_5 = 1'b0;
    wrenable_reg_6 = 1'b0;
    wrenable_reg_7 = 1'b0;
    wrenable_reg_8 = 1'b0;
    wrenable_reg_9 = 1'b0;
    case (_present_state)
      S_13 :
        if(start_port == 1'b1)
        begin
          wrenable_reg_0 = 1'b1;
          _next_state = S_11;
        end
        else
        begin
          _next_state = S_13;
        end
      S_11 :
        begin
          fuselector_BMEMORY_CTRLN_83_i0_LOAD = 1'b1;
          selector_MUX_136_reg_0_0_0_0 = 1'b1;
          wrenable_reg_0 = 1'b1;
          wrenable_reg_1 = 1'b1;
          wrenable_reg_2 = 1'b1;
          wrenable_reg_3 = 1'b1;
          wrenable_reg_4 = 1'b1;
          _next_state = S_12;
        end
      S_12 :
        begin
          selector_MUX_169_reg_6_0_0_0 = 1'b1;
          wrenable_reg_5 = 1'b1;
          wrenable_reg_6 = 1'b1;
          _next_state = S_0;
        end
      S_0 :
        begin
          fuselector_BMEMORY_CTRLN_83_i0_LOAD = 1'b1;
          selector_MUX_168_reg_5_0_0_0 = 1'b1;
          selector_MUX_1_BMEMORY_CTRLN_83_i0_1_0_1 = 1'b1;
          wrenable_reg_10 = 1'b1;
          wrenable_reg_5 = 1'b1;
          wrenable_reg_7 = 1'b1;
          wrenable_reg_8 = 1'b1;
          wrenable_reg_9 = 1'b1;
          _next_state = S_1;
        end
      S_1 :
        begin
          fuselector_BMEMORY_CTRLN_83_i0_LOAD = 1'b1;
          selector_MUX_1_BMEMORY_CTRLN_83_i0_1_0_0 = 1'b1;
          selector_MUX_1_BMEMORY_CTRLN_83_i0_1_1_0 = 1'b1;
          wrenable_reg_11 = 1'b1;
          wrenable_reg_12 = 1'b1;
          wrenable_reg_13 = 1'b1;
          wrenable_reg_14 = 1'b1;
          wrenable_reg_15 = 1'b1;
          wrenable_reg_16 = 1'b1;
          wrenable_reg_17 = 1'b1;
          _next_state = S_2;
        end
      S_2 :
        begin
          wrenable_reg_18 = 1'b1;
          wrenable_reg_19 = 1'b1;
          wrenable_reg_20 = 1'b1;
          wrenable_reg_21 = 1'b1;
          wrenable_reg_22 = 1'b1;
          wrenable_reg_23 = 1'b1;
          wrenable_reg_24 = 1'b1;
          _next_state = S_3;
        end
      S_3 :
        begin
          wrenable_reg_25 = 1'b1;
          wrenable_reg_26 = 1'b1;
          wrenable_reg_27 = 1'b1;
          _next_state = S_4;
        end
      S_4 :
        begin
          wrenable_reg_28 = 1'b1;
          wrenable_reg_29 = 1'b1;
          wrenable_reg_30 = 1'b1;
          wrenable_reg_31 = 1'b1;
          wrenable_reg_32 = 1'b1;
          wrenable_reg_33 = 1'b1;
          wrenable_reg_34 = 1'b1;
          _next_state = S_5;
        end
      S_5 :
        begin
          wrenable_reg_35 = 1'b1;
          _next_state = S_6;
        end
      S_6 :
        begin
          selector_IN_UNBOUNDED_forward_kernel_500073_500104 = 1'b1;
          _next_state = S_7;
        end
      S_7 :
        begin
          _next_state = S_8;
        end
      S_8 :
        begin
          _next_state = S_9;
        end
      S_9 :
        begin
          wrenable_reg_36 = 1'b1;
          _next_state = S_10;
        end
      S_10 :
        begin
          fuselector_BMEMORY_CTRLN_83_i0_STORE = 1'b1;
          selector_MUX_1_BMEMORY_CTRLN_83_i0_1_1_0 = 1'b1;
          wrenable_reg_6 = 1'b1;
          casez (OUT_MULTIIF_forward_kernel_500073_503980)
            2'b?1 :
              begin
                _next_state = S_0;
              end
            2'b10 :
              begin
                _next_state = S_11;
                wrenable_reg_6 = 1'b0;
              end
            default:
              begin
                _next_state = S_14;
                done_port = 1'b1;
                wrenable_reg_6 = 1'b0;
              end
          endcase
        end
      S_14 :
        begin
          _next_state = S_13;
        end
      default :
        begin
          _next_state = S_13;
        end
    endcase
  end
endmodule

// Top component for forward_kernel
// This component has been derived from the input source code and so it does not fall under the copyright of PandA framework, but it follows the input source code copyright, and may be aggregated with components of the BAMBU/PANDA IP LIBRARY.
// Author(s): Component automatically generated by bambu
// License: THIS COMPONENT IS PROVIDED "AS IS" AND WITHOUT ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, WITHOUT LIMITATION, THE IMPLIED WARRANTIES OF MERCHANTIBILITY AND FITNESS FOR A PARTICULAR PURPOSE.
`timescale 1ns / 1ps
module _forward_kernel(clock,
  reset,
  start_port,
  done_port,
  P0,
  P1,
  P2,
  M_Rdata_ram,
  M_DataRdy,
  Min_oe_ram,
  Min_we_ram,
  Min_addr_ram,
  Min_Wdata_ram,
  Min_data_ram_size,
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
  input [1:0] Min_oe_ram;
  input [1:0] Min_we_ram;
  input [63:0] Min_addr_ram;
  input [63:0] Min_Wdata_ram;
  input [11:0] Min_data_ram_size;
  // OUT
  output done_port;
  output [1:0] Mout_oe_ram;
  output [1:0] Mout_we_ram;
  output [63:0] Mout_addr_ram;
  output [63:0] Mout_Wdata_ram;
  output [11:0] Mout_data_ram_size;
  // Component and signal declarations
  wire [1:0] OUT_MULTIIF_forward_kernel_500073_503980;
  wire OUT_UNBOUNDED_forward_kernel_500073_500104;
  wire done_delayed_REG_signal_in;
  wire done_delayed_REG_signal_out;
  wire fuselector_BMEMORY_CTRLN_83_i0_LOAD;
  wire fuselector_BMEMORY_CTRLN_83_i0_STORE;
  wire selector_IN_UNBOUNDED_forward_kernel_500073_500104;
  wire selector_MUX_136_reg_0_0_0_0;
  wire selector_MUX_168_reg_5_0_0_0;
  wire selector_MUX_169_reg_6_0_0_0;
  wire selector_MUX_1_BMEMORY_CTRLN_83_i0_1_0_0;
  wire selector_MUX_1_BMEMORY_CTRLN_83_i0_1_0_1;
  wire selector_MUX_1_BMEMORY_CTRLN_83_i0_1_1_0;
  wire wrenable_reg_0;
  wire wrenable_reg_1;
  wire wrenable_reg_10;
  wire wrenable_reg_11;
  wire wrenable_reg_12;
  wire wrenable_reg_13;
  wire wrenable_reg_14;
  wire wrenable_reg_15;
  wire wrenable_reg_16;
  wire wrenable_reg_17;
  wire wrenable_reg_18;
  wire wrenable_reg_19;
  wire wrenable_reg_2;
  wire wrenable_reg_20;
  wire wrenable_reg_21;
  wire wrenable_reg_22;
  wire wrenable_reg_23;
  wire wrenable_reg_24;
  wire wrenable_reg_25;
  wire wrenable_reg_26;
  wire wrenable_reg_27;
  wire wrenable_reg_28;
  wire wrenable_reg_29;
  wire wrenable_reg_3;
  wire wrenable_reg_30;
  wire wrenable_reg_31;
  wire wrenable_reg_32;
  wire wrenable_reg_33;
  wire wrenable_reg_34;
  wire wrenable_reg_35;
  wire wrenable_reg_36;
  wire wrenable_reg_4;
  wire wrenable_reg_5;
  wire wrenable_reg_6;
  wire wrenable_reg_7;
  wire wrenable_reg_8;
  wire wrenable_reg_9;
  
  controller_forward_kernel Controller_i (.done_port(done_delayed_REG_signal_in),
    .fuselector_BMEMORY_CTRLN_83_i0_LOAD(fuselector_BMEMORY_CTRLN_83_i0_LOAD),
    .fuselector_BMEMORY_CTRLN_83_i0_STORE(fuselector_BMEMORY_CTRLN_83_i0_STORE),
    .selector_IN_UNBOUNDED_forward_kernel_500073_500104(selector_IN_UNBOUNDED_forward_kernel_500073_500104),
    .selector_MUX_136_reg_0_0_0_0(selector_MUX_136_reg_0_0_0_0),
    .selector_MUX_168_reg_5_0_0_0(selector_MUX_168_reg_5_0_0_0),
    .selector_MUX_169_reg_6_0_0_0(selector_MUX_169_reg_6_0_0_0),
    .selector_MUX_1_BMEMORY_CTRLN_83_i0_1_0_0(selector_MUX_1_BMEMORY_CTRLN_83_i0_1_0_0),
    .selector_MUX_1_BMEMORY_CTRLN_83_i0_1_0_1(selector_MUX_1_BMEMORY_CTRLN_83_i0_1_0_1),
    .selector_MUX_1_BMEMORY_CTRLN_83_i0_1_1_0(selector_MUX_1_BMEMORY_CTRLN_83_i0_1_1_0),
    .wrenable_reg_0(wrenable_reg_0),
    .wrenable_reg_1(wrenable_reg_1),
    .wrenable_reg_10(wrenable_reg_10),
    .wrenable_reg_11(wrenable_reg_11),
    .wrenable_reg_12(wrenable_reg_12),
    .wrenable_reg_13(wrenable_reg_13),
    .wrenable_reg_14(wrenable_reg_14),
    .wrenable_reg_15(wrenable_reg_15),
    .wrenable_reg_16(wrenable_reg_16),
    .wrenable_reg_17(wrenable_reg_17),
    .wrenable_reg_18(wrenable_reg_18),
    .wrenable_reg_19(wrenable_reg_19),
    .wrenable_reg_2(wrenable_reg_2),
    .wrenable_reg_20(wrenable_reg_20),
    .wrenable_reg_21(wrenable_reg_21),
    .wrenable_reg_22(wrenable_reg_22),
    .wrenable_reg_23(wrenable_reg_23),
    .wrenable_reg_24(wrenable_reg_24),
    .wrenable_reg_25(wrenable_reg_25),
    .wrenable_reg_26(wrenable_reg_26),
    .wrenable_reg_27(wrenable_reg_27),
    .wrenable_reg_28(wrenable_reg_28),
    .wrenable_reg_29(wrenable_reg_29),
    .wrenable_reg_3(wrenable_reg_3),
    .wrenable_reg_30(wrenable_reg_30),
    .wrenable_reg_31(wrenable_reg_31),
    .wrenable_reg_32(wrenable_reg_32),
    .wrenable_reg_33(wrenable_reg_33),
    .wrenable_reg_34(wrenable_reg_34),
    .wrenable_reg_35(wrenable_reg_35),
    .wrenable_reg_36(wrenable_reg_36),
    .wrenable_reg_4(wrenable_reg_4),
    .wrenable_reg_5(wrenable_reg_5),
    .wrenable_reg_6(wrenable_reg_6),
    .wrenable_reg_7(wrenable_reg_7),
    .wrenable_reg_8(wrenable_reg_8),
    .wrenable_reg_9(wrenable_reg_9),
    .OUT_MULTIIF_forward_kernel_500073_503980(OUT_MULTIIF_forward_kernel_500073_503980),
    .OUT_UNBOUNDED_forward_kernel_500073_500104(OUT_UNBOUNDED_forward_kernel_500073_500104),
    .clock(clock),
    .reset(reset),
    .start_port(start_port));
  datapath_forward_kernel Datapath_i (.Mout_oe_ram(Mout_oe_ram),
    .Mout_we_ram(Mout_we_ram),
    .Mout_addr_ram(Mout_addr_ram),
    .Mout_Wdata_ram(Mout_Wdata_ram),
    .Mout_data_ram_size(Mout_data_ram_size),
    .OUT_MULTIIF_forward_kernel_500073_503980(OUT_MULTIIF_forward_kernel_500073_503980),
    .OUT_UNBOUNDED_forward_kernel_500073_500104(OUT_UNBOUNDED_forward_kernel_500073_500104),
    .clock(clock),
    .reset(reset),
    .in_port_P0(P0),
    .in_port_P1(P1),
    .in_port_P2(P2),
    .M_Rdata_ram(M_Rdata_ram),
    .M_DataRdy(M_DataRdy),
    .Min_oe_ram(Min_oe_ram),
    .Min_we_ram(Min_we_ram),
    .Min_addr_ram(Min_addr_ram),
    .Min_Wdata_ram(Min_Wdata_ram),
    .Min_data_ram_size(Min_data_ram_size),
    .fuselector_BMEMORY_CTRLN_83_i0_LOAD(fuselector_BMEMORY_CTRLN_83_i0_LOAD),
    .fuselector_BMEMORY_CTRLN_83_i0_STORE(fuselector_BMEMORY_CTRLN_83_i0_STORE),
    .selector_IN_UNBOUNDED_forward_kernel_500073_500104(selector_IN_UNBOUNDED_forward_kernel_500073_500104),
    .selector_MUX_136_reg_0_0_0_0(selector_MUX_136_reg_0_0_0_0),
    .selector_MUX_168_reg_5_0_0_0(selector_MUX_168_reg_5_0_0_0),
    .selector_MUX_169_reg_6_0_0_0(selector_MUX_169_reg_6_0_0_0),
    .selector_MUX_1_BMEMORY_CTRLN_83_i0_1_0_0(selector_MUX_1_BMEMORY_CTRLN_83_i0_1_0_0),
    .selector_MUX_1_BMEMORY_CTRLN_83_i0_1_0_1(selector_MUX_1_BMEMORY_CTRLN_83_i0_1_0_1),
    .selector_MUX_1_BMEMORY_CTRLN_83_i0_1_1_0(selector_MUX_1_BMEMORY_CTRLN_83_i0_1_1_0),
    .wrenable_reg_0(wrenable_reg_0),
    .wrenable_reg_1(wrenable_reg_1),
    .wrenable_reg_10(wrenable_reg_10),
    .wrenable_reg_11(wrenable_reg_11),
    .wrenable_reg_12(wrenable_reg_12),
    .wrenable_reg_13(wrenable_reg_13),
    .wrenable_reg_14(wrenable_reg_14),
    .wrenable_reg_15(wrenable_reg_15),
    .wrenable_reg_16(wrenable_reg_16),
    .wrenable_reg_17(wrenable_reg_17),
    .wrenable_reg_18(wrenable_reg_18),
    .wrenable_reg_19(wrenable_reg_19),
    .wrenable_reg_2(wrenable_reg_2),
    .wrenable_reg_20(wrenable_reg_20),
    .wrenable_reg_21(wrenable_reg_21),
    .wrenable_reg_22(wrenable_reg_22),
    .wrenable_reg_23(wrenable_reg_23),
    .wrenable_reg_24(wrenable_reg_24),
    .wrenable_reg_25(wrenable_reg_25),
    .wrenable_reg_26(wrenable_reg_26),
    .wrenable_reg_27(wrenable_reg_27),
    .wrenable_reg_28(wrenable_reg_28),
    .wrenable_reg_29(wrenable_reg_29),
    .wrenable_reg_3(wrenable_reg_3),
    .wrenable_reg_30(wrenable_reg_30),
    .wrenable_reg_31(wrenable_reg_31),
    .wrenable_reg_32(wrenable_reg_32),
    .wrenable_reg_33(wrenable_reg_33),
    .wrenable_reg_34(wrenable_reg_34),
    .wrenable_reg_35(wrenable_reg_35),
    .wrenable_reg_36(wrenable_reg_36),
    .wrenable_reg_4(wrenable_reg_4),
    .wrenable_reg_5(wrenable_reg_5),
    .wrenable_reg_6(wrenable_reg_6),
    .wrenable_reg_7(wrenable_reg_7),
    .wrenable_reg_8(wrenable_reg_8),
    .wrenable_reg_9(wrenable_reg_9));
  flipflop_AR #(.BITSIZE_in1(1),
    .BITSIZE_out1(1)) done_delayed_REG (.out1(done_delayed_REG_signal_out),
    .clock(clock),
    .reset(reset),
    .in1(done_delayed_REG_signal_in));
  // io-signal post fix
  assign done_port = done_delayed_REG_signal_out;

endmodule

// Minimal interface for function: forward_kernel
// This component has been derived from the input source code and so it does not fall under the copyright of PandA framework, but it follows the input source code copyright, and may be aggregated with components of the BAMBU/PANDA IP LIBRARY.
// Author(s): Component automatically generated by bambu
// License: THIS COMPONENT IS PROVIDED "AS IS" AND WITHOUT ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, WITHOUT LIMITATION, THE IMPLIED WARRANTIES OF MERCHANTIBILITY AND FITNESS FOR A PARTICULAR PURPOSE.
`timescale 1ns / 1ps
module forward_kernel(clock,
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
  // Component and signal declarations
  
  _forward_kernel _forward_kernel_i0 (.done_port(done_port),
    .Mout_oe_ram(Mout_oe_ram),
    .Mout_we_ram(Mout_we_ram),
    .Mout_addr_ram(Mout_addr_ram),
    .Mout_Wdata_ram(Mout_Wdata_ram),
    .Mout_data_ram_size(Mout_data_ram_size),
    .clock(clock),
    .reset(reset),
    .start_port(start_port),
    .P0(P0),
    .P1(P1),
    .P2(P2),
    .M_Rdata_ram(M_Rdata_ram),
    .M_DataRdy(M_DataRdy),
    .Min_oe_ram({1'b0,
      1'b0}),
    .Min_we_ram({1'b0,
      1'b0}),
    .Min_addr_ram({32'b00000000000000000000000000000000,
      32'b00000000000000000000000000000000}),
    .Min_Wdata_ram({32'b00000000000000000000000000000000,
      32'b00000000000000000000000000000000}),
    .Min_data_ram_size({6'b000000,
      6'b000000}));

endmodule


