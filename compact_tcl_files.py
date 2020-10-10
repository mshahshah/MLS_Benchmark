import os,pickle


def compact_tcl_files(source_path, cap_range):
    listOfDirectives = []
    for file in range(cap_range):
        filename = '{}/untimate_new_directive{}.tcl'.format(source_path,file)
        with open(filename, 'r') as reader:
            txt = reader.readlines()
        listOfDirectives.append(txt)
    print("{} tcl files are loaded.".format(len(listOfDirectives)))
    pickle_file = '{}/compacted_tcl_files.pickle'.format(source_path)
    with open(pickle_file, 'wb') as f:
        pickle.dump(listOfDirectives, f)

    print("All directives are save in {}".format(pickle_file))


if __name__ == '__main__':
    source_path = 'C:/Users/mxs161831/Box/HLS Benchmarks/designs_n_directives/matrix_mult_2019'
    cap_range = 100
    compact_tcl_files(source_path, cap_range)