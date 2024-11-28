import torch
from torch.utils.data import Dataset

from data.augmentations import RandomRemoveNodes, RandomShiftChannel, \
    RandomShiftTime, RandomSpreadChannel, RandomSpreadTime

class SpikingDS(Dataset):
    def __init__(self,
                 files,
                 config,
                 train: bool = True):
        
        self.config = config

        self.files = files

        self.time_window = config.general.time_window
        self.num_channels = config.general.num_channels

        self.time_radius = config.graph.time_radius
        self.channel_radius = config.graph.channel_radius
        self.skip_channels = config.graph.skip_channels

        self.features = config.graph.features
        self.train = train

        # Augmentations
        if train:
            self.random_remove_nodes = RandomRemoveNodes()
            self.random_shift_time = RandomShiftTime(time_window=self.time_window)
            self.random_shift_channel = RandomShiftChannel(channels=self.num_channels)
            self.random_spread_time = RandomSpreadTime(time_window=self.time_window)
            self.random_spread_channel = RandomSpreadChannel(channels=self.num_channels)

    def __len__(self) -> int:
        return len(self.files)
    
    def __getitem__(self, index: int):
        data_file = self.files[index]
        data = torch.load(data_file, weights_only=False)

        # TODO: Implement augmentations here
        if self.train:
            data = self.random_remove_nodes(data)
            data = self.random_shift_time(data)
            data = self.random_shift_channel(data)
            # data = self.random_spread_time(data)
            # data = self.random_spread_channel(data)

        data.pos[:, 0] = data.pos[:, 0] - data.pos[0, 0] # Start time from 0
        mask = data.pos[:, 0] < self.time_window
        data.pos = data.pos[mask] # Cut data to time window

        # Generate edge_index

        if self.features:
            data.edge_index, data.x = self.generate_edges(data.pos[:, 0], 
                                                        data.pos[:, 1])
        else:
            data.edge_index = self.generate_edges(data.pos[:, 0], 
                                                  data.pos[:, 1])

        # TODO: Calculate node features here outside the generate_edges function
        
        # Normalise node positions
        data.pos[:, 0] = data.pos[:, 0] / self.time_window
        data.pos[:, 1] = data.pos[:, 1] / self.num_channels

        return data
    
    def generate_edges(self, 
                       times: torch.Tensor, 
                       channels: torch.Tensor):
        edges = []
        feature = []
        
        channel_last_event = [None] * self.num_channels

        for idx, (time, channel) in enumerate(zip(times, channels)):

            sum_t = 0
            sum_channel = 0
            sum_idx = 0

            time, channel = time.item(), channel.item()

            for n_channel in range(max(0, int(channel - self.channel_radius)), 
                                   min(self.num_channels - 1, int(channel + self.channel_radius + 1)), 
                                   self.skip_channels):
                
                if channel_last_event[n_channel] is not None:
                    n_time, n_idx = channel_last_event[n_channel]

                    if time - n_time <= self.time_radius:
                        edges.append((n_idx, idx))

                        if self.features == 'local':
                            sum_t += (time - n_time)
                            sum_channel += (channel - n_channel)
                        
                        elif self.features == 'global':
                            sum_t += n_time
                            sum_channel += n_channel

                        sum_idx += 1

            if sum_idx == 0:
                mean_t = 0
                mean_channel = 0
            else:
                mean_t = sum_t / sum_idx
                mean_channel = sum_channel / sum_idx

            channel_last_event[int(channel)] = (time, idx)

            if self.features == 'local':
                feature.append([mean_t / self.time_radius, mean_channel / self.channel_radius])
            elif self.features == 'global':
                feature.append([mean_t / self.time_window, mean_channel / self.num_channels])
        
        edges = torch.tensor(edges).t().contiguous()

        if self.features:
            feature = torch.tensor(feature)
            return edges, feature
        
        return edges