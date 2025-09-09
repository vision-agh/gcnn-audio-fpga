import os
import glob
import h5py
import numpy as np
import torch
import lightning as L

from tqdm import tqdm
from torch.utils.data import DataLoader

from data.dataset import SpikingDS

device = torch.device(torch.cuda.current_device()) if torch.cuda.is_available() else torch.device('cpu')

class SpikingDigits(L.LightningDataModule):
    def __init__(self,
                 config):
        super().__init__()

        self.data_dir = config.general.data_dir
        self.config = config

    def prepare_data(self):
        self.save_to_file('train')
        self.save_to_file('test')
            
    def save_to_file(self, mode: str):
        file = h5py.File(self.data_dir + f'/shd_{mode}.h5', 'r')
        data = file['spikes']
        labels = file['labels']

        for idx, (times, units, label) in tqdm(enumerate(zip(data["times"], data["units"], labels))):
            # print(labels)
            new_file_name = self.data_dir + f'/processed/{mode}/{idx}.pt'

            if os.path.exists(new_file_name):
                continue
            os.makedirs(os.path.dirname(new_file_name), exist_ok=True)

            pos = np.column_stack((times, units))

            data = {'pos': torch.tensor(pos, dtype=torch.float), 
                    'y': torch.tensor(label, dtype=torch.long)}
            
            torch.save(data, new_file_name)

    def setup(self, stage=None):
        train_data = glob.glob(os.path.join(self.data_dir, 'processed/train/*'))
        test_data = glob.glob(os.path.join(self.data_dir, 'processed/test/*'))

        if self.config.preprocess.create_val:
            train_data = np.random.permutation(train_data)
            n_val = int(len(train_data) * self.config.preprocess.val_split)
            valid_data = train_data[:n_val]
            train_data = train_data[n_val:]

        try:
            self.valid_data = SpikingDS(valid_data, self.config)
            print(f'Using {len(valid_data)} samples as validation data')
        except:
            self.valid_data = SpikingDS(test_data, self.config)
            print('Using test data as validation data')

        self.train_data = SpikingDS(train_data, self.config, train=True)
        self.test_data = SpikingDS(test_data, self.config)

    def train_dataloader(self):
        return DataLoader(self.train_data, 
                            batch_size=self.config.train.batch_size,
                            shuffle=True,
                            num_workers=self.config.train.num_workers,
                            persistent_workers=True,
                            collate_fn=self.collate_fn)

    def val_dataloader(self):
        return DataLoader(self.valid_data,
                            batch_size=self.config.train.batch_size,
                            shuffle=False,
                            num_workers=self.config.train.num_workers,
                            persistent_workers=True,
                            collate_fn=self.collate_fn)
    
    def test_dataloader(self):
        return DataLoader(self.test_data,
                            batch_size=self.config.train.batch_size,
                            shuffle=False,
                            num_workers=self.config.train.num_workers,
                            persistent_workers=True,
                            collate_fn=self.collate_fn)
    
    @staticmethod
    def collate_fn(data_list):
        x = torch.cat([data['x'] for data in data_list], dim=0)
        pos = torch.cat([data['pos'] for data in data_list], dim=0)

        edge_index = []
        offset = 0
        for d in data_list:
            edge_index.append(d['edge_index'].T + offset)
            offset += d['x'].shape[0]
        edge_index = torch.cat(edge_index, dim=0)

        y = torch.stack([data['y'] for data in data_list], dim=0)

        batch = torch.cat([
            torch.full((d['x'].shape[0],), i, dtype=torch.long)
            for i, d in enumerate(data_list)
        ], dim=0)


        return {"x": x,
                "pos": pos,
                "edge_index": edge_index,
                "y": y,
                "batch": batch}