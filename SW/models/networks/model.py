import torch
import torch.nn.functional as F
from torch.nn import Module, ModuleList, Linear, Dropout, Sequential, Conv1d


from models.networks.layers.my_pointnet import MyPointNetConv
from models.networks.layers.my_pooling_moving import MyMovingGlobalPooling


class GCN(Module):
    def __init__(self, 
                 config):
        super(GCN, self).__init__()
        
        self.config = config

        conv_ch = config.model.conv_channels
        conv_bits = config.model.conv_bits

        linear_ch = config.model.linear_channels
        num_classes = config.model.num_classes

        input_dim = 2 if config.graph.features else 0
        
        self.conv1 = MyPointNetConv(input_dim+2, conv_ch[0], bias=False, num_bits=conv_bits[0], first_layer=True)
        self.conv2 = MyPointNetConv(conv_ch[0]+2, conv_ch[1], bias=False, num_bits=conv_bits[1])
        self.conv3 = MyPointNetConv(conv_ch[1]+2, conv_ch[2], bias=False, num_bits=conv_bits[2])
        self.conv4 = MyPointNetConv(conv_ch[2]+2, conv_ch[3], bias=False, num_bits=conv_bits[3])
        
        self.pooling = MyMovingGlobalPooling(config.model.global_pooling, num_bits=conv_bits[3])

        self.fc1 = Linear(conv_ch[3], linear_ch)
        self.fc2 = Linear(linear_ch, linear_ch)

        self.conf = Conv1d(linear_ch, 1, kernel_size=1, stride=1, padding=0, bias=True)
        self.cls = Conv1d(linear_ch, num_classes+1, kernel_size=5, stride=1, padding=2, bias=True)


    def forward(self, data):
        outputs = []

        x, pos, edge_index, batch = data['x'], data['pos'], data['edge_index'], data['batch']

        x = self.conv1(x, pos, edge_index)
        outputs.append(x)
        x = self.conv2(x, pos, edge_index)
        outputs.append(x)
        x = self.conv3(x, pos, edge_index)
        outputs.append(x)
        x = self.conv4(x, pos, edge_index)
        outputs.append(x)
        x = self.pooling(x, pos, batch, self.conv4.observer_output)
        outputs.append(x)

        x = self.fc1(x)
        x = torch.relu(x)
        outputs.append(x)
        # x = F.dropout(x, p=0.5, training=self.training)
        x = self.fc2(x)
        x = torch.relu(x)
        outputs.append(x)

        x = x.permute(0, 2, 1)  # change shape to (B, C, T) for Conv1d
        conf = self.conf(x)
        conf = conf.squeeze(1)

        cls = self.cls(x)
        cls = cls.squeeze(1)

        return conf, cls
    
    def calibrate(self):
        self.conv1.calibrate()
        self.conv2.calibrate()
        self.conv3.calibrate()
        self.conv4.calibrate()
        self.pooling.calibrate()

    def quantize(self):
        self.conv1.quantize()
        self.conv2.quantize(observer_input=self.conv1.observer_output)
        self.conv3.quantize(observer_input=self.conv2.observer_output)
        self.conv4.quantize(observer_input=self.conv3.observer_output)
        self.pooling.quantize()