import argparse
import logging
from time import sleep
import time
from typing import Tuple
from athena.tiramisu.tiramisu_actions.fusion import Fusion
from athena.tiramisu import Schedule, TiramisuProgram, tiramisu_actions
from athena.tiramisu.compiling_service import CompilingService

import json

from athena.utils.config import BaseConfig


################################3


def get_schedule_str(program_json, sched_json):
    # to track order of iterators mapped to levels
    buffer_interchanges = {}
    reversal_buffer = {}
    skewing_buffer = {}
    affine_buffer = {}
    parallelization_buffer = {}
    t2_buffer = {}
    t3_buffer = {}
    U_buffer = {}

    # at this step we are getting the computation names

    comp_name = [
        n
        for n in sched_json.keys()
        if not n
        in [
            "unfuse_iterators",
            "tree_structure",
            "execution_times",
            "fusions",
            "sched_str",
            "legality_check",
            "exploration_method",
            "dependenceis_distance",
        ]
    ]

    # print(comp_name)

    sched_str = ""
    new_str = ""

    if "fusions" in sched_json and sched_json["fusions"]:
        for fusion in sched_json["fusions"]:
            sched_str += "F("
            new_str += "F("
            new_str += str(fusion[-1]) + ",comps=["

            for name in comp_name:
                if name in fusion:
                    sched_str += "'" + name + "'" + ","
                    new_str += "'" + name + "'" + ","

            sched_str = sched_str[:-1]
            sched_str += ")"
            new_str = new_str[:-1]
            new_str += "])|"

    # print(sched_str)

    for name in comp_name:
        transf_loop_nest = program_json["computations"][name]["iterators"].copy()
        # print(transf_loop_nest)
        schedule = sched_json[name]
        if "fusions" in sched_json and sched_json["fusions"]:
            for fusion in sched_json["fusions"]:
                # if this computation was involved in a fusion, we know it uses the same iterators as the computation it was fused with
                if name in fusion:
                    iterator_comp_name = fusion[0]
                    transf_loop_nest = program_json["computations"][iterator_comp_name][
                        "iterators"
                    ].copy()
                    schedule = sched_json[iterator_comp_name]

            # print(transf_loop_nest)

        # Change fusion to include loops
        sched_str += "{" + name + "}:"

        # print(sched_str)
        for transformation in schedule["transformations_list"]:
            if transformation[0] == 1:
                # buffer_interchanges.append({})
                if (
                    "I(L"
                    + str(transf_loop_nest[transformation[1]])
                    + ",L"
                    + str(transf_loop_nest[transformation[2]])
                    + ")"
                    in buffer_interchanges.keys()
                ):
                    buffer_interchanges[
                        "I(L"
                        + str(transf_loop_nest[transformation[1]])
                        + ",L"
                        + str(transf_loop_nest[transformation[2]])
                        + ")"
                    ]["comps"].append(name)
                else:
                    buffer_interchanges[
                        "I(L"
                        + str(transf_loop_nest[transformation[1]])
                        + ",L"
                        + str(transf_loop_nest[transformation[2]])
                        + ")"
                    ] = {
                        "levels": "I(L"
                        + str(transformation[1])
                        + ",L"
                        + str(transformation[2])
                        + ")",
                        "comps": [name],
                    }

                sched_str += (
                    "I(L" + str(transformation[1]) + ",L" + str(transformation[2]) + ")"
                )
                new_str += (
                    "I(L"
                    + str(transformation[1])
                    + ",L"
                    + str(transformation[2])
                    + ",comps="
                    + str([name])
                    + ")|"
                )

                # Change loop nest to reflect interchange

                # interchange = transf_loop_nest[transformation[1]]
                # transf_loop_nest[transformation[1]] = transf_loop_nest[
                #     transformation[2]
                # ]
                # transf_loop_nest[transformation[2]] = interchange

            elif transformation[0] == 2:
                sched_str += "R(L" + str(transformation[3]) + ")"

                if (
                    "R(L" + str(transf_loop_nest[transformation[3]]) + ")"
                    in reversal_buffer.keys()
                ):
                    reversal_buffer[
                        "R(L" + str(transf_loop_nest[transformation[3]]) + ")"
                    ]["comps"].append(name)
                else:
                    reversal_buffer[
                        "R(L" + str(transf_loop_nest[transformation[3]]) + ")"
                    ] = {
                        "levels": "R(L" + str(transformation[3]) + ")",
                        "comps": [name],
                    }

                new_str += (
                    "R(L" + str(transformation[3]) + ",comps=" + str([name]) + ")|"
                )
            elif transformation[0] == 3:
                if (
                    "S(L"
                    + str(transf_loop_nest[transformation[4]])
                    + ",L"
                    + str(transf_loop_nest[transformation[5]])
                    + ","
                    + str(transformation[6])
                    + ","
                    + str(transformation[7])
                    + ")"
                    in skewing_buffer.keys()
                ):
                    skewing_buffer[
                        "S(L"
                        + str(transf_loop_nest[transformation[4]])
                        + ",L"
                        + str(transf_loop_nest[transformation[5]])
                        + ","
                        + str(transformation[6])
                        + ","
                        + str(transformation[7])
                        + ")"
                    ]["comps"].append(name)
                else:
                    skewing_buffer[
                        "S(L"
                        + str(transf_loop_nest[transformation[4]])
                        + ",L"
                        + str(transf_loop_nest[transformation[5]])
                        + ","
                        + str(transformation[6])
                        + ","
                        + str(transformation[7])
                        + ")"
                    ] = {
                        "levels": "S(L"
                        + str(transformation[4])
                        + ",L"
                        + str(transformation[5])
                        + ","
                        + str(transformation[6])
                        + ","
                        + str(transformation[7])
                        + ")",
                        "comps": [name],
                    }

                sched_str += (
                    "S(L"
                    + str(transformation[4])
                    + ",L"
                    + str(transformation[5])
                    + ","
                    + str(transformation[6])
                    + ","
                    + str(transformation[7])
                    + ")"
                )
                new_str += (
                    "S(L"
                    + str(transformation[4])
                    + ",L"
                    + str(transformation[5])
                    + ","
                    + str(transformation[6])
                    + ","
                    + str(transformation[7])
                    + ",comps="
                    + str([name])
                    + ")|"
                )

        if schedule["parallelized_dim"]:
            dim_index = transf_loop_nest.index(schedule["parallelized_dim"])

            if (
                "P(L" + str(transf_loop_nest[dim_index]) + ")"
                in parallelization_buffer.keys()
            ):
                parallelization_buffer["P(L" + str(transf_loop_nest[dim_index]) + ")"][
                    "comps"
                ].append(name)
            else:
                parallelization_buffer[
                    "P(L" + str(transf_loop_nest[dim_index]) + ")"
                ] = {"levels": "P(L" + str(dim_index) + ")", "comps": [name]}

            sched_str += "P(L" + str(dim_index) + ")"
            new_str += "P(L" + str(dim_index) + ",comps=" + str([name]) + ")|"

        if schedule["shiftings"]:
            for shifting in schedule["shiftings"]:
                dim_index = transf_loop_nest.index(shifting[0])
                sched_str += "Sh(L" + str(dim_index) + "," + str(shifting[1]) + ")"

        if schedule["tiling"]:
            if schedule["tiling"]["tiling_depth"] == 2:
                first_dim = schedule["tiling"]["tiling_dims"][0]
                second_dim = schedule["tiling"]["tiling_dims"][1]

                first_dim_index = transf_loop_nest.index(first_dim)
                second_dim_index = transf_loop_nest.index(second_dim)
                first_factor = schedule["tiling"]["tiling_factors"][0]
                second_factor = schedule["tiling"]["tiling_factors"][1]

                if (
                    "T2(L"
                    + str(first_dim)
                    + ",L"
                    + str(second_dim)
                    + ","
                    + str(first_factor)
                    + ","
                    + str(second_factor)
                    + ")"
                    in t2_buffer.keys()
                ):
                    t2_buffer[
                        "T2(L"
                        + str(first_dim)
                        + ",L"
                        + str(second_dim)
                        + ","
                        + str(first_factor)
                        + ","
                        + str(second_factor)
                        + ")"
                    ]["comps"].append(name)
                else:
                    t2_buffer[
                        "T2(L"
                        + str(first_dim)
                        + ",L"
                        + str(second_dim)
                        + ","
                        + str(first_factor)
                        + ","
                        + str(second_factor)
                        + ")"
                    ] = {
                        "levels": "T2(L"
                        + str(first_dim_index)
                        + ",L"
                        + str(second_dim_index)
                        + ","
                        + str(first_factor)
                        + ","
                        + str(second_factor)
                        + ")",
                        "comps": [name],
                    }

                sched_str += (
                    "T2(L"
                    + str(first_dim_index)
                    + ",L"
                    + str(second_dim_index)
                    + ","
                    + str(first_factor)
                    + ","
                    + str(second_factor)
                    + ")"
                )

                new_str += (
                    "T2(L"
                    + str(first_dim_index)
                    + ",L"
                    + str(second_dim_index)
                    + ","
                    + str(first_factor)
                    + ","
                    + str(second_factor)
                    + ",comps="
                    + str([name])
                    + ")|"
                )

                i = transf_loop_nest.index(first_dim)
                transf_loop_nest[i : i + 1] = (
                    first_dim + "_outer",
                    second_dim + "_outer",
                )
                i = transf_loop_nest.index(second_dim)
                transf_loop_nest[i : i + 1] = (
                    first_dim + "_inner",
                    second_dim + "_inner",
                )
            else:
                first_dim = schedule["tiling"]["tiling_dims"][0]
                second_dim = schedule["tiling"]["tiling_dims"][1]
                third_dim = schedule["tiling"]["tiling_dims"][2]
                first_dim_index = transf_loop_nest.index(first_dim)
                second_dim_index = transf_loop_nest.index(second_dim)
                third_dim_index = transf_loop_nest.index(third_dim)
                first_factor = schedule["tiling"]["tiling_factors"][0]
                second_factor = schedule["tiling"]["tiling_factors"][1]
                third_factor = schedule["tiling"]["tiling_factors"][2]

                if (
                    "T3(L"
                    + str(first_dim)
                    + ",L"
                    + str(second_dim)
                    + ",L"
                    + str(third_dim)
                    + ","
                    + str(first_factor)
                    + ","
                    + str(second_factor)
                    + ","
                    + str(third_factor)
                    + ")"
                    in t3_buffer.keys()
                ):
                    t3_buffer[
                        "T3(L"
                        + str(first_dim)
                        + ",L"
                        + str(second_dim)
                        + ",L"
                        + str(third_dim)
                        + ","
                        + str(first_factor)
                        + ","
                        + str(second_factor)
                        + ","
                        + str(third_factor)
                        + ")"
                    ]["comps"].append(name)
                else:
                    t3_buffer[
                        "T3(L"
                        + str(first_dim)
                        + ",L"
                        + str(second_dim)
                        + ",L"
                        + str(third_dim)
                        + ","
                        + str(first_factor)
                        + ","
                        + str(second_factor)
                        + ","
                        + str(third_factor)
                        + ")"
                    ] = {
                        "levels": "T3(L"
                        + str(first_dim_index)
                        + ",L"
                        + str(second_dim_index)
                        + ",L"
                        + str(third_dim_index)
                        + ","
                        + str(first_factor)
                        + ","
                        + str(second_factor)
                        + ","
                        + str(third_factor)
                        + ")",
                        "comps": [name],
                    }

                sched_str += (
                    "T3(L"
                    + str(first_dim_index)
                    + ",L"
                    + str(second_dim_index)
                    + ",L"
                    + str(third_dim_index)
                    + ","
                    + str(first_factor)
                    + ","
                    + str(second_factor)
                    + ","
                    + str(third_factor)
                    + ")"
                )
                new_str += (
                    "T3(L"
                    + str(first_dim_index)
                    + ",L"
                    + str(second_dim_index)
                    + ",L"
                    + str(third_dim_index)
                    + ","
                    + str(first_factor)
                    + ","
                    + str(second_factor)
                    + ","
                    + str(third_factor)
                    + ",comps="
                    + str([name])
                    + ")|"
                )

                i = transf_loop_nest.index(first_dim)
                transf_loop_nest[i : i + 1] = (
                    first_dim + "_outer",
                    second_dim + "_outer",
                    third_dim + "_outer",
                )
                i = transf_loop_nest.index(second_dim)
                transf_loop_nest[i : i + 1] = (
                    first_dim + "_inner",
                    second_dim + "_inner",
                    third_dim + "_inner",
                )
                transf_loop_nest.remove(third_dim)
        # print(transf_loop_nest)
        if schedule["unrolling_factor"]:
            dim_index = len(transf_loop_nest) - 1
            dim_name = transf_loop_nest[-1]

            if (
                "U(L" + str(dim_name) + "," + schedule["unrolling_factor"] + ")"
                in U_buffer.keys()
            ):
                U_buffer[
                    "U(L" + str(dim_name) + "," + schedule["unrolling_factor"] + ")"
                ]["comps"].append(name)
            else:
                U_buffer[
                    "U(L" + str(dim_name) + "," + schedule["unrolling_factor"] + ")"
                ] = {
                    "levels": "U(L"
                    + str(dim_index)
                    + ","
                    + schedule["unrolling_factor"]
                    + ")",
                    "comps": [name],
                }

            sched_str += (
                "U(L" + str(dim_index) + "," + schedule["unrolling_factor"] + ")"
            )
            new_str += (
                "U(L"
                + str(dim_index)
                + ","
                + schedule["unrolling_factor"]
                + ",comps="
                + str([name])
                + ")|"
            )

            transf_loop_nest[dim_index : dim_index + 1] = (
                dim_name + "_Uouter",
                dim_name + "_Uinner",
            )

    print(sched_str)
    # print(transf_loop_nest)
    # print(buffer_interchanges)
    # print(reversal_buffer)
    # print(skewing_buffer)
    # print(parallelization_buffer)
    # print(t2_buffer)
    # print(t3_buffer)
    # print(U_buffer)

    # for index, item in enumerate(buffer_interchanges):
    #     new_str += buffer_interchanges[item]['levels'][:-1] + ',comps=' + str(buffer_interchanges[item]['comps']) + ")|"
    # for index, item in enumerate(reversal_buffer):
    #     new_str += reversal_buffer[item]['levels'][:-1] + ',comps=' + str(reversal_buffer[item]['comps']) + ")|"

    # for index, item in enumerate(skewing_buffer):
    #     new_str += skewing_buffer[item]['levels'][:-1] + ',comps=' + str(skewing_buffer[item]['comps']) + ")|"

    # for index, item in enumerate(parallelization_buffer):
    #     new_str += parallelization_buffer[item]['levels'][:-1] + ',comps=' + str(parallelization_buffer[item]['comps']) + ")|"

    # for index, item in enumerate(t2_buffer):
    #     new_str += t2_buffer[item]['levels'][:-1] + ',comps=' + str(t2_buffer[item]['comps']) + ")|"

    # for index, item in enumerate(t3_buffer):
    #     new_str += t3_buffer[item]['levels'][:-1] + ',comps=' + str(t3_buffer[item]['comps']) + ")|"

    # for index, item in enumerate(U_buffer):
    #     new_str += U_buffer[item]['levels'][:-1] + ',comps=' + str(U_buffer[item]['comps'])    + ")|"

    new_str = new_str[:-1]

    print(new_str)

    # add fusion there don't forget it
    # create str that will contain the data
    # loop over the
    return new_str


