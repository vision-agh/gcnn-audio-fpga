import yaml
import dotmap
import lightning as L
import torch
import argparse
import multiprocessing as mp

from lightning.pytorch.loggers.wandb import WandbLogger
from lightning.pytorch.callbacks import ModelCheckpoint, LearningRateMonitor
from models.recognition import LNRecognition
from data.spiking_digits import SpikingDigits

import matplotlib.pyplot as plt
import numpy as np

from time import time

cfg = yaml.load(open('configs/digits.yaml', 'r'), Loader=yaml.FullLoader)
cfg = dotmap.DotMap(cfg)
cfg.train.batch_size = 1  # Set batch size to 1 for testing

dm = SpikingDigits(cfg)
dm.setup()

model = LNRecognition.load_from_checkpoint('checkpoints/best_model_float.ckpt', config=cfg)
model.eval()

for data in dm.test_dataloader():
    for key in data:
        if isinstance(data[key], torch.Tensor):
            data[key] = data[key].to('cuda' if torch.cuda.is_available() else 'cpu')


output = model(data)

x1 = output[2]  # Get the output of the first conv layer for observer input

model.model.calibrate()

output = model(data)

x2 = output[2]  # Get the output of the first conv layer after calibration

model.model.quantize()

output = model(data)

x3 = output[2]  # Get the output of the first conv layer after quantization
x3 = model.model.conv1.observer_output.dequantize_tensor(x3)

print(x1)
print(x2)
print(x3)

print((x1 - x2).abs().max())
print((x2 - x3).abs().max())
print(model.model.conv1.observer_output.scale, model.model.conv1.observer_output.zero_point)

# print the line where the x2 and x3 are different
diff = (x2 - x3).abs()
for i in range(diff.shape[0]):
    for j in range(diff.shape[1]):
        if diff[i, j].item() > 0:
            print(f"Difference at index {i}, {j}: {diff[i, j].item()}")
            print(f"x2: {x2[i, j].item()}, x3: {x3[i, j].item()}")
            print(f"x1: {x1[i, j].item()}")