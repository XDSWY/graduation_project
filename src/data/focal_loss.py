import torch
import torch.nn as nn
import torch.nn.functional as F


class FocalLoss(nn.Module):
    """
    Focal Loss for multi-label classification
    """

    def __init__(self, alpha=None, gamma=2.0, reduction='mean'):
        super().__init__()
        self.alpha = alpha  # 类别权重
        self.gamma = gamma  # 聚焦参数
        self.reduction = reduction

    def forward(self, inputs, targets):
        """
        inputs: 模型输出 (未经过sigmoid)
        targets: 真实标签 (0或1)
        """
        # 计算BCE loss
        bce_loss = F.binary_cross_entropy_with_logits(inputs, targets, reduction='none')

        # 计算pt (预测的概率)
        pt = torch.exp(-bce_loss)

        # 应用focal loss调制
        focal_loss = (1 - pt) ** self.gamma * bce_loss

        # 应用类别权重
        if self.alpha is not None:
            # 确保alpha形状正确
            if self.alpha.dim() == 1:
                alpha = self.alpha.view(1, -1).expand_as(focal_loss)
            else:
                alpha = self.alpha
            focal_loss = focal_loss * alpha

        if self.reduction == 'mean':
            return focal_loss.mean()
        elif self.reduction == 'sum':
            return focal_loss.sum()
        else:
            return focal_loss