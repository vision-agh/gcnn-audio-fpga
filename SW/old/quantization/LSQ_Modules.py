import torch
from torch import nn
from torch.nn import functional as F
import math

from LSQ_Functions import LinearDiscretizer, LSQ



class QuantizedLinear(nn.Linear):
    def __init__(
        self,
        in_features: int,
        out_features: int,
        bias: bool = True,
        device=None,
        dtype=None,
        weight_bits: int = 8,
    ):
        super().__init__(in_features, out_features, bias, device, dtype)
        self.device = device

        self.has_bias = bias
        if weight_bits < 32:
            self.weight_bits= (
                weight_bits.to(device)
                if isinstance(weight_bits, torch.Tensor)
                else torch.tensor(weight_bits, dtype=torch.float32).to(device)
            )
            self.scale = nn.Parameter(
                self.weight.abs().max().detach().clone() / 2 ** (weight_bits - 1)
            )
        else:
            self.weight_bits= None


    def forward(self, input):
        if self.weight_bits is not None:
            if self.weight_bits < 8:
                w_q = lsq_discretizer(self.weight, self.weight_bits, self.scale)
                if self.has_bias:
                    b_q = lsq_discretizer(self.bias, self.weight_bits, self.scale)
            else:
                w_q = LinearDiscretizer(self.weight, self.weight_bits)
                if self.has_bias:
                    b_q = LinearDiscretizer(self.bias, self.weight_bits)
        else:
            w_q = self.weight
            b_q = self.bias

        out = F.linear(input, w_q)

        if self.has_bias:
            out += b_q

        return out


class ActivationQuantizer(nn.Module):
    def __init__(self, activation_bits: int = 32, signed : bool = True, device=None):
        super().__init__()
        self.device = device
        self.is_initialized = False
        self.signed = signed

        if activation_bits < 32:
            self.activation_bits= (
                activation_bits.to(device)
                if isinstance(activation_bits, torch.Tensor)
                else torch.tensor(activation_bits, dtype=torch.float32).to(device)
            )
            self.scale = nn.Parameter(torch.empty((1,)))
        else:
            self.activation_bits= None

    def _initialize_scale(self, in_tensor):
        if self.signed:
            self.scale.data = in_tensor.abs().max() / 2 ** (self.activation_bits - 1)
        else:
            self.scale.data = in_tensor.max() / (2**self.activation_bits - 1) 
        self.is_initialized = True

    def forward(self, in_tensor):
        if not self.is_initialized and self.activation_bits is not None:
            self._initialize_scale(in_tensor)
        if self.activation_bits is not None:
            if self.activation_bits < 8:
                return lsq_discretizer(in_tensor, self.activation_bits, self.scale, self.signed)
            else:
                return LinearDiscretizer(in_tensor, self.activation_bits)
        else:
            return in_tensor
