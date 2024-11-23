import yaml
import dotmap
import lightning as L
import argparse
import multiprocessing as mp

from lightning.pytorch.loggers.wandb import WandbLogger
from models.recognition import LNRecognition
from data.spiking_digits import SpikingDigits

def main():
    cfg = yaml.load(open('configs/digits.yaml', 'r'), Loader=yaml.FullLoader)
    cfg = dotmap.DotMap(cfg)

    dm = SpikingDigits(cfg)
    model = LNRecognition(cfg)

    dm.setup()

    wandb_logger = WandbLogger(project='audio_event', name=f'hdspiking')
    wandb_logger.watch(model)
    trainer = L.Trainer(max_epochs=100, log_every_n_steps=1, gradient_clip_val=0.0, logger=wandb_logger)
    trainer.fit(model, dm)


if __name__ == '__main__':
    mp.set_start_method('spawn', force=True)
    L.seed_everything(42)
    main()