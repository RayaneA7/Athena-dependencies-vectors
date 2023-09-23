import json
import random
import re
from pathlib import Path
from typing import Dict, List

from athena.tiramisu.compiling_service import CompilingService
from athena.tiramisu.tiramisu_tree import TiramisuTree


class TiramisuProgram:
    """
    This class represents a tiramisu function. It contains all the neccessary information
    about the function to be able to generate the code for it.

    Attributes
    ----------
    `file_path`: str
        The path to the cpp file of the tiramisu function
    `annotations`: dict
        The tiramisu annotations of the function
    `comps`: list[str]
        The list of computations in the function
    `name`: str
        The name of the function
    `schedules_legality`: dict
        The legality of the schedules of the function
    `schedules_solver`: dict
        The solver results of the schedules of the function
    `original_str`: str
        The original code string of the function
    `initial_execution_times`: dict
        The initial execution times of the function
    `current_machine_initial_execution_time`: float
        The initial execution time of the function on the current machine
    `tree`: TiramisuTree
        The tree of the function
    """

    def __init__(self: "TiramisuProgram"):
        self.file_path = ""
        self.annotations: Dict | None = None
        self.isl_ast_string: str | None = None
        self.comps: list[str] | None = None
        self.name: str | None = None
        # self.schedules_legality = {}
        # self.schedules_solver = {}
        self.schedules_dict: Dict = {}
        self.original_str: str | None = None
        self.wrappers: Dict | None = None
        self.initial_execution_times = {}
        # self.current_machine_initial_execution_time: float | None = None
        self.tree: TiramisuTree = None

    @classmethod
    def from_dict(
        cls,
        name: str,
        data: dict,
        original_str: str | None = None,
        load_code_lines: bool = True,
        load_tree: bool = True,
    ) -> "TiramisuProgram":
        # Initiate an instante of the TiramisuProgram class
        tiramisu_prog = cls()
        tiramisu_prog.name = name
        tiramisu_prog.annotations = data["program_annotation"]
        if tiramisu_prog.annotations:
            tiramisu_prog.comps = list(tiramisu_prog.annotations["computations"].keys())
        if "schedules_dict" in data:
            tiramisu_prog.schedules_dict = data["schedules_dict"]

            # Initialize the initial_execution_times attribute and the current_machine_initial_execution_time attribute
            if "initial_execution_times" in data:
                tiramisu_prog.initial_execution_times = data["initial_execution_times"]
            # if cfg.Config.config.tiramisu.hpc_name in data["initial_execution_times"]:
            #     tiramisu_prog.current_machine_initial_execution_time = min(data[
            #         "initial_execution_times"][cfg.Config.config.tiramisu.hpc_name])

        if load_code_lines:
            tiramisu_prog.load_code_lines(original_str)

        # construct the wrapper code
        wrapper_cpp, wrapper_header = tiramisu_prog.construct_wrapper_code()

        tiramisu_prog.wrappers = {"cpp": wrapper_cpp, "h": wrapper_header}
        # If the current_machine_initial_execution_time attribute is not found in the data, compute itcio
        # if not tiramisu_prog.current_machine_initial_execution_time:
        #     tmp_exec_times = CompilingModule.CompilingService.get_cpu_exec_times(
        #         tiramisu_program=tiramisu_prog, optims_list=[])
        #     # Store the minimum execution time in the initial_execution_time attribute
        #     tiramisu_prog.current_machine_initial_execution_time = min(
        #         tmp_exec_times)

        #     tiramisu_prog.initial_execution_times[
        #         cfg.Config.config.tiramisu.hpc_name] = tmp_exec_times

        # After taking the neccessary fields return the instance
        if load_tree:
            tiramisu_prog.tree = TiramisuTree.from_annotations(
                tiramisu_prog.annotations
            )
        return tiramisu_prog

    @classmethod
    def from_file(
        cls,
        file_path: str,
        load_annotations=False,
        load_isl_ast=False,
        load_tree=False,
    ) -> "TiramisuProgram":
        """
        This function loads a tiramisu function from its cpp file and its wrapper files.

        Parameters
        ----------
        `file_path`: str
            The path to the cpp file of the tiramisu function
        `load_annotations`: bool
            A flag to indicate if the annotations should be loaded or not

        Returns
        -------
        `tiramisu_prog`: TiramisuProgram
            An instance of the TiramisuProgram class
        """
        # Initiate an instante of the TiramisuProgram class
        tiramisu_prog = cls()
        tiramisu_prog.file_path = file_path
        tiramisu_prog.load_code_lines()

        # load the wrapper code
        wrapper_cpp, wrapper_header = tiramisu_prog.construct_wrapper_code()

        tiramisu_prog.wrappers = {"cpp": wrapper_cpp, "h": wrapper_header}

        if load_annotations:
            tiramisu_prog.annotations = json.loads(
                CompilingService.compile_annotations(tiramisu_prog)
            )
        elif load_isl_ast:
            tiramisu_prog.isl_ast_string = CompilingService.compile_isl_ast_tree(
                tiramisu_prog
            )

        if load_tree:
            if tiramisu_prog.annotations:
                assert tiramisu_prog.annotations is not None
                tiramisu_prog.tree = TiramisuTree.from_annotations(
                    tiramisu_prog.annotations
                )
            elif tiramisu_prog.isl_ast_string:
                tiramisu_prog.tree = TiramisuTree.from_isl_ast_string_list(
                    tiramisu_prog.isl_ast_string.split("\n")
                )
            else:
                raise Exception(
                    "You should load either the annotations or the isl ast string to load the tree"
                )

        # After taking the neccessary fields return the instance
        return tiramisu_prog

    def load_code_lines(self, original_str: str | None = None):
        """
        This function loads the file code , it is necessary to generate legality check code and annotations
        """

        if original_str:
            self.original_str = original_str
        else:
            with open(self.file_path, "r") as f:
                self.original_str = f.read()

        self.func_folder = (
            "/".join(Path(self.file_path).parts[:-1])
            if len(Path(self.file_path).parts) > 1
            else "."
        ) + "/"
        self.body = re.findall(
            r"(tiramisu::init(?s:.)+)tiramisu::codegen", self.original_str
        )[0]
        self.name = re.findall(r"tiramisu::init\(\"(\w+)\"\);", self.original_str)[0]
        # Remove the wrapper include from the original string
        self.wrapper_str = f'#include "{self.name}_wrapper.h"'
        self.original_str = self.original_str.replace(
            self.wrapper_str, f"// {self.wrapper_str}"
        )
        self.comps = re.findall(r"computation (\w+)\(", self.original_str)
        self.code_gen_line = re.findall(r"tiramisu::codegen\({.+;", self.original_str)[
            0
        ]
        buffers_vect = re.findall(r"{(.+)}", self.code_gen_line)[0]
        self.IO_buffer_names = re.findall(r"\w+", buffers_vect)
        self.buffer_sizes = []
        for buf_name in self.IO_buffer_names:
            sizes_vect = re.findall(
                r"buffer " + buf_name + ".*{(.*)}", self.original_str
            )[0]
            self.buffer_sizes.append(re.findall(r"\d+", sizes_vect))
        self.wrapper_is_compiled = False

    def construct_wrapper_code(
        self,
    ):  # construct the wrapper.cpp and wrapper.h from the program
        buffers_init_lines = ""
        for i, buffer_name in enumerate(self.IO_buffer_names):
            buffers_init_lines += f"""
    double *c_{buffer_name} = (double*)malloc({'*'.join(self.buffer_sizes[i][::-1])}* sizeof(double));
    parallel_init_buffer(c_{buffer_name}, {'*'.join(self.buffer_sizes[i][::-1])}, (double){str(random.randint(1,10))});
    Halide::Buffer<double> {buffer_name}(c_{buffer_name}, {','.join(self.buffer_sizes[i][::-1])});
    """
        if self.name is None:
            raise Exception("TiramisuProgram.name is None")

        wrapper_cpp_code = wrapper_cpp_template.replace("$func_name$", self.name)
        wrapper_cpp_code = wrapper_cpp_code.replace(
            "$buffers_init$", buffers_init_lines
        )
        wrapper_cpp_code = wrapper_cpp_code.replace(
            "$func_folder_path$", self.func_folder
        )
        wrapper_cpp_code = wrapper_cpp_code.replace(
            "$func_params$",
            ",".join([name + ".raw_buffer()" for name in self.IO_buffer_names]),
        )

        wrapper_h_code = wrapper_h_template.replace("$func_name$", self.name)
        wrapper_h_code = wrapper_h_code.replace(
            "$func_params$",
            ",".join(["halide_buffer_t *" + name for name in self.IO_buffer_names]),
        )

        return wrapper_cpp_code, wrapper_h_code

    def __str__(self) -> str:
        return f"TiramisuProgram(name={self.name})"

    def __repr__(self) -> str:
        return self.__str__()
    
    def set_name(self,name):
        self.name = name
        return self.name


