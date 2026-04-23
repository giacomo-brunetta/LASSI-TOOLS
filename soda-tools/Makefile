# Reusable SODA/Bambu synthesis driver.
#
# Typical usage from a model directory:
#   make -f /home/gbrun/LASSI-TOOLS/soda-tools/Makefile
#
# Override inputs as needed:
#   make -f /home/gbrun/LASSI-TOOLS/soda-tools/Makefile \
#     FILE_PATH=/path/to/torchscript.py \
#     TRANSFORM_PATH=/path/to/transform.mlir \
#     ODIR=/path/to/output \
#     BUILD_MODE=transformed \
#     STOP_STAGE=bambu-verilog

SODA_ROOT ?= /home/gbrun/soda-benchmarks
TOOLS_ROOT := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))
SCRIPTS_DIR := $(TOOLS_ROOT)/scripts

FILE_PATH ?= $(CURDIR)/torchscript.py
TRANSFORM_PATH ?= $(CURDIR)/transform.mlir
ODIR ?= $(CURDIR)/output

# Valid STOP_STAGE values:
#   tosa
#   linalg
#   llvm-mlir
#   llvm-ll
#   llvm-mode-mlir
#   llvm-mode-ll
#   bambu-verilog
#   bambu-sim
#
# Valid BUILD_MODE values:
#   baseline
#   optimized
#   transformed
BUILD_MODE ?= transformed
STOP_STAGE ?= bambu-verilog

ifeq ($(STOP_STAGE),tosa)
TARGET := $(ODIR)/01_tosa.mlir
else ifeq ($(STOP_STAGE),linalg)
TARGET := $(ODIR)/02_linalg.mlir
else ifeq ($(STOP_STAGE),llvm-mlir)
TARGET := $(ODIR)/03_llvm.mlir
else ifeq ($(STOP_STAGE),llvm-ll)
TARGET := $(ODIR)/04_llvm.ll
else ifeq ($(STOP_STAGE),llvm-mode-mlir)
TARGET := $(ODIR)/04_llvm_$(BUILD_MODE).mlir
else ifeq ($(STOP_STAGE),llvm-mode-ll)
TARGET := $(ODIR)/05_llvm_$(BUILD_MODE).ll
else ifeq ($(STOP_STAGE),bambu-verilog)
TARGET := $(ODIR)/bambu/$(BUILD_MODE)/06_verilog.v
else ifeq ($(STOP_STAGE),bambu-sim)
TARGET := $(ODIR)/bambu/$(BUILD_MODE)/07_results.txt
else
$(error Unsupported STOP_STAGE '$(STOP_STAGE)')
endif

ifneq ($(filter $(BUILD_MODE),baseline optimized transformed),$(BUILD_MODE))
$(error Unsupported BUILD_MODE '$(BUILD_MODE)')
endif

all: $(TARGET)

$(ODIR)/01_tosa.mlir: $(FILE_PATH)
	python $(FILE_PATH) $@ --dialect=tosa

$(ODIR)/04_transform_sched.mlir: $(TRANSFORM_PATH)
	cp $< $@

BAMBU_DEVICE ?= asap7-BC
BAMBU_CLOCK_PERIOD ?= 5

include $(SCRIPTS_DIR)/mkinc/tosa_to_llvm.mk
include $(SCRIPTS_DIR)/mkinc/soda_to_llvm.mk
include $(SCRIPTS_DIR)/mkinc/llvm_to_verilog.mk
