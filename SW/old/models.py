import torch
import torch.nn.functional as F
from torch_geometric.nn import GCNConv, PointNetConv, GATConv, GATv2Conv, GINConv, GAT, GIN, global_mean_pool, \
    global_add_pool, global_max_pool, SplineConv, BatchNorm, PairNorm
from torch.nn import Module, ModuleList, InstanceNorm1d, Linear, GRU, LSTM, Dropout
from utils import get_shd_dataset, GraphDataset, SpikeTrainList, EdgeDrop, NodeDrop, Compose, GRUSplineConv
from torch.nn.utils.rnn import pack_padded_sequence, pad_packed_sequence


class GCN_combined(Module):
    def __init__(self, num_node_features, num_hidden, depth, num_classes, num_phonemes, res_mode, mode, conv="all_gcn",
                 norm='pair', no_abs_time=True, event_normals=True, window_size=0.02):
        super().__init__()
        self.res_mode = res_mode
        self.mode = mode
        self.no_abs_time = no_abs_time
        self.event_normals = event_normals
        if conv == "all_gcn":
            self.conv_layers = ModuleList([GCNConv(num_node_features, num_hidden)]
                                          + [GCNConv(num_hidden, num_hidden) for _ in range(depth - 1)])
        elif conv == "hybrid":
            self.conv_layers = ModuleList([SplineConv(num_node_features, num_hidden, dim=4, kernel_size=5)]
                                          + [GCNConv(num_hidden, num_hidden) for _ in range(depth - 1)])
        elif conv == "all_spline":
            self.conv_layers = ModuleList([SplineConv(num_node_features, num_hidden, dim=4, kernel_size=5)]
                                          + [SplineConv(num_hidden, num_hidden, dim=3, kernel_size=5) for _ in
                                             range(depth - 1)])
        elif conv == "pointnet":
            self.conv_layers = ModuleList([PointNetConv(Linear(num_node_features + 2, num_hidden))]
                                          + [PointNetConv(Linear(num_hidden + 2, num_hidden)) for _ in
                                             range(depth - 1)])

        self.norm_layers = ModuleList([BatchNorm(num_hidden, affine=True) if norm == 'batch' else
                                       (InstanceNorm1d(num_hidden) if norm == 'instance' else
                                        PairNorm()) for _ in range(depth)])

        self.gn = InstanceNorm1d(num_hidden * depth if res_mode == "append" else num_hidden)
        if "label" in self.mode:
            self.fc1 = Linear(num_hidden * depth, 64) if res_mode == "append" else Linear(num_hidden, 64)
            self.fc2 = Linear(64, num_classes)
        elif "phoneme" in self.mode:
            self.fc1_p = Linear(num_hidden * depth, 64) if res_mode == "append" else Linear(num_hidden, 64)
            self.fc2_p = Linear(64, num_phonemes)
        elif "combined" in self.mode:
            self.fc1 = Linear(num_hidden * depth, 64) if res_mode == "append" else Linear(num_hidden, 64)
            self.fc2 = Linear(64, num_classes)
            self.fc1_p = Linear(num_hidden * depth, 64) if res_mode == "append" else Linear(num_hidden, 64)
            self.fc2_p = Linear(64, num_phonemes)
        elif "temporal" in self.mode:
            self.window_size = window_size
            self.inst_norm = InstanceNorm1d(256)
            self.temporal_head = TemporalHeadPhoneme(256, 128, 2, num_classes, model_type='GRU')

    def forward(self, data):
        x, edge_index, batch = data.x, data.edge_index, data.batch
        try:
            edge_attr = data.edge_attr.unsqueeze(-1)
        except:
            pass  # print("Tried loading edge attributes, but failed")
        pos = x[:, :2]
        if self.no_abs_time:
            x = x[:, 1:]
        if not self.event_normals:
            x = x[:, :-2]
        # if self.no_abs_time and not self.event_normals:
        #    x = torch.unsqueeze(x, 1)
        residuals = []
        for conv, norm in zip(self.conv_layers, self.norm_layers):
            if isinstance(conv, SplineConv):
                x = conv(x, edge_index, edge_attr)
            elif isinstance(conv, GCNConv):
                x = conv(x, edge_index)  # , edge_attr)
            elif isinstance(conv, PointNetConv):
                x = conv(x, pos, edge_index)
            if self.mode == "temporal":
                residuals.append(x)
            else:
                # Overwriting here because of memory issues, remove this for sum and for append
                residuals = [global_add_pool(x, batch)]  # esiduals.append(global_add_pool(x, batch))
            x = norm(F.relu(x))
        if self.res_mode == "append":
            a = torch.cat(residuals, 1)
        elif self.res_mode == "sum":
            a = torch.stack(residuals).sum(dim=0)
        elif self.res_mode == "final_layer":
            a = residuals[-1]
        if "label" in self.mode:
            y1 = self.fc2(F.relu(self.fc1(F.relu(self.gn(a)))))
            return y1
        elif "temporal" in self.mode:
            a = self.inst_norm(a)
            embedded_seq_tensor, seq_lengths = rebatch_average_and_pad(a, batch, pos[:, 0], self.window_size)
            packed_input_gru = pack_padded_sequence(embedded_seq_tensor, seq_lengths.cpu().numpy(), batch_first=True,
                                                    enforce_sorted=False).to(a.device)
            y, y_lengths = self.temporal_head(packed_input_gru)
            return y, y_lengths, self.window_size
        elif "phoneme" in self.mode:
            y2 = self.fc2_p(F.relu(self.fc1_p(F.relu(self.gn(a)))))  # Could be undefined as of now!
            return y2
        elif "combined" in self.mode:
            y1 = self.fc2(F.relu(self.fc1(F.relu(self.gn(a)))))
            y2 = self.fc2_p(F.relu(self.fc1_p(F.relu(self.gn(a)))))
            return y1, y2