wrapper_cpp_template = """#include "Halide.h"
#include "$func_name$_wrapper.h"
#include "tiramisu/utils.h"
#include <iostream>
#include <time.h>
#include <fstream>
#include <chrono>

using namespace std::chrono;
using namespace std;

int main(int, char **argv){
        
$buffers_init$
    
    //halide_set_num_threads(48);
    
    int nb_execs = get_nb_exec();

    double duration;
    
    for (int i = 0; i < nb_execs; ++i) {
        auto begin = std::chrono::high_resolution_clock::now(); 
        $func_name$($func_params$);
        auto end = std::chrono::high_resolution_clock::now(); 

        duration = std::chrono::duration_cast<std::chrono::nanoseconds>(end-begin).count() / (double)1000000;
        std::cout << duration << " "; 

    }
    std::cout << std::endl;
    return 0;
}"""
wrapper_h_template = """#include <tiramisu/utils.h>
#include <sys/time.h>
#include <cstdlib>
#include <algorithm>
#include <vector>

#define NB_THREAD_INIT 48
struct args {
    double *buf;
    unsigned long long int part_start;
    unsigned long long int part_end;
    double value;
};

void *init_part(void *params)
{
   double *buffer = ((struct args*) params)->buf;
   unsigned long long int start = ((struct args*) params)->part_start;
   unsigned long long int end = ((struct args*) params)->part_end;
   double val = ((struct args*) params)->value;
   for (unsigned long long int k = start; k < end; k++){
       buffer[k]=val;
   }
   pthread_exit(NULL);
}

void parallel_init_buffer(double* buf, unsigned long long int size, double value){
    pthread_t threads[NB_THREAD_INIT]; 
    struct args params[NB_THREAD_INIT];
    for (int i = 0; i < NB_THREAD_INIT; i++) {
        unsigned long long int start = i*size/NB_THREAD_INIT;
        unsigned long long int end = std::min((i+1)*size/NB_THREAD_INIT, size);
        params[i] = (struct args){buf, start, end, value};
        pthread_create(&threads[i], NULL, init_part, (void*)&(params[i])); 
    }
    for (int i = 0; i < NB_THREAD_INIT; i++) 
        pthread_join(threads[i], NULL); 
    return;
}
#ifdef __cplusplus
extern "C" {
#endif
int $func_name$($func_params$);
#ifdef __cplusplus
}  // extern "C"
#endif


int get_beam_size(){
    if (std::getenv("BEAM_SIZE")!=NULL)
        return std::stoi(std::getenv("BEAM_SIZE"));
    else{
        std::cerr<<"error: Environment Variable BEAM_SIZE not declared"<<std::endl;
        exit(1);
    }
}

int get_max_depth(){
    if (std::getenv("MAX_DEPTH")!=NULL)
        return std::stoi(std::getenv("MAX_DEPTH"));
    else{
        std::cerr<<"error: Environment Variable MAX_DEPTH not declared"<<std::endl;
        exit(1);
    }
}

void declare_memory_usage(){
    setenv("MEM_SIZE", std::to_string((double)(256*192+320*256+320*192)*8/1024/1024).c_str(), true); // This value was set by the Code Generator
}

int get_nb_exec(){
    if (std::getenv("NB_EXEC")!=NULL)
        return std::stoi(std::getenv("NB_EXEC"));
    else{
        return 30;
    }
}
"""
