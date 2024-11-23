import torch
from torch.utils.data import Dataset

class SpikingDS(Dataset):
    def __init__(self,
                 files,
                 config):
        
        self.config = config

        self.files = files

        self.time_window = config.general.time_window
        self.num_channels = config.general.num_channels

        self.time_radius = config.graph.time_radius
        self.channel_radius = config.graph.channel_radius

    def __len__(self) -> int:
        return len(self.files)
    
    def __getitem__(self, index: int):
        data_file = self.files[index]
        data = torch.load(data_file, weights_only=False)

        # TODO: Implement augmentations here

        data.pos[:, 0] = data.pos[:, 0] - data.pos[0, 0] # Start time from 0
        mask = data.pos[:, 0] < self.time_window
        data.pos = data.pos[mask] # Cut data to time window

        # TODO: Generate edge_index here
        data.edge_index = self.generate_edges(data.pos[:, 0], 
                                              data.pos[:, 1],
                                              self.time_radius,
                                              self.channel_radius)

        # TODO: Normalise node positions here
        data.pos[:, 0] = data.pos[:, 0] / self.time_window
        data.pos[:, 1] = data.pos[:, 1] / self.num_channels

        # TODO: Generate node features here
        data.x = torch.ones(data.pos.shape[0], 1)

        return data
    
    def generate_edges(self, 
                       times: torch.Tensor, 
                       channels: torch.Tensor, 
                       time_radius: float = 0.02, 
                       channel_radius: int = 10):
        edges = []
        channel_last_event = [None] * self.num_channels

        for idx, (time, channel) in enumerate(zip(times, channels)):
            time, channel = time.item(), channel.item()

            for n_channel in (max(0, int(channel - channel_radius)), 
                              min(self.num_channels - 1, int(channel + channel_radius + 1))):
                
                if channel_last_event[n_channel] is not None:
                    n_time, n_idx = channel_last_event[n_channel]

                    if time - n_time <= time_radius:
                        edges.append((n_idx, idx))

            channel_last_event[int(channel)] = (time, idx)

        edges = torch.tensor(edges).t().contiguous()
        return edges

    # @torch.jit.script
    # def generate_edges(times: torch.Tensor, 
    #                    channels: torch.Tensor,
    #                    num_channels: int,
    #                    time_radius: float,
    #                    channel_radius: int) -> torch.Tensor:
    #     # Calculate the maximum possible number of edges
    #     max_edges = times.size(0) * (2 * channel_radius + 1)
        
    #     # Preallocate edges tensor
    #     edges = torch.full((max_edges, 2), -1, dtype=torch.int32)

    #     # Create tensor to store the last event for each channel
    #     channel_last_event = torch.full((num_channels, 2), -1, dtype=torch.float32)  # [time, idx]
    #     edge_count = 0

    #     for idx in range(times.size(0)):
    #         time = times[idx].item()
    #         channel = channels[idx].item()

    #         # Determine the range of channels to check
    #         min_channel = max(0, int(channel - channel_radius))
    #         max_channel = min(num_channels - 1, int(channel + channel_radius))

    #         # Check for edges within the channel range
    #         for n_channel in range(min_channel, max_channel + 1):
    #             n_time = float(channel_last_event[n_channel, 0])
    #             n_idx = int(channel_last_event[n_channel, 1])
    #             if n_idx != -1 and time - n_time <= time_radius:
    #                 edges[edge_count, 0] = int(n_idx)
    #                 edges[edge_count, 1] = idx
    #                 edge_count += 1

    #         # Update the last event for the current channel
    #         channel_last_event[int(channel), 0] = time
    #         channel_last_event[int(channel), 1] = float(idx)

    #     # Trim unused space in edges tensor
    #     edges = edges[:edge_count].t().contiguous()
    #     return edges