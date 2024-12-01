import torch
import torch.nn.functional as F
from torch_geometric.nn import GCNConv, PointNetConv, GATConv, GATv2Conv, GINConv, GAT, GIN, global_mean_pool, \
    global_add_pool, global_max_pool, SplineConv, BatchNorm, PairNorm
from torch.nn import Module, ModuleList, Linear, Dropout, Sequential


from models.networks.layers.my_pointnet import MyPointNetConv
from models.networks.layers.my_pooling import MyGlobalPooling


class GCN(Module):
    def __init__(self, 
                 config):
        super(GCN, self).__init__()
        
        self.config = config

        conv_ch = config.model.conv_channels
        linear_ch = config.model.linear_channels
        num_classes = config.model.num_classes

        input_dim = 2+2 if config.graph.features else 2
        
        self.conv1 = MyPointNetConv(input_dim, conv_ch, bias=False, num_bits=16, first_layer=True)
        self.conv2 = MyPointNetConv(conv_ch+2, conv_ch, bias=False, num_bits=16)
        self.conv3 = MyPointNetConv(conv_ch+2, conv_ch, bias=False, num_bits=16)
        self.conv4 = MyPointNetConv(conv_ch+2, conv_ch, bias=False, num_bits=16)

        if config.model.use_rnn:
            self.lstm = torch.nn.LSTM(config.rnn_channels, 
                                      config.rnn_channels, 
                                      config.rnn_layers)

        self.fc1 = Linear(conv_ch, linear_ch)
        self.fc2 = Linear(linear_ch, num_classes)

        self.pooling = MyGlobalPooling(config.model.global_pooling)

    def forward(self, data):
        data.x = self.conv1(data)
        data.x = self.conv2(data)
        data.x = self.conv3(data)
        data.x = self.conv4(data)

        if self.config.model.use_rnn:
            x = self.apply_lstm(data)
        else:
            x = self.pooling(data, self.conv4.observer_output)

        x = self.fc1(x)
        x = torch.relu(x)
        x = self.fc2(x)

        return x
    
    def calibrate(self):
        self.conv1.calibrate()
        self.conv2.calibrate()
        self.conv3.calibrate()
        self.conv4.calibrate()
        self.pooling.calibrate()
    
    def apply_lstm(self,
                   data):
        
        seq_len = self.config.model.seq_length
        pooled_outputs = []

        max_batch = data.batch.max().item() + 1

        for i in range(seq_len):
            mask1 = data.pos[:, 0] >= 1/seq_len * i
            mask2 = data.pos[:, 0] < 1/seq_len * (i + 1)
            mask = mask1 & mask2

            mean = torch.zeros((max_batch, x.size(1)), device=x.device)

            if mask.sum() > 0:
                new_x = x[mask]
                batch = data.batch[mask]
                out = self.pooling(new_x, batch)
                batch_idx = torch.unique(batch)

                for idx in range(batch_idx.max().item() + 1):
                    mean[idx] = out[idx]

            pooled_outputs.append(mean)

        lstm_input = torch.stack(pooled_outputs, dim=0)

        lstm_out, (h_n, c_n) = self.lstm(lstm_input)

        x = lstm_out[-1] 

        return x