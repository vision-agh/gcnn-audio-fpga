# Hardware-accelerated graph neural networks: an alternative approach for event-based audio classification and keyword spotting on SoC FPGA

This repository provides the end-to-end FPGA implementation of the keyword spotting system utilising the Neuromorphic Auditory Sensor and Graph Neural Networks as published and presented during the 2026 ARC conference.

<div align="center" style="background-color: white; padding: 10px; display: inline-block;">
  <img src="assets/Diagram.png" width="1000px"/><br>
    <p style="font-size:1.5vw;">The proposed architecture is illustrated with the sensor and filtering modules highlighted in green, the feature extraction stage in blue, and the MaxPool and network head modules in yellow. The scheduling mechanism is marked in purple, while the timestamp propagation mechanism is indicated in red.. </p>
</div>


## Authors

|Name|Contact|Affilation|
|-|-|-|
|Kamil Jeziorek|kjeziorek@agh.edu.pl|AGH University of Krakow, Poland|
|Piotr Wzorek|pwzorek@agh.edu.pl|AGH University of Krakow, Poland|
|Krzysztof Błachut|kblachut@agh.edu.pl|AGH University of Krakow, Poland|
|Hiroshi Nakano|nahikaro1234@keio.jp|Graduate School of Science and Technology, Keio University Japan|
|Manon Dampfhoffer|Manon.DAMPFHOFFER@cea.fr|CEA-List, Université Grenoble Alpes, France|
|Thomas Mesquida|thomas.mesquida@cea.fr|CEA-List, Université Grenoble Alpes, France|
|Hiroaki Nishi|west@keio.jp|Graduate School of Science and Technology, Keio University, Japan|
|Thomas Dalgaty|Thomas.DALGATY@cea.fr|CEA-List, Université Grenoble Alpes, France|
|Tomasz Kryjak|kryjak@agh.edu.pl|AGH University of Krakow, Poland|

## Getting Started

The project is divided into two parts: Software and Hardware.

### Software

The software part of the project is responsible for training and evaluating GCN models (PyTroch implementation).

### Hardware

The hardware part contains necessary files for implementing GCN on the FPGA.

## Citation
If you find this project useful in your research, please consider citing our work:

```BibTeX
@article{jeziorek2026hardware,
  title={Hardware-Accelerated Graph Neural Networks: An Alternative Approach for Event-Based Audio Classification and Keyword Spotting on SoC FPGA},
  author={Jeziorek, Kamil and Wzorek, Piotr and Blachut, Krzysztof and Nakano, Hiroshi and Dampfhoffer, Manon and Mesquida, Thomas and Nishi, Hiroaki and Dalgaty, Thomas and Kryjak, Tomasz},
  journal={ACM Transactions on Reconfigurable Technology and Systems},
  volume={19},
  number={3},
  pages={1--34},
  year={2026},
  publisher={ACM New York, NY}
}
```
```BibTeX
@InProceedings{10.1007/978-3-031-87995-1_4,
author="Nakano, Hiroshi
and Blachut, Krzysztof
and Jeziorek, Kamil
and Wzorek, Piotr
and Dampfhoffer, Manon
and Mesquida, Thomas
and Nishi, Hiroaki
and Kryjak, Tomasz
and Dalgaty, Thomas",
title="Hardware-Accelerated Event-Graph Neural Networks for Low-Latency Time-Series Classification on SoC FPGA",
booktitle="Applied Reconfigurable Computing. Architectures, Tools, and Applications",
year="2025",
publisher="Springer Nature Switzerland",
address="Cham",
pages="51--68",
isbn="978-3-031-87995-1"
}
```
