import torch
import torch.nn.functional as F
from torch.nn import Module, ModuleList, Linear, Dropout, Sequential


from models.networks.layers.my_pointnet import MyPointNetConv
from models.networks.layers.my_pooling import MyGlobalPooling


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
        
        self.pooling = MyGlobalPooling(config.model.global_pooling, num_bits=conv_bits[3])

        self.fc1 = Linear(conv_ch[3], linear_ch)
        self.fc2 = Linear(linear_ch, num_classes)

        self.register_buffer('calib_mode', torch.tensor(False, requires_grad=False))
        self.register_buffer('quantize_mode', torch.tensor(False, requires_grad=False))


    def forward(self, data):
        outputs = []
        x, pos, edge_index, batch = data['x'], data['pos'], data['edge_index'], data['batch']

        x = self.conv1(x, pos, edge_index)
        x = self.conv2(x, pos, edge_index)
        x = self.conv3(x, pos, edge_index)
        x = self.conv4(x, pos, edge_index)
        x = self.pooling(x, batch, self.conv4.observer_output)
        x = self.fc1(x)
        if not self.quantize_mode:
            x = F.relu(x)
        else:
            x[x < self.fc1.observer_output.zero_point] = self.fc1.observer_output.zero_point
        x = self.fc2(x)

        return x, outputs
    
    def calibrate(self):
        self.calib_mode.fill_(True)
        self.conv1.calibrate()
        self.conv2.calibrate()
        self.conv3.calibrate()
        self.conv4.calibrate()
        self.pooling.calibrate()
        self.fc1.calibrate()
        self.fc2.calibrate()

    def quantize(self):
        self.quantize_mode.fill_(True)
        self.conv1.quantize()
        self.conv2.quantize(observer_input=self.conv1.observer_output)
        self.conv3.quantize(observer_input=self.conv2.observer_output)
        self.conv4.quantize(observer_input=self.conv3.observer_output)
        self.pooling.quantize()
        self.fc1.quantize(observer_input=self.conv4.observer_output)
        self.fc2.quantize(observer_input=self.fc1.observer_output)