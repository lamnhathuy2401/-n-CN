"""ResNet50 binary classifier service — Real (0) vs AI-Generated (1)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import torch
import torch.nn as nn
from PIL import Image
from torchvision import models, transforms
from torchvision.models import ResNet50_Weights

LABEL_NAMES = ["Real", "AI-Generated"]
IMG_SIZE = 224
IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]

EVAL_TRANSFORMS = transforms.Compose(
    [
        transforms.Resize((IMG_SIZE, IMG_SIZE)),
        transforms.ToTensor(),
        transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD),
    ]
)


def build_resnet50_binary(
    freeze_early_blocks: bool = True,
    *,
    pretrained: bool = False,
) -> nn.Module:
    # Inference / checkpoint load: weights=None (faster, no ImageNet download).
    # Training notebooks may still pass pretrained=True.
    weights = ResNet50_Weights.IMAGENET1K_V2 if pretrained else None
    model = models.resnet50(weights=weights)

    if freeze_early_blocks:
        for i, child in enumerate(model.children()):
            if i < 7:
                for param in child.parameters():
                    param.requires_grad = False

    num_ftrs = model.fc.in_features
    model.fc = nn.Sequential(
        nn.Linear(num_ftrs, 256),
        nn.ReLU(inplace=True),
        nn.Dropout(p=0.5),
        nn.Linear(256, 1),
    )
    return model


def load_checkpoint(model: nn.Module, checkpoint_path: Path | str, device: torch.device) -> dict[str, Any]:
    try:
        ckpt = torch.load(checkpoint_path, map_location=device, weights_only=False)
    except TypeError:
        ckpt = torch.load(checkpoint_path, map_location=device)
    if isinstance(ckpt, dict) and "model_state_dict" in ckpt:
        model.load_state_dict(ckpt["model_state_dict"])
        meta = {k: v for k, v in ckpt.items() if k != "model_state_dict"}
    else:
        model.load_state_dict(ckpt)
        meta = {}
    model.eval()
    return meta


class AIImageDetector:
    """Load once, predict many times."""

    def __init__(self, checkpoint_path: str | Path, device: str | None = None):
        self.checkpoint_path = Path(checkpoint_path)
        if not self.checkpoint_path.exists():
            raise FileNotFoundError(
                f"Checkpoint not found: {self.checkpoint_path}. "
                "Copy best_ai_image_detector.pth into deployment/models/ "
                "or set MODEL_PATH."
            )

        if device is None:
            device = "cuda" if torch.cuda.is_available() else "cpu"
        self.device = torch.device(device)

        self.model = build_resnet50_binary(freeze_early_blocks=True, pretrained=False).to(self.device)
        self.meta = load_checkpoint(self.model, self.checkpoint_path, self.device)

    @torch.inference_mode()
    def predict(self, image: Image.Image, threshold: float = 0.6) -> dict[str, Any]:
        image = image.convert("RGB")
        tensor = EVAL_TRANSFORMS(image).unsqueeze(0).to(self.device)
        prob_ai = float(torch.sigmoid(self.model(tensor)).item())
        pred_id = int(prob_ai >= threshold)

        return {
            "prediction": LABEL_NAMES[pred_id],
            "label_id": pred_id,
            "prob_real": round(1.0 - prob_ai, 4),
            "prob_ai_generated": round(prob_ai, 4),
            "threshold": threshold,
        }
