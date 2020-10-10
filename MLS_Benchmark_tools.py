import os, shutil
import csv, time
from shutil import copyfile
import sys, glob, json, random, pickle
import numpy as np
import yaml, random, logging
from datetime import datetime
import subprocess
import pandas as pd
import pprint
import xml.etree.ElementTree as ET
from utils import *
import subprocess
from subprocess import TimeoutExpired
from func_timeout import func_timeout, FunctionTimedOut

import psutil, os

def kill_proc_tree(pid, including_parent=True):
    parent = psutil.Process(pid)
    children = parent.children(recursive=True)
    for child in children:
        child.kill()
    gone, still_alive = psutil.wait_procs(children, timeout=5)
    if including_parent:
        parent.kill()
        parent.wait(5)


def run_hls_syn(timeout, version, sol):
    if version == 'vitis':
        command = "vitis_hls -f run_hls_syn.tcl {} > syn_report.log".format(sol)
    else:
        command = "vivado_hls -f run_hls_syn.tcl {} > syn_report.log".format(sol)
    proc = subprocess.Popen(command, shell=True)
    try:
        outs, errs = proc.communicate(timeout=timeout)
        beep('syn')
        return True
    except TimeoutExpired:
        print("PYTHON: SYN STOPPED: The Synthesize could not complete within {} seconds !".format(timeout))
        kill_proc_tree(proc.pid, False)
        outs, errs = proc.communicate()
        beep('failed')
        return False



class utils():
    def __init__(self,cfg):
        self.hello=0
        self.cfg = cfg
    def record_time(self):
        return time.time()

    def end_and_print_time(self,start_time):
        syn_time = time.time() - start_time
        min, sec = divmod(syn_time, 60)
        #print("PYTHON : Total synthesis time : {:3d} Minutes and {:2d} Seconds".format(int(min), int(sec)))
        return [int(min), int(sec)]

    def end_and_print_time_and_label(self,start_time, label):
        syn_time = time.time() - start_time
        min, sec = divmod(syn_time, 60)
        if min == 0 and sec < 1:
            print("TIME : {} in {:3d}M : {:2d}S : {:5.2f}mS ".format(label, int(min), int(sec), float(syn_time*1000)))
        else:
            print("TIME : {} in {:3d}M : {:2d}S".format(label, int(min), int(sec)))
        return round(min), round(sec)

    def save_a_variable(self,fname,variable):
        with open(os.path.join(self.cfg.paths.dse_report,'{}.pickle'.format(fname)), 'wb') as f:
            pickle.dump(variable, f)

    def load_a_variable(self,variable_name):
        with open(os.path.join(self.cfg.paths.dse_report,'{}.pickle'.format(variable_name)), 'rb') as f:
            variable = pickle.load(f)
        return variable

    def save_list_to_file(self,filename,data):
        with open(filename, 'w') as f:
            for line in data:
                f.write("%s\n" % line)

    def load_file_to_list(self,filename):
        with open(filename, 'r') as reader:
            return reader.readlines()


