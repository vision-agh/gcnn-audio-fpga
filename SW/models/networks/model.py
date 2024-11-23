import torch
import torch.nn.functional as F
from torch_geometric.nn import GCNConv, PointNetConv, GATConv, GATv2Conv, GINConv, GAT, GIN, global_mean_pool, \
    global_add_pool, global_max_pool, SplineConv, BatchNorm, PairNorm
from torch.nn import Module, ModuleList, Linear, Dropout, Sequential


class GCN(Module):
    def __init__(self, 
                 config):
        super(GCN, self).__init__()
        
        self.config = config

        conv_ch = config.model.conv_channels
        linear_ch = config.model.linear_channels
        num_classes = config.model.num_classes
        
        self.conv1 = PointNetConv(Sequential(Linear(1+2, conv_ch, bias=False), BatchNorm(conv_ch)))
        self.conv2 = PointNetConv(Sequential(Linear(conv_ch+2, conv_ch, bias=False), BatchNorm(conv_ch)))
        self.conv3 = PointNetConv(Sequential(Linear(conv_ch+2, conv_ch, bias=False), BatchNorm(conv_ch)))
        self.conv4 = PointNetConv(Sequential(Linear(conv_ch+2, conv_ch, bias=False), BatchNorm(conv_ch)))

        self.fc1 = Linear(conv_ch, linear_ch)
        self.fc2 = Linear(linear_ch, num_classes)

    def forward(self, data):
        x = self.conv1(data.x, data.pos, data.edge_index)
        x = torch.relu(x)
        x = self.conv2(x, data.pos, data.edge_index)
        x = torch.relu(x)
        x = self.conv3(x, data.pos, data.edge_index)
        x = torch.relu(x)
        x = self.conv4(x, data.pos, data.edge_index)
        x = torch.relu(x)

        x = global_mean_pool(x, data.batch)

        x = self.fc1(x)
        x = self.fc2(x)

        return x