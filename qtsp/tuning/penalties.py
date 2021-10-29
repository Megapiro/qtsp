from src.code.quantum_annealing.hamiltonian_builder import HamiltonianBuilder
from src.dataset.parse_experiments import get_embedding

num_samples = 5
np_num_reads = 5000


def __build_hamiltonian(distance_matrix, charge_array, norm_dict):
    hamiltonian_with_charge = HamiltonianBuilder(distance_matrix, charge_array)
    H_with_charge = hamiltonian_with_charge.get_hamiltonian(norm_dict)

    return H_with_charge


def __execute_exp(tuning_mode, exp, distance_matrix, charge_array, client_conf, norm_dict):
    hamiltonian = __build_hamiltonian(distance_matrix, charge_array, norm_dict)
    exp_model = QPU_Model(hamiltonian, client_conf, get_embedding())
    exp_res = exp_model.solve(np_num_reads, exp.qpu_experiment.chain_strength,
                              'normalization parameters fine tuning starting from ' + tuning_mode +
                              ' num_reads = ' + str(np_num_reads),
                              do_print=False)

    return exp_res


def __compare_results_on_norm_dicts(mode, results_dicts, mode_parameters):
    best_index = dicts_comparer(mode, results_dicts, mode_parameters)

    return (results_dicts[1])[best_index]


# Methods for tuning normalization hyperparameters starting from the value present in the default dict


def __get_random_bs_cs(default_a, max_W, max_Q):
    bs_cs = []

    # compute initial B and C starting from default A
    C = int(default_a / max_Q)
    B = int(C / max_W)

    # A >> C >> B
    magnitudes = [10, 100, 1000]

    for m in magnitudes:
        first = True
        ran_sums = random.sample(range(m), num_samples)
        C = int(C / m)
        mag_c = math.floor(math.log(C, 10))
        mag_b = math.floor(math.log(B, 10))

        # compare magnitudes of B and C to be sure that C >> B
        if mag_c / mag_b > 2:
            for s in ran_sums:
                C += s
                B += s

                if first:
                    bs_cs.append([B])
                    bs_cs.append([C])

                    first = False

                bs_cs[0].append(B)
                bs_cs[1].append(C)

    return bs_cs


def __fine_tune_a(exp, distance_matrix, charge_array, client_conf, def_norm_dict, default_a, max_W, max_Q):
    results_dicts = []

    # build hamiltonian and execute model for default dict
    exp_res = __execute_exp('A', exp, distance_matrix, charge_array, client_conf, def_norm_dict)
    results_dicts.append([exp_res])
    results_dicts.append([np.array(list(def_norm_dict.values()))])

    # for every couple of B and C generated we set the dictionary and execute the model
    bs_cs = __get_random_bs_cs(default_a, max_W, max_Q)
    for i in range(len(bs_cs[0])):
        B = (bs_cs[0])[i]
        C = (bs_cs[1])[i]

        tuned_dict = {
            'A_Normalization': default_a,
            'B_Normalization': B,
            'C_Normalization': C
        }

        # once we have A, B and C we build the hamiltonian and execute the model
        tuned_res = __execute_exp('A', exp, distance_matrix, charge_array, client_conf, tuned_dict)

        # now we can append result and dict to the double array
        results_dicts[0].append(tuned_res)
        results_dicts[1].append(np.array(list(tuned_dict.values())))

    best_dict = __compare_results_on_norm_dicts('A', results_dicts, default_a)

    return best_dict


# Methods for tuning normalization hyperparameters starting from random initializations of B


def __init_b(default_b):
    # initialize a list of b normalization values of the same magnitude order of the default b
    mag_order = math.floor(math.log(default_b, 10))
    int_list = random.sample(range(10**mag_order, 10**(mag_order + 1)), num_samples)
    b_list = [x for x in int_list]

    return b_list


def __fine_tune_b(exp, distance_matrix, charge_array, client_conf, def_norm_dict, random_bs, max_W, max_Q):
    results_dicts = []

    # build hamiltonian and execute model for default dict
    exp_res = __execute_exp('B', exp, distance_matrix, charge_array, client_conf, def_norm_dict)
    results_dicts.append([exp_res])
    results_dicts.append([np.array(list(def_norm_dict.values()))])

    # for every B in random_bs compute A and C and execute the model
    for B in random_bs:
        C = B * max_W * 100
        A = C * max_Q

        tuned_dict = {
            'A_Normalization': A,
            'B_Normalization': B,
            'C_Normalization': C
        }

        # once we have A, B and C we build the hamiltonian and execute the model
        tuned_res = __execute_exp('B', exp, distance_matrix, charge_array, client_conf, tuned_dict)

        # now we can append result and dict to the double array
        results_dicts[0].append(tuned_res)
        results_dicts[1].append(np.array(list(tuned_dict.values())))

    best_dict = __compare_results_on_norm_dicts('B', results_dicts, random_bs)

    return {'A_Normalization': best_dict[0], 'B_Normalization': best_dict[1], 'C_Normalization': best_dict[2]}


def tune_norm_parameters_abc(mode, exp, def_norm_dict, distance_matrix, charge_array, client_conf):
    # compute multiplicative factors
    max_W = np.amax(distance_matrix)
    max_charge = np.amax(charge_array)
    min_charge = np.amin(charge_array)
    max_Q = (max_charge - min_charge)**2

    if mode == 'A':
        default_a = def_norm_dict['A_Normalization']
        tuned_dict = __fine_tune_a(exp, distance_matrix, charge_array, client_conf, def_norm_dict, default_a, max_W,
                                   max_Q)
    else:
        # randomly initialize B
        default_b = def_norm_dict['B_Normalization']
        random_bs = __init_b(default_b)
        tuned_dict = __fine_tune_b(exp, distance_matrix, charge_array, client_conf, def_norm_dict, random_bs, max_W,
                                   max_Q)

    return tuned_dict