class TemporalHeadPhoneme(torch.nn.Module):
    def __init__(self, input_size, hidden_size, num_layers, num_classes, model_type='GRU'):
        super(TemporalHeadPhoneme, self).__init__()
        if model_type == 'GRU':
            self.rnn = GRU(input_size, hidden_size, num_layers, batch_first=True)
        elif model_type == 'LSTM':
            self.rnn = LSTM(input_size, hidden_size, num_layers, batch_first=True)
        self.fc1 = Linear(hidden_size, hidden_size // 2)
        self.fc2 = Linear(hidden_size // 2, num_classes)
        self.dropout = Dropout(0.5)

    def forward(self, x):
        # pdb.set_trace()
        out, _ = self.rnn(x)
        out, output_lengths = pad_packed_sequence(out, batch_first=True)
        out = self.fc1(out)
        out = self.fc2(self.dropout(F.relu(out)))
        return out, output_lengths


def rebatch_average_and_pad(data_tensor, batch_tensor, time_stamps, window_size=0.1):
    _, sizes = batch_tensor.unique(return_counts=True)
    max_time = time_stamps.max().item()
    max_bin = int(max_time // window_size) + 1
    output_format = torch.zeros((sizes.shape[0], max_bin, data_tensor.shape[1]))
    output_size = torch.ones(sizes.shape[0]) * max_bin
    current_pos = 0

    for i in range(sizes.shape[0]):
        sample = data_tensor[current_pos:current_pos + sizes[i]]
        sample_time = torch.div(time_stamps[current_pos:current_pos + sizes[i]], window_size, rounding_mode="trunc")
        for j in range(max_bin):
            sup = (sample_time >= j)
            indexes = (sample_time == j)
            if (sup * 1).sum() == 0:
                output_size[i] = j
                break
            elif (indexes * 1).sum() > 0:
                output_format[i, j] = sample[indexes].mean(dim=0)
        current_pos = current_pos + sizes[i]
    return output_format, output_size


class GCN_combined_moved_MLP(Module):
    def __init__(self, num_node_features, num_hidden, depth, num_classes, num_phonemes, res_mode, mode, conv="all_gcn",
                 norm='batch'):
        super().__init__()
        self.res_mode = res_mode
        self.mode = mode
        if conv == "all_gcn":
            self.conv_layers = ModuleList([GCNConv(num_node_features, num_hidden)]
                                          + [GCNConv(num_hidden, num_hidden)] * (depth - 1))
        elif conv == "hybrid":
            self.conv_layers = ModuleList([SplineConv(num_node_features, num_hidden, dim=4, kernel_size=5)]
                                          + [GCNConv(num_hidden, num_hidden)] * (depth - 1))
        elif conv == "all_spline":
            self.conv_layers = ModuleList([SplineConv(num_node_features, num_hidden, dim=4, kernel_size=5)]
                                          + [SplineConv(num_hidden, num_hidden, dim=3, kernel_size=5)] * (depth - 1))

        self.gn = InstanceNorm1d(num_hidden * depth if res_mode == "append" else num_hidden)
        if "label" in self.mode:
            self.fc1 = Linear(num_hidden * depth, 64) if res_mode == "append" else Linear(num_hidden, 64)
            self.fc2 = Linear(64, num_classes)
        elif "phoneme" in self.mode:
            self.fc1_p = Linear(num_hidden * depth, 64) if res_mode == "append" else Linear(num_hidden, 64)
            self.fc2_p = Linear(64, num_phonemes)
        elif "combined" in self.mode:
            self.fc1 = Linear(num_hidden * depth, 64) if res_mode == "append" else Linear(num_hidden, 64)
            self.fc2 = Linear(64, num_classes)
            self.fc1_p = Linear(num_hidden * depth, 64) if res_mode == "append" else Linear(num_hidden, 64)
            self.fc2_p = Linear(64, num_phonemes)

    def forward(self, data):
        x, edge_index, batch = data.x, data.edge_index, data.batch
        try:
            edge_attr = data.edge_attr.unsqueeze(-1)
        except:
            print("Tried loading edge attributes, but failed")

        residuals = []
        for conv, norm in zip(self.conv_layers, self.norm_layers):
            if isinstance(conv, SplineConv):
                x = conv(x, edge_index, edge_attr)
            else:
                x = conv(x, edge_index)  # , edge_attr)
            residuals.append(x)
            x = norm(F.relu(x))
        if self.res_mode == "append":
            a = torch.cat(residuals, 1)
        elif self.res_mode == "sum":
            a = torch.stack(residuals).sum(dim=0)
        elif self.res_mode == "final_layer":
            a = residuals[-1]
        # Fully connected layer for classification
        if "label" in self.mode:
            y1 = self.fc2(F.relu(self.fc1(F.relu(self.gn(a)))))
            y1 = global_max_pool(y1, batch)
            return F.log_softmax(y1, dim=1)
        elif "phoneme" in self.mode:
            y2 = self.fc2_p(F.relu(self.fc1_p(F.relu(self.gn(a)))))
            y2 = global_max_pool(y2, batch)
            return torch.sigmoid(y2)
        elif "combined" in self.mode:
            y1 = self.fc2(F.relu(self.fc1(F.relu(self.gn(a)))))
            y2 = self.fc2_p(F.relu(self.fc1_p(F.relu(self.gn(a)))))
            y1 = global_max_pool(y1, batch)
            y2 = global_max_pool(y2, batch)
            return F.log_softmax(y1, dim=1), torch.sigmoid(y2)