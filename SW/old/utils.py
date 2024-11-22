import os
import urllib.request
import shutil
import gzip, shutil
import hashlib
import pickle
from bisect import bisect_left, bisect_right, bisect
import torch_geometric as tg
from abc import ABC
from typing import Union, List, Tuple
from torch_geometric.utils import from_networkx, dropout_edge, dropout_node, subgraph
import torch
from six.moves.urllib.error import HTTPError
from six.moves.urllib.error import URLError
from six.moves.urllib.request import urlretrieve

import collections
import os.path as osp
import os
import errno
import numpy as np
import glob
import scipy.io as sio
import torch

import torch.utils.data
from torch_geometric.data import Data, DataLoader
from torch.utils.data import Dataset

import os.path as osp
import networkx as nx
import torch
import torch.nn.functional as F
from torch_geometric.data.data import BaseData
from torch_geometric.nn import GCNConv, SplineConv, aggr
from torch_geometric.nn import global_mean_pool


# The functions used in this file to download the dataset are based on
# code from the keras library. Specifically, from the following file:
# https://github.com/tensorflow/tensorflow/blob/v2.3.1/tensorflow/python/keras/utils/data_utils.py


# TODO, make a GRU version of the Spline Convolution
class GRUSplineConv(SplineConv):
    """A permutation variant version"""

    def __init__(self, in_channels, out_channels, dim, kernel_size, **kwargs):
        super().__init__(in_channels, out_channels, dim, kernel_size, **kwargs)
        self.aggr = aggr.GRUAggregation(in_channels=in_channels, out_channels=in_channels)

    def aggregate(self, inputs, index, dim_size=None):
        """ overrides parent's aggregate function with a permutation variant one"""
        node_dim = self.node_dim
        print("inputs shape: ", inputs.shape, "sorted on: ", inputs[:, 2].shape)
        edge_index, sort_order = torch.sort(inputs[:, 2])
        x = inputs[sort_order]
        out = self.aggr(x, index=edge_index, dim=node_dim, dim_size=dim_size)
        return out


class GraphDataset_new(Dataset):
    def __init__(self, root, augm=[], mode="shd_label"):
        print("ROOT: ", root)
        self.root = root
        self.mode = mode
        self.augm = augm
        self.files = [f for f in os.listdir(root) if os.path.isfile(os.path.join(self.root, f))]

    def __len__(self):
        return len(self.files)

    def __getitem__(self, idx):
        #print("FILE: ", self.files[0], "ADS")
        with open(os.path.join(self.root, self.files[idx]), 'rb') as f:
            if "pkl" in self.files[idx]:
                graph, label = pickle.load(f)
                #DELETE THIS LINE FOR CORRECT DATASETS
                #return graph
                if "node_drop" in self.augm and np.random.rand() < 0.2:
                    graph = node_drop(graph) 
                if "edge_drop" in self.augm and np.random.rand() < 0.2:
                    graph = edge_drop(graph) 
                if "mask_drop" in self.augm and np.random.rand() < 0.2:
                    graph = mask_drop(graph) 

                g = from_networkx(graph)
                if "time_stretch" in self.augm and np.random.rand() < 0.2:
                    g = time_stretch(g)
                if "random_shift" in self.augm and np.random.rand() < 0.2:
                    g = random_shift(g)
                g.phoneme = digit_to_phonemes(label) if "shd" in self.mode else command_to_phonemes(label)
                g.x = g.x.float()
                g.y = torch.tensor([label], dtype=torch.long)
            if "pt" in self.files[idx]:
                g = torch.load(os.path.join(self.root, self.files[idx]))
                if "node_drop" in self.augm:
                    print("ID:", idx)
                    new_edge_index, _, node_mask = dropout_node(g.edge_index, p=0.2, relabel_nodes=True)
                    g.edge_index = new_edge_index
                    print(g.x.shape, node_mask.shape)
                    g.x = g.x[node_mask]
                    print(g.edge_index)
                if "edge_drop" in self.augm:
                    new_edge_index, _ = dropout_edge(g.edge_index, p=0.2)
                    g.edge_index = new_edge_index
                if "mask_drop" in self.augm:
                    print("ID:", idx)
                    print(g.x.shape)
                    avg = torch.mean(g.x[:,:2], axis=0)
                    node_indices_to_keep = torch.where(torch.sqrt(torch.sum((g.x[:,:2]-avg) ** 2, dim=1)) > 0.1)[0]
                    new_edge_index, _ = subgraph(node_indices_to_keep, g.edge_index, relabel_nodes=True)
                    print(node_indices_to_keep.shape)
                    g.x = g.x[node_indices_to_keep]
                    g.edge_index = new_edge_index
                if "time_stretch" in self.augm:
                    g.x[:,0] *= np.random.normal(loc=1, scale=0.3)
                if "random_shift" in self.augm:
                    g.x += torch.randn(2)/10
        return g

