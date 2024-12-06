import torch
import torch.nn as nn
from torch import Tensor
import torch.nn.functional as F
from torch_geometric.nn import global_mean_pool, global_add_pool, global_max_pool
from torch_geometric.data import Data
from typing import Optional, Union

from models.networks.layers.quantisation.observer import Observer, FakeQuantize, quantize_tensor, dequantize_tensor

Pooling = {
    'mean': global_mean_pool,
    'add': global_add_pool,
    'max': global_max_pool
}

class MyGlobalPooling(nn.Module):
    def __init__(
        self,
        aggregator: str = 'mean',
        num_bits: int = 8
    ):
        super().__init__()

        self.aggregator = Pooling[aggregator]
        self.calib_mode = False
        self.freeze_mode = False
        self.num_bits = num_bits

    def forward(
        self,
        data: Data,
        observer: Observer
    ) -> Tensor:
        
        if self.calib_mode is False and self.freeze_mode is False:
            out = self.aggregator(data.x, data.batch)
        elif self.calib_mode is True and self.freeze_mode is False:
            out = self.aggregator(data.x, data.batch)
            out = FakeQuantize.apply(out, observer)
        elif self.freeze_mode is True:
            out = self.aggregator(data.x, data.batch)
            out = torch.clamp(out, 0, 2**self.num_bits-1)
            out = out.round()
            out = observer.dequantize_tensor(out)
        return out
    
    def calibrate(self):
        self.calib_mode = True

    def freeze(self):
        self.freeze_mode = True
    
    # def __repr__(self) -> str:
    #     return (f'{self.__class__.__name__}(local_nn={self.local_nn}, '
    #             f'global_nn={self.global_nn})')