class configure_design:
    def __init__(self):
        self.hello=0

    def create_cfg(self,options):
        cfg={}
        self.options = options
        t1 = self.parse_yaml_input_arguments()
        cfg.update(t1)
        self.cfg = Struct(**cfg)

        t2 = self.parse_yaml_design_arguments()
        cfg.update(t2)
        self.cfg = Struct(**cfg)

        cfg['run_options'] = options
        [cfg['paths'], cfg['files']] = self.create_paths()
        # [self.paths, self.files] = self.create_paths()
        self.cfg = Struct(**cfg)
        cfg.update(t1)
        self.cfg = Struct(**cfg)
        return self.cfg

    def parse_yaml_design_arguments(self):
        datamap_dict = {}
        with open('{}/design_cfg.yaml'.format(self.cfg.design_setting.design_model)) as f:
            datamap = yaml.safe_load(f)
            datamap = Struct(**datamap)
            datamap_dict['design'] = Struct(**datamap.design)
            datamap_dict['pragmas'] = {}
            datamap_dict['pragmas']['best'] = datamap.best_pragma_list
            datamap_dict['pragmas']['base'] = datamap.base_pragma_list
            datamap_dict['pragmas']['minimal'] = datamap.minimal_pragma_list
            datamap_dict['pragmas']['none'] = datamap.none
        return datamap_dict

    def parse_yaml_input_arguments(self):
        datamap_dict={}
        fpga_chips = self.parse_yaml_FPGA_chips()
        temp = {}
        with open('input_arguments.yaml') as f:
            datamap = yaml.safe_load(f)
            datamap = Struct(**datamap)
            datamap_dict['design_setting'] = Struct(**datamap.design_setting)
            #
        if datamap.FPGA['chip'] in fpga_chips.keys():
            for i in ['DSP', 'BRAM', 'LUT', 'FF', 'part']:
                datamap.FPGA[i] = fpga_chips[datamap.FPGA['chip']][i]
            datamap_dict['FPGA'] = Struct(**datamap.FPGA)
        else:
            IOError('Select a right FPGA chip in input_arguments!')

        return datamap_dict

    def parse_yaml_FPGA_chips(self):
        datamap_dict={}
        with open('fpga_resources.yaml') as f:
            datamap = yaml.safe_load(f)
            #for i in datamap.keys():
            #    datamap_dict[i] = Struct(**datamap[i])
        return datamap

    def create_paths(self):
        paths={}
        files={}
        paths['design_top'] = os.getcwd()
        paths['design_model'] = os.path.join(paths['design_top'], self.cfg.design_setting.design_model)
        paths['hls'] = os.path.join(paths['design_model'], 'hls')
        paths['solution'] = os.path.join(paths['hls'], self.cfg.design_setting.solution_name)
        paths['directive_list'] = os.path.join(paths['design_model'], 'directive_list')
        paths['src'] = os.path.join(paths['design_model'], 'src')
        paths['report'] = os.path.join(paths['design_model'], self.cfg.design_setting.dse_name)
        paths['dse_report'] = os.path.join(paths['report'])
        paths['dse_figures'] = os.path.join(paths['dse_report'],  'figures')
        files['synLogFile'] = os.path.join(paths['solution'] , '{}.log'.format(self.cfg.design_setting.solution_name))
        files['SolutionFile'] = os.path.join(paths['solution'], '{}_data.json'.format(self.cfg.design_setting.solution_name))
        files['DirectiveFile'] = os.path.join(paths['solution'], 'directives.tcl')
        files['user_defined_arguments'] = os.path.join( 'input_arguments.yaml')
        files['user_defined_layers'] = os.path.join(paths['src'],'user_defined_layers.yaml')
        self.paths = Struct(**paths)
        self.files = Struct(**files)
        return Struct(**paths) , Struct(**files)

    def copy_design_source_files(self,extensions):
        for extension in extensions:
            files = glob.iglob(os.path.join(self.paths.src, '*.{}'.format(extension)))
            for file in files:
                if os.path.isfile(file):
                    shutil.copy(file, self.paths.design_model)

    def prepare_design(self, cleaning = False):
        if self.options.mode in ['','syn_report', 'dse_pragma_report','dse_dtype_report','dse_clock_report']:
            return
        elif self.options.mode in ['dse_pragma','dse_clock', 'syn','dse_dtype']:
            if self.cfg.design_setting.run_vivado_power_analyzer: #force vivado synthesizer if power is asked
                self.cfg.design_setting.run_vivado_synthesize = True

            if os.path.exists(self.cfg.paths.solution):
                shutil.rmtree(self.cfg.paths.solution)
                os.makedirs(self.cfg.paths.solution)
            else:
                os.makedirs(self.cfg.paths.solution)

            if self.options.mode not in ['syn']:
                if os.path.exists(self.cfg.paths.dse_report):
                    print("PYTHON : The report folder exist. Do you want to remove previous work? (yes/no) ")
                    #if input().lower() == 'yes':
                    shutil.rmtree(self.cfg.paths.dse_report)
                    os.makedirs(self.cfg.paths.dse_report)
                else:
                    os.makedirs(self.cfg.paths.dse_report)





