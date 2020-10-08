import os, shutil
import csv, time
from shutil import copyfile
import sys, glob, json, random, pickle
import numpy as np
import yaml, random
import subprocess
from dnn_tools import *
import pandas as pd
import pprint
import xml.etree.ElementTree as ET


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
        t3 = {}
        t3['analyze_results'] = {}
        cfg.update(t3)
        self.cfg = Struct(**cfg)
        return self.cfg

    def parse_yaml_design_arguments(self):
        datamap_dict = {}
        with open('src/{}.yaml'.format(self.cfg.design_setting.design_model)) as f:
            datamap = yaml.safe_load(f)
            datamap = Struct(**datamap)
            datamap_dict['design'] = Struct(**datamap.design)
            datamap_dict['design_layers'] = datamap.design_layers
            datamap_dict['design_variable_types'] = datamap.design_variable_types
            datamap_dict['pragmas'] = {}
            datamap_dict['pragmas']['variable'] = datamap.pragmas
            datamap_dict['pragmas']['custom'] = datamap.custom_pragma_list
            datamap_dict['pragmas']['best'] = datamap.best_pragma_list
            datamap_dict['pragmas']['base'] = datamap.base_pragma_list
            datamap_dict['pragmas']['minimal'] = datamap.minimal_pragma_list
            datamap_dict['pragmas']['none'] = datamap.none
            datamap_dict['interface'] = datamap.interface
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
        paths['python'] = os.path.join(paths['design_top'], 'dnn_python')
        paths['hls'] = os.path.join(paths['design_model'], 'hls')
        paths['solution'] = os.path.join(paths['hls'], self.cfg.design_setting.solution_name)
        paths['directive_list'] = os.path.join(paths['design_model'], self.cfg.design_setting.solution_name + '_sol_list')
        paths['hw'] = os.path.join(paths['design_model'], 'dnn_hw')
        paths['src'] = os.path.join(paths['design_top'], 'src')
        paths['test_data'] = os.path.join(paths['design_top'], 'test_data')
        paths['dse'] = os.path.join(paths['design_model'], 'dnn_DSE')
        paths['report'] = os.path.join(paths['design_model'], 'reports')
        paths['test_files'] = os.path.join(paths['design_model'], 'test_files')
        paths['ml_dataset'] = os.path.join(paths['design_top'], 'training_dataset')
        #paths['dse_report'] = os.path.join(paths['report'], self.cfg.design_setting.DSE_setting['dse_name'])
        mode = '_'.join(self.options.mode.split('_')[0:2])
        if mode == 'syn':
            rpt_path_name = 'syn'
        elif mode in ['dse_pragma', 'dse_universal']:
            rpt_path_name = mode+ str(self.cfg.design_setting.DSE_setting['solution_counts']) +\
                            self.cfg.design_setting.DSE_setting['directive_selection'] +\
                            '_' + self.cfg.design_setting.DSE_setting['dse_name']
        elif mode in ['dse_clock', 'dse_dtype', 'dse_cfg']:
            rpt_path_name = mode + '_' + self.cfg.design_setting.syn_directive_type +\
                '_' + self.cfg.design_setting.DSE_setting['dse_name']
        else:
            rpt_path_name = 'unknown_report'

        paths['dse_report'] = os.path.join(paths['report'], rpt_path_name)
        paths['dse_figures'] = os.path.join(paths['dse_report'],  'figures')
        paths['dnn_weights'] = os.path.join(paths['design_model'], 'dnn_weights')
        files['synLogFile'] = os.path.join(paths['solution'] , '{}.log'.format(self.cfg.design_setting.solution_name))
        files['SolutionFile'] = os.path.join(paths['solution'], '{}_data.json'.format(self.cfg.design_setting.solution_name))
        files['DirectiveFile'] = os.path.join(paths['solution'], 'directives.tcl')
        files['TopModuleRptFile'] = os.path.join(paths['solution'],'syn','report','{}_csynth.rpt'.format(self.cfg.design_setting.topmodule))
        files['user_defined_arguments'] = os.path.join( 'input_arguments.yaml')
        files['user_defined_layers'] = os.path.join(paths['src'],'user_defined_layers.yaml')
        files['dnn_cfg_cppfile'] = os.path.join(paths['design_model'], 'dnn_configs.h')
        files['dnn_main_cppfile'] = os.path.join(paths['design_model'], 'top.cpp')
        files['dnn_main_hfile'] = os.path.join(paths['design_model'], 'top.h')

        files['trained_model_weights_float'] = os.path.join(paths['dnn_weights'], 'model_weights_float')
        files['trained_model_weights_fixed'] = os.path.join(paths['dnn_weights'], 'model_weights_fixed')
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
        if self.options.mode in ['','syn_report', 'dse_pragma_report','dse_dtype_report','dse_clock_report','dse_universal_report','dse_variable_report', 'dse_cfg_report']:
            return
        elif self.options.mode in ['dse_pragma','dse_clock', 'syn','dse_dtype','dse_universal','dse_variable', 'dse_cfg']:
            if self.cfg.design_setting.run_vivado_power_analyzer: #force vivado synthesizer if power is asked
                self.cfg.design_setting.run_vivado_synthesize = True

            self.copy_design_source_files(['h', 'cpp'])
            if os.path.exists(self.cfg.paths.solution):
                shutil.rmtree(self.cfg.paths.solution)
                os.makedirs(self.cfg.paths.solution)
            else:
                os.makedirs(self.cfg.paths.solution)

            if not os.path.exists(self.cfg.paths.test_files):
                os.makedirs(self.cfg.paths.test_files)
            else:
                shutil.rmtree(self.cfg.paths.test_files)
                os.makedirs(self.cfg.paths.test_files)

            if self.options.mode not in ['syn']:
                if not os.path.exists(self.cfg.paths.directive_list):
                    os.makedirs(self.cfg.paths.directive_list)
                else:
                    shutil.rmtree(self.cfg.paths.directive_list)
                    os.makedirs(self.cfg.paths.directive_list)

                if os.path.exists(self.cfg.paths.dse_report):
                    print("PYTHON : The report folder exist. choose another DSE report folder name!")
                    #exit()
                    shutil.rmtree(self.cfg.paths.dse_report)
                    os.makedirs(self.cfg.paths.dse_report)
                    os.makedirs(self.cfg.paths.dse_figures)
                else:
                    os.makedirs(self.cfg.paths.dse_report)
                    os.makedirs(self.cfg.paths.dse_figures)




