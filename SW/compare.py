import numpy as np
import torch

import edge_generator

def generate_edges(times: torch.Tensor, 
                    channels: torch.Tensor,
                    features: str = 'global',
                    time_radius: float = 0.02,
                    time_window: float = 1,
                    channel_radius: int = 100,
                    skip_channels: int = 10,
                    num_channels: int = 700):
    edges = []
    feature = []
    
    channel_last_event = [None] * 700

    for idx, (time, channel) in enumerate(zip(times, channels)):

        sum_t = 0
        sum_channel = 0
        sum_idx = 0

        time, channel = time.item(), channel.item()

        for n_channel in range(max(0, int(channel - channel_radius)), 
                                min(num_channels - 1, int(channel + channel_radius + 1)), 
                                skip_channels):
            
            if channel_last_event[n_channel] is not None:
                n_time, n_idx = channel_last_event[n_channel]

                if time - n_time <= time_radius:
                    edges.append((n_idx, idx))

                    if features == 'local':
                        sum_t += (time - n_time)
                        sum_channel += (channel - n_channel)
                    
                    elif features == 'global':
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

        if features == 'local':
            feature.append([mean_t / time_radius, mean_channel / channel_radius])
        elif features == 'global':
            feature.append([mean_t / time_window, mean_channel / num_channels])
    
    edges = torch.tensor(edges).t().contiguous()

    if features:
        feature = torch.tensor(feature)
        return edges, feature
    
    return edges



data = torch.load("datasets/hdspikes/processed/train/0.pt", weights_only=False)

num_channels = 700
channel_radius = 100.0
time_radius = 0.02
time_window = 1.0
skip_channels = 10
features = "global"  # or "global"


data.pos[:, 0] = data.pos[:, 0] - data.pos[0, 0]
data.pos[:,0] = torch.round(data.pos[:, 0], decimals=6)
mask = data.pos[:, 0] < time_window
data.pos = data.pos[mask]

from time import time


start = time()
edge_index1, feature1 = generate_edges(data.pos[:, 0], 
                                            data.pos[:, 1],
                                            features=features,
                                            time_radius=time_radius,
                                            time_window=time_window,
                                            channel_radius=channel_radius,
                                            skip_channels=skip_channels,
                                            num_channels=num_channels)

print("Time:", time() - start)

edge_gen = edge_generator.EdgeGenerator(
    num_channels, channel_radius, time_radius, time_window, skip_channels, features
)

for i in range(100):
    start = time()
    edge_index2, feature2 = edge_gen.generate_edges(data.pos[:, 0], data.pos[:, 1])

    # print(feature2)
    print("Max diff:", torch.max(torch.abs(feature1 - feature2)))
    print("Edges equal:", torch.equal(edge_index1, edge_index2))



print(feature1)

