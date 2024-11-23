import torch
from torch.utils.data import Dataset

class SpikingDS(Dataset):
    def __init__(self, files):
        self.files = files

    def __len__(self) -> int:
        return len(self.files)
    
    def __getitem__(self, index: int):
        data_file = self.files[index]
        data = torch.load(data_file, weights_only=False)
        return data