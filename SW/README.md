# Setup

These are all the libraries I used (I might have installed some additional ones — if anything is missing, just install it manually):

```bash
conda create -n dvs_rec python=3.9
pip3 install --pre torch torchvision torchaudio --index-url https://download.pytorch.org/whl/nightly/cu128
conda install h5py
conda install blosc-hdf5-plugin -c conda-forge
pip install omegaconf opencv-python matplotlib psutil wandb lightning numba

python setup.py build_ext --inplace
```

---

## Datasets

This code was tested on the **Spiking Heidelberg Digits (SHD)** and **Spiking Speech Commands (SSC)** datasets.
To use it, first download the original data from the [official website](https://zenkelab.org/resources/spiking-heidelberg-datasets-shd/).

You can extract all `.h5` files into a single folder, specified later in the configuration `.yaml` files.
The required files are:

* For **Heidelberg Digits**: `shd_train.h5`, `shd_test.h5`
* For **Speech Commands**: `ssc_train.h5`, `ssc_valid.h5`, `ssc_test.h5`

Before training, the data is preprocessed — all events and labels are read from `.h5` files and saved into `.pt` (PyTorch) files.
This preprocessing should happen automatically during the first training run for each dataset.
If it doesn’t, use the **prepare.py** script (you can comment out lines to preprocess only a specific dataset).

---

## Code Structure

Important folders are described below:

### 1. `configs`

Contains all hyperparameters for dataset preprocessing, graph generation, model training, and model definition.
**You must specify the data directory here.**

Configs inside the `recognition` subfolder are used for the recognition/classification task, while the others are for **KWS** (keyword spotting).
`commands-11.yaml` and `commands-35.yaml` differ only by the number of classes:

* `35` – uses all commands
* `11` – selects only a subset (e.g. `stop`, `go`, `up`, etc.)

The list of 11 selected commands is in `data/utils/convert_ssc_cls.py`.

---

### 2. `data`

* The `utils` folder contains only one used file: `convert_ssc_cls.py`.
* `spiking_digits.py` and `spiking_commands.py` define **LightningDataModules** for preprocessing and preparing datasets for recognition.
* `spiking_digits_kws.py` and `spiking_commands_kws.py` are the same but for the **KWS** task.
* `edge_generator.cpp` implements a graph generator (from the ARC paper) in C++ for speedup.
  Compile it using:

  ```bash
  python setup.py build_ext --inplace
  ```
* `dataset.py` defines the dataset class for recognition — it loads data, normalizes timestamps, and generates edges.
* `kws_dataset.py` does the same for KWS, but additionally:

  * converts labels for SSC-11 and SSC-35 versions,
  * detects activation ranges (start/stop words) - I defined `detect_active_range` for this purpouse,
  * and generates one-hot vectors for the word class and word-end indicators (with small before/after activations to relax training).

---

### 3. `models`

Inside `networks/layers`, you’ll find custom implementations of all required and quantizable layers:

* `my_gru_cell.py` / `my_gru.py` — standard GRU layer with iterative (non-unfolded) implementation (i know, this is slow)
* `my_pointnet.py` — reimplementation of **PointNetConv** from PyTorch Geometric (pure PyTorch)
* `my_pooling.py` — graph global pooling (supports `add`, `mean`, `max`)
* `my_pooling_moving.py` — graph pooling across selected time bins
* `my_linear.py` — linear layer with quantization support

In the `networks` folder:

* `recognition.py` – model for recognition task
* `model.py` – model for KWS (sorry for the confusing name)

Outside of `networks`, the files:

* `kws.py` and `recognition.py` define **LightningModules** wrapping the networks with optimizers, training/validation steps, etc.

---

### 4. `utils`

Contains `generate_outputs.py`, used only for debugging within network implementations.
It saves tensors into `.txt` files when `debug=True` is set in the config file.

---

Other folders contain example model weights and generated layer outputs for debugging.

In the main directory, you’ll find these important files:

1. `setup.py` — compiles the C++ graph generator
2. `train_{digits/commands}_{kws/recognition}.py` — training scripts for each dataset/task; trains a float model, performs QAT, and runs final quantization/testing
3. `generate_weights.py` — initializes a model and loads pretrained `calibrated` or `quantized` weights
   (if loading `calibrated`, call `model.quantize()` afterward)
4. `generate_outputs*.py` — loads one data batch and runs it through the model; requires `cfg.debug=True` and `utils/generate_outputs.py` functions
5. `test_quant.py` — checks if `calibrated/fake_quantized` and `quantized` models give consistent outputs
6. `test.py` — visualizes a trained KWS model on a single sample, showing confidence and class outputs

---

## Working with the Code

If you have any questions or encounter issues, feel free to contact me.
This project was written entirely by me (for my own research), so some parts may be difficult to understand.

I recommend starting by exploring the **layers** and building your own model.
Each layer’s `forward()` function supports three modes: `float`, `calib`, and `quantize`.

* **Float mode** – standard (non-quantized) operation
* **Calibrate mode** – uses fake quantization and updates observer parameters (scale and zero point)
* **Quantize mode** – performs real quantization of weights and computes lookup tables (e.g., for GRU activations)

Within each network, the methods `calibrate()` and `quantize()` call the corresponding methods of all layers.
Importantly, during quantization, each layer should receive the `observer_input` and `observer_output` from the previous layer (pooling layers are an exception).

