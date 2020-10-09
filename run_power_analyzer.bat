: ==============================================================
: Vivado(TM) HLS - High-Level Synthesis from C, C++ and SystemC v2019.1 (64-bit)
: Copyright 1986-2019 Xilinx, Inc. All Rights Reserved.
: ==============================================================

@echo off
echo CMD : Running Vivado power analyzer
C:/Xilinx/Vivado/2020.1/bin/vivado  -notrace -mode batch -source power_analyzer.tcl >report_power.log || exit $?


