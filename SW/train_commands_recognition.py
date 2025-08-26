import yaml
import dotmap
import lightning as L
import torch
import argparse
import multiprocessing as mp

from lightning.pytorch.loggers.wandb import WandbLogger
from lightning.pytorch.callbacks import ModelCheckpoint, LearningRateMonitor
from models.recognition import LNRecognition
from data.spiking_commands import SpikingCommands

def main():
    cfg = yaml.load(open('configs/recognition/commands-35.yaml', 'r'), Loader=yaml.FullLoader)
    cfg = dotmap.DotMap(cfg)

    dm = SpikingCommands(cfg)
    dm.prepare_data()
    dm.setup()

    model = LNRecognition(cfg)

    wandb_logger = WandbLogger(project='audio_event', name=f'commands_rec')
    wandb_logger.watch(model)

    lr_monitor = LearningRateMonitor(logging_interval='step')

    print(cfg)
    print(model.model)

    print("\n#####################################################################################")
    print("############################### TRAINING FLOAT MODEL ################################")
    print("#####################################################################################\n")

    checkpoint_callback = ModelCheckpoint(
        dirpath='checkpoints',
        filename='best_model_float_commands',
        monitor='val_acc',
        mode='max',
        save_top_k=1
    )

    trainer = L.Trainer(max_epochs=100, 
                        log_every_n_steps=1000, 
                        gradient_clip_val=0.0,
                        logger=wandb_logger,
                        callbacks=[lr_monitor, checkpoint_callback],
                        # precision=16,
                        deterministic=False)


    trainer.fit(model, dm)
    best_model_path = checkpoint_callback.best_model_path
    # best_model_path = 'checkpoints/best_model_float.ckpt'
    print(f"\nBest float model saved at: {best_model_path}\n")
    model = LNRecognition.load_from_checkpoint(best_model_path, config=cfg)
    trainer.test(model, datamodule=dm)

    wandb_logger.experiment.finish()


    print(" \n#####################################################################################")
    print("############################### TRAINING QAT MODEL ################################")
    print("#####################################################################################\n")

    cfg.train.lr = 0.00001
    wandb_logger = WandbLogger(project='audio_event', name=f'commands_qat_rec')
    wandb_logger.watch(model)
    lr_monitor = LearningRateMonitor(logging_interval='step')

    checkpoint_callback = ModelCheckpoint(
        dirpath='checkpoints',
        filename='best_model_calibrated_commands_rec',
        monitor='val_acc',
        mode='max',
        save_top_k=1
    )

    trainer = L.Trainer(max_epochs=20,
                        log_every_n_steps=1000, 
                        gradient_clip_val=0.0,
                        logger=wandb_logger,
                        callbacks=[lr_monitor, checkpoint_callback],
                        # precision=16,
                        deterministic=False)
    
    model.model.calibrate()
    trainer.fit(model, dm)
    best_model_path = checkpoint_callback.best_model_path
    # best_model_path = 'checkpoints/best_model_calibrated.ckpt'
    print(f"\nBest model saved at: {best_model_path}\n")
    model = LNRecognition.load_from_checkpoint(best_model_path, config=cfg)

    trainer.test(model, datamodule=dm)

    print(" \n#####################################################################################")
    print("############################### QUANTIZING MODEL ################################")
    print("#####################################################################################\n")

    model.model.quantize()
    trainer.test(model, datamodule=dm)
    
    torch.save(model.model, best_model_path.replace('calibrated', 'quantized'))


if __name__ == '__main__':
    mp.set_start_method('spawn', force=True)
    L.seed_everything(42)
    main()