import itertools
import dwave.inspector
import numpy as np
import os
import pandas as pd

from matplotlib import pyplot as plt


def __get_best_lines(dataframe, parameter_type):
    # drop Mean Enery and Best columns
    dataframe = dataframe.drop(columns=['Mean Energy', 'Best'])

    # first get all the lines that have at least a solution
    df_with_sol = dataframe.loc[dataframe['Correct Sol Num'] >= 1]

    # then all the lines that have the minimum energy
    df_min_energy = dataframe.loc[dataframe['Energy'] == dataframe['Energy'].min()]

    df_best_lines = pd.concat([df_with_sol, df_min_energy], axis=0)
    df_best_lines.insert(1, 'Type', parameter_type)

    return df_best_lines


def write_results(num_nodes):
    # first of all we add to the paths the directory of the experiment executed
    results_path = '../resources/results/' + str(num_nodes) + '/'
    csv_path = '../resources/performance/'
    norm_path = csv_path + 'norm_abc/' + str(num_nodes)
    chain_path = csv_path + 'chain_strength/' + str(num_nodes)
    anneal_path = csv_path + 'anneal_schedule/' + str(num_nodes)

    # once we have the paths we can read the datasets
    chain_csv = os.listdir(chain_path)
    anneal_csv = os.listdir(anneal_path)

    chain_df = read_input(os.path.join(chain_path, chain_csv[0]), ',')  # change it if only one chain csv is present
    chain_df = chain_df.rename(columns={'Chain Strength': 'Parameter'})
    pause_df = read_input(os.path.join(anneal_path, anneal_csv[0]), ',')  # anneal csv are always ordered as: p,pq and q
    pause_df = pause_df.rename(columns={'Schedule': 'Parameter'})
    quench_df = read_input(os.path.join(anneal_path, anneal_csv[2]), ',')
    quench_df = quench_df.rename(columns={'Schedule': 'Parameter'})
    pause_quench_df = read_input(os.path.join(anneal_path, anneal_csv[1]), ',')
    pause_quench_df = pause_quench_df.rename(columns={'Schedule': 'Parameter'})

    # create the results dataframe
    results_df = pd.DataFrame(columns=['Parameter', 'Type', 'Energy', 'Correct Sol Num', 'QPU Access Time',
                                       'QPU Programming Time'])

    # for each csv line we keep all lines that have at least one correct solution and those that have the minimum energy
    # 0 -> chain type
    # 1 -> pause, quench, pause or quench
    results_df = pd.concat([results_df, __get_best_lines(chain_df, 0)], axis=0)
    results_df = pd.concat([results_df, __get_best_lines(pause_df, 1)], axis=0)
    results_df = pd.concat([results_df, __get_best_lines(quench_df, 2)], axis=0)
    results_df = pd.concat([results_df, __get_best_lines(pause_quench_df, 3)], axis=0)

    # finally once the results dataframe is built we can write it
    results_path += 'performance_results.csv'
    results_df.to_csv(results_path, index=False)


def __get_best(dataframe):
    temp_df = dataframe.loc[dataframe['Correct Sol Num'] >= 1]

    if len(temp_df.index) == 0:
        temp_df = dataframe.loc[dataframe['Energy'] == dataframe['Energy'].min()]
    else:
        temp_df = temp_df.loc[temp_df['Energy'] == temp_df['Energy'].min()]

    if len(temp_df.index) > 1:
        temp_df = temp_df.loc[temp_df['QPU Access Time'] == temp_df['QPU Access Time'].min()]

    return temp_df['Parameter']


def get_best_parameters(num_nodes):
    csv_results_path = '../resources/results/' + str(num_nodes) + '/performance_results.csv'
    results_df = read_input(csv_results_path, ',')

    best_chain = round(float(__get_best(results_df.loc[results_df['Type'] == 0]).values[0]), 2)
    best_schedule = __get_best(results_df.loc[results_df['Type'] != 0]).values[0]
    bs = best_schedule.replace("[", "").replace("]", "").split(',')

    best_schedule = [[float(bs[i]), float(bs[i + 1])] for i in range(0, len(bs), 2)]

    return best_chain, best_schedule

def embedding_inspector(qpu_res: Result):
    # if we have a decorator incompatible version for dwave-networkx just upgrade it
    # pip install dwave-networkx --upgrade
    dwave.inspector.show(qpu_res.response)


def histogram_energies(sampleset_SA, sampleset_QPU):
    # Plot energy histograms for both QPUs
    num_bins = 100
    use_bin = 50

    fig = plt.figure(figsize=(8, 5))
    SA = sampleset_SA.record.energy
    QPU = sampleset_QPU.record.energy

    bins=np.histogram(np.hstack((SA, QPU)), bins=num_bins)[1]

    ax = fig.add_subplot(1, 1, 1)

    ax.hist(SA, bins[0:use_bin], color='g', alpha=0.4, label="SA")
    ax.hist(QPU, bins[0:use_bin], color='r', alpha=0.4, label="QPU")

    ax.set_xlabel("Energy")
    ax.set_ylabel("Samples")
    ax.legend()
    plt.show()

def qubits_number(embedded_graph):
    # return the number of qubits required in the embedding
    sublist = [values for keys, values in embedded_graph.items()]
    flat_list = set(itertools.chain(*sublist))

    return len(flat_list)


def chain_lengths(embedded_graph):
    # return the in and max chain length in the embedding provided
    max_chain_length = None
    min_chain_length = None

    for _, chain in embedded_graph.items():
        if max_chain_length is None:
            max_chain_length = len(chain)
            min_chain_length = len(chain)

        if len(chain) > max_chain_length:
            max_chain_length = len(chain)

        if len(chain) < min_chain_length:
            min_chain_length = len(chain)

    return min_chain_length, max_chain_length