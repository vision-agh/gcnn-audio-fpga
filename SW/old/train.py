import os
import torch
import torch.nn as nn
import numpy as np
import warnings
from datetime import datetime
from torch_geometric.loader import DataLoader
from torch.utils.data import random_split
from utils import GraphDataset_new
import argparse
from tqdm import tqdm
import torch.nn.functional as F
from torch_geometric.nn import PointNetConv, global_add_pool, BatchNorm, PairNorm, global_max_pool, global_mean_pool
from torch.nn import Module, ModuleList, InstanceNorm1d, Linear
import json

class EarlyStopping:
    def __init__(self, patience=10, min_delta=0):
        self.patience = patience
        self.min_delta = min_delta
        self.counter = 0
        self.best_loss = None
        self.early_stop = False

    def __call__(self, val_loss):
        if self.best_loss is None:
            self.best_loss = val_loss
        elif val_loss > self.best_loss - self.min_delta:
            self.counter += 1
            if self.counter >= self.patience:
                self.early_stop = True
        else:
            self.best_loss = val_loss
            self.counter = 0

class GCN_combined(Module):
    def __init__(self, num_node_features, gcn_dim, fc_dim, num_classes, norm='pair', event_normals=True, use_gn=True, disable_norm=False, pooling="max"):
        super().__init__()
        self.event_normals = event_normals
        self.use_gn = use_gn
        self.disable_norm = disable_norm
        self.pooling = pooling 

        self.conv_layers = ModuleList(
            [PointNetConv(Linear(num_node_features + 2, gcn_dim[0]))] +
            [PointNetConv(Linear(gcn_dim[i] + 2, gcn_dim[i + 1])) for i in range(len(gcn_dim) - 1)]
        )

        print(self.conv_layers)
        fc_layers = []
        in_dim = gcn_dim[-1]
        
        if self.use_gn:
            self.gn = InstanceNorm1d(in_dim)
        
        for out_dim in fc_dim:
            fc_layers.append(Linear(in_dim, out_dim))
            in_dim = out_dim
        self.fc_layers = ModuleList(fc_layers)

        self.final_fc = Linear(fc_dim[-1], num_classes)
        
        self.norm_layers = ModuleList(
            [None if self.disable_norm else (BatchNorm(dim, affine=True) if norm == 'batch' else PairNorm()) for dim in gcn_dim]
        )

    def forward(self, data):
        x, edge_index, batch = data.x, data.edge_index, data.batch
        pos = x[:, :2]
        if not self.event_normals:
            x = x[:, :-2]

        residuals = []
        for conv, norm in zip(self.conv_layers, self.norm_layers):
            x = conv(x, pos, edge_index)
            if self.pooling == "add":
                residuals = [global_add_pool(x, batch)]
            elif self.pooling == "max":
                residuals = [global_max_pool(x, batch)]
            elif self.pooling == "mean":
                residuals = [global_mean_pool(x, batch)]
            else:
                raise ValueError("Invalid pooling type. Choose 'add' or 'max'.")
            
            if norm is not None: 
                x = norm(F.relu(x))
            else:
                x = F.relu(x)

        a = residuals[-1]
        if self.use_gn:
            a = self.gn(a)
        
        for fc in self.fc_layers:
            a = F.relu(fc(a))
        x = self.final_fc(a)
        return x

def train(model, data_loader, optimizer, criterion, device):
    model.train()
    correct = 0
    loss_sum = 0.0
    for batch in tqdm(data_loader, desc="Training Batches"):
        batch = batch.to(device)
        optimizer.zero_grad()
        out = model(batch)
        pred = out.argmax(dim=1)
        correct += pred.eq(batch.y).sum().item()
        loss = criterion(out, batch.y)
        loss.backward()
        optimizer.step()
        loss_sum += loss.item()
    return loss_sum / len(data_loader), correct / len(data_loader.dataset)

def evaluate(model, data_loader, criterion, device, mode="Validation"):
    model.eval()
    correct = 0
    loss_sum = 0.0
    with torch.no_grad():
        for batch in tqdm(data_loader, desc=f"{mode} Batches"):
            batch = batch.to(device)
            out = model(batch)
            pred = out.argmax(dim=1)
            correct += pred.eq(batch.y).sum().item()
            loss = criterion(out, batch.y)
            loss_sum += loss.item()
    return loss_sum / len(data_loader), correct / len(data_loader.dataset)


#to the first step we use the parameter below
#"--gcn_dim 32 32 32 32 --fc_dim 64 --early_stopping --lr 0.002048824748826067 --weight_decay 0.0000879254070332143 --batch_size 16 --pooling mean --disable_norm"

