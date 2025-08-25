import yaml
import dotmap
import lightning as L
import torch
import argparse
import multiprocessing as mp

from lightning.pytorch.loggers.wandb import WandbLogger
from lightning.pytorch.callbacks import ModelCheckpoint, LearningRateMonitor
from models.recognition import LNRecognition
from data.spiking_digits_kws import SpikingDigits

import matplotlib.pyplot as plt
import numpy as np

cfg = yaml.load(open('configs/digits.yaml', 'r'), Loader=yaml.FullLoader)
cfg = dotmap.DotMap(cfg)
cfg.train.batch_size = 1  # Set batch size to 1 for testing

dm = SpikingDigits(cfg)
dm.setup()

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
# model = torch.load('checkpoints/best_model_calibrated.ckpt', map_location='cpu', weights_only=False)
model = LNRecognition.load_from_checkpoint('checkpoints/best_model_calibrated.ckpt', config=cfg, strict=False)
model.eval().to(device)

model.model.quantize()


model.model.conv1.get_parameters('weights/conv1.txt')
model.model.conv2.get_parameters('weights/conv2.txt')
model.model.conv3.get_parameters('weights/conv3.txt')
model.model.conv4.get_parameters('weights/conv4.txt')
model.model.fc1.get_parameters('weights/fc1.txt')
model.model.fc2.get_parameters('weights/fc2.txt')

model.model.rnn.gru.get_parameters('weights/rnn.txt')
model.model.cls.get_parameters('weights/cls.txt')
model.model.conf.get_parameters('weights/conf.txt')
# for data in dm.val_dataloader():
#     for key in data:
#         if isinstance(data[key], torch.Tensor):
#             data[key] = data[key].to(device)
#     output, cls = model(data)
