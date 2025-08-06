import torch
import edge_generator
from torch.utils.data import Dataset

import cv2
import numpy as np
# from data.augmentations import RandomRemoveNodes, RandomShiftChannel, \
#     RandomShiftTime, RandomSpreadChannel, RandomSpreadTime


def detect_active_range(hist, bin_edges, T_high=None, T_low=None, cooldown_steps=5):
    hist = hist.astype(np.float32)
    hist_smoothed = cv2.GaussianBlur(hist.reshape(1, -1), (7, 1), 0).flatten()

    # Progi: można dobrać ręcznie lub na podstawie statystyk
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
                    break  # koniec aktywności

    if active and end_idx is None:
        end_idx = len(hist_smoothed) - 1  # jeśli nie zakończyło się spadkiem

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

        # Augmentations
        # self.random_remove_nodes = RandomRemoveNodes()
        # self.random_shift_time = RandomShiftTime(time_window=self.time_window)
        # self.random_shift_channel = RandomShiftChannel(channels=self.num_channels)
        # self.random_spread_time = RandomSpreadTime(time_window=self.time_window)
        # self.random_spread_channel = RandomSpreadChannel(channels=self.num_channels)

    def apply_augmentations(self, data):
        if self.train:
            data = self.random_remove_nodes(data)
            data = self.random_shift_time(data)
            data = self.random_shift_channel(data)
            data = self.random_spread_time(data)
            data = self.random_spread_channel(data)
        return data

    def __len__(self) -> int:
        return len(self.files)
    
    def __getitem__(self, index: int):
        data_file = self.files[index]
        data = torch.load(data_file, weights_only=False)

        # data = self.apply_augmentations(data)

        # data['pos'][:, 0] = data['pos'][:, 0] - data['pos'][0, 0] # Start time from 0
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


        bin_width = 0.01
        bins = np.arange(0, 1 + bin_width, bin_width)
        hist, bin_edges = np.histogram(data['pos'][:, 0].cpu().numpy(), bins=bins)
        hist = hist.astype(np.float32)

        start_time, end_time, hist_smoothed = detect_active_range(hist, bin_edges)

        # Poprawne przypisanie end_time
        data['end_time'] = end_time  # w sekundach w skali [0,1]

        # --- tutaj generujemy etykietę y ---
        T = int(1.0 / bin_width)      # liczba binów = 100
        y = torch.zeros(T, dtype=torch.float32)
        cls = torch.zeros(T, dtype=torch.float32)

        if end_time is not None:
            # indeks biny, w której kończy się słowo
            bin_idx = int(end_time // bin_width)
            # upewniamy się, że nie wychodzi poza zakres
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

            for n_channel in range(int(channel - self.channel_radius), 
                                   int(channel + self.channel_radius + 1), 
                                   self.skip_channels):

                if n_channel < 0 or n_channel >= self.num_channels:
                    continue
                
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
                mean_t = round((sum_t / sum_idx) + 1e-6) # Add 1e-6 because Python is stupid
                mean_channel = round((sum_channel / sum_idx) + 1e-6)

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