class hls_tools():
    def __init__(self, cfg):
        self.cfg = cfg
        self.utils = utils(cfg)
        #self.module['MOPS'] = {}

    def create_syn_tcl_file(self, clock_period):
        tcl_lines = []
        tcl_lines.append("############################################################")
        tcl_lines.append("## This file is generated automatically by python tool")
        tcl_lines.append("############################################################")
        tcl_lines.append('puts \"CMD : run_hls_syn.tcl is running!\"')
        tcl_lines.append('open_project hls')
        tcl_lines.append('set_top   {}'.format(self.cfg.design.top_function))
        for file in self.cfg.design.source_files:
            tcl_lines.append('add_files  src/{}'.format(file))

        for file in self.cfg.design.tb_files:
            tcl_lines.append('add_files  -tb src/{}'.format(file))
        if self.cfg.design_setting.vivado_version == 'vitis':
            tcl_lines.append('open_solution -reset \"{}\"  -flow_target vivado'.format(self.cfg.design_setting.solution_name))
            tcl_lines.append('set_part {' + self.cfg.FPGA.part + '}')
        else:
            tcl_lines.append('open_solution -reset \"{}\"'.format(self.cfg.design_setting.solution_name))
            tcl_lines.append('set_part {' + self.cfg.FPGA.part + '} -tool vivado')
        tcl_lines.append('create_clock -period {} -name default'.format(clock_period))
        tcl_lines.append('set_clock_uncertainty 12.5%')
        tcl_lines.append('source \"./hls/{}/directives.tcl\"'.format(self.cfg.design_setting.solution_name))

        tcl_lines.append('csynth_design')
        if self.cfg.design_setting.run_vivado_synthesize:
            tcl_lines.append('export_design -flow syn -rtl verilog -format ip_catalog')

        tcl_lines.append('quit')
        filename = os.path.join(self.cfg.paths.design_model, "run_hls_syn.tcl")
        self.utils.save_list_to_file(filename, tcl_lines)




    def run_power_analyzer(self, sol_counter, mode, print_out='silent', clean=False):
        if not self.cfg.design_setting.run_vivado_power_analyzer:
            return {'LUT_PS': 'NP', 'FF_PS': 'NP', 'DSP_PS': 'NP', 'BRAM_PS': 'NP', 'Timing_PS': 'NF','power': 'NP'}

        dest_path = self.cfg.paths.solution

        if not os.path.exists(os.path.join(dest_path, 'impl')):
            return 'Er'
        start_time = self.utils.record_time()
        impl_file = ['power_analyzer.tcl',
                     'run_power_analyzer.bat']
        for fname in impl_file:
            srcfile = os.path.join(self.cfg.paths.design_top, fname)
            destfile = os.path.join(dest_path, 'impl', fname)
            shutil.copyfile(srcfile, destfile)
        os.chdir(os.path.join(dest_path, 'impl'))

        if sys.platform == 'win32':
            print("PYTHON : implementation begins from python on Windows")
            sr = os.system('run_power_analyzer.bat')
        elif sys.platform == 'linux':
            print("PYTHON : implementation begins from python on Linux")
            command = "/home/eng/m/mxs161831/Desktop/dnn_small/run_hls_synthesis.sh {} {}".format(mode, print_out)
        #            sr = subprocess.call(command, shell=True)
        else:
            print("PYTHON : Wrong operating system selection")

        if (sr != 0):
            print("PYTHON : run_power_analyzer file not found, or a problem in bash file!")
            return 'Er'

        [mm, ss] = self.utils.end_and_print_time(start_time)

        os.chdir(self.cfg.paths.design_top)
        print("PYTHON : Power measured in Vivado  - Total implementation time : {:3d} Minutes and {:2d} Seconds".format(int(mm), int(ss)))
        return self.read_impl_results(dest_path)


    def run_hls_synth(self, mode, print_out='silent', clean=False, sol=0):
        if mode in ['', 'skip', 'syn_report', 'dse_report']:
            print("PYTHON : Synthesize Skipped\n")
            return True

        if clean:
            self.utils.cleanSolution()

        start_time = self.utils.record_time()

        if sys.platform == 'win32':
            print("PYTHON : Synthesis begins from python on Windows")
            if self.cfg.design_setting.vivado_version == 'vitis':
                sr = os.system("run_vitis_hls_synthesis.bat {} {}".format(self.cfg.design_setting.design_model, print_out))
            else:
                sr = os.system("run_vivado_hls_synthesis.bat {} {}".format(self.cfg.design_setting.design_model, print_out))
        elif sys.platform == 'linux':
            print("PYTHON : Synthesis begins from python on Linux")
            command = "/home/eng/m/mxs161831/Desktop/dnn_small/run_hls_synthesis.sh {} {}".format(mode, print_out)
            sr = subprocess.call(command, shell=True)
        else:
            print("PYTHON : Wrong operating system selection")

        [mm, ss] = self.utils.end_and_print_time(start_time)

        if (sr != 0):
            print("PYTHON : Synthesis file not found, or a problem in bash file!")
            return False

        errors = self.utils.find_Aword_in_file(self.cfg.files.synLogFile, 'error', save_results=False)
        warning = self.utils.find_Aword_in_file(self.cfg.files.synLogFile, 'warning', save_results=True)
        if errors != 0:
            print("PYTHON : *** Synthesize Failed ***  - Total synthesis time : {:3d} Minutes and {:2d} Seconds".format(
                int(mm), int(ss)))
            copyfile(self.cfg.files.synLogFile,
                     os.path.join(self.cfg.paths.solution, "failed_syn_log_sol{}.log".format(sol)))
            return False
        else:
            print("PYTHON : *** Synthesize Passed ***  - Total synthesis time : {:3d} Minutes and {:2d} Seconds".format(
                int(mm), int(ss)))
            return True


    def read_design_pragmas(self, fname):
        fname = os.path.join(self.cfg.paths.src, fname)
        with open(fname) as f:
            datamap = yaml.safe_load(f)

        design_pragmas = Struct(**datamap)
        return datamap


    def read_impl_results(self, sol_path):
        try:
            power_rptFile = os.path.join(sol_path, 'impl', 'verilog', 'report', 'rpt_power.xml')
            power_rpt = pd.read_fwf(power_rptFile, skiprows=list(range(31)), nrows=45 - 31 - 1)
            power = power_rpt.T[0].values[0].split()[-2]
        except:
            power = 'NF'

        try:
            utilization_rptFile = os.path.join(sol_path, 'impl', 'report', 'verilog', '{}_export.xml'.format(self.cfg.design.top_function))
            tree = ET.parse(utilization_rptFile)
            root = tree.getroot()
            PR_results = {i.tag+'_PS': i.text for i in root[0][0]}
            PR_results['Timing_PS'] = root[1][1].text
            PR_results['power'] = power
            PR_results.pop('SLICE_PS')
            PR_results.pop('SRL_PS')
            print('Post Syn hardware utilization : ', PR_results)
        except:
            PR_results = {'LUT_PS': 'NF', 'FF_PS': 'NF', 'DSP_PS': 'NF', 'BRAM_PS': 'NF', 'Timing_PS':'NF','power': 'NF'}


        return  PR_results




    def read_parallel_syn_results(self, solution_num, syn_exec_time, print_out=False):
        file = os.path.join(self.cfg.paths.design_model,'hls', self.cfg.design_setting.solution_name,
                                '{}_data.json'.format(self.cfg.design_setting.solution_name))
        try:
            with open(file) as json_file:
                json_data = json.load(json_file)
                if self.cfg.design_setting.vivado_version == 'vitis':
                    passed_sol = self.extract_hls_json_info_vitis(json_data)
                else:
                    passed_sol = self.extract_hls_json_info(json_data)
                model_layers_name = passed_sol.keys()
                passed_sol['solution'] = solution_num
                passed_sol['syn_status'] = 'passed'
                passed_sol['syn_time'] = '{:3d}:{:2d}'.format(syn_exec_time[0], syn_exec_time[1])
                json_file.close()
                if print_out:
                    pprint.pprint(passed_sol[self.cfg.design.top_function], depth=5)

        except IOError:
            passed_sol = {}
            passed_sol['solution'] = solution_num
            passed_sol['syn_status'] = 'failed'
            passed_sol['syn_time'] = '{:3d}:{:2d}'.format(syn_exec_time[0], syn_exec_time[1])
            print("PYTHON : can't open {} file. Synthesize failed".format(file))
        return passed_sol, model_layers_name

    def read_single_syn_results(self, solution_num, syn_exec_time, print_out=False):
        try:
            with open(self.cfg.files.SolutionFile) as json_file:
                json_data = json.load(json_file)
                if self.cfg.design_setting.vivado_version == 'vitis':
                    passed_sol = self.extract_hls_json_info_vitis(json_data)
                else:
                    passed_sol = self.extract_hls_json_info(json_data)
                model_layers_name = list(passed_sol.keys())
                passed_sol['solution'] = solution_num
                passed_sol['syn_status'] = 'passed'
                passed_sol['syn_time'] = '{:3d}:{:2d}'.format(syn_exec_time[0], syn_exec_time[1])
                json_file.close()
                if print_out:
                    pprint.pprint(passed_sol[self.cfg.design_setting.topmodule], depth=5)

        except IOError:
            print("PYTHON : can't open {} file".format(self.cfg.files.SolutionFile))
            passed_sol = {}
            passed_sol['solution'] = solution_num
            passed_sol['syn_status'] = 'failed'
            passed_sol['syn_time'] = '{:3d}:{:2d}'.format(syn_exec_time[0], syn_exec_time[1])
        return passed_sol, model_layers_name

    def extract_hls_json_info(self, json_data):
        syn_rslt_summary = {}
        keys = ['Area', 'Latency']
        temp = json_data["ModuleInfo"]["Metrics"]
        topmodule = self.cfg.design_setting.topmodule
        for p_id, p_info in temp.items():
            syn_rslt_summary[p_id] = {}
            # print("\nModule name:", p_id)
            for key in p_info:
                if key == "Area" and key in keys:
                    a = syn_rslt_summary[p_id]['BRAM %'] = str(
                        round(int(temp[p_id][key]["BRAM_18K"]) / self.cfg.FPGA.BRAM * 100, 2))
                    syn_rslt_summary[p_id]['BRAM'] = temp[p_id][key]["BRAM_18K"]
                    b = syn_rslt_summary[p_id]['LUT %'] = str(
                        round(int(temp[p_id][key]["LUT"]) / self.cfg.FPGA.LUT * 100, 2))
                    syn_rslt_summary[p_id]['LUT'] = temp[p_id][key]["LUT"]
                    c = syn_rslt_summary[p_id]['FF %'] = str(round(int(temp[p_id][key]["FF"]) / self.cfg.FPGA.FF * 100, 2))  # ...
                    syn_rslt_summary[p_id]['FF'] = temp[p_id][key]["FF"]
                    syn_rslt_summary[p_id]['DSP'] = temp[p_id][key]["DSP48E"]
                    d = syn_rslt_summary[p_id]['DSP %'] = str(
                        round(int(temp[p_id][key]["DSP48E"]) / self.cfg.FPGA.DSP * 100, 2))
                    syn_rslt_summary[p_id]['Total %'] = str(round(
                        (float(a) + float(b) + float(c) + float(d)) / 4, 2))
                elif key == "Latency" and key in keys:
                    syn_rslt_summary[p_id]['latency'] = str(temp[p_id][key]["LatencyWorst"])
                    exec_us = (float(temp[p_id][key]["LatencyWorst"])) * float(temp[p_id]["Timing"]["Target"]) / pow(10, 3)
                    syn_rslt_summary[p_id]['exec us'] = str(round(exec_us, 2))
                    syn_rslt_summary[p_id]['clock period'] = float(temp[p_id]["Timing"]["Target"])
                    syn_rslt_summary[p_id]['Timing'] = float(temp[p_id]["Timing"]["Estimate"])
        return syn_rslt_summary

    def extract_hls_json_info_vitis(self, json_data):
        syn_rslt_summary = {}
        keys = ['Area', 'Latency']
        temp = json_data["ModuleInfo"]["Metrics"]
        topmodule = self.cfg.design.top_function

        for p_id, p_info in temp.items():
            syn_rslt_summary[p_id] = {}
            # print("\nModule name:", p_id)
            for key in p_info:
                if key == "Area" and key in keys:
                    a = syn_rslt_summary[p_id]['BRAM %'] = str(
                        round(int(temp[p_id][key]["BRAM_18K"]) / int(temp[p_id][key]["AVAIL_BRAM"]) * 100, 2))
                    syn_rslt_summary[p_id]['BRAM'] = temp[p_id][key]["BRAM_18K"]
                    b = syn_rslt_summary[p_id]['LUT %'] = str(
                        round(int(temp[p_id][key]["LUT"]) / int(temp[p_id][key]["AVAIL_LUT"]) * 100, 2))
                    syn_rslt_summary[p_id]['LUT'] = temp[p_id][key]["LUT"]
                    c = syn_rslt_summary[p_id]['FF %'] = str(round(int(temp[p_id][key]["FF"]) / int(temp[p_id][key]["AVAIL_FF"]) * 100, 2))  # ...
                    syn_rslt_summary[p_id]['FF'] = temp[p_id][key]["FF"]
                    syn_rslt_summary[p_id]['DSP'] = temp[p_id][key]["DSP"]
                    d = syn_rslt_summary[p_id]['DSP %'] = str(
                        round(int(temp[p_id][key]["DSP"]) / int(temp[p_id][key]["AVAIL_DSP"]) * 100, 2))
                    syn_rslt_summary[p_id]['Total %'] = str(round(
                        (float(a) + float(b) + float(c) + float(d)) / 4, 2))
                elif key == "Latency" and key in keys:
                    LatencyWorst = 0 if str(temp[p_id][key]["LatencyWorst"]) == '' else str(temp[p_id][key]["LatencyWorst"])
                    syn_rslt_summary[p_id]['latency'] = str(LatencyWorst)
                    exec_us = (float(LatencyWorst)) * float(temp[p_id]["Timing"]["Target"]) / pow(10, 3)
                    syn_rslt_summary[p_id]['exec us'] = str(round(exec_us, 2))
                    syn_rslt_summary[p_id]['clock period'] = float(temp[p_id]["Timing"]["Target"])
                    syn_rslt_summary[p_id]['Timing'] = float(temp[p_id]["Timing"]["Estimate"])
        return syn_rslt_summary


    def copy_hls_bc_files(self, syn_path, sol_counter):
        if self.cfg.design_setting.copy_bc_files:
            temp = os.path.join(self.cfg.paths.dse_report, 'hls_syn{}'.format(sol_counter))
            if os.path.exists(temp):
                shutil.rmtree(temp)
            os.makedirs(temp)
            bc_path = os.path.join(syn_path, '.autopilot', 'db')
            for file in glob.iglob(os.path.join(bc_path, 'a.o.3.bc')):
                shutil.copy2(file, temp)
            for file in glob.iglob(os.path.join(bc_path, '*.{}'.format('verbose.bind.rpt'))):
                shutil.copy2(file, temp)
            for file in glob.iglob(os.path.join(bc_path, '*.{}'.format('verbose.rpt'))):
                shutil.copy2(file, temp)