if __name__ == "__main__":
    warnings.filterwarnings("ignore")
    parser = argparse.ArgumentParser(description='Training script')
    parser.add_argument('--root_dirs', nargs='+', type=str, help='List of root directories of the datasets', default=["graphs_hw_modified/e_to_n-tr-0.02-cr-hemi/deg_10"])
    parser.add_argument('--gcn_dim', nargs='+', type=int, help='Dimensions for each GCN layer', default=[32, 32, 32, 32])
    parser.add_argument('--fc_dim', nargs='+', type=int, help='Dimensions for each FC layer', default=[64])
    parser.add_argument('--batch_size', type=int, default=16, help='Batch size')
    parser.add_argument('--norm', type=str, default="batch", help='Normalization type')
    parser.add_argument('--lr', type=float, default=0.00159943, help='Learning rate')
    parser.add_argument('--weight_decay', type=float, default=0.000540453, help='Weight decay')
    parser.add_argument('--augm', nargs='+', default=[], help='Augmentation list')
    parser.add_argument('--event_normals', action='store_true', help='Disable event normals (default: False)')
    parser.add_argument('--use_gn', action='store_true', help='Enable use of gn layer (default: False)')
    parser.add_argument('--early_stopping', action='store_true', help='Enable early stopping (default: False)', default=True)
    parser.add_argument('--patience', type=int, default=10, help='Patience for early stopping')
    parser.add_argument('--min_delta', type=float, default=0, help='Minimum delta for early stopping')
    parser.add_argument('--disable_norm', action='store_true', help='Disable all normalization layers (default: False)', default=True)
    parser.add_argument('--pooling', type=str, choices=['max', 'add','mean'], default='mean', help="Type of pooling to use: 'max' or 'add'")

    args = parser.parse_args()

    torch.manual_seed(0)
    now = datetime.now()
    dt_string = now.strftime("%d-%m-%Y_%H-%M-%S")

    config = {
        "gcn_dim": args.gcn_dim,
        "fc_dim": args.fc_dim,
        "batch_size": args.batch_size,
        "norm": args.norm,
        "lr": args.lr,
        "weight_decay": args.weight_decay,
        "augm": args.augm,
        "event_normals": args.event_normals,
        "use_gn": args.use_gn,
        "early_stopping": args.early_stopping,
        "patience": args.patience,
        "min_delta": args.min_delta,
        "disable_norm": args.disable_norm,
        "pooling": args.pooling
    }

    device = torch.device("cuda") if torch.cuda.is_available() else torch.device("cpu")
    OUT_DIR = args.root_dirs[0]
    results_root_dir = os.path.join(OUT_DIR, "results")
    config_summary = (
        f"gcn_{config['gcn_dim']}_fc_{config['fc_dim']}_lr_{config['lr']:.1e}"
        f"_wd_{config['weight_decay']:.1e}_batch_{config['batch_size']}_event_{config['event_normals']}"
        f"_norm_{config['norm']}_gn_{int(config['use_gn'])}_disable_norm_{int(config['disable_norm'])}_pooling_{config['pooling']}"
    )

    train_ds = GraphDataset_new(f"{OUT_DIR}/train", augm=config["augm"])
    train_len = int(0.8 * len(train_ds))
    val_len = len(train_ds) - train_len
    train_ds, val_ds = random_split(train_ds, [train_len, val_len], generator=torch.Generator().manual_seed(42))
    val_ds.augm = []

    test_ds = GraphDataset_new(f"{OUT_DIR}/test")
    train_loader = DataLoader(train_ds, batch_size=config["batch_size"], shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=64)
    test_loader = DataLoader(test_ds, batch_size=64)

    num_node_features = train_ds[0].x.shape[1] - (2 if not config["event_normals"] else 0)
    model = GCN_combined(num_node_features, config["gcn_dim"], config["fc_dim"], 20, config["norm"], config["event_normals"], config["use_gn"], config["disable_norm"], config["pooling"])
    model.to(device)

    optimizer = torch.optim.Adam(model.parameters(), lr=config["lr"], weight_decay=config["weight_decay"])
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, patience=5)
    criterion = torch.nn.CrossEntropyLoss()

    early_stopping = EarlyStopping(patience=config["patience"], min_delta=config["min_delta"]) if config["early_stopping"] else None

    output_dir = os.path.join(results_root_dir, f"{config_summary}")
    os.makedirs(output_dir, exist_ok=True)

    loss_acc_dict = {"train_loss": [], "train_acc": [], "val_loss": [], "val_acc": []}
    best_model_state = None
    best_val_loss = float('inf')

    for epoch in range(100):
        train_loss, train_acc = train(model, train_loader, optimizer, criterion, device)
        val_loss, val_acc = evaluate(model, val_loader, criterion, device, mode="Validation")
        loss_acc_dict["train_loss"].append(train_loss)
        loss_acc_dict["train_acc"].append(train_acc)
        loss_acc_dict["val_loss"].append(val_loss)
        loss_acc_dict["val_acc"].append(val_acc)
        print(f"Epoch {epoch+1}, Train Loss: {train_loss}, Train Acc: {train_acc}, Val Loss: {val_loss}, Val Acc: {val_acc}")

        if val_loss < best_val_loss:
            best_val_loss = val_loss
            best_model_state = model.state_dict()
            torch.save(best_model_state, os.path.join(output_dir, "best_model.pt"))

        if early_stopping:
            early_stopping(val_loss)
            if early_stopping.early_stop:
                print(f"Early stopping at epoch {epoch+1}")
                break

    model.load_state_dict(torch.load(os.path.join(output_dir, "best_model.pt")))
    test_loss, test_acc = evaluate(model, test_loader, criterion, device, mode="Test")
    print(f'Test Loss: {test_loss:.6f}, Test Accuracy: {test_acc:.6f}')

    loss_acc_dict["test_loss"] = test_loss
    loss_acc_dict["test_acc"] = test_acc

    result_file_path = os.path.join(output_dir, f"{dt_string}.json")
    with open(result_file_path, "w") as f:
        json.dump(loss_acc_dict, f, indent=4)

    print("Training and Validation Loss/Accuracy Data:")
    print(loss_acc_dict)