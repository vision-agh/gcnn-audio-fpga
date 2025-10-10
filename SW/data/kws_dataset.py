import torch
import edge_generator
from torch.utils.data import Dataset

import cv2
import numpy as np
from data.utils.convert_ssc_cls import label_map


def detect_active_range(hist, bin_edges, T_high=None, T_low=None, cooldown_steps=5):
    hist = hist.astype(np.float32)
    hist_smoothed = cv2.GaussianBlur(hist.reshape(1, -1), (7, 1), 0).flatten()

    if T_high is None:
        T_high = np.mean(hist_smoothed) + 0.5 * np.std(hist_smoothed)
    if T_low is None:
        T_low = 0.2 * T_high

    active = False
    cooldown = 0
    start_idx = None
    end_idx = None

    for i, val in enumerate(hist_smoothed):
        if not active and val >= T_high:
            active = True
            start_idx = i
            cooldown = 0
        elif active:
            if val >= T_low:
                cooldown = 0  # reset cooldown
            else:
                cooldown += 1
                if cooldown >= cooldown_steps:
                    end_idx = i - cooldown
                    break  # end of activity

    if active and end_idx is None:
        end_idx = len(hist_smoothed) - 1 

    if start_idx is not None and end_idx is not None:
        start_time = bin_edges[start_idx]
        end_time = bin_edges[end_idx + 1]
        return start_time, end_time, hist_smoothed
    else:
        return None, None, hist_smoothed
    
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

        if self.config.general.name == 'Google_Speech_Commands' and \
              self.config.model.num_classes == 11:
            data['y'] = torch.tensor(label_map[int(data['y'].item())], dtype=torch.long)
        
        # Normalise node positions
        data['pos'][:, 0] = data['pos'][:, 0] / self.time_window
        data['pos'][:, 1] = data['pos'][:, 1] / self.num_channels


        bin_width = 0.01
        bins = np.arange(0, 1 + bin_width, bin_width)
        hist, bin_edges = np.histogram(data['pos'][:, 0].cpu().numpy(), bins=bins)
        hist = hist.astype(np.float32)

        start_time, end_time, hist_smoothed = detect_active_range(hist, bin_edges)

        data['end_time'] = end_time  # seconds in range [0,1]

        # --- here we generate labels y ---
        T = int(1.0 / bin_width)      # num of bins = 100
        y = torch.zeros(T, dtype=torch.float32)
        cls = torch.zeros(T, dtype=torch.float32)

        if end_time is not None:
            # index of bin, where words ends
            bin_idx = int(end_time // bin_width)
            if 0 <= bin_idx < T:
                y[bin_idx] = 1.0
                cls[bin_idx] = data['y']

                if bin_idx + 1 < T:
                    y[bin_idx+1] = 0.5
                    cls[bin_idx+1] = data['y']

                if bin_idx - 1 >= 0:
                    y[bin_idx-1] = 0.5
                    cls[bin_idx-1] = data['y']

        data['keyword'] = y
        data['cls'] = cls

        return data