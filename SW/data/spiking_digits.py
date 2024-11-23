import os
import glob
import h5py
import numpy as np
import torch
import lightning as L

from tqdm import tqdm
from tqdm.contrib.concurrent import process_map
from torch.utils.data import DataLoader

from torch_geometric.data import Data

device = torch.device(torch.cuda.current_device()) if torch.cuda.is_available() else torch.device('cpu')


class SpikingDigits(L.LightningDataModule):
    def __init__(self,
                 config):
        super().__init__()

        self.data_dir = config.general.data_dir
        self.time_window = config.general.time_window

    def prepare_data(self):
        self.save_to_file('train')
        self.save_to_file('test')
            
    def save_to_file(self, mode: str):
        file = h5py.File(self.data_dir + f'/shd_{mode}.h5', 'r')
        data = file['spikes']
        labels = file['labels']

        for idx, (times, units, labels) in enumerate(zip(data["times"], data["units"], labels)):
            # we only want spikes that occur within the time window
            mask = times < self.time_window 
            times = times[mask]
            units = units[mask]
            pos = np.column_stack((times, units))

            data = Data(pos=torch.tensor(pos, dtype=torch.float),
                        y=torch.tensor(labels, dtype=torch.long))
            
            torch.save(data, self.data_dir + f'/processed/train/{idx}.pt')

    def generate_ds(self, mode):
        data_dir = os.path.join(self.data_dir, 'processed/' f'{mode}', '*.pt')
        data_files = glob.glob(data_dir)
        # return DS(data_files, self.cfg, mode)

    def setup(self, stage=None):
        self.train_data = self.generate_ds('train')
        self.val_data = self.generate_ds('val')
        self.test_data = self.generate_ds('test')

    def train_dataloader(self):
        return DataLoader(self.train_data, 
                            batch_size=self.cfg.train.batch_size,
                            shuffle=True,
                            num_workers=self.cfg.train.num_workers,
                            persistent_workers=True)

    def val_dataloader(self):
        return DataLoader(self.val_data,
                            batch_size=self.cfg.train.batch_size,
                            shuffle=False,
                            num_workers=self.cfg.train.num_workers,
                            persistent_workers=True)
    
    def test_dataloader(self):
        return DataLoader(self.test_data,
                            batch_size=self.cfg.train.batch_size,
                            shuffle=False,
                            num_workers=self.cfg.train.num_workers,
                            persistent_workers=True)