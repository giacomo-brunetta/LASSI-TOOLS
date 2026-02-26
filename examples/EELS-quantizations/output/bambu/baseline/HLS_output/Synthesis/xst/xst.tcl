set -tmpdir HLS_output/Synthesis/xst
set -xsthdpdir HLS_output/Synthesis/xst
run
-ifn HLS_output/Synthesis/xst/forward_kernel.prj
-ifmt mixed
-ofn HLS_output/Synthesis/xst/forward_kernel
-ofmt NGC
-p xc7z020clg484-1
-top forward_kernel
-optimize_primitives Yes
-opt_mode SPEED
-opt_level 2
-auto_bram_packing Yes
-reduce_control_sets Auto
-register_duplication Yes
-register_balancing Yes
-equivalent_register_removal Yes
-iobuf no
-uc HLS_output/Synthesis/ucf/forward_kernel.xcf
-write_timing_constraints Yes
quit

