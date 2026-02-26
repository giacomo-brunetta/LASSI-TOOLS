#include <memory>

#include <verilated.h>

#if VM_TRACE
#include <verilated_vcd_c.h>
#define _dtos(str) #str
#define VCD_OUT_FILENAME(dir, stem) _dtos(dir) "/" stem
#endif

#include "Vbambu_testbench.h"


static vluint64_t CLOCK_PERIOD = 2;
static vluint64_t HALF_CLOCK_PERIOD = CLOCK_PERIOD/2;

vluint64_t main_time = 0;

double sc_time_stamp ()  {return main_time;}

int main (int argc, char **argv, char **env)
{
   Verilated::commandArgs(argc, argv);
   Verilated::debug(0);
   const std::unique_ptr<Vbambu_testbench> top{new Vbambu_testbench{"clocked_bambu_testbench"}};
   
   main_time=0;
   #if VM_TRACE
   Verilated::traceEverOn(true);
   const std::unique_ptr<VerilatedVcdC> tfp{new VerilatedVcdC};
   top->trace (tfp.get(), 99);
   tfp->set_time_unit("p");
   tfp->set_time_resolution("p");
   tfp->open(VCD_OUT_FILENAME(VCD_OUT_DIR, "test.vcd"));
   #endif
   top->clock = 1;
   while (!Verilated::gotFinish())
   {
      top->clock = !top->clock;
      top->eval();
      #if VM_TRACE
      tfp->dump (main_time);
      #endif
      main_time += HALF_CLOCK_PERIOD;
   }
   #if VM_TRACE
   tfp->dump (main_time);
   tfp->close();
   #endif
   top->final();
   
   return 0;
}