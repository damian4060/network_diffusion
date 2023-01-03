# Copyright 2022 by Michał Czuba, Piotr Bródka. All Rights Reserved.
#
# This file is part of Network Diffusion.
#
# Network Diffusion is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 3 of the License, or (at your option) any
# later version.
#
# Network Diffusion is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the  GNU General Public License for
# more details.
#
# You should have received a copy of the GNU General Public License along with
# Network Diffusion. If not, see <http://www.gnu.org/licenses/>.
# =============================================================================

"""Functions for the phenomena spreading definition."""
from typing import List

from tqdm import tqdm

from network_diffusion.experiment_logger import ExperimentLogger
from network_diffusion.mln.mln_network import MultilayerNetwork
from network_diffusion.models.base_model import BaseModel
from network_diffusion.models.utils.types import NetworkUpdateBuffer


class MultiSpreading:
    """Perform experiment defined by PropagationModel on MultiLayerNetwork."""

    def __init__(self, model: BaseModel, network: MultilayerNetwork) -> None:
        """
        Construct an object.

        :param model: model of propagation which determines how experiment
            looks like
        :param network: a network which is being examined during experiment
        """
        self._model = model
        self._network = network
        self.stopping_counter = 0

    def _update_counter(
        self, nodes_to_update: List[NetworkUpdateBuffer]
    ) -> None:
        """Update a counter of dead epochs."""
        if len(nodes_to_update) == 0:
            self.stopping_counter += 1
        else:
            self.stopping_counter = 0

    def perform_propagation(
        self, n_epochs: int, stop_on_hold: bool = False
    ) -> ExperimentLogger:
        """
        Perform experiment on given network and given model.

        It saves logs in ExperimentLogger object which can be used for further
        analysis.

        :param n_epochs: number of epochs to do experiment
        :param stop_on_hold: stop if there was no propagation in last 5 epochs
        :return: logs of experiment stored in special object
        """
        logger = ExperimentLogger(str(self._model), str(self._network))

        # set and add logs from initialising states
        self._model.set_initial_states(self._network)
        logger.add_global_stat(self._network.get_nodes_states())

        # iterate through epochs
        progress_bar = tqdm(range(n_epochs))
        for epoch in progress_bar:
            progress_bar.set_description_str(f"Processing epoch {epoch}")

            # do a forward step and update network
            nodes_to_update = self._model.network_evaluation_step(
                self._network
            )
            epoch_json = self._model.update_network(
                self._network, nodes_to_update
            )

            # add logs from current epoch
            logger.add_global_stat(self._network.get_nodes_states())
            logger.add_local_stat(epoch, epoch_json)

            # check if there is no progress and therefore stop simulation
            if stop_on_hold:
                self._update_counter(nodes_to_update)
                if self.stopping_counter >= 5:
                    progress_bar.set_description_str(
                        "Experiment stopped - no progress in last 5 epochs!"
                    )
                    break

        # convert logs to dataframe
        logger.convert_logs(self._model.get_allowed_states(self._network))

        return logger
