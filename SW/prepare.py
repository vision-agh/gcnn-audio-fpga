import yaml
import dotmap

from data.spiking_digits_kws import SpikingDigits
from data.spiking_commands_kws import SpikingCommands

cfg = yaml.load(open('configs/digits.yaml', 'r'), Loader=yaml.FullLoader)
cfg = dotmap.DotMap(cfg)
dm = SpikingDigits(cfg)
dm.prepare_data()

cfg = yaml.load(open('configs/commands-11.yaml', 'r'), Loader=yaml.FullLoader)
cfg = dotmap.DotMap(cfg)
dm = SpikingCommands(cfg)
dm.prepare_data()