class MLS_Benchmark():
    def __init__(self,cfg):
        self.cfg = cfg
        self.hls_tools = hls_tools(cfg)
        self.utils = utils(cfg)
        with open(os.path.join('{}/compacted_tcl_files.pickle'.format(self.cfg.design_setting.design_model)), 'rb') as f:
            self.listOfDirectives = pickle.load(f)
        self.available_sol = len(self.listOfDirectives)
        self.max_sol = min(self.available_sol, self.cfg.design_setting.solution_counts)




    def read_dse_syn_results(self, syn_exec_time, print_out = False):
        solution_syn_list = []
        for solNum, file in enumerate(glob.glob(self.cfg.paths.directive_list + "/" + "*.json")):
            try:
                with open(file) as json_file:
                    json_data = json.load(json_file)
                    passed_sol = self.extract_hls_json_info(json_data)
                    passed_sol['solution'] = re.findall(r'\w+',file)[-2]
                    passed_sol['syn_status'] = 'passed'
                    passed_sol['syn_time'] = '{:3d}:{:2d}'.format(syn_exec_time[solNum][0],syn_exec_time[solNum][1])
                    solution_syn_list.append(passed_sol)
                    json_file.close()
            except IOError:
                print("PYTHON : can't open {} file".format(file))
        return solution_syn_list

    def load_a_directive_file(self, sol_counter):
        directive_name = 'untimate_new_directive{}.tcl'.format(sol_counter)
        srf_file = os.path.join(self.cfg.paths.directive_list,directive_name)
        shutil.copyfile(srf_file, self.cfg.files.DirectiveFile)

    def load_a_directive_list(self, sol_counter):
        direcitves = self.listOfDirectives[sol_counter]
        self.utils.save_list_to_file(self.cfg.files.DirectiveFile,direcitves)
        return direcitves

    def create_dse_excel_report(self, design_solutions,  sort1_by='latency', sort2_by='DSP'):
        design_solutions_passed = []
        top_function = self.cfg.design.top_function
        for solution in design_solutions:
            if solution['syn_status'] == 'passed':
                design_solutions_passed.append(solution)
        filename = os.path.join(self.cfg.paths.dse_report, "dse_{}.csv".format(top_function))
        sorted_solutions = sorted(design_solutions_passed, key=lambda x: (float(x[top_function][sort1_by]),int(x[top_function][sort2_by])))

        labels_list = list(sorted_solutions[0][self.cfg.design.top_function].keys())
        labels_list2 = ['solution', 'syn_status', 'syn_time', 'power', 'dtype', 'LUT_PS', 'FF_PS', 'DSP_PS', 'BRAM_PS', 'Timing_PS']
        f = open(filename, "w+")
        for item in labels_list2:
            f.write('{},'.format(item))
        for item in labels_list:
            f.write(item + ',')
        f.write('\n')

        for indx, solution in enumerate(sorted_solutions, start=1):
            if solution['syn_status'] == 'failed':
                f.write(str(solution['solution']) + ',')
                f.write(solution['syn_status'] + ',')
                f.write(solution['syn_time'] + ',')
            else:
                for i in labels_list2:
                    f.write(str(solution[i]) + ',')
                for key in labels_list:
                    if key in solution[top_function]:
                        f.write(str(solution[top_function][key]) + ',')
                    else:
                        f.write('NA ,')

            f.write('\n')
        f.close()
        print('\nPYTHON : DSE: Summary of {} {} DSE is created in the report directory!'.format(top_function,indx))

    def collect_all_pickles(self):
        solution_syn_list = []
        for file in glob.iglob(os.path.join(self.cfg.paths.dse_report,'*/*.pickle')):
            variable = pickle.load( open( file, "rb" ) )
            solution_syn_list.append(variable)
        return solution_syn_list

    def updated_timeout_value(self, start_time):
        syn_time = time.time() - start_time
        self.cfg.design_setting.time_out_value = round(syn_time * 2)
        print('The timeout is updated to {}'.format(self.cfg.design_setting.time_out_value))


    def run_dse_pragma(self, options):
        if options.mode == 'dse_pragma_report':
            print("PYTHON : DSE Skipped")
            solution_syn_list = self.collect_all_pickles()

        else:
            solution_syn_list = []
            time_out_value = self.cfg.design_setting.time_out_value
            selected_solutions = np.random.randint(0, self.available_sol, self.max_sol).tolist()

            format = "%(asctime)s: %(message)s"
            logging.basicConfig(format=format, level=logging.INFO, datefmt="%H:%M:%S")
            dt_string = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

            for sol in selected_solutions:
                syn_path = os.path.join(self.cfg.paths.design_model, 'hls', self.cfg.design_setting.solution_name)
                start_time = self.utils.record_time()
                now = datetime.now()
                dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
                print("\nPYTHON : DSE on pragmas: Synthesis of design {} is started at {}.".format(sol, dt_string))
                #self.load_a_directive_file(sol)
                pragmas = self.load_a_directive_list(sol)
                self.hls_tools.create_syn_tcl_file(clock_period=self.cfg.FPGA.clock_period)
                os.chdir(self.cfg.paths.design_model)

                if run_hls_syn(time_out_value, self.cfg.design_setting.vivado_version, sol):
                    [mm, ss] = self.utils.end_and_print_time(start_time)
                    temp, model_layers_name = self.hls_tools.read_parallel_syn_results(sol, [mm, ss], False)
                    print("PYTHON : DSE on pragmas: Synthesis of design {} is finished. Synthesis time : {:3d} Minutes and {:2d} Seconds"
                        .format(sol, mm, ss))

                    postSyn = self.hls_tools.run_power_analyzer(sol, 'syn', print_out='silent', clean=True)

                    self.hls_tools.copy_hls_bc_files(syn_path, sol)

                    os.chdir(self.cfg.paths.design_top)

                    final_rpt = {}
                    final_rpt.update(temp)
                    final_rpt.update(postSyn)
                    final_rpt['dtype'] = '{} bits'.format('NA')
                    final_rpt['pragmas'] = pragmas
                    self.utils.save_a_variable('hls_syn{}/solution_{}'.format(sol,sol), final_rpt)
                    solution_syn_list.append(final_rpt)

                self.updated_timeout_value(start_time)
            [mm, ss] = self.utils.end_and_print_time(start_time)
            print("\nPYTHON : Total synthesis time : {:3d} Minutes and {:2d} Seconds".format(mm, ss))

        self.utils.save_a_variable('dse_pragma_results', solution_syn_list)
        #self.remove_all_synthesize_results(total_dse_solutions)
        return solution_syn_list



print("PYTHON : hls_tools is imported")