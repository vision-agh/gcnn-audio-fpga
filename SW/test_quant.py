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

cfg = yaml.load(open('configs/digits.yaml', 'r'), Loader=yaml.FullLoader)
cfg = dotmap.DotMap(cfg)
cfg.train.batch_size = 1  # Set batch size to 1 for testing

dm = SpikingDigits(cfg)
dm.setup()

model = LNRecognition.load_from_checkpoint('checkpoints/best_model_calibrated-v2.ckpt', config=cfg)

for data in dm.val_dataloader():

    for key in data:
        if isinstance(data[key], torch.Tensor):
            data[key] = data[key].to(model.device)
    output, cls = model(data)
    # print(output)

    break

model.model.quantize()

for data in dm.val_dataloader():

    for key in data:
        if isinstance(data[key], torch.Tensor):
            data[key] = data[key].to(model.device)
    output, cls = model(data)
    # print(output)

    break