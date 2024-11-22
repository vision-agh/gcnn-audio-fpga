import math
from typing import Any

import torch
from torch.autograd import Function



class LSQ(Function):
    """
    Learned Step Size Quantization
    from: "Learned Step Size Quantization"
    link: https://arxiv.org/abs/1902.08153
    """

    @staticmethod
    def forward(ctx, in_tensor: torch.Tensor, bits: torch.Tensor, scale: torch.Tensor, signed: bool = True):
        if bits > 1:
            if signed:
                min_V = -(2 ** (bits.int() - 1))
                max_V = 2 ** (bits.int() - 1) - 1
            else:
                min_V = torch.tensor(0.0).to(in_tensor.device)
                max_V = 2 ** bits.int() - 1

            # Added +1e-9 in case scale is 0 (i.e. 0 tensor or negative output in unsigned configuration)
            ctx.save_for_backward(in_tensor / (scale+1e-9), min_V, max_V)
            return (in_tensor / (scale+1e-9)).clamp(min_V, max_V).round() * scale
        else:
            scale = in_tensor.abs().mean()
            input_mask = in_tensor.abs() < scale
            ctx.save_for_backward(input_mask, scale)
            sgn = in_tensor.sign()
            sgn[sgn == 0] = 1
            return sgn * scale

    @staticmethod
    def backward(ctx, grad_output):
        if len(ctx.saved_tensors) == 3:
            in_tensor, min_V, max_V = ctx.saved_tensors
            grad_scale = grad_output.clone()

            In, Ip = in_tensor < min_V, in_tensor > max_V
            grad_output[In] = 0
            grad_output[Ip] = 0

            grad_scale[In] *= min_V
            grad_scale[Ip] *= max_V
            grad_scale[~In * ~Ip] *= (
                -in_tensor[~In * ~Ip] + in_tensor[~In * ~Ip].round()
            )
            return (
                grad_output,
                None,
                grad_scale.sum() / (math.sqrt(in_tensor.numel()) * torch.sqrt(max_V)),
                None,
                None,
                None
            )
        else:
            mask, scale = ctx.saved_tensors
            return (1 / mask.numel() + mask * scale) * grad_output, None, None, None, None, None


lsq_discretizer = LSQ.apply


class LinearDiscretizer(Function):
    @staticmethod
    def forward(_, in_tensor: torch.Tensor, bits: torch.Tensor, signed : bool = True):
        if signed:
            scale = in_tensor.abs().max() / (2 ** (bits - 1) - 1)
        else:
            scale = in_tensor.max() / (2**bits - 1)
        
        # Added +1e-9 in case scale is 0 (i.e. 0 tensor or negative output in unsigned configuration)
        return (in_tensor / (scale + 1e-9)).round() * scale

    @staticmethod
    def backward(_, grad_output):
        return grad_output, None, None


linear_discretizer = LinearDiscretizer.apply