main_dataset_path1 = "function_gramschmidt_explored_schedules.json"
main_dataset_path2 = "function606428_explored_schedules.json"
main_dataset_path = "function800111_explored_schedules.json"


def read_json_file(file_path):
    with open(file_path, "r") as file:
        data = json.load(file)
    return data


main_dataset = read_json_file(main_dataset_path)
####################################

# def function_to_run(dataset_actor: DatasetActor, id: int, progress_actor: "ProgressActor", suffix: str = None):  # type: ignore
#     while True:
#         next_program = dataset_actor.get_next_function()

#         legalities, solver_results = generate_legalities_random_schedules(
#             next_program, id_worker=id, log_file=f"athena_search_{suffix}.log"
#         )

#         next_program.schedules_legality.update(legalities)
#         next_program.schedules_solver.update(solver_results)

#         assert next_program.name

#         dataset_actor.update_dataset(
#             next_program.name,
#             {
#                 "schedules_legality": next_program.schedules_legality,
#                 "schedules_solver": next_program.schedules_solver,
#             },
#             suffix=f"{suffix}",
#         )

#         logging.info(
#             f"Progress Report: worker {id} generated {len(legalities)} schedules and {len(solver_results)} solver results"
#         )


if __name__ == "__main__":
    BaseConfig.init(logging_level=logging.INFO)
    assert BaseConfig.base_config

    suffix = time.time()

    # sched_str = "R(L1,comps=['R_up_init', 'R_up', 'A_out'])|R(L2,comps=['A_out'])"

    # sched_str = "R(L1,comps=['R_up_init'])|R(L1,comps=['R_up'])|R(L2,comps=['A_out'])|R(L1,comps=['A_out'])"
    # dataset_actor = DatasetActor(BaseConfig.base_config.dataset)

    # next_program = dataset_actor.get_next_function()

    # schedule = Schedule(next_program)

    # print(schedule.apply_schedule(3, 0.000001))
    # print(schedule.apply_schedule(3))

    # matmul = TiramisuProgram.from_file(
    #     "./examples/function_matmul_MEDIUM.cpp", load_annotations=True, load_tree=True
    # )

    # schedule = Schedule(matmul)

    # print(schedule.apply_schedule(3))

    # assert schedule.tree

    # schedule.add_optimizations(
    #     [tiramisu_actions.Parallelization(params=[("comp02", 0)])]
    # )

    # print(schedule.apply_schedule(3))

    # matmul = TiramisuProgram.from_file(
    # "./function_gramschmidt_generator.cpp", load_annotations=True, load_tree=True
    # )

    # matmul = TiramisuProgram.from_file(
    #     "./function_606428_generator.cpp", load_annotations=True, load_tree=True
    # )
    matmul = TiramisuProgram.from_file(
        "./function_800111_generator.cpp", load_annotations=True, load_tree=True
    )
    schedule = Schedule(matmul)
    ################### this is a modification
    # print(schedule.apply_schedule(3))

    assert schedule.tree

    matmul_name = matmul.name

    for index, item in enumerate(main_dataset["schedules_list"]):
        sched_str = get_schedule_str(main_dataset["program_annotation"], item)
        # print(matmul.set_name(matmul.name + str(index)))
        # if sched_str == None : pass
        # sched_str = "S(L0,L1,0,1,comps=['comp00'])"
        sched_str = "F(2,comps=['comp00','comp01'])|S(L1,L2,0,1,comps=['comp00'])|S(L1,L2,0,1,comps=['comp01'])"
        # sched_str = "I(L0,L1,comps=['comp00'])|P(L0,comps=['comp00'])|I(L0,L1,comps=['comp01'])|P(L0,comps=['comp01'])"
        new_schd = Schedule.from_sched_str(sched_str, matmul)
        # print(new_schd.set_name(TiramisuProgram.__name__ + str(index)))

        # CompilingService.get_schedule_code(matmul,new_schd)
        # print(new_schd)
        print(new_schd.apply_schedule())
        # matmul.set_name(matmul_name)

    # schedule.add_optimizations(
    # [
    #     tiramisu_actions.Reversal(
    #         [
    #             ("A_out", 2),
    #         ]
    #     ),
    #     tiramisu_actions.Parallelization(
    #         [
    #             ("Q_out", 1),
    #         ]
    #     ),
    # ]
    #         [
    #     tiramisu_actions.Reversal(
    #         [
    #             ("Q_out", 1),
    #         ]
    #     ),
    #     tiramisu_actions.Reversal([("A_out", 2)]),
    # ],
    # [tiramisu_actions.Reversal([("A_out", 2)])],
    # [tiramisu_actions.Parallelization([("Q_out",1)])],
    #   [tiramisu_actions.Unrolling([("Q_out",1),4])],
    # )

    # print(schedule.apply_schedule(3))

###################################################################3

new_schd = Schedule.from_sched_str(sched_str, matmul)
# print(new_schd)

print(new_schd.apply_schedule(3))
