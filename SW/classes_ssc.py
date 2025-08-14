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
from data.spiking_commands import SpikingCommands

import matplotlib.pyplot as plt
import numpy as np
import h5py

file = h5py.File('/home/imperator/Datasets/hdspikes'+ f'/ssc_train.h5', 'r')

print(file['extra']['keys'][29])