from exceptions import InvalidSolverName

def get_client_conf(solver, config_path=None):
    """Returns the client_conf dict used by models to access D-Wave APIs.

    Args:
        solver (string):
            The solver name as specified in the client_config.conf file.
            '2000Q' for DW_2000Q_6
            'advantage1' for Advantage_system1.1
            'advantage4' for Advantage_system4.1
            'bmq_hybrid' for hybrid_binary_quadratic_model_version2

        config_path (optional):
            If provided it contains the path that points to the user
            defined client_config.conf file. Care that the solver
            parameter has to follow the same convension of the file
            present in resources.

    Returns:
        dict: the dictionary used by models executing on D-Wave solvers.

    Raises:
        InvalidSolverName: when the solver string does not match any of
        the possible solvers available on D-Wave.
    """
    valid_solvers = [
        '2000Q',
        'advantage1',
        'advantage4',
        'bqm_hybrid'
    ]
    if solver not in valid_solvers:
        raise InvalidSolverName("The solver name provided does not match any of the possible solvers provided by D-Wave")

    if config_path is None:
        correct_path = '../resources/client_config.conf'
    else:
        correct_path = config_path

    return {
        'config_path': correct_path,
        'profile': solver
    }