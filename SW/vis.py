import yaml
import dotmap
import lightning as L
import torch
import argparse
import multiprocessing as mp

from data.spiking_digits_kws import SpikingDigits 
from data.spiking_commands_kws import SpikingCommands 
import cv2
import matplotlib.pyplot as plt
import numpy as np



def detect_active_range(hist, bin_edges, T_high=None, T_low=None, cooldown_steps=5):
    hist = hist.astype(np.float32)
    hist_smoothed = cv2.GaussianBlur(hist.reshape(1, -1), (7, 1), 0).flatten()

    # Progi: można dobrać ręcznie lub na podstawie statystyk
    if T_high is None:
        T_high = np.mean(hist_smoothed) + 0.5 * np.std(hist_smoothed)
    if T_low is None:
        T_low = 0.3 * T_high

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
        print(f"[✓] Wykryto zakres mowy: {start_time:.4f}s - {end_time:.4f}s")
        return start_time, end_time, hist_smoothed
    else:
        print("[!] Nie wykryto aktywności.")
        return None, None, hist_smoothed



def main():
    cfg = yaml.load(open('configs/commands-35.yaml', 'r'), Loader=yaml.FullLoader)
    cfg = dotmap.DotMap(cfg)
    cfg.train.batch_size = 1  # Set batch size to 64
    cfg.train.num_workers = 1  # Set num_workers to 0 for debugging
    cfg.graph.time_radius = 10000
    cfg.graph.channel_radius = 30

    dm = SpikingCommands(cfg)
    dm.setup()

    for data in dm.val_dataloader():
        print(data)
        print(data['y'])
        pos = data['pos'].cpu().numpy()
        edges = data['edge_index'].cpu().numpy()

        # visualize the data

        plt.figure(figsize=(10, 10))
        plt.scatter(pos[:, 0], pos[:, 1], c='black', s=0.2, label='Lips Points')

        # plot edges
        # for i in range(edges.shape[0]):
        #     src_idx = edges[i, 0]
        #     dst_idx = edges[i, 1]
        #     plt.plot([pos[src_idx, 0], pos[dst_idx, 0]], 
        #              [pos[src_idx, 1], pos[dst_idx, 1]], 
        #              c='gray', alpha=0.4, linewidth=1)
        
        # crop to [0.5, 0.7] [0.4, 0.6]
        # save in high resolution
        # plt.title('Lips Points Visualization')
        # remove ticks
        plt.xticks([])
        plt.yticks([])

        # set aspect to 2 to 1
        plt.gca().set_aspect(1/2)
        # plt.xlim(0.8, 0.9)
        # plt.ylim(0.7, 1)
        plt.savefig('lips_points.png', dpi=300, bbox_inches='tight')
        plt.show(block=False)

        bin_width = 0.01
        bins = np.arange(0, 1 + bin_width, bin_width)
        hist, bin_edges = np.histogram(pos[:, 0], bins=bins)
        hist = hist.astype(np.float32)

        start_time, end_time, hist_smoothed = detect_active_range(hist, bin_edges)

        # make histogram of the pos values (based on time)
        plt.figure(figsize=(10, 5))
        plt.bar(bin_edges[:-1], hist_smoothed, width=bin_width, color='blue', alpha=0.7, label='Smoothed Histogram')

        # highlight the active region
        plt.axvspan(start_time, end_time, color='red', alpha=0.5, label='Active Region')
        plt.axvline(start_time, color='red', linestyle='--', label='Start Time')
        plt.axvline(end_time, color='red', linestyle='--', label='End Time')

        plt.title('Histogram of Time Values')
        plt.xlabel('Time (microseconds)')
        plt.ylabel('Frequency')
        plt.grid()
        plt.show()

        # break



if __name__ == '__main__':
    mp.set_start_method('spawn', force=True)
    L.seed_everything(42)
    main()