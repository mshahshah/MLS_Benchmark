
import numpy as np
import os, shutil
from os import listdir
import csv, time
import pickle,re
import matplotlib.pyplot as plt
import winsound

class Struct:
    def __init__(self, **entries):
        self.__dict__.update(entries)


def beep(type):
    if type == 'syn':
        for i in range(3):
            winsound.Beep(1200, 150)
            time.sleep(0.05)
    elif type == 'dse':
        for i in range(2):
            winsound.Beep(1200, 100)
            time.sleep(0.05)
    elif type == 'impl':
        winsound.Beep(2000, 400)
    elif type == 'finish':
        for i in [5,4,3,2]:
            winsound.Beep(1000 + i*100, int(800/i))
            time.sleep(0.01*i)
        winsound.Beep(600, 700)

class utils:
    def __init__(self,cfg):
        self.hello=0
        self.cfg = cfg

    def find_Aword_in_file(self,filename,keyword,save_results):
        try:
            file = open(filename,'r')
            read=file.readlines()
            file.close()
            count = 0
            detected_list = []
            for lineNum,line in enumerate(read, start = 1):
                if line != '\n': # if line is not blank
                    first_word = line.split()[0].lower()
                    if (keyword.lower() == first_word.strip(":!@()_+=")):
                        count +=1
                        detected_list.append(line)
            if count != 0 :
                print("PYTHON : {}  \"{}\" found in the \"{}\" file".format(count,keyword,filename))
        except FileExistsError:
            print("PYTHON : faild to open {}".format(filename))
        if save_results:
            filename = file = os.path.join(self.cfg.paths.design_top, "{}.log".format(keyword))
            self.save_list_to_file(filename,detected_list)
        return count

    def cleanSolution(self):
        filesToBeRemoved = [self.cfg.files.synLogFile, self.cfg.files.SolutionFile]
        for file in filesToBeRemoved:
            if os.path.exists(file):
                os.remove(file)

    def save_list_to_file(self,filename,data):
        with open(filename, 'w') as f:
            for line in data:
                f.write("%s\n" % line)

    def load_file_to_list(self,filename):
        with open(filename, 'r') as reader:
            return reader.readlines()

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

    def remove_directory(self, path, directoryName):
        path = os.path.join(path,directoryName)
        if os.path.exists(path):
            try:
                os.rmdir(path)
            except OSError as e:
                print("Error: %s : %s" % (path, e.strerror))

    def create_directory(self, path, directoryName):
        sol_copy_name = os.path.join(path,directoryName)
        if not os.path.exists(sol_copy_name):
            os.makedirs(sol_copy_name)

    def copy_a_file(self, src, dest):
        copyfile(src, dest)

    def save_a_variable(self,fname,variable):
        with open(os.path.join(self.cfg.paths.dse_report,'{}.pickle'.format(fname)), 'wb') as f:
            pickle.dump(variable, f)

    def load_a_variable(self,variable_name):
        with open(os.path.join(self.cfg.paths.dse_report,'{}.pickle'.format(variable_name)), 'rb') as f:
            variable = pickle.load(f)
        return variable

    def list_files_with_ext(self, directory, extension):
        return (f for f in listdir(directory) if f.endswith('.' + extension))

    def save_fig(self,fig_id, tight_layout=True, fig_extension="png", resolution=300):
        path = os.path.join(self.cfg.paths.dse_figures, fig_id + "." + fig_extension)
        print("PYTHON : utils : Saved figure \'{}.{}\'".format(fig_id,fig_extension))
        if tight_layout:
            plt.tight_layout()
        plt.savefig(path, format=fig_extension, dpi=resolution)

    def read_yaml_file(self,file):
        with open(file) as f:
            datamap = yaml.safe_load(f)
        return datamap

    def dec2hex(self,dec_array,precision):
        if precision > 24:
            hex_data = [format(x % (1 << 32), '08x') for x in dec_array]
        elif precision > 16:
            hex_data = [format(x % (1 << 24), '06x') for x in dec_array]
        elif precision > 8:
            hex_data = [format(x % (1 << 16), '04x') for x in dec_array]
        else:
            hex_data = [format(x % (1 << 8), '02x') for x in dec_array]
        return hex_data

    def hex2dec(self,hex_string,precision):
        dec_list=[]
        for data in hex_string:
            try:
                a = int(data, 16)
            except:
                a = 2 ** (precision-1)
            if a & (1 << (precision-1)):
                a -= 1 << precision
            dec_list.append(a)
        return dec_list

    def float2fixed(self,float_num_list, int_width, fractional_width):
        fixed_num_list = []
        for float_num in float_num_list:
            total_width = int_width + fractional_width
            temp1 = float_num * 2 ** fractional_width
            if (temp1 > 0 and temp1 > 2 ** (total_width - 1) - 1):
                fixed_num = 2 ** (total_width - 1) - 1
                print('error in float2fixed conversion +ve saturation implemented')
            elif (temp1 < 0 and temp1 < 2 ** (total_width - 1)):
                fixed_num = -1 * 2 ** (total_width - 1)
                print('error in float2fixed conversion -ve saturation implemented')
            else:
                fixed_num = temp1
            fixed_num_list.append(fixed_num)
        return fixed_num_list

    def float2int(self,float_num_list, int_width, mode = 'round'):
        fixed_num_list = []
        for float_num in float_num_list:
            fixed_num = float_num * (2**(int_width-1))
            if mode == 'ceil':
                fixed_num_list.append(math.ceil(fixed_num))
            else:
                fixed_num_list.append(math.floor(fixed_num))
        return fixed_num_list


print("PYTHON : utils is imported")

