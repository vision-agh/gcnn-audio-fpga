import torch
from torch.utils.data import Dataset

class SpikingDS(Dataset):
    def __init__(self,
                 files,
                 config):
        
        self.config = config
        self.files = files

    def __len__(self) -> int:
        return len(self.files)
    
    def __getitem__(self, index: int):
        data_file = self.files[index]
        data = torch.load(data_file, weights_only=False)

        # TODO: Implement augmentations here

        data.pos[:, 0] = data.pos[:, 0] - data.pos[0, 0] # Start time from 0
        mask = data.pos[:, 0] < self.config.general.time_window
        data.pos = data.pos[mask] # Cut data to time window

        # TODO: Generate edge_index here

        # TODO: Generate node features here

        return data