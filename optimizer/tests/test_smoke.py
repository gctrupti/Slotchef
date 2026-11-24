from ortools.sat.python import cp_model


def test_ortools_cp_sat_smoke() -> None:
    model = cp_model.CpModel()
    x = model.new_int_var(0, 10, "x")
    model.maximize(x)

    solver = cp_model.CpSolver()
    status = solver.solve(model)

    assert status == cp_model.OPTIMAL
    assert solver.value(x) == 10

