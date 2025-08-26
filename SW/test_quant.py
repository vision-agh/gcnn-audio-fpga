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

from time import time

cfg = yaml.load(open('configs/digits.yaml', 'r'), Loader=yaml.FullLoader)
cfg = dotmap.DotMap(cfg)
cfg.train.batch_size =1  # Set batch size to 1 for testing

dm = SpikingDigits(cfg)
dm.setup()

# model = LNRecognition.load_from_checkpoint('checkpoints/best_model_float.ckpt', config=cfg)
model = LNRecognition(cfg).to('cuda' if torch.cuda.is_available() else 'cpu')
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

print(x1)
print(x2)
print(x3)

# print the original values of x1 x2 x3 where x2 and x3 differ
idx = (x2 - x3).abs() > 0.0001
print(idx.shape)
print("Differences in x1 and x2:")
print(x2[idx].cpu().detach().numpy())
print(x3[idx].cpu().detach().numpy())

print((x1 - x2).abs().max())
print((x2 - x3).abs().max())
print(model.model.conv4.observer_output.scale, model.model.conv4.observer_output.zero_point)