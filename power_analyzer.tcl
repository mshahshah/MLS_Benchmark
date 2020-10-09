open_project verilog/project.xpr
update_compile_order -fileset sources_1
open_run synth_1 -name synth_1
report_power -file {verilog/report/rpt_power.xml} -name {rpt_power}