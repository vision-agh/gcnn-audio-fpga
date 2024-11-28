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
        
        self.conv1 = PointNetConv(Sequential(Linear(2+2, conv_ch, bias=False), BatchNorm(conv_ch)))
        self.conv2 = PointNetConv(Sequential(Linear(conv_ch+2, conv_ch, bias=False), BatchNorm(conv_ch)))
        self.conv3 = PointNetConv(Sequential(Linear(conv_ch+2, conv_ch, bias=False), BatchNorm(conv_ch)))
        self.conv4 = PointNetConv(Sequential(Linear(conv_ch+2, conv_ch, bias=False), BatchNorm(conv_ch)))

        self.lstm = torch.nn.LSTM(conv_ch, conv_ch, 1)

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

        seq_len = 20
        pooled_outputs = []

        max_batch = data.batch.max().item() + 1

        # Divide into chunks and apply global mean pooling
        for i in range(seq_len):
            mask1 = data.pos[:, 0] >= 1/seq_len * i
            mask2 = data.pos[:, 0] < 1/seq_len * (i + 1)
            mask = mask1 & mask2

            mean = torch.zeros((max_batch, x.size(1)), device=x.device)  # Empty chunk fallback

            # Ensure there are nodes in the current chunk
            if mask.sum() > 0:
                new_x = x[mask]
                batch = data.batch[mask]
                out = global_mean_pool(new_x, batch)  # [batch_size, feature_dim]
                batch_idx = torch.unique(batch)

                for idx in range(batch_idx.max().item() + 1):
                    mean[idx] = out[idx]

                # print(batch)
                # print(mean.shape)
                # print(batch_idx)
                # mean[batch_idx] = out

            pooled_outputs.append(mean)

        lstm_input = torch.stack(pooled_outputs, dim=0)

        lstm_out, (h_n, c_n) = self.lstm(lstm_input)  # lstm_out: [seq_len, batch_size, feature_dim]

        # Use last LSTM output for classification
        last_lstm_output = lstm_out[-1] 

        x = self.fc1(last_lstm_output)
        x = torch.relu(x)
        x = self.fc2(x)

        return x