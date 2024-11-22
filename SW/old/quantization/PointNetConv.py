from typing import Optional, Union

import torch
from torch import Tensor
from LSQ_Modules import QuantizedLinear,ActivationQuantizer
# from .LSQ_Modules import QuantizedLinear, ActivationQuantizer

# from torch_scatter import scatter_max
from torch_geometric.nn.conv import MessagePassing
from torch_geometric.utils import add_self_loops, remove_self_loops
from torch_geometric.nn.inits import reset
from torch_geometric.typing import (
    Adj,
    OptTensor,
    PairOptTensor,
    PairTensor,
)

class PointNetConv(MessagePassing):
    r"""The PointNet set layer from the `"PointNet: Deep Learning on Point Sets
    for 3D Classification and Segmentation"
    <https://arxiv.org/abs/1612.00593>`_ and `"PointNet++: Deep Hierarchical
    Feature Learning on Point Sets in a Metric Space"
    <https://arxiv.org/abs/1706.02413>`_ papers.

    .. math::
        \mathbf{x}^{\prime}_i = \gamma_{\mathbf{\Theta}} \left( \max_{j \in
        \mathcal{N}(i) \cup \{ i \}} h_{\mathbf{\Theta}} ( \mathbf{x}_j,
        \mathbf{p}_j - \mathbf{p}_i) \right),

    PointNetConv is the legacy implementation using the aggregation method passed in kwargs (default max).
    Used for max, mean and sum (all deature-wise).
    """
    def __init__(self, 
                 in_features: int,
                 in_coords: int,
                 out_features: int,
                 add_self_loops: bool = True,
                 weight_bits: int= 8,
                 activation_bits: int= 8,
                 device=None,
                 **kwargs):
        kwargs.setdefault('aggr', 'max')
        super().__init__(**kwargs)
        self.aggreg = kwargs['aggr']

        self.quant_local_nn = QuantizedLinear(in_features+in_coords, out_features, device = device, weight_bits= weight_bits, bias=True)
        self.quant_act = ActivationQuantizer(activation_bits= activation_bits, signed=True, device = device)

        self.add_self_loops = add_self_loops

        self.reset_parameters()

    def reset_parameters(self):
        # super().reset_parameters()
        reset(self.quant_local_nn)

    def forward(
        self,
        x: Union[OptTensor, PairOptTensor],
        pos: Union[Tensor, PairTensor],
        edge_index: Adj,
    ) -> Tensor:

        if not isinstance(x, tuple):
            x = (x, None)

        if isinstance(pos, Tensor):
            pos = (pos, pos)

        if self.add_self_loops:
            if isinstance(edge_index, Tensor):
                edge_index, _ = remove_self_loops(edge_index)
                edge_index, _ = add_self_loops(
                    edge_index, num_nodes=min(pos[0].size(0), pos[1].size(0)))
            elif isinstance(edge_index, SparseTensor):
                edge_index = torch_sparse.set_diag(edge_index)

        # propagate_type: (x: PairOptTensor, pos: PairTensor)
        out = self.propagate(edge_index, x=x, pos=pos)
        return self.quant_act(out)


    def message(self, x_j: Optional[Tensor], pos_i: Tensor,
                pos_j: Tensor) -> Tensor:
        msg = pos_j - pos_i
        if x_j is not None:
            msg = torch.cat([x_j, msg], dim=1)
        if self.quant_local_nn is not None:
            msg = self.quant_local_nn(msg)
        return msg

    def __repr__(self) -> str:
        return (f'{self.__class__.__name__}(quant_local_nn={self.quant_local_nn}, '
                f'global_nn=None), aggreg={self.aggreg}, self_loop={self.add_self_loops}')