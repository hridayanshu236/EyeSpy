import torch
import torch.nn as nn

class ObjectDetectionCNN(nn.Module):
    def __init__(self, input_channels=3, num_predictions=2):
        super(ObjectDetectionCNN, self).__init__()
        def conv_block(in_channels, out_channels, num_convs, pool=True):
            layers = []
            for _ in range(num_convs):
                layers.append(nn.Conv2d(in_channels, out_channels, kernel_size=3, padding=1))
                layers.append(nn.ReLU(inplace=True))
                in_channels = out_channels
            if pool:
                layers.append(nn.MaxPool2d(kernel_size=2, stride=2))
            return nn.Sequential(*layers)
        self.features = nn.Sequential(
            conv_block(input_channels, 64, num_convs=2),
            conv_block(64, 128, num_convs=2),
            conv_block(128, 256, num_convs=4),
            conv_block(256, 512, num_convs=4),
            conv_block(512, 512, num_convs=4),
        )
        self.adapt_pool = nn.AdaptiveAvgPool2d((7, 7))
        self.classifier = nn.Sequential(
            nn.Flatten(),
            nn.Linear(512 * 7 * 7, 4096),
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