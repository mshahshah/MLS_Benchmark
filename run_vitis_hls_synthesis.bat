@echo off
set arg1=%1
set arg2=%2
echo CMD : Calling Vitis HLS, "%arg1%" and "%arg2%" are the input arguments

if [%arg1%]==[] (
echo no option is selected
echo enter 'dse' or 'syn' as an option
echo CMD : Synthesize failed!
goto END_OF_PROCESS
)


set PATH=%~dp0;%PATH%
cd %arg1%


set AUTOESL_HOME=%~dp0..
set VIVADO_HLS_HOME=%~dp0..
set RDI_OS_ARCH=32
if [%PROCESSOR_ARCHITECTURE%] == [x86] (
  if defined PROCESSOR_ARCHITEW6432 (
    set RDI_OS_ARCH=64
  )
) else (
  if defined PROCESSOR_ARCHITECTURE (
    set RDI_OS_ARCH=64
  )
)

if not "%RDI_OS_ARCH%" == "64" goto _NotX64
set COMSPEC=%WINDIR%\SysWOW64\cmd.exe

if [%arg2%]==[silent] (
vitis_hls -f run_hls_syn.tcl > synthesis_report.txt
) else  (
vitis_hls -f run_hls_syn.tcl )

%COMSPEC% 


goto END_OF_PROCESS

:_NotX64
set COMSPEC=%WINDIR%\System32\cmd.exe
rem %COMSPEC% /c %0 %1 %2 %3 %4 %5 %6 %7 %8 %9 
vitis_hls -f %arg1%/run_hls_syn.tcl
%COMSPEC% 



:END_OF_PROCESS
echo CMD : =============   Synthesis done =====================
echo

:EOF