class GraphDataset(Dataset):
    def __init__(self, root, w_augm=True, mode="label", transform=None, pre_transform=None, pre_filter=None):
        super().__init__(root, transform, pre_transform, pre_filter)
        self.root = root
        self.mode = mode
        if w_augm:
            self.files = [f for f in os.listdir(root) if os.path.isfile(os.path.join(self.root, f))]
        else:
            self.files = [f for f in os.listdir(root) if (os.path.isfile(os.path.join(root, f)) and (not ("aug" in f)))]

    def len(self):
        return len(self.files)

    def get(self, idx):
        g = torch.load(os.path.join(self.root, self.files[idx]))
        g.x = g.x.float()
        g.y = g.y.type(torch.LongTensor)
        g.phoneme = digit_to_phonemes(int(g.y)) if "shd" in self.mode else command_to_phonemes(int(g.y))
        #if "phoneme" in self.mode:
            #g.y = digit_to_phonemes(int(g.y)) if "shd" in self.mode else command_to_phonemes(int(g.y))
        #    g.y = g.y.type(torch.LongTensor)
        #    g.phoneme = digit_to_phonemes(int(g.y)) if "shd" in self.mode else command_to_phonemes(int(g.y))
        #elif "hybrid" in self.mode:
        #    g.y = g.y.type(torch.LongTensor)
        #    g.phoneme = digit_to_phonemes(int(g.y)) if "shd" in self.mode else command_to_phonemes(int(g.y))
        return g

    @property
    def raw_file_names(self):
        return []  # No raw files

    @property
    def processed_file_names(self):
        return []  # No processed files

    def download(self):
        pass  # No download

    def process(self):
        pass  # No processing

def edge_drop(graph, p=0.1):
    drop_edges = np.random.rand(len(graph.edges)) < p
    graph.remove_edges_from(np.array(graph.edges)[drop_edges])
    return graph

def node_drop(graph, p=0.1):
    drop_nodes = np.random.rand(len(graph.nodes)) < p
    graph.remove_nodes_from(np.array(graph.nodes)[drop_nodes])
    return graph

def mask_drop(graph, t_radius=0, channel_radius=0, size=0.1):
    points = from_networkx(graph).x[:,:2]
    avg = np.average(points, axis=0)
    drop_nodes = np.where(np.linalg.norm(points-avg, axis=1) < size)[0]
    graph.remove_nodes_from(np.array(graph.nodes)[drop_nodes])
    return graph

def time_stretch(data):
    data.x[:,0] *= np.random.normal(loc=0, scale=0.1)
    return data

def random_shift(data):
    data.x[:,:2] += torch.randn(2)/10
    return data



def overlap(start1, end1, start2, end2):
    return max(0, min(end1, end2) - max(start1, start2))

def adjust_labels(gru_output, labels, label_times, window_size):
    gru_times = np.linspace(min(label_times).item(), max(label_times).item(), len(gru_output))
    adjusted_labels = torch.zeros(len(gru_output), 61).to(labels.device)
    #print("MIN, MAX:", min(label_times).item(), max(label_times).item())
    #print("SHAPES: gru_output, gru_times, adjusted_labels", gru_output.shape, gru_times.shape, adjusted_labels.shape)
    #print("labels, label_times, window_size ", labels.shape, label_times.shape, window_size)
    for idx, time in enumerate(gru_times):
        start_idx = bisect(list(label_times), time) - 1
        end_idx = bisect(list(label_times), time + window_size) - 1
        for label_idx in range(start_idx, end_idx + 1):
            end_label = 1000
            if label_idx + 1 < len(label_times):
                end_label = label_times[label_idx + 1]
            adjusted_labels[idx] += overlap(time, time + window_size, label_times[label_idx], end_label) / window_size * labels[label_idx]
    return adjusted_labels


