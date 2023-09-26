from __future__ import annotations

import logging
import os
import re
import subprocess
from typing import TYPE_CHECKING, List

from athena.tiramisu.tiramisu_tree import TiramisuTree

if TYPE_CHECKING:
    from athena.tiramisu.tiramisu_actions.tiramisu_action import TiramisuAction
    from athena.tiramisu.schedule import Schedule
    from athena.tiramisu.tiramisu_program import TiramisuProgram

from athena.utils.config import BaseConfig


class CompilingService:
    """
    Class responsible of compiling the generated code and running it to get the results
    Contains nothing but class methods
    """

    @classmethod
    def compile_legality(cls, schedule: Schedule, with_ast: bool = False):
        """CompilingService.get_schedule_code(matmul,)
        Compile the generated code with the added code to check legality of the schedule

        Parameters
        ----------
        `schedule` : `Schedule`
            The schedule to check legality of

        Returns
        -------
        `bool`
            True if the schedule is legal, False otherwise
        """
        assert BaseConfig.base_config
        assert schedule.tiramisu_program

        output_path = os.path.join(
            BaseConfig.base_config.workspace,
            f"{schedule.tiramisu_program.name}_legality",
        )

        cpp_code = cls.get_legality_code(schedule=schedule, with_ast=with_ast)

        logging.debug("Legality Code: \n" + cpp_code)

        result = cls.run_cpp_code(cpp_code=cpp_code, output_path=output_path)

        if with_ast:
            result_lines = result.split("\n")
            legality_result = result_lines[0]
            legality_result = legality_result.strip()
            if legality_result not in ["0", "1"]:
                raise Exception(f"Error in legality check: {legality_result}")
            ast = TiramisuTree.from_isl_ast_string_list(
                isl_ast_string_list=result_lines[1:]
            )
            return legality_result == "1", ast

        else:
            result = result.strip()
            if result not in ["0", "1"]:
                raise Exception(f"Error in legality check: {result}")
            return result == "1", None

    @classmethod
    def get_legality_code(cls, schedule: Schedule, with_ast: bool = False):
        """
        Constructs the code to check legality of the schedule

        Parameters
        ----------
        `tiramisu_program` : `TiramisuProgram`
            The tiramisu program to compile
        `optims_list` : `List[TiramisuAction]`
            The list of optimizations to apply to the schedule

        Returns
        -------
        `str`
            The code to check legality of the schedule
        """
        assert schedule.tiramisu_program
        assert schedule.tiramisu_program.original_str
        assert schedule.tree

        # Add code to the original file to get legality result
        legality_check_lines = """
    prepare_schedules_for_legality_checks();
    perform_full_dependency_analysis();
    bool is_legal=true;

"""
        for optim in schedule.optims_list:
            # if optim.is_parallelization():
            legality_check_lines += "    " + optim.legality_check_string
            # elif optim.is_unrolling():
            #     for branch in schedule_object.branches:
            #         comps = branch["comps"]
            #         level = len(branch["iterators"]) - 1
            #         legality_check_lines += print(
            #             f"\n\tis_legal &= loop_unrolling_is_legal({level}, {{{', '.join([f'&{comp}' for comp in comps])}}});")
            # legality_check_lines += optim.tiramisu_optim_str + "\n"

        legality_check_lines += """
    prepare_schedules_for_legality_checks();
    is_legal &= check_legality_of_function();   
    std::cout << is_legal << std::endl;
"""

        if with_ast:
            legality_check_lines += """
    auto fct = tiramisu::global::get_implicit_function();

    fct->gen_time_space_domain();
    fct->gen_isl_ast();
    fct->print_isl_ast_representation(nullptr, 0);
"""

        # Paste the lines responsable of checking legality of schedule in the cpp file
        cpp_code = schedule.tiramisu_program.original_str.replace(
            schedule.tiramisu_program.code_gen_line, legality_check_lines
        )
        return cpp_code

    @classmethod
    def compile_annotations(cls, tiramisu_program: TiramisuProgram):
        """
        Compile the generated code with the added code to get the annotations

        Parameters
        ----------
        `tiramisu_program` : `TiramisuProgram`
            The tiramisu program to compile

        Returns
        -------
        `str`
            The annotations in json format
        """
        if not BaseConfig.base_config:
            raise ValueError("BaseConfig not initialized")

        if not tiramisu_program.original_str:
            raise ValueError("Tiramisu program not initialized")

        # TODO : add getting tree structure object from executing the file instead of building it
        output_path = os.path.join(
            BaseConfig.base_config.workspace, f"{tiramisu_program.name}_annotations"
        )
        # Add code to the original file to get json annotations

        get_json_lines = """
            auto ast = tiramisu::auto_scheduler::syntax_tree(tiramisu::global::get_implicit_function(), {});
            std::string program_json = tiramisu::auto_scheduler::evaluate_by_learning_model::get_program_json(ast);
            std::cout << program_json;
            """

        # Paste the lines responsable of generating the program json tree in the cpp file
        cpp_code = tiramisu_program.original_str.replace(
            tiramisu_program.code_gen_line, get_json_lines
        )
        return cls.run_cpp_code(cpp_code=cpp_code, output_path=output_path)

    @classmethod
    def compile_isl_ast_tree(
        cls, tiramisu_program: TiramisuProgram, schedule: Schedule | None = None
    ):
        if not BaseConfig.base_config:
            raise ValueError("BaseConfig not initialized")

        if not tiramisu_program.original_str:
            raise ValueError("Tiramisu program not initialized")

        # TODO : add getting tree structure object from executing the file instead of building it
        output_path = os.path.join(
            BaseConfig.base_config.workspace, f"{tiramisu_program.name}_isl_ast"
        )
        get_isl_ast_lines = ""
        if schedule:
            for optim in schedule.optims_list:
                # if optim.is_parallelization():
                get_isl_ast_lines += "    " + optim.tiramisu_optim_str

        get_isl_ast_lines += """
    auto fct = tiramisu::global::get_implicit_function();

    fct->gen_time_space_domain();
    fct->gen_isl_ast();
    fct->print_isl_ast_representation(nullptr, 0);
"""

        # Paste the lines responsable of generating the program json tree in the cpp file
        cpp_code = tiramisu_program.original_str.replace(
            tiramisu_program.code_gen_line, get_isl_ast_lines
        )
        return cls.run_cpp_code(cpp_code=cpp_code, output_path=output_path)

    @classmethod
    def run_cpp_code(cls, cpp_code: str, output_path: str):
        """
        Helper function to compile and run the generated code

        Parameters
        ----------
        `cpp_code` : `str`
            The code to compile
        `output_path` : `str`
            The path to the output file

        Returns
        -------
        `str`
            The output of the compilation
        """
        if not BaseConfig.base_config:
            raise ValueError("BaseConfig not initialized")

        env_vars = [
            f"export {key}={value}"
            for key, value in BaseConfig.base_config.env_vars.items()
        ]
        if BaseConfig.base_config.tiramisu.is_new_tiramisu:
            # Making the tiramisu root path explicit to the env
            shell_script = [
                # Compile intermidiate tiramisu file
                "$CXX -I$TIRAMISU_ROOT/3rdParty/Halide/install/include -I$TIRAMISU_ROOT/include -I$TIRAMISU_ROOT/3rdParty/isl/include  -Wl,--no-as-needed -ldl -g -fno-rtti   -lpthread -std=c++17 -O0 -o {}.o -c -x c++ -".format(
                    output_path
                ),
                # Link generated file with executer
                "$CXX -Wl,--no-as-needed -ldl -g -fno-rtti -lpthread -std=c++17 -O0 {}.o -o {}.out   -L$TIRAMISU_ROOT/build  -L$TIRAMISU_ROOT/3rdParty/Halide/install/lib64  -L$TIRAMISU_ROOT/3rdParty/isl/build/lib  -Wl,-rpath,$TIRAMISU_ROOT/build:$TIRAMISU_ROOT/3rdParty/Halide/install/lib64:$TIRAMISU_ROOT/3rdParty/isl/build/lib -ltiramisu -ltiramisu_auto_scheduler -lHalide -lisl".format(
                    output_path, output_path
                ),
                # Run the program
                "{}.out &&".format(output_path),
                # Clean generated files
                "rm {}*".format(output_path),
            ]
        else:
            shell_script = [
                # Compile intermidiate tiramisu file
                "$CXX -I$TIRAMISU_ROOT/3rdParty/Halide/include -I$TIRAMISU_ROOT/include -I$TIRAMISU_ROOT/3rdParty/isl/include  -Wl,--no-as-needed -ldl -g -fno-rtti   -lpthread -std=c++11 -O0 -o {}.o -c -x c++ -".format(
                    output_path
                ),
                # Link generated file with executer
                "$CXX -Wl,--no-as-needed -ldl -g -fno-rtti -lpthread -std=c++11 -O0 {}.o -o {}.out   -L$TIRAMISU_ROOT/build  -L$TIRAMISU_ROOT/3rdParty/Halide/lib  -L$TIRAMISU_ROOT/3rdParty/isl/build/lib  -Wl,-rpath,$TIRAMISU_ROOT/build:$TIRAMISU_ROOT/3rdParty/Halide/lib:$TIRAMISU_ROOT/3rdParty/isl/build/lib -ltiramisu -ltiramisu_auto_scheduler -lHalide -lisl".format(
                    output_path, output_path
                ),
                # Run the program
                f"{output_path}.out &&",
                # Clean generated files
                "rm {}*".format(output_path),
            ]
        try:
            print(cpp_code)
            compiler = subprocess.run(
                ["\n".join(env_vars + shell_script)],
                input=cpp_code,
                capture_output=True,
                text=True,
                shell=True,
                check=True,
            )

            # print("dononnnnnnnnne")
            if compiler.stdout:
                return compiler.stdout
            else:
                print(compiler.stderr)
                raise Exception("Compiler returned no output")
        except subprocess.CalledProcessError as e:
            logging.error(f"Process terminated with error code: {e.returncode}")
            logging.error(f"Error output: {e.stderr}")
            raise e
        except Exception as e:
            raise e

    @classmethod
    def call_skewing_solver(
        cls,
        schedule: Schedule,
        loop_levels: List[int],
        comps_skewed_loops: List[str],
    ):
        """
        Calls the skewing solver to generate the skewing code

        Parameters
        ----------
        `schedule` : `Schedule`
            The schedule to generate the skewing code for
        `loop_levels` : `List[int]`
            The loop levels to skew
        `comps_skewed_loops` : `List[str]`
            The computations that have skewed loops
        """
        assert schedule.tiramisu_program
        assert schedule.tiramisu_program.comps
        if BaseConfig.base_config is None:
            raise Exception("The base config is not loaded yet")
        legality_cpp_code = cls.get_legality_code(schedule)
        to_replace = re.findall(
            r"std::cout << is_legal << std::endl;", legality_cpp_code
        )[0]
        header = """
        function * fct = tiramisu::global::get_implicit_function();\n"""
        legality_cpp_code = legality_cpp_code.replace(
            "is_legal &= check_legality_of_function();", ""
        )
        legality_cpp_code = legality_cpp_code.replace("bool is_legal=true;", "")
        legality_cpp_code = re.sub(
            r"is_legal &= loop_parallelization_is_legal.*\n", "", legality_cpp_code
        )
        legality_cpp_code = re.sub(
            r"is_legal &= loop_unrolling_is_legal.*\n", "", legality_cpp_code
        )

        solver_lines = (
            header
            + "\n\tauto auto_skewing_result = fct->skewing_local_solver({"
            + ", ".join([f"&{comp}" for comp in comps_skewed_loops])
            + "}"
            + ",{},{},1);\n".format(*loop_levels)
        )

        solver_lines += """    
        std::vector<std::pair<int,int>> outer1, outer2,outer3;
        tie( outer1,  outer2,  outer3 )= auto_skewing_result;
        if (outer1.size()>0){
            std::cout << outer1.front().first;
            std::cout << ",";
            std::cout << outer1.front().second;
            std::cout << ",";
        }else {
            std::cout << "None,None,";
        }
        if(outer2.size()>0){
            std::cout << outer2.front().first;
            std::cout << ",";
            std::cout << outer2.front().second;
            std::cout << ",";
        }else {
            std::cout << "None,None,";
        }
        if(outer3.size()>0){
            std::cout << outer3.front().first;
            std::cout << ",";
            std::cout << outer3.front().second;
        }else {
            std::cout << "None,None";
        }
        
            """

        solver_code = legality_cpp_code.replace(to_replace, solver_lines)
        logging.debug("Skewing Solver Code:\n" + solver_code)
        output_path = os.path.join(
            BaseConfig.base_config.workspace,
            f"{schedule.tiramisu_program.name}_skewing_solver",
        )

        result_str = cls.run_cpp_code(cpp_code=solver_code, output_path=output_path)
        result_str = result_str.split(",")

        # Skewing Solver returns 3 solutions in form of tuples, the first tuple is for outer parallelism ,
        # second is for inner parallelism , and last one is for locality, we are going to use the first preferably
        # if availble , else , we are going to use the scond one if available, this policy of choosing factors may change
        # in later versions!
        # The compiler in our case returns a tuple of type : (fac0,fac1,fac2,fac3,fac4,fac5) each 2 factors represent the
        # solutions mentioned above
        if result_str[0] != "None":
            # Means we have a solution for outer parallelism
            fac1 = int(result_str[0])
            fac2 = int(result_str[1])
            return fac1, fac2
        if result_str[2] != "None":
            # Means we have a solution for inner parallelism
            fac1 = int(result_str[2])
            fac2 = int(result_str[3])
            return fac1, fac2
        else:
            return None

    @classmethod
    def get_schedule_code(
        cls, tiramisu_program: TiramisuProgram, optims_list: List[TiramisuAction]
    ):
        """
        Returns the code of the schedule after applying the optimizations in the optims_list

        Parameters
        ----------
        `tiramisu_program`: `TiramisuProgram`
            The program to optimize
        `optims_list`: `List[TiramisuAction]`
            The list of optimizations to apply on the program

        Returns
        -------
        `str`
            The schedule code to add to the original file
        """
        if not tiramisu_program.original_str:
            raise ValueError("The program is not loaded yet")
        # Add code to the original file to get the schedule code
        schedule_code = ""
        for optim in optims_list:
            schedule_code += optim.tiramisu_optim_str + "\n"

        # Add code gen line to the schedule code
        schedule_code += "\n    " + tiramisu_program.code_gen_line + "\n"
        # Paste the lines responsable of checking legality of schedule in the cpp file
        cpp_code = tiramisu_program.original_str.replace(
            tiramisu_program.code_gen_line, schedule_code
        )
        cpp_code = cpp_code.replace(
            f"// {tiramisu_program.wrapper_str}", tiramisu_program.wrapper_str
        )
        return cpp_code

    @classmethod
    def write_to_disk(cls, cpp_code: str, output_path: str, extension: str = ".cpp"):
        """
        Writes the code to a file

        Parameters
        ----------
        `cpp_code`: str
            The code to write to the file
        `output_path`: str
            The path of the file to write to
        `extension`: str
            The extension of the file
        """
        with open(output_path + extension, "w") as f:
            f.write(cpp_code)

    @classmethod
    def get_cpu_exec_times(
        cls,
        tiramisu_program: TiramisuProgram,
        optims_list: List[TiramisuAction],
        max_runs: int = 0,
        max_mins_per_schedule: float | None = None,
    ) -> List[float]:
        """
        Returns the execution times of the program on the CPU after applying the optimizations in the optims_list

        Parameters
        ----------
        `tiramisu_program`: `TiramisuProgram`
            The program to optimize
        `optims_list`: `List[TiramisuAction]`
            The list of optimizations to apply on the program
        `max_runs`: `int`
            The maximum number of times to run the program

        Returns
        -------
        `List[float]`
            The execution times of the program
        """
        if not BaseConfig.base_config:
            raise ValueError("BaseConfig not initialized")
        if (
            not tiramisu_program.name
            or not tiramisu_program.original_str
            or not tiramisu_program.wrappers
        ):
            raise ValueError("The program is not loaded yet")
        if max_runs is None:
            max_runs = BaseConfig.base_config.tiramisu.max_runs
        # Get the code of the schedule
        cpp_code = cls.get_schedule_code(tiramisu_program, optims_list)
        # Write the code to a file
        output_path = os.path.join(
            BaseConfig.base_config.workspace, tiramisu_program.name
        )

        cls.write_to_disk(cpp_code, output_path + "_schedule")

        # write the wrappers
        cls.write_to_disk(tiramisu_program.wrappers["cpp"], output_path + "_wrapper")
        cls.write_to_disk(
            tiramisu_program.wrappers["h"], output_path + "_wrapper", ".h"
        )

        env_vars = [
            f"export {key}={value}"
            for key, value in BaseConfig.base_config.env_vars.items()
        ]

        results = []

        if BaseConfig.base_config.tiramisu.is_new_tiramisu:
            # Making the tiramisu root path explicit to the env
            shell_script = [
                f"cd {BaseConfig.base_config.workspace}",
                # Compile intermidiate tiramisu file
                f"$CXX -I$TIRAMISU_ROOT/3rdParty/Halide/install/include -I$TIRAMISU_ROOT/include -I$TIRAMISU_ROOT/3rdParty/isl/include  -Wl,--no-as-needed -ldl -g -fno-rtti   -lpthread -std=c++17 -O0 -o {tiramisu_program.name}.o -c {tiramisu_program.name}_schedule.cpp",
                # Link generated file with executer
                f"$CXX -Wl,--no-as-needed -ldl -g -fno-rtti -lpthread -std=c++17 -O0 {tiramisu_program.name}.o -o {tiramisu_program.name}.out   -L$TIRAMISU_ROOT/build  -L$TIRAMISU_ROOT/3rdParty/Halide/install/lib64  -L$TIRAMISU_ROOT/3rdParty/isl/build/lib  -Wl,-rpath,$TIRAMISU_ROOT/build:$TIRAMISU_ROOT/3rdParty/Halide/install/lib64:$TIRAMISU_ROOT/3rdParty/isl/build/lib -ltiramisu -ltiramisu_auto_scheduler -lHalide -lisl",
                # Run the generator
                f"./{tiramisu_program.name}.out",
                # compile the wrapper
                f"$CXX -shared -o {tiramisu_program.name}.o.so {tiramisu_program.name}.o",
                f"$CXX -std=c++17 -fno-rtti -I$TIRAMISU_ROOT/include -I$TIRAMISU_ROOT/3rdParty/Halide/install/include -I$TIRAMISU_ROOT/3rdParty/isl/include/ -I$TIRAMISU_ROOT/benchmarks -L$TIRAMISU_ROOT/build -L$TIRAMISU_ROOT/3rdParty/Halide/install/lib64/ -L$TIRAMISU_ROOT/3rdParty/isl/build/lib -o {tiramisu_program.name}_wrapper -ltiramisu -lHalide -ldl -lpthread -lm -Wl,-rpath,$TIRAMISU_ROOT/build {tiramisu_program.name}_wrapper.cpp ./{tiramisu_program.name}.o.so -ltiramisu -lHalide -ldl -lpthread -lm -lisl",
            ]

        else:
            shell_script = [
                f"cd {BaseConfig.base_config.workspace}",
                # Compile intermidiate tiramisu file
                f"$CXX -I$TIRAMISU_ROOT/3rdParty/Halide/include -I$TIRAMISU_ROOT/include -I$TIRAMISU_ROOT/3rdParty/isl/include  -Wl,--no-as-needed -ldl -g -fno-rtti   -lpthread -std=c++11 -O0 -o {tiramisu_program.name}.o -c {tiramisu_program.name}_schedule.cpp",
                # Link generated file with executer
                f"$CXX -Wl,--no-as-needed -ldl -g -fno-rtti -lpthread -std=c++11 -O0 {tiramisu_program.name}.o -o {tiramisu_program.name}.out   -L$TIRAMISU_ROOT/build  -L$TIRAMISU_ROOT/3rdParty/Halide/lib  -L$TIRAMISU_ROOT/3rdParty/isl/build/lib  -Wl,-rpath,$TIRAMISU_ROOT/build:$TIRAMISU_ROOT/3rdParty/Halide/lib:$TIRAMISU_ROOT/3rdParty/isl/build/lib -ltiramisu -ltiramisu_auto_scheduler -lHalide -lisl",
                # Run the generator
                f"./{tiramisu_program.name}.out",
                # compile the wrapper
                f"$CXX -shared -o {tiramisu_program.name}.o.so {tiramisu_program.name}.o",
                f"$CXX -std=c++11 -fno-rtti -I$TIRAMISU_ROOT/include -I$TIRAMISU_ROOT/3rdParty/Halide/include -I$TIRAMISU_ROOT/3rdParty/isl/include/ -I$TIRAMISU_ROOT/benchmarks -L$TIRAMISU_ROOT/build -L$TIRAMISU_ROOT/3rdParty/Halide/lib/ -L$TIRAMISU_ROOT/3rdParty/isl/build/lib -o {tiramisu_program.name}_wrapper -ltiramisu -lHalide -ldl -lpthread -lm -Wl,-rpath,$TIRAMISU_ROOT/build {tiramisu_program.name}_wrapper.cpp ./{tiramisu_program.name}.o.so -ltiramisu -lHalide -ldl -lpthread -lm -lisl",
            ]

        try:
            # run the compilation of the generator and wrapper
            compiler = subprocess.run(
                [" ; ".join(env_vars + shell_script)],
                capture_output=True,
                text=True,
                shell=True,
                check=True,
            )

            halide_repr = compiler.stdout
            logging.debug(f"Generated Halide code:\n{halide_repr}")

            if max_mins_per_schedule:
                # run the wrapper and get the execution time
                compiler = subprocess.run(
                    [
                        " ; ".join(
                            env_vars
                            + CompilingService.get_n_runs_script(
                                max_runs=1, tiramisu_program=tiramisu_program
                            )
                        )
                    ],
                    capture_output=True,
                    text=True,
                    shell=True,
                    check=True,
                )

                if compiler.stdout:
                    max_millis_per_run = max_mins_per_schedule * 60 * 1000
                    exec_time = float(compiler.stdout)
                    results = [exec_time]
                    if exec_time > max_millis_per_run / max_runs:
                        max_runs = int(max_millis_per_run / exec_time)
                        max_runs = min(0, max_runs - 1)
                else:
                    raise ScheduleExecutionCrashed("No output from schedule execution")

            # run the wrapper and get the execution time
            compiler = subprocess.run(
                [
                    " ; ".join(
                        env_vars
                        + CompilingService.get_n_runs_script(
                            max_runs=max_runs,
                            tiramisu_program=tiramisu_program,
                            delete_files=True,
                        )
                    )
                ],
                capture_output=True,
                text=True,
                shell=True,
                check=True,
            )

            # Extract the execution times from the output and return the minimum
            if compiler.stdout:
                results += [float(x) for x in compiler.stdout.split()]
                return results
            else:
                logging.error("No output from schedule execution")
                logging.error(compiler.stderr)
                logging.error(compiler.stdout)
                logging.error(
                    f"The following schedule execution crashed: {tiramisu_program.name}, schedule: {optims_list} \n\n {cpp_code}\n\n"
                )
                raise ScheduleExecutionCrashed("No output from schedule execution")
        except subprocess.CalledProcessError as e:
            logging.error(f"Process terminated with error code: {e.returncode}")
            logging.error(f"Error output: {e.stderr}")
            logging.error(f"Output: {e.stdout}")
            raise ScheduleExecutionCrashed(
                f"Schedule execution crashed: function: {tiramisu_program.name}, schedule: {optims_list}"
            )
        except Exception as e:
            raise e

    def get_n_runs_script(
        tiramisu_program: TiramisuProgram, max_runs: int = 1, delete_files=False
    ):
        return [
            # cd to the workspace
            f"cd {BaseConfig.base_config.workspace}",
            #  set the env variables
            f"export DYNAMIC_RUNS=0",
            f"export MAX_RUNS={max_runs}",
            f"export NB_EXEC={max_runs}",
            # run the wrapper
            f"./{tiramisu_program.name}_wrapper",
            # Clean generated files
            f"rm {tiramisu_program.name}*" if delete_files else "",
        ]


class ScheduleExecutionCrashed(Exception):
    """Raised when the execution of the schedule crashes"""

    pass
