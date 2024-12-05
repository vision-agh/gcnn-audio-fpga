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

def main():
    cfg = yaml.load(open('configs/digits.yaml', 'r'), Loader=yaml.FullLoader)
    cfg = dotmap.DotMap(cfg)

    dm = SpikingDigits(cfg)
    dm.setup()

    model = LNRecognition(cfg)

    wandb_logger = WandbLogger(project='audio_event', name=f'hdspiking')
    wandb_logger.watch(model)

    lr_monitor = LearningRateMonitor(logging_interval='step')

    checkpoint_callback = ModelCheckpoint(
        dirpath='checkpoints',
        filename='best_model',
        monitor='val_acc',
        mode='max',
        save_top_k=1
    )

    trainer = L.Trainer(max_epochs=1, 
                        log_every_n_steps=1, 
                        gradient_clip_val=0.0,
                        logger=wandb_logger,
                        callbacks=[lr_monitor, checkpoint_callback],
                        deterministic=True)

    trainer.fit(model, dm)

    # print(model)

    # best_model_path = checkpoint_callback.best_model_path
    # print(f"Best model saved at: {best_model_path}")

    # # model = model.load_from_checkpoint(best_model_path)
    # model = model.model.load_state_dict(torch.load(best_model_path))


    trainer.test(model, datamodule=dm)

    model.model.freeze()

    trainer.test(model, datamodule=dm)

    torch.save(model.model.state_dict(), 'model.pth')



if __name__ == '__main__':
    mp.set_start_method('spawn', force=True)
    L.seed_everything(42)
    main()