def get_phoneme_list_shd():
    phonemes = [torch.zeros(31) for _ in range(20)]
    phonemes[0][[18, 13, 6, 19]] = 1
    phonemes[1][[0, 1, 2]] = 1
    phonemes[2][[3, 4]] = 1
    phonemes[3][[5, 6, 7]] = 1
    phonemes[4][[8, 9, 6]] = 1
    phonemes[5][[8, 10, 11]] = 1
    phonemes[6][[12, 13, 14]] = 1
    phonemes[7][[12, 15, 11, 16, 2]] = 1
    phonemes[8][[17, 3]] = 1
    phonemes[9][[2, 10]] = 1
    phonemes[10][[2, 29, 30]] = 1
    phonemes[11][[10, 2, 12]] = 1
    phonemes[12][[21, 11, 10]] = 1
    phonemes[13][[22, 6, 10]] = 1
    phonemes[14][[8, 7, 23]] = 1
    phonemes[15][[8, 24, 2]] = 1
    phonemes[16][[18, 15, 14, 12]] = 1
    phonemes[17][[18, 7, 15, 16, 2]] = 1
    phonemes[18][[26, 27, 3]] = 1
    phonemes[19][[2, 28]] = 1
    return phonemes

def get_phoneme_list_ssc():
    phonemes = [torch.zeros(43) for _ in range(35)]
    phonemes[0][[14, 7, 26]] = 1
    phonemes[1][[18, 19]] = 1
    phonemes[2][[33, 23]] = 1
    phonemes[3][[5, 2, 18]] = 1
    phonemes[4][[16, 7, 8, 28]] = 1
    phonemes[5][[24, 1, 28]] = 1
    phonemes[6][[0, 18]] = 1
    phonemes[7][[20, 8]] = 1
    phonemes[8][[26, 28, 0, 23]] = 1
    phonemes[9][[9, 19]] = 1
    phonemes[10][[37, 12, 24, 19]] = 1
    phonemes[11][[35, 33, 18]] = 1
    phonemes[12][[28, 31]] = 1
    phonemes[13][[39, 24, 11]] = 1
    phonemes[14][[8, 21, 24]] = 1
    phonemes[15][[8, 1, 34]] = 1
    phonemes[16][[26, 12, 15]] = 1
    phonemes[17][[26, 7, 34, 41, 18]] = 1
    phonemes[18][[6, 28]] = 1
    phonemes[19][[18, 1]] = 1
    phonemes[20][[4, 7, 5]] = 1
    phonemes[21][[4, 42, 24, 5]] = 1
    phonemes[22][[15, 3, 28]] = 1
    phonemes[23][[5, 20, 9]] = 1
    phonemes[24][[10, 3, 23, 11]] = 1
    phonemes[25][[10, 2, 26]] = 1
    phonemes[26][[17, 0, 24, 34, 12, 18]] = 1
    phonemes[27][[27, 11, 16, 41]] = 1
    phonemes[28][[28, 24, 11]] = 1
    phonemes[29][[35, 2]] = 1
    phonemes[30][[4, 3, 15, 35, 41, 24, 5]] = 1
    phonemes[31][[8, 20, 24, 35, 41, 24, 5]] = 1
    phonemes[32][[8, 0, 16, 19]] = 1
    phonemes[33][[16, 42, 24, 18]] = 1
    phonemes[34][[34, 12, 33, 41, 16]] = 1
    return phonemes


