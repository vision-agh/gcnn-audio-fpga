import yaml
import dotmap
import lightning as L
import torch
import argparse
import multiprocessing as mp

from data.spiking_digits import SpikingDigits 
from data.spiking_commands import SpikingCommands 
import cv2
import matplotlib.pyplot as plt
import numpy as np



def main():
    cfg = yaml.load(open('configs/digits.yaml', 'r'), Loader=yaml.FullLoader)
    cfg = dotmap.DotMap(cfg)
    cfg.train.batch_size = 1  # Set batch size to 64
    cfg.train.num_workers = 1  # Set num_workers to 0 for debugging

    dm = SpikingDigits(cfg)
    dm.setup()

    sum_pos = 0
    sum_edges = 0
    iter = 0

    for data in dm.val_dataloader():
        pos = data['pos'].cpu().numpy()
        edges = data['edge_index'].cpu().numpy()

        sum_pos += pos.shape[0]
        sum_edges += edges.shape[0]
        iter += 1

    print(f"Average number of positions per sample: {sum_pos / iter}")
    print(f"Average number of edges per sample: {sum_edges / iter}")





if __name__ == '__main__':
    mp.set_start_method('spawn', force=True)
    L.seed_everything(42)
    main()