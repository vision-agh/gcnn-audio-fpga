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

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = torch.load('checkpoints/best_model_quantized.ckpt', map_location='cpu', weights_only=False)
model.eval().to(device)


model.conv1.get_parameters('outputs/conv1.txt')
model.conv2.get_parameters('outputs/conv2.txt')
model.conv3.get_parameters('outputs/conv3.txt')
model.conv4.get_parameters('outputs/conv4.txt')
model.fc1.get_parameters('outputs/fc1.txt')
model.fc2.get_parameters('outputs/fc2.txt')


model.cls.get_parameters('outputs/cls.txt')
model.conf.get_parameters('outputs/conf.txt')
# for data in dm.val_dataloader():
#     for key in data:
#         if isinstance(data[key], torch.Tensor):
#             data[key] = data[key].to(device)
#     output, cls = model(data)
