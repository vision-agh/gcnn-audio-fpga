"""
LNRecognition – LightningModule do detekcji i klasyfikacji słów kluczowych
z poprawkami:

• klasyfikacja liczona wyłącznie w timesteps, w których `keyword == 1`
• waga gałęzi klasyfikacji konfigurowalna (`config.train.cls_weight`, domyślnie 5.0)
• `pos_weight` zarejestrowany jako buffer – zawsze na tym samym urządzeniu co model
"""

from typing import Dict

import torch
import lightning as L
from torch.nn import functional as F

from models.networks.model import GCN   # ← Twoja architektura feature-extractora


class LNRecognition(L.LightningModule):
    """Keyword-spotter: confidence + klasyfikacja słowa"""

    # -------------------------------------------------- setup
    def __init__(self, config):
        super().__init__()

        # --------- hiperpary ---------
        self.save_hyperparameters(config)
        self.lr           = config.train.lr
        self.weight_decay = config.train.weight_decay
        self.batch_size   = config.train.batch_size
        self.num_classes  = config.model.num_classes      # 11 (10 słów + background)

        # --------- sieć --------------
        self.model = GCN(config)

        # --------- straty ------------
        # confidence – 20 logitów (po 50 ms)
        # pos_weight = (liczba negatywów / liczba pozytywów) ≈ 19
        self.register_buffer("pos_weight", torch.full((100,), 99.0))
        self.conf_criterion = torch.nn.BCEWithLogitsLoss(
            pos_weight=self.pos_weight, reduction="mean"
        )

        # gałąź klasyfikacji – waga względem confidence
        self.cls_weight = 5.0

    # -------------------------------------------------- core API
    def forward(self, data):
        """
        Zwraca:
            conf_logits – [B, T]   (T = 20)
            cls_logits  – [B, C, T]
        """
        return self.model(data)

    def configure_optimizers(self):
        return torch.optim.Adam(
            self.parameters(), lr=self.lr, weight_decay=self.weight_decay
        )

    # -------------------------------------------------- utils
    @staticmethod
    def _timestamp_accuracy(
        conf_logits: torch.Tensor,
        cls_logits: torch.Tensor,
        gt_keyword: torch.Tensor,
        gt_cls_idx: torch.Tensor,
        tolerance: int = 0.05,
    ) -> torch.Tensor:
        """
        Trafiamy, jeśli:
        • pred_timestamp w odległości ≤ `tolerance` od GT
        • pred_class == GT_class w tym timestampie
        """
        B, T = gt_keyword.shape

        gt_ts = gt_keyword.argmax(dim=-1)                # [B]
        pred_ts = conf_logits.argmax(dim=-1)             # [B]
        pred_cls_btC = cls_logits.permute(0, 2, 1)       # [B,T,C]
        pred_lbl = pred_cls_btC[torch.arange(B), gt_ts].argmax(dim=-1)

        gt_lbl = gt_cls_idx[torch.arange(B), gt_ts]      # [B]

        time_ok = (pred_ts - gt_ts).abs() <= tolerance
        return ((pred_lbl == gt_lbl) & time_ok).float().mean(), ((pred_lbl == gt_lbl)).float().mean()

    # -------------------------------------------------- train / val / test
    def _shared_step(self, batch: Dict, stage: str):
        conf_logits, cls_logits = self.forward(batch)

        # -------- confidence loss (liczony na wszystkich T)
        loss_conf = self.conf_criterion(conf_logits, batch["keyword"])

        # -------- classification loss (tylko tam, gdzie keyword == 1)
        pos_mask = batch["keyword"] > 0.5         # [B,T] bool
        num_pos = pos_mask.sum()

        if num_pos > 0:
            cls_logits_btC = cls_logits.permute(0, 2, 1)        # [B,T,C]
            loss_cls = F.cross_entropy(
                cls_logits_btC[pos_mask],                       # [N_pos,C]
                batch["cls"][pos_mask].long(),                  # [N_pos]
            )
        else:
            # rzadki przypadek całego batcha bez słów
            loss_cls = torch.zeros((), device=self.device)

        total_loss = loss_conf + self.cls_weight * loss_cls

        # -------- logi
        self.log(f"{stage}_loss_conf", loss_conf, prog_bar=True, batch_size=self.batch_size)
        self.log(f"{stage}_loss_cls",  loss_cls,  prog_bar=True, batch_size=self.batch_size)
        self.log(f"{stage}_loss",      total_loss, prog_bar=True, batch_size=self.batch_size)

        ts_acc, acc = self._timestamp_accuracy(
            conf_logits, cls_logits, batch["keyword"], batch["cls"]
        )
        self.log(f"{stage}_ts_acc", ts_acc, prog_bar=True, batch_size=self.batch_size)
        self.log(f"{stage}_acc", ts_acc, prog_bar=True, batch_size=self.batch_size)

        return total_loss

    def training_step(self, batch, batch_idx):
        return self._shared_step(batch, "train")

    def validation_step(self, batch, batch_idx):
        self._shared_step(batch, "val")

    def test_step(self, batch, batch_idx):
        self._shared_step(batch, "test")
