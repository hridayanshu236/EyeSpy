import torch
import torch.nn as nn
import torchvision.models as models

class ObjectDetectionMobileNetV2(nn.Module):
    def __init__(self, num_predictions=2):
        super(ObjectDetectionMobileNetV2, self).__init__()
        backbone = models.mobilenet_v2(weights=models.MobileNet_V2_Weights.DEFAULT)
        self.features = backbone.features  # Output: [batch, 1280, 10, 10] for 320x320 input
        self.adapt_pool = nn.AdaptiveAvgPool2d((7, 7))
        self.classifier = nn.Sequential(
            nn.Flatten(),
            nn.Linear(1280 * 7 * 7, 4096),
            nn.ReLU(inplace=True),
            nn.Linear(4096, 4096),
            nn.ReLU(inplace=True),
            nn.Linear(4096, num_predictions * 5)
        )
        self.num_predictions = num_predictions

    def forward(self, x):
        x = self.features(x)
        x = self.adapt_pool(x)
        x = self.classifier(x)
        x = x.view(x.shape[0], self.num_predictions, 5)
        return x