class hls_tools():
    def __init__(self, cfg):
        self.cfg = cfg
        self.utils = utils(cfg)
        #self.module['MOPS'] = {}

        self.pragmas_dict = {
            'unroll': 'set_directive_unroll         ',
            'pipeline': 'set_directive_pipeline       ',
            'dataflow': 'set_directive_dataflow       ',
            'inline': 'set_directive_inline         ',
            'partition': 'set_directive_array_partition',
            'reshape': 'set_directive_array_reshape  ',
            'interface': 'set_directive_interface      ',
            'mul': 'set_directive_allocation     '
        }

    def create_syn_tcl_file(self, clock_period):
        tcl_lines = []
        tcl_lines.append("############################################################")
        tcl_lines.append("## This file is generated automatically by python tool")
        tcl_lines.append("############################################################")
        tcl_lines.append('puts \"CMD : run_hls_syn.tcl is running!\"')
        tcl_lines.append('set sol_name [lindex  $argv 2 ]')
        tcl_lines.append('open_project hls$sol_name')
        tcl_lines.append('set_top   {}'.format(self.cfg.design_setting.topmodule))
        for file in self.cfg.design.source_files:
            tcl_lines.append('add_files  {}'.format(file))

        for file in self.cfg.design.tb_files:
            tcl_lines.append('add_files  -tb {}'.format(file))
        if self.cfg.design_setting.vivado_version == 'vitis':
            tcl_lines.append('open_solution -reset \"{}\"  -flow_target vivado'.format(self.cfg.design_setting.solution_name))
            tcl_lines.append('set_part {' + self.cfg.FPGA.part + '}')
        else:
            tcl_lines.append('open_solution -reset \"{}\"'.format(self.cfg.design_setting.solution_name))
            tcl_lines.append('set_part {' + self.cfg.FPGA.part + '} -tool vivado')
        tcl_lines.append('create_clock -period {} -name default'.format(clock_period))
        tcl_lines.append('set_clock_uncertainty 12.5%')
        if self.cfg.run_options.mode == 'dse_pragma':
            tcl_lines.append('source \"ip_test_sol_list/solution_$sol_name.tcl\"')
        else:
            tcl_lines.append('source \"./hls/{}/directives.tcl\"'.format(self.cfg.design_setting.solution_name))

        tcl_lines.append('csynth_design')
        if self.cfg.design_setting.run_vivado_synthesize:
            tcl_lines.append('export_design -flow syn -rtl verilog -format ip_catalog')
        elif self.cfg.design_setting.create_ip:
            tcl_lines.append('export_design -format ip_catalog')

        tcl_lines.append('quit')
        filename = os.path.join(self.cfg.paths.design_model, "run_hls_syn.tcl")
        self.utils.save_list_to_file(filename, tcl_lines)




    def run_power_analyzer(self, sol_counter, mode, print_out='silent', clean=False):
        if not self.cfg.design_setting.run_vivado_power_analyzer:
            return 'NP', {'LUT_PS': 'NP', 'FF_PS': 'NP', 'DSP_PS': 'NP', 'BRAM_PS': 'NP'}

        if self.cfg.run_options.mode == 'dse_pragma':
            dest_path = os.path.join(self.cfg.paths.design_model, 'hls{}'.format(sol_counter),
                                     self.cfg.design_setting.solution_name)
        else:
            dest_path = self.cfg.paths.solution

        if not os.path.exists(os.path.join(dest_path, 'impl')):
            return 'Er'
        start_time = self.utils.record_time()
        impl_file = ['power_analyzer.tcl',
                     'run_power_analyzer.bat']
        for fname in impl_file:
            srcfile = os.path.join(self.cfg.paths.src, fname)
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


    def create_fixed_directive_tcl_file(self, directive_type):

        ctrl_intf = {'hs': "set_directive_interface -mode ap_ctrl_hs \"{}\"".format(self.cfg.design_setting.topmodule),
        'none': "set_directive_interface -mode ap_ctrl_none \"{}\"".format(self.cfg.design_setting.topmodule),
        'axi':"set_directive_interface -mode s_axilite \"{}\"".format(self.cfg.design_setting.topmodule)}

        tcl_lines = []
        tcl_lines.append("############################################################")
        tcl_lines.append(
            "## This file is generated automatically by dnn tool. This is {} Solution.".format(directive_type))
        tcl_lines.append("############################################################")

        tcl_lines.append(ctrl_intf.get(self.cfg.design.module_controller,''))

        for intf in self.cfg.interface[self.cfg.design.data_interface]:
            tcl_lines.append(intf)

        if not self.cfg.pragmas[directive_type] == None:
            for item in self.cfg.pragmas[directive_type]:
                if item is not None:
                    tcl_lines.append(item)

        if self.cfg.design.dataflow:
            tcl_lines.append('\nset_directive_dataflow    \"{}\"'.format(self.cfg.design_setting.topmodule))
        filename = os.path.join(self.cfg.paths.solution, "directives.tcl")
        self.utils.save_list_to_file(filename, tcl_lines)

    def read_impl_results(self, sol_path):
        try:
            power_rptFile = os.path.join(sol_path, 'impl', 'verilog', 'report', 'rpt_power.xml')
            power_rpt = pd.read_fwf(power_rptFile, skiprows=list(range(31)), nrows=45 - 31 - 1)
            power = power_rpt.T[0].values[0].split()[-2]
        except:
            power = 'NF'

        try:
            utilization_rptFile = os.path.join(sol_path, 'impl', 'report', 'verilog', 'dnn_LeNet_export.xml')
            tree = ET.parse(utilization_rptFile)
            root = tree.getroot()
            PR_utilzation = {i.tag+'_PS': i.text for i in root[0][0]}
            PR_utilzation.pop('SLICE_PS')
            PR_utilzation.pop('SRL_PS')
            print('Post Syn hardware utilization : ', PR_utilzation)
        except:
            PR_utilzation = {'LUT_PS': 'NF', 'FF_PS': 'NF', 'DSP_PS': 'NF', 'BRAM_PS': 'NF'}
        return power, PR_utilzation

    def read_parallel_syn_results(self, solution_num, syn_exec_time, print_out=False):
        file = os.path.join(self.cfg.paths.design_model,'hls{}'.format(solution_num),self.cfg.design_setting.solution_name,
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
                    pprint.pprint(passed_sol[self.cfg.design_setting.topmodule], depth=5)

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
                    syn_rslt_summary[p_id]['FPS'] = int(pow(10, 6)/exec_us)
                    if topmodule == p_id:
                        total_OP = self.cfg.analyze_results[topmodule].get('ops', 0)
                        syn_rslt_summary[p_id]['ratio'] = round(self.cfg.analyze_results[topmodule]['ops'] /
                                                                int(syn_rslt_summary[p_id]['latency']), 2)
                    else:
                        total_OP = 0
                        syn_rslt_summary[p_id]['ratio'] = 0
                    syn_rslt_summary[p_id]['OP'] = total_OP
                    syn_rslt_summary[p_id]['GOPS'] = round(total_OP / (exec_us * pow(10, 3)), 3)

                elif key == "Loops" and key in keys:
                    for II in temp[p_id][key]:
                        syn_rslt_summary[p_id]['II {}'.format(II["Name"])] = II["PipelineII"]
        return syn_rslt_summary

    def extract_hls_json_info_vitis(self, json_data):
        syn_rslt_summary = {}
        keys = ['Area', 'Latency']
        temp = json_data["ModuleInfo"]["Metrics"]
        topmodule = self.cfg.design_setting.topmodule
        new_temp = {}
        for i in temp.keys():
            if i == self.cfg.design_setting.topmodule:
                new_label = i
            else:
                new_label = '_'.join(i.split('_')[0:2]+[i.split('_')[-3]])
            new_temp[new_label] = temp[i]
        for p_id, p_info in new_temp.items():
            syn_rslt_summary[p_id] = {}
            # print("\nModule name:", p_id)
            for key in p_info:
                if key == "Area" and key in keys:
                    a = syn_rslt_summary[p_id]['BRAM %'] = str(
                        round(int(new_temp[p_id][key]["BRAM_18K"]) / int(new_temp[p_id][key]["AVAIL_BRAM"]) * 100, 2))
                    syn_rslt_summary[p_id]['BRAM'] = new_temp[p_id][key]["BRAM_18K"]
                    b = syn_rslt_summary[p_id]['LUT %'] = str(
                        round(int(new_temp[p_id][key]["LUT"]) / int(new_temp[p_id][key]["AVAIL_LUT"]) * 100, 2))
                    syn_rslt_summary[p_id]['LUT'] = new_temp[p_id][key]["LUT"]
                    c = syn_rslt_summary[p_id]['FF %'] = str(round(int(new_temp[p_id][key]["FF"]) / int(new_temp[p_id][key]["AVAIL_FF"]) * 100, 2))  # ...
                    syn_rslt_summary[p_id]['FF'] = new_temp[p_id][key]["FF"]
                    syn_rslt_summary[p_id]['DSP'] = new_temp[p_id][key]["DSP"]
                    d = syn_rslt_summary[p_id]['DSP %'] = str(
                        round(int(new_temp[p_id][key]["DSP"]) / int(new_temp[p_id][key]["AVAIL_DSP"]) * 100, 2))
                    syn_rslt_summary[p_id]['Total %'] = str(round(
                        (float(a) + float(b) + float(c) + float(d)) / 4, 2))
                elif key == "Latency" and key in keys:
                    syn_rslt_summary[p_id]['latency'] = str(new_temp[p_id][key]["LatencyWorst"])
                    exec_us = (float(new_temp[p_id][key]["LatencyWorst"])) * float(new_temp[p_id]["Timing"]["Target"]) / pow(10, 3)
                    syn_rslt_summary[p_id]['exec us'] = str(round(exec_us, 2))
                    syn_rslt_summary[p_id]['clock period'] = float(new_temp[p_id]["Timing"]["Target"])
                    syn_rslt_summary[p_id]['FPS'] = int(pow(10, 6)/exec_us) if exec_us != 0 else 'NA'
                    if topmodule == p_id:
                        total_OP = self.cfg.analyze_results[topmodule].get('ops', 0)
                        syn_rslt_summary[p_id]['ratio'] = round(self.cfg.analyze_results[topmodule]['ops'] /
                                                                int(syn_rslt_summary[p_id]['latency']), 2)
                    else:
                        total_OP = 0
                        syn_rslt_summary[p_id]['ratio'] = 0
                    syn_rslt_summary[p_id]['OP'] = total_OP
                    syn_rslt_summary[p_id]['GOPS'] = round(total_OP / (exec_us * pow(10, 3)), 3) if exec_us != 0 else 'NA'

                elif key == "Loops" and key in keys:
                    for II in new_temp[p_id][key]:
                        syn_rslt_summary[p_id]['II {}'.format(II["Name"])] = II["PipelineII"]
        return syn_rslt_summary


    def copy_hls_bc_files(self, syn_path, sol_counter):
        if self.cfg.design_setting.DSE_setting['copy_bc_files']:
            bc_report_path = os.path.join(self.cfg.paths.dse_report, 'bcfiles')
            if not os.path.exists(bc_report_path):
                os.mkdir(bc_report_path)
            temp = os.path.join(bc_report_path, 'bc_sol{}'.format(sol_counter))
            os.mkdir(temp)
            bc_path = os.path.join(syn_path, '.autopilot', 'db')
            files = glob.iglob(os.path.join(bc_path, '*.{}'.format('bc')))
            for file in files:
                shutil.copy2(file, temp)

    def save_syn_records(self, syn_rslt, power, PR_syn_rslt, time):
        record_file = os.path.join(self.cfg.paths.report, '{}'.format('syn_records'))
        try:
            with open(record_file+'.pickle', 'rb') as f:
                previous_records = pickle.load(f)
                print("Record file is updated.")
        except IOError:
            previous_records = []
            print("Record file not exist! A new record file is created.")

        record = {}
        record['syntime'] = '{}:{}'.format(time[0], time[1])
        record['hls_tool'] = self.cfg.design_setting.vivado_version
        record['syn_label'] = self.cfg.design_setting.syn_label
        record['power'] = str(power)
        record['sol'] = self.cfg.design_setting.syn_directive_type
        record['dataflow'] = self.cfg.design.dataflow

        record.update(syn_rslt[self.cfg.design_setting.topmodule])
        record.update(PR_syn_rslt)
        previous_records.append(record)
        with open(record_file+'.pickle', 'wb') as f:
            pickle.dump(previous_records, f)
        keys = previous_records[0].keys()
        with open(record_file+'.csv', 'w', newline='') as output_file:
            dict_writer = csv.DictWriter(output_file, keys)
            dict_writer.writeheader()
            dict_writer.writerows(previous_records)

        txtlines = []
        temp = ''
        for i in previous_records[0].keys():
            temp = temp + '{:^11} '.format(i)
        txtlines.append(temp)
        for rec in previous_records:
            temp = ''
            for i in rec.keys():
                temp = temp + '{:^11} '.format(str(rec[i]))
            txtlines.append(temp)
        self.utils.save_list_to_file(record_file+'.txt', txtlines)




print("PYTHON : hls_tools is imported")