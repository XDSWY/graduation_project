import torch
import torch.nn as nn
import pandas as pd
import numpy as np
import os
import time
from PIL import Image
from torchvision import transforms
from tqdm import tqdm
from torch.utils.data import DataLoader
from torch.utils.tensorboard import SummaryWriter
from transformers import ViTForImageClassification, ViTImageProcessor
from sklearn.metrics import precision_score, recall_score, f1_score
from torch.multiprocessing import freeze_support

from src.data.config import config, device
from src.data.dataset import FundusDataset
from src.data.class_balance import calculate_multilabel_weights, create_multilabel_balanced_sampler, WeightedBCEWithLogitsLoss


if __name__ == '__main__':
    freeze_support()

    # 数据路径
    train_dir = r'C:\Users\lenovo\Desktop\graduation_project\data\latest\Training Images'
    test_dir = r'C:\Users\lenovo\Desktop\graduation_project\data\latest\Testing Images'
    val_dir = r'C:\Users\lenovo\Desktop\graduation_project\data\latest\validation images'
    excel_dir = r'C:\Users\lenovo\Desktop\graduation_project\data\raw\ODIR-5K\data.xlsx'

    # 训练集
    train_dataset = FundusDataset(train_dir, excel_dir, is_training=True)

    # 验证集
    val_dataset = FundusDataset(val_dir, excel_dir, is_training=False)

    # 测试集
    test_dataset = FundusDataset(test_dir, excel_dir, is_training=False)

    print("收集训练集标签用于类别平衡计算...")
    all_train_labels = []
    for i in range(len(train_dataset)):
        _, labels, _ = train_dataset[i]
        all_train_labels.append(labels.numpy())
    all_train_labels = np.stack(all_train_labels)

    # 计算类别权重
    class_weights = calculate_multilabel_weights(
        all_train_labels,
        beta=0.999,
        clip_min=0.5,
        clip_max=5.0
    )
    class_weights = class_weights.to(device)

    # 创建平衡采样器
    balanced_sampler = create_multilabel_balanced_sampler(
        all_train_labels,
        num_classes=config['num_classes']
    )

    print(f"类别权重已计算: {class_weights.cpu().numpy()}")
    # ====================================================

    # 创建DataLoader - 使用平衡采样器替换 shuffle=True
    train_loader = DataLoader(
        train_dataset,
        batch_size=config['batch_size'],
        sampler=balanced_sampler,  # 使用采样器替代 shuffle
        num_workers=4,
        pin_memory=True,
        drop_last=True
    )

    val_loader = DataLoader(
        val_dataset,
        batch_size=config['batch_size'],
        shuffle=False,
        num_workers=4,
        pin_memory=True
    )

    test_loader = DataLoader(
        test_dataset,
        batch_size=config['batch_size'],
        shuffle=False,
        num_workers=4,
        pin_memory=True
    )

    # 用已经预训练过的模型可以增加准确率
    local_model_path = config['pretrained_path']

    # 加载预训练的处理器
    processor = ViTImageProcessor.from_pretrained(local_model_path)

    # 加载预训练的ViT模型
    model = ViTForImageClassification.from_pretrained(
        local_model_path,
        num_labels=config['num_classes'],  # 指定分类数
        ignore_mismatched_sizes=True  # 允许模型权重尺寸不匹配时自动调整
    )
    model = model.to(device)

    # 回归任务(预测连续值)：MSELoss,L1Loss,SmoothL1Loss
    # 分类任务：1.多类分类(每个样本只属一类)：CrossEntropyLoss   2.多标签分类(每个样本可属多类)：BCEWithLogitsLoss

    # 数值更稳定，每个类别可独立判断
    pos_rates = [0.06, 0.08, 0.02, 0.04, 0.04, 0.10, 0.06, 0.72]
    pos_weight = torch.tensor([1.0 / (r + 0.01) for r in pos_rates]).to(device)
    # 使用计算出的类别权重
    criterion = WeightedBCEWithLogitsLoss(
        class_weights=class_weights,  # 使用计算出的类别权重
        # pos_weight=pos_weight,      # 可以选择是否使用pos_weight
        reduction='mean'
    )

    # 优化器
    optimizer = torch.optim.AdamW(  # AdamW收敛快，准确率高，泛化性好
        model.parameters(),
        lr=config['learning_rate'],
        weight_decay=config['weight_decay']
    )

    # 训练阶段
    best_val = 0
    global_step = 0
    best_accuracy = 0
    best_val_f1 = 0  # 记录最好的验证集F1

    writer = SummaryWriter('../logs')
    train_start_time = time.time()

    for epoch in range(config['epochs']):
        model.train()
        train_loss = 0
        train_correct = 0  # 累计正确标签数
        train_total = 0  # 累计总标签数
        train_strict_correct = 0  # 累计严格正确样本数
        train_strict_total = 0  # 累计总样本数

        train_process = tqdm(train_loader, desc='Training')  # 显示训练进度条

        for image, labels, img_name in train_process:
            image = image.to(device)
            labels = labels.to(device)

            optimizer.zero_grad()  # 更新梯度
            outputs = model(image)
            loss = criterion(outputs.logits, labels)

            probability = torch.sigmoid(outputs.logits)
            predict = (probability > 0.5).float()

            # 1. 严格准确率（8个标签全对）- 用于保存最佳模型
            strict_correct = (predict == labels).all(dim=1).sum().item()
            strict_total = labels.size(0)
            strict_acc = strict_correct / strict_total

            # 2. 宽松准确率（每个标签独立计算）- 用于显示训练进度
            total_correct = (predict == labels).sum().item()
            total_elements = labels.numel()  # batch_size * 8
            batch_acc = total_correct / total_elements

            loss.backward()
            optimizer.step()  # 根据前面的梯度值动态更新

            # 累计损失
            train_loss += loss.item()

            # 累计两种准确率的计数
            train_strict_correct += strict_correct
            train_strict_total += strict_total
            train_correct += total_correct
            train_total += total_elements

            # 在进度条中显示宽松准确率
            train_process.set_postfix({
                'loss': f'{loss.item():.4f}',
                'acc': f'{batch_acc:.3f}',
                'strict': f'{strict_acc:.3f}'
            })

            writer.add_scalar('Batch/Train_Loss', loss.item(), global_step)
            writer.add_scalar('Batch/Train_Strict_Accuracy', strict_acc, global_step)
            writer.add_scalar('Batch/Train_Label_Accuracy', batch_acc, global_step)
            global_step += 1

        # ========== 计算epoch平均值 ==========
        # 严格准确率（用于保存最佳模型）
        train_strict_accuracy = train_strict_correct / train_strict_total
        # 宽松准确率（每个标签的准确率）
        train_label_accuracy = train_correct / train_total
        # 平均损失
        avg_train_loss = train_loss / len(train_loader)

        # 记录到TensorBoard
        writer.add_scalar('Loss/Train', avg_train_loss, epoch)  # 损失曲线
        writer.add_scalar('Accuracy/Train_Strict', train_strict_accuracy, epoch)
        writer.add_scalar('Accuracy/Train_Label', train_label_accuracy, epoch)
        current_lr = optimizer.param_groups[0]['lr']
        writer.add_scalar('Hyperparameters/Learning_Rate', current_lr, epoch)  # 学习率曲线

        print(f"\nEpoch {epoch + 1}:")
        print(f"  损失: {avg_train_loss:.4f}")
        print(f"  标签准确率: {train_label_accuracy:.3f} (每个标签)")
        print(f"  严格准确率: {train_strict_accuracy:.3f} (8标签全对)")

        # ========== 验证集F1计算 ==========
        model.eval()
        all_val_probs = []
        all_val_labels = []

        with torch.no_grad():
            for val_images, val_labels, _ in val_loader:
                val_images = val_images.to(device)
                val_outputs = model(val_images)
                val_probs = torch.sigmoid(val_outputs.logits).cpu().numpy()

                all_val_probs.append(val_probs)
                all_val_labels.append(val_labels.numpy())

        all_val_probs = np.vstack(all_val_probs)
        all_val_labels = np.vstack(all_val_labels)

        # 计算验证集F1
        val_preds = (all_val_probs > 0.5).astype(int)
        val_f1 = f1_score(all_val_labels, val_preds, average='macro', zero_division=0)

        print(f"  验证集Macro F1: {val_f1:.4f}")

        # 用验证集F1保存模型
        if val_f1 > best_val_f1:
            best_val_f1 = val_f1
            torch.save({
                'epoch': epoch,
                'model_state_dict': model.state_dict(),
                'optimizer_state_dict': optimizer.state_dict(),
                'loss': avg_train_loss,
                'strict_accuracy': train_strict_accuracy,
                'label_accuracy': train_label_accuracy,
                'val_f1': val_f1,
                'config': config
            }, os.path.join(config['save_dir'], 'best_model_by_val_f1.pth'))
            print(f"  保存验证集最佳模型！F1={val_f1:.4f}")

        # 原有的保存逻辑（用严格准确率）
        torch.save({
            'epoch': epoch,
            'model_state_dict': model.state_dict(),
            'optimizer_state_dict': optimizer.state_dict(),
            'loss': avg_train_loss,
            'accuracy': train_strict_accuracy,
            'config': config
        }, os.path.join(config['save_dir'], 'latest_model.pth'))

        if train_strict_accuracy > best_accuracy:
            best_accuracy = train_strict_accuracy
            torch.save({
                'epoch': epoch,
                'model_state_dict': model.state_dict(),
                'optimizer_state_dict': optimizer.state_dict(),
                'loss': avg_train_loss,
                'accuracy': train_strict_accuracy,
                'config': config
            }, os.path.join(config['save_dir'], 'best_model.pth'))

    train_time = time.time() - train_start_time
    print(f"\n训练完成！总训练时间: {train_time / 60:.2f} 分钟")
    print(f"最佳验证集F1: {best_val_f1:.4f}")
    writer.close()