def command_to_phonemes(digit):
    phoneme = torch.zeros(43)
    if digit == 0:  # [j], [ɛ], [s]
        phoneme[[14, 7, 26]] = 1
    elif digit == 1:  # [n], [oʊ]
        phoneme[[18, 19]] = 1
    elif digit == 2:  # [ʌ], [p]
        phoneme[[33, 23]] = 1
    elif digit == 3:  # [d], [aʊ], [n]
        phoneme[[5, 2, 18]] = 1
    elif digit == 4:  # [l], [ɛ], [f], [t]
        phoneme[[16, 7, 8, 28]] = 1
    elif digit == 5:  # [r], [aɪ], [t]
        phoneme[[24, 1, 28]] = 1
    elif digit == 6:  # [ɑ], [n]
        phoneme[[0, 18]] = 1
    elif digit == 7:  # [ɔ], [f]
        phoneme[[20, 8]] = 1
    elif digit == 8:  # [s], [t], [ɑ], [p]
        phoneme[[26, 28, 0, 23]] = 1
    elif digit == 9:  # [g], [oʊ]
        phoneme[[9, 19]] = 1
    elif digit == 10:  # [z], [ɪ], [r], [oʊ]
        phoneme[[37, 12, 24, 19]] = 1
    elif digit == 11:  # [w], [ʌ], [n]
        phoneme[[35, 33, 18]] = 1
    elif digit == 12:  # [t], [uː]
        phoneme[[28, 31]] = 1
    elif digit == 13:  # [θ], [r], [iː]
        phoneme[[39, 24, 11]] = 1
    elif digit == 14:  # [f], [ɔː], [r]
        phoneme[[8, 21, 24]] = 1
    elif digit == 15:  # [f], [aɪ], [v]
        phoneme[[8, 1, 34]] = 1
    elif digit == 16:  # [s], [ɪ], [k], [s]
        phoneme[[26, 12, 15]] = 1
    elif digit == 17:  # [s], [ɛ], [v], [ə], [n]
        phoneme[[26, 7, 34, 41, 18]] = 1
    elif digit == 18:  # [eɪ], [t]
        phoneme[[6, 28]] = 1
    elif digit == 19:  # [n], [aɪ], [n]
        phoneme[[18, 1]] = 1
    elif digit == 20:  # [b], [ɛ], [d]
        phoneme[[4, 7, 5]] = 1
    elif digit == 21:  # [b], [ɜ], [r], [d]
        phoneme[[4, 42, 24, 5]] = 1
    elif digit == 22:  # [k], [æ], [t]
        phoneme[[15, 3, 28]] = 1
    elif digit == 23:  # [d], [ɔ], [g]
        phoneme[[5, 20, 9]] = 1
    elif digit == 24:  # [h], [æ], [p], [i]
        phoneme[[10, 3, 23, 11]] = 1
    elif digit == 25:  # [h], [aʊ], [s]
        phoneme[[10, 2, 26]] = 1
    elif digit == 26:  # [m], [ɑ], [r], [v], [ɪ], [n]
        phoneme[[17, 0, 24, 34, 12, 18]] = 1
    elif digit == 27:  # [ʃ], [iː], [l], [ə]
        phoneme[[27, 11, 16, 41]] = 1
    elif digit == 28:  # [t], [r], [i]
        phoneme[[28, 24, 11]] = 1
    elif digit == 29:  # [w], [aʊ]
        phoneme[[35, 2]] = 1
    elif digit == 30:  # [b], [æ], [k], [w], [ə], [r], [d]
        phoneme[[4, 3, 15, 35, 41, 24, 5]] = 1
    elif digit == 31:  # [f], [ɔ], [r], [w], [ə], [r], [d]
        phoneme[[8, 20, 24, 35, 41, 24, 5]] = 1
    elif digit == 32:  # [f], [ɑ], [l], [oʊ]
        phoneme[[8, 0, 16, 19]] = 1
    elif digit == 33:  # [l], [ɜ], [r], [n]
        phoneme[[16, 42, 24, 18]] = 1
    elif digit == 34:  # [v], [ɪ], [ʒ], [u], [ə], [l]
        phoneme[[34, 12, 33, 41, 16]] = 1
    return phoneme.reshape(1, 43)



def digit_from_pred(pred, shd=True):
    phonemes = get_phoneme_list_shd() if shd else get_phoneme_list_ssc()
    max_matches = -1
    closest_digit = -1
    for idx, phon in enumerate(phonemes):
        matches = pred.eq(phon).sum()
        if matches > max_matches:
            max_matches = matches
            closest_digit = idx
    return closest_digit


def label_from_pred(pred, shd=True):
    phonemes = get_phoneme_list_shd() if shd else get_phoneme_list_ssc()
    max_matches = -1
    closest_label = -1
    for idx, phon in enumerate(phonemes):
        matches = pred.eq(phon).sum()
        if matches > max_matches:
            max_matches = matches
            closest_label = idx
    return closest_label


def digit_to_phonemes(digit):
    phoneme = torch.zeros(31)
    if digit == 0:  # [z], [ɪ], [r], [oʊ]
        phoneme[[18, 13, 6, 19]] = 1
    elif digit == 1:  # [w], [ʌ], [n]
        phoneme[[0, 1, 2]] = 1
    elif digit == 2:  # [t], [uː]
        phoneme[[3, 4]] = 1
    elif digit == 3:  # [θ], [r], [iː]
        phoneme[[5, 6, 7]] = 1
    elif digit == 4:  # [f], [ɔː], [r]
        phoneme[[8, 9, 6]] = 1
    elif digit == 5:  # [f], [aɪ], [v]
        phoneme[[8, 10, 11]] = 1
    elif digit == 6:  # [s], [ɪ], [k], [s]
        phoneme[[12, 13, 14]] = 1
    elif digit == 7:  # [s], [ɛ], [v], [ə], [n]
        phoneme[[12, 15, 11, 16, 2]] = 1
    elif digit == 8:  # [eɪ], [t]
        phoneme[[17, 3]] = 1
    elif digit == 9:  # [n], [aɪ], [n]
        phoneme[[2, 10]] = 1
    elif digit == 10:  # [n], [ʊ], [l]
        phoneme[[2, 29, 30]] = 1
    elif digit == 11:  # [aɪ], [n], [s]
        phoneme[[10, 2, 12]] = 1
    elif digit == 12:  # [t͡s], [v], [aɪ]
        phoneme[[21, 11, 10]] = 1
    elif digit == 13:  # [d], [r], [aɪ]
        phoneme[[22, 6, 10]] = 1
    elif digit == 14:  # [f], [iː], [ʁ]
        phoneme[[8, 7, 23]] = 1
    elif digit == 15:  # [f], [ʏ], [n], [f]
        phoneme[[8, 24, 2]] = 1
    elif digit == 16:  # [z], [ɛ], [k], [s]
        phoneme[[18, 15, 14, 12]] = 1
    elif digit == 17:  # [z], [iː], [b], [ə], [n]
        phoneme[[18, 7, 15, 16, 2]] = 1
    elif digit == 18:  # [a], [x], [t]
        phoneme[[26, 27, 3]] = 1
    elif digit == 19:  # [n], [ɔʏ], [n]
        phoneme[[2, 28]] = 1
    return phoneme.reshape(1, 31)



class Compose(torch.nn.Module):
    def __init__(self, transforms):
        super().__init__()
        self.transforms = transforms

    def forward(self, data):
        for aug in self.transforms:
            data = aug(data)
        return data


# needs to work with edges as well


class NodeDrop(torch.nn.Module):
    def __init__(self, p=0.05):
        super().__init__()
        self.p = p

    def forward(self, g):
        idx = torch.empty(g.x.size(0)).uniform_(0, 1)
        g.x = g.x[idx > self.p]
        return g


class EdgeDrop(torch.nn.Module):
    def __init__(self, p=0.05):
        super().__init__()
        self.p = p

    def forward(self, g):
        idx = torch.empty(g.edge_index.shape[1]).uniform_(0, 1)
        g.edge_index = g.edge_index[:, idx >= self.p]
        g.edge_attr = g.edge_attr[idx.T >= self.p, :]
        return g


def get_shd_dataset(cache_dir, cache_subdir):
    # The remote directory with the data files
    base_url = "https://zenkelab.org/datasets"

    # Retrieve MD5 hashes from remote
    response = urllib.request.urlopen("%s/md5sums.txt" % base_url)
    data = response.read()
    lines = data.decode('utf-8').split("\n")
    file_hashes = {line.split()[1]: line.split()[0] for line in lines if len(line.split()) == 2}

    # Download the Spiking Heidelberg Digits (SHD) dataset
    files = ["shd_train.h5.gz",
             "shd_test.h5.gz",
             ]
    for fn in files:
        origin = "%s/%s" % (base_url, fn)
        hdf5_file_path = get_and_gunzip(origin, fn, md5hash=file_hashes[fn], cache_dir=cache_dir,
                                        cache_subdir=cache_subdir)
        # print("File %s decompressed to:"%(fn))
        print("Available at: %s" % hdf5_file_path)


def get_and_gunzip(origin, filename, md5hash=None, cache_dir=None, cache_subdir=None):
    gz_file_path = get_file(filename, origin, md5_hash=md5hash, cache_dir=cache_dir, cache_subdir=cache_subdir)
    hdf5_file_path = gz_file_path[:-3]
    if not os.path.isfile(hdf5_file_path) or os.path.getctime(gz_file_path) > os.path.getctime(hdf5_file_path):
        print("Decompressing %s" % gz_file_path)
        with gzip.open(gz_file_path, 'r') as f_in, open(hdf5_file_path, 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)
    return hdf5_file_path


def validate_file(fpath, file_hash, algorithm='auto', chunk_size=65535):
    if (algorithm == 'sha256') or (algorithm == 'auto' and len(file_hash) == 64):
        hasher = 'sha256'
    else:
        hasher = 'md5'

    if str(_hash_file(fpath, hasher, chunk_size)) == str(file_hash):
        return True
    else:
        return False


