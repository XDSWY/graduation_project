import torch
import numpy as np
from torch.utils.data import WeightedRandomSampler
import torch.nn as nn
import torch.nn.functional as F


def calculate_multilabel_weights(labels, beta=0.999, clip_min=0.5, clip_max=5.0):

    if isinstance(labels, torch.Tensor):
        labels = labels.cpu().numpy()

    n_samples, n_classes = labels.shape

    # 计算每个类别的正样本数
    pos_counts = np.sum(labels, axis=0)

    # 计算每个类别的负样本数
    neg_counts = n_samples - pos_counts

    print("\n📊 多标签类别统计:")
    for i in range(n_classes):
        print(
            f"  类别 {i}: 正样本={int(pos_counts[i])}, 负样本={int(neg_counts[i])}, 正比例={pos_counts[i] / n_samples:.3f}")

    # 方法1: 基于正样本比例的权重（适用于多标签）
    # 使用有效样本数量 (Effective Number of Samples)
    effective_num = 1.0 - np.power(beta, pos_counts)
    weights = (1.0 - beta) / effective_num
    weights = weights / np.sum(weights) * n_classes  # 归一化

    # 方法2: 也可以使用逆频率
    # weights = n_samples / (pos_counts * n_classes)

    # 限制权重范围，避免极端值
    weights = np.clip(weights, clip_min, clip_max)

    print("\n📊 类别权重:")
    for i, w in enumerate(weights):
        print(f"  类别 {i}: {w:.3f}")

    return torch.tensor(weights, dtype=torch.float32)


def create_multilabel_balanced_sampler(labels, num_classes, replacement=True):

    if isinstance(labels, torch.Tensor):
        labels = labels.cpu().numpy()

    n_samples = len(labels)

    # 计算每个样本的权重 - 基于该样本中出现的正类
    # 对于多标签，样本权重 = 所有正类权重的平均值
    sample_weights = np.zeros(n_samples)

    for i in range(n_samples):
        # 获取该样本的正类
        positive_classes = np.where(labels[i] == 1)[0]

        if len(positive_classes) > 0:
            # 计算正类的平均权重
            pos_counts = np.sum(labels, axis=0)
            class_weights = n_samples / (pos_counts * num_classes)
            sample_weights[i] = np.mean(class_weights[positive_classes])
        else:
            # 全负样本的情况（很少见）
            sample_weights[i] = 1.0

    # 归一化权重
    sample_weights = sample_weights / np.sum(sample_weights) * n_samples

    # 创建采样器
    sampler = WeightedRandomSampler(
        weights=torch.tensor(sample_weights, dtype=torch.double),
        num_samples=n_samples,
        replacement=replacement
    )

    return sampler


class WeightedBCEWithLogitsLoss(nn.Module):

    def __init__(self, class_weights=None, pos_weight=None, reduction='mean'):
        super().__init__()
        self.class_weights = class_weights
        self.pos_weight = pos_weight
        self.reduction = reduction

    def forward(self, inputs, targets):
        """
        inputs: 模型输出 (未经过sigmoid)
        targets: 真实标签 (0或1)
        """
        # 计算每个元素的BCE损失
        loss = F.binary_cross_entropy_with_logits(
            inputs, targets,
            reduction='none',
            pos_weight=self.pos_weight
        )

        # 应用类别权重
        if self.class_weights is not None:
            # class_weights形状: (n_classes,)
            # 扩展维度以便广播
            class_weights = self.class_weights.view(1, -1).expand_as(loss)
            loss = loss * class_weights

        # 聚合
        if self.reduction == 'mean':
            return loss.mean()
        elif self.reduction == 'sum':
            return loss.sum()
        else:
            return loss


class FocalLoss(nn.Module):

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
        # 计算BCE损失
        bce_loss = F.binary_cross_entropy_with_logits(
            inputs, targets, reduction='none'
        )

        # 计算pt (预测的概率)
        pt = torch.exp(-bce_loss)

        # 应用focal loss调制
        focal_loss = (1 - pt) ** self.gamma * bce_loss

        # 应用类别权重
        if self.alpha is not None:
            alpha = self.alpha.view(1, -1).expand_as(focal_loss)
            focal_loss = focal_loss * alpha

        if self.reduction == 'mean':
            return focal_loss.mean()
        elif self.reduction == 'sum':
            return focal_loss.sum()
        else:
            return focal_loss