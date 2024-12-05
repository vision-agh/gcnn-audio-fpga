import yaml
import dotmap
import lightning as L
import argparse
import multiprocessing as mp
import torch

from lightning.pytorch.loggers.wandb import WandbLogger
from lightning.pytorch.callbacks import ModelCheckpoint, LearningRateMonitor
from models.recognition import LNRecognition
from data.spiking_digits import SpikingDigits

best_model_path = "checkpoints/best_model-v2.ckpt"
print(f"Best model saved at: {best_model_path}")

model = LNRecognition.load_from_checkpoint(best_model_path)

print(torch.load(best_model_path))
model.model.freeze()

print(model)