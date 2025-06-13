import torch
import torch.nn as nn
import torchvision.models as models

class ObjectDetectionResNet(nn.Module):
    def __init__(self, num_predictions=2):
        super(ObjectDetectionResNet, self).__init__()
        self.backbone = models.resnet18(weights=models.ResNet18_Weights.DEFAULT)
        self.backbone.fc = nn.Identity()
        self.classifier = nn.Sequential(
            nn.Linear(512, 4096),
            nn.ReLU(inplace=True),
            nn.Linear(4096, num_predictions * 5)
        )
        self.num_predictions = num_predictions

    def forward(self, x):
        x = self.backbone(x)
        x = self.classifier(x)
        x = x.view(x.shape[0], self.num_predictions, 5)
        return x