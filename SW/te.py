import yaml
import dotmap
import lightning as L
import torch
import argparse
import multiprocessing as mp

from lightning.pytorch.loggers.wandb import WandbLogger
from lightning.pytorch.callbacks import ModelCheckpoint, LearningRateMonitor
from models.kws import LNRecognition
from data.spiking_digits_kws import SpikingDigits

import matplotlib.pyplot as plt
import numpy as np

cfg = yaml.load(open('configs/digits.yaml', 'r'), Loader=yaml.FullLoader)
cfg = dotmap.DotMap(cfg)
cfg.train.batch_size = 1  # Set batch size to 1 for testing

dm = SpikingDigits(cfg)
dm.setup()

# model = LNRecognition.load_from_checkpoint('checkpoints/best_model_float.ckpt', config=cfg)

# model.model.calibrate()
# model.model.quantize()
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = torch.load('checkpoints/best_model_quantized.ckpt', map_location='cpu', weights_only=False)
model.eval().to(device)

sum_edge = 0
sum_idx = 0
sum_nodes = 0

for data in dm.train_dataloader():
    sum_edge += data['edge_index'].shape[0]
    sum_idx += 1
    sum_nodes += data['x'].shape[0]


print(f"Average edge_index length: {sum_edge/sum_idx}")
print(f"Average number of nodes: {sum_nodes/sum_idx}")

print(f"Sum edge_index length: {sum_edge}")
print(f"Sum number of nodes: {sum_nodes}")
print(f"Number of samples: {sum_idx}")