import os,sys, copy,numpy
import argparse, random, glob,pandas, time
print("Welcome! MLS_Benchmark.py is executed")
cur_path = os.getcwd()
sys.path.append(cur_path)

from utils import *
from MLS_Benchmark_tools import *

def getOptions(args=sys.argv[1:]):
    parser = argparse.ArgumentParser(description="Parses command.")
    parser.add_argument("-mode"   , help="To run synthesize." , default='skip')
    parser.add_argument("-clean"  , help="To clean before synthesize" , default='False')
    #parser.add_argument("-v", "--verbose",dest='verbose',action='store_true', help="Verbose mode.")
    options = parser.parse_args(args)
    return options



def run_DSE(cfg, MLS_Benchmark):
    start_time = time.time()
    design_solutions = MLS_Benchmark.run_dse_pragma(options)
    MLS_Benchmark.create_dse_excel_report(design_solutions, sort1_by='exec us', sort2_by='DSP')

# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    start_time = time.time()
    options = getOptions()

    gen_configs = configure_design()
    cfg = gen_configs.create_cfg(options)
    gen_configs.prepare_design(cleaning=options.clean)


    utils = utils(cfg)
    hls_tools = hls_tools(cfg)
    MLS_Benchmark = MLS_Benchmark(cfg)

    run_DSE(cfg, MLS_Benchmark)
