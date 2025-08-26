import torch
import edge_generator
from torch.utils.data import Dataset

import cv2
import numpy as np
from data.utils.convert_ssc_cls import label_map
    
class SpikingDS(Dataset):
    def __init__(self,
                 files,
                 config,
                 train: bool = False):
        
        self.config = config

        self.files = files

        self.time_window = config.general.time_window
        self.num_channels = config.general.num_channels

        self.time_radius = config.graph.time_radius
        self.channel_radius = config.graph.channel_radius
        self.skip_channels = config.graph.skip_channels

        self.features = config.graph.features
        self.train = train

    def __len__(self) -> int:
        return len(self.files)
    
    def __getitem__(self, index: int):
        data_file = self.files[index]
        data = torch.load(data_file, weights_only=False)

        data['pos'][:, 0] = data['pos'][:, 0] - data['pos'][0, 0]  # Shift so that the first event is at time 0
        data['pos'][:, 0] *= 1e6 # Convert to microseconds
        data['pos'][:, 0] = torch.round(data['pos'][:, 0]) # Round to nearest microsecond
        data['pos'] = data['pos'][data['pos'][:, 0] < self.time_window] # Cut data to time window

        # Generate edge_index and features
        edge_gen = edge_generator.EdgeGenerator(self.config.general.num_channels, 
                                                        self.config.graph.channel_radius, 
                                                        self.config.graph.time_radius, 
                                                        self.config.general.time_window, 
                                                        self.config.graph.skip_channels, 
                                                        self.config.graph.features)

        edge_index, x = edge_gen.generate_edges(data['pos'][:, 0], 
                                                            data['pos'][:, 1])
        
        data['edge_index'] = edge_index
        data['x'] = x
        
        # Normalise node positions
        data['pos'][:, 0] = data['pos'][:, 0] / self.time_window
        data['pos'][:, 1] = data['pos'][:, 1] / self.num_channels

        return data