def _hash_file(fpath, algorithm='sha256', chunk_size=65535):
    if (algorithm == 'sha256') or (algorithm == 'auto' and len(hash) == 64):
        hasher = hashlib.sha256()
    else:
        hasher = hashlib.md5()

    with open(fpath, 'rb') as fpath_file:
        for chunk in iter(lambda: fpath_file.read(chunk_size), b''):
            hasher.update(chunk)

    return hasher.hexdigest()


def get_file(fname,
             origin,
             md5_hash=None,
             file_hash=None,
             cache_subdir='datasets',
             hash_algorithm='auto',
             extract=False,
             archive_format='auto',
             cache_dir=None):
    if cache_dir is None:
        cache_dir = os.path.join(os.path.expanduser('~'), '.data-cache')
    if md5_hash is not None and file_hash is None:
        file_hash = md5_hash
        hash_algorithm = 'md5'
    datadir_base = os.path.expanduser(cache_dir)
    if not os.access(datadir_base, os.W_OK):
        datadir_base = os.path.join('/tmp', '.data-cache')
    datadir = os.path.join(datadir_base, cache_subdir)

    # Create directories if they don't exist
    os.makedirs(cache_dir, exist_ok=True)
    os.makedirs(datadir, exist_ok=True)

    fpath = os.path.join(datadir, fname)

    download = False
    if os.path.exists(fpath):
        # File found; verify integrity if a hash was provided.
        if file_hash is not None:
            if not validate_file(fpath, file_hash, algorithm=hash_algorithm):
                print('A local file was found, but it seems to be '
                      'incomplete or outdated because the ' + hash_algorithm +
                      ' file hash does not match the original value of ' + file_hash +
                      ' so we will re-download the data.')
                download = True
    else:
        download = True

    if download:
        print('Downloading data from', origin)

        error_msg = 'URL fetch failure on {}: {} -- {}'
        try:
            try:
                urlretrieve(origin, fpath)
            except HTTPError as e:
                raise Exception(error_msg.format(origin, e.code, e.msg))
            except URLError as e:
                raise Exception(error_msg.format(origin, e.errno, e.reason))
        except (Exception, KeyboardInterrupt) as e:
            if os.path.exists(fpath):
                os.remove(fpath)

    return fpath


class SpikeTrainList():
    def __init__(self, hdf5_data):
        self.spikes_list = []
        for times, units in zip(hdf5_data["times"], hdf5_data["units"]):
            assert times.shape[0] == units.shape[0]
            spike_train = torch.zeros((times.shape[0], 2))
            spike_train[:, 0] = torch.from_numpy(times)
            spike_train[:, 1] = torch.from_numpy(units.astype("float16"))
            self.spikes_list.append(spike_train)

    def get_data(self):
        return self.spikes_list


"""
class SpikeTrainDataSet(Dataset):
    def __init__(self, root, transform=None, pre_transform=None):
        super(SpikeTrainDataSet, self).__init__(root, transform, pre_transform)


    @property
    def processed_file_names(self):
        filenames = glob.glob(os.path.join(self.raw_dir, '*.mat'))
        file = [f.split('/')[4] for f in filenames]
        saved_file = [f.replace('.mat', '.pt') for f in file]
        return saved_file

    def __len__(self):
        return len(self.processed_file_names)

    def download(self):
        if files_exist(self.raw_paths):
            return
        print('No found data!!!!!!!')

    def process(self):
        for raw_path in self.raw_paths:
            # Read data from `raw_path`.
            content = sio.loadmat(raw_path)
            feature = torch.tensor(content['feature'])
            edge_index = torch.tensor(np.array(content['edge'], np.int32), dtype=torch.long)
            pos = torch.tensor(content['pseudo'])

            label_idx = torch.tensor(content['label'], dtype=torch.long)

            data = Data(x=feature, edge_index=edge_index, pos=pos, y=label_idx.squeeze(0))

            if self.pre_filter is not None and not self.pre_filter(data):
                continue

            if self.pre_transform is not None:
                data = self.pre_transform(data)

            saved_name = raw_path.split('/')[4].replace('.mat', '.pt')
            torch.save(data, osp.join(self.processed_dir, saved_name))

    def get(self, idx):
        data = torch.load(osp.join(self.processed_paths[idx]))
        return data
"""
