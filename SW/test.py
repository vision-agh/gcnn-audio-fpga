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

# model = LNRecognition.load_from_checkpoint('checkpoints/best_model_float.ckpt', config=cfg)

# model.model.calibrate()
# model.model.quantize()
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = torch.load('checkpoints/best_model_quantized.ckpt', map_location='cpu', weights_only=False)
model.eval().to(device)

for data in dm.val_dataloader():

    for key in data:
        if isinstance(data[key], torch.Tensor):
            data[key] = data[key].to(device)
    output, cls = model(data)
    cls = torch.softmax(cls, dim=1)  # Apply softmax to the class scores
    y = data['y'].cpu().numpy()
    print(cls.shape)
    for i in range(cls.shape[2]):
        print(f"Class {i}: {torch.softmax(cls[:,:,i], dim=1)}")

    print(data['y'])
    output = torch.sigmoid(output)  # Apply sigmoid activation to the output
    print(output.shape)  # Should print the shape of the output tensor
    pos = data['pos'].cpu().numpy()

    # Visualize the positions
    plt.scatter(pos[:, 0], pos[:, 1], s=1, alpha=0.5)
    plt.title('Spiking Digits Positions')
    plt.xlabel('Time')
    plt.ylabel('Unit')

    # visualise the output
    output_np = output.cpu().detach().numpy()
    # create vec of time steps (from 0 to 1 for each 20 sample)
    vec_time = np.linspace(0, 1, output_np.shape[1])
    plt.plot(vec_time, output_np[0], label='Model Output', color='red')
    for i in range(20):
        plt.plot(vec_time, cls[0,i,:].cpu().detach().numpy(), label=f'Class {i} Output', linestyle='--')
    plt.title(f'Model Output for Sample {y}') 
    plt.xlabel('Time')
    plt.ylabel('Output Value')
    plt.legend()
    plt.show()  # Use block=False to avoid blocking the script

