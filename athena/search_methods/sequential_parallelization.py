from athena.tiramisu.schedule import Schedule
from athena.tiramisu.tiramisu_actions.parallelization import Parallelization
from athena.tiramisu.tiramisu_program import TiramisuProgram


def parallelize_first_legal_outermost(
    tiramisu_program: TiramisuProgram,
) -> Schedule:
    schedule = Schedule(tiramisu_program)
    candidates_per_root = Parallelization.get_candidates(tiramisu_program.tree)

    for root in tiramisu_program.tree.roots:
        tmp_schedule = schedule.copy()
        for candidate in candidates_per_root[root]:
            for node in candidate:
                comps = tiramisu_program.tree.get_iterator_subtree_computations(node)
                tmp_schedule.add_optimizations(
                    [
                        Parallelization(
                            [(comps[0], tiramisu_program.tree.iterators[node].level)]
                        )
                    ]
                )
            if tmp_schedule.is_legal():
                schedule = tmp_schedule
                break

    if not schedule.optims_list:
        return None
    return schedule
