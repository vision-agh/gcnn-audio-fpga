import yaml
import dotmap
import lightning as L
import torch
from models.recognition import LNRecognition
from data.spiking_digits import SpikingDigits
from data.dataset import SpikingDS


cfg = yaml.load(open('configs/digits.yaml', 'r'), Loader=yaml.FullLoader)
cfg = dotmap.DotMap(cfg)

input = torch.load('datasets/hdspikes/processed/test/0.pt', weights_only=False)
print(input.pos)

dm = SpikingDS(files=['datasets/hdspikes/processed/test/0.pt'], config=cfg)

data = dm[0]

lm = LNRecognition.load_from_checkpoint('checkpoints/best_model_calibrated-v2.ckpt')


model = lm.model
model.eval()

out, _ = model(data.to('cuda'))
print(out)


model.quantize()

data = dm[0]
out, _ = model(data.to('cuda'))
print(out)
# with open('model.txt', 'w') as f:
#     for i, (x, pos) in enumerate(zip(data.x, data.pos)):
#         t = pos[0]
#         idx = pos[1]
#         ts = (t.item()*1000000)
#         ts = int(ts)
#         idxs = int((idx*700).round().item())

#         avg_t = x[0]
#         avg_idx = x[1]

#         avg_t = model.conv1.observer_input.quantize_tensor(avg_t)
#         avg_idx = model.conv1.observer_input.quantize_tensor(avg_idx)

#         print('T=', ts, '\tIdx=', idxs, '\tAvg_T=', int(avg_t.item()), '\tAvg_Idx=', int(avg_idx.item()))
#         f.write(f'T={ts}\tIdx={idxs}\tAvg_T={int(avg_t.item())}\tAvg_Idx={int(avg_idx.item())}\n')
        
#         mask = data.edge_index[1, :] == i
#         neighbour_pos = data.pos[data.edge_index[0, mask].T]

#         if len(neighbour_pos) > 0:
#             # Sort by idx from smallest to largest
#             neighbour_pos = neighbour_pos[neighbour_pos[:, 1].argsort()]

#             for n_pos in neighbour_pos:
#                 n_t = int(n_pos[0].item()*1000000)
#                 n_idx = int((n_pos[1]*700).round().item())

#                 diff_t = (n_pos[0] - t)*(-50)
#                 diff_idx = (n_pos[1] - idx + 1/7) * (7/2)

#                 print("   Diff T=", n_t - ts, 
#                     " Diff Idx=", n_idx - idxs, 
#                     " Quantized Diff T=", int(model.conv1.observer_input.quantize_tensor(torch.tensor(diff_t)).item()), 
#                     " Quantized Diff Idx=", int(model.conv1.observer_input.quantize_tensor(torch.tensor(diff_idx)).item()))
                
#                 f.write(f'   Diff T={n_t - ts} Diff Idx={n_idx - idxs} Quantized Diff T={int(model.conv1.observer_input.quantize_tensor(torch.tensor(diff_t)).item())} Quantized Diff Idx={int(model.conv1.observer_input.quantize_tensor(torch.tensor(diff_idx)).item())}\n')
