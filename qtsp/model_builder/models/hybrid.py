from dwave.system.samplers import DWaveSampler
from hybrid.reference.kerberos import KerberosSampler


class Hybrid_Model(ModelBuilder):
    hybrid_parameters = None

    def __init__(self, hamiltonian, client_conf):
        super(Hybrid_Model, self).__init__(hamiltonian)
        self.qpu_sampler = DWaveSampler(config_file=client_conf['config_path'], profile=client_conf['profile'])

    def set_parameters(self, params_dict):
        self.hybrid_parameters = params_dict

    def solve_hybrid(self, do_print):
        sampler = KerberosSampler()
        h_response = sampler.sample(self.BQM,
                                    init_sample=None,
                                    num_reads=self.hybrid_parameters['hybrid_num_reads'],
                                    max_iter=self.hybrid_parameters['max_iter'],
                                    convergence=self.hybrid_parameters['convergence'],
                                    sa_reads=self.hybrid_parameters['sa_reads'],
                                    qpu_reads=self.hybrid_parameters['qpu_reads'],
                                    qpu_sampler=self.qpu_sampler,
                                    qpu_params=self.hybrid_parameters['qpu_params'])

        h_result = Result(h_response, do_print=do_print)

        return h_result