
import torch
import numpy as np
import os
import time
from torch.utils.data import DataLoader
from transformers import ViTForImageClassification
from sklearn.metrics import precision_score, recall_score, f1_score, accuracy_score

from config import config, device
from dataset import FundusDataset


# ========== 数据路径 ==========
val_dir = r'C:\Users\lenovo\Desktop\graduation_project\data\new\Validation Images'
excel_dir = r'C:\Users\lenovo\Desktop\graduation_project\data\raw\ODIR-5K\data.xlsx'

# 测试集
val_dataset = FundusDataset(val_dir, excel_dir, is_training=False)

# 创建DataLoader
val_loader = DataLoader(
    val_dataset,
    batch_size=config['batch_size'],
    shuffle=False,
    num_workers=4,
    pin_memory=True
)

print(f"测试集样本数: {len(val_dataset)}")


# ========== 加载模型 ==========
def load_model(model_path):
    """加载训练好的ViT模型"""
    local_model_path = config['pretrained_path']  # 预训练权重路径

    model = ViTForImageClassification.from_pretrained(
        local_model_path,
        num_labels=config['num_classes'],
        ignore_mismatched_sizes=True
    )

    checkpoint = torch.load(model_path, map_location=device)
    model.load_state_dict(checkpoint['model_state_dict'])
    model = model.to(device)
    model.eval()

    print(f"模型加载成功！来自: {model_path}")
    if 'val_f1' in checkpoint:
        print(f"验证集F1: {checkpoint['val_f1']:.4f}")
    return model


# ========== 评估函数 ==========
def evaluate_model(model, test_loader):
    """
    在测试集上评估模型，计算各项指标
    """
    all_predicts = []
    all_labels = []
    all_probs = []
    inference_times = []

    total_start_time = time.time()

    with torch.no_grad():
        for images, labels, img_names in val_loader:
            images = images.to(device)
            labels_np = labels.numpy()

            # 记录单次推理时间
            start_time = time.time()
            outputs = model(images)
            inference_time = time.time() - start_time
            inference_times.append(inference_time)

            # 计算概率和预测
            probabilities = torch.sigmoid(outputs.logits).cpu().numpy()
            predictions = (probabilities > 0.5).astype(int)

            all_probs.append(probabilities)
            all_predicts.append(predictions)
            all_labels.append(labels_np)

    total_time = time.time() - total_start_time

    # 合并所有batch
    all_predicts = np.vstack(all_predicts)
    all_labels = np.vstack(all_labels)
    all_probs = np.vstack(all_probs)

    # ========== 计算各项指标 ==========

    # 1. 严格准确率（8个标签全对）
    strict_correct = (all_predicts == all_labels).all(axis=1).sum()
    strict_accuracy = strict_correct / len(all_labels)

    # 2. 每个标签的准确率
    per_label_accuracy = (all_predicts == all_labels).mean(axis=0)

    # 3. 宏平均精确率、召回率、F1
    macro_precision = precision_score(all_labels, all_predicts, average='macro', zero_division=0)
    macro_recall = recall_score(all_labels, all_predicts, average='macro', zero_division=0)
    macro_f1 = f1_score(all_labels, all_predicts, average='macro', zero_division=0)

    # 4. 微平均精确率、召回率、F1
    micro_precision = precision_score(all_labels, all_predicts, average='micro', zero_division=0)
    micro_recall = recall_score(all_labels, all_predicts, average='micro', zero_division=0)
    micro_f1 = f1_score(all_labels, all_predicts, average='micro', zero_division=0)

    # 5. 每个类别的精确率、召回率、F1
    per_class_precision = precision_score(all_labels, all_predicts, average=None, zero_division=0)
    per_class_recall = recall_score(all_labels, all_predicts, average=None, zero_division=0)
    per_class_f1 = f1_score(all_labels, all_predicts, average=None, zero_division=0)

    # 6. 推理时间统计
    mean_inference_time = np.mean(inference_times)
    std_inference_time = np.std(inference_times)
    total_inference_time = np.sum(inference_times)

    # ========== 打印结果 ==========
    print("\n" + "="*60)
    print("测试集评估结果")
    print("="*60)

    print(f"\n【总体指标】")
    print(f"  严格准确率 (8标签全对): {strict_accuracy:.4f}")
    print(f"  宏平均精确率 (Macro Precision): {macro_precision:.4f}")
    print(f"  宏平均召回率 (Macro Recall): {macro_recall:.4f}")
    print(f"  宏平均F1分数 (Macro F1): {macro_f1:.4f}")
    print(f"  微平均精确率 (Micro Precision): {micro_precision:.4f}")
    print(f"  微平均召回率 (Micro Recall): {micro_recall:.4f}")
    print(f"  微平均F1分数 (Micro F1): {micro_f1:.4f}")

    print(f"\n【每个类别的指标】")
    print(f"{'类别':<20} {'精确率':<10} {'召回率':<10} {'F1分数':<10}")
    print("-" * 55)
    for i, disease in enumerate(config['class_names']):
        print(f"{disease:<20} {per_class_precision[i]:<10.4f} {per_class_recall[i]:<10.4f} {per_class_f1[i]:<10.4f}")

    print(f"\n【每个标签的准确率】")
    for i, disease in enumerate(config['class_names']):
        print(f"  {disease}: {per_label_accuracy[i]:.4f}")

    print(f"\n【推理时间统计】")
    print(f"  平均推理时间 (每batch): {mean_inference_time*1000:.2f} ms")
    print(f"  推理时间标准差: {std_inference_time*1000:.2f} ms")
    print(f"  总推理时间: {total_inference_time:.2f} s")
    print(f"  总评估时间: {total_time:.2f} s")
    print(f"  Batch大小: {config['batch_size']}")

    # 返回所有指标
    results = {
        'strict_accuracy': strict_accuracy,
        'macro_precision': macro_precision,
        'macro_recall': macro_recall,
        'macro_f1': macro_f1,
        'micro_precision': micro_precision,
        'micro_recall': micro_recall,
        'micro_f1': micro_f1,
        'per_class_precision': per_class_precision,
        'per_class_recall': per_class_recall,
        'per_class_f1': per_class_f1,
        'per_label_accuracy': per_label_accuracy,
        'mean_inference_time': mean_inference_time,
        'total_evaluation_time': total_time
    }

    return results


# ========== 主函数 ==========
if __name__ == '__main__':
    model_path = r'C:\Users\lenovo\Desktop\graduation_project\checkpoints\best_model_by_val_f1.pth'

    if not os.path.exists(model_path):
        candidates = [
            os.path.join(config['save_dir'], 'best_model.pth'),
            os.path.join(config['save_dir'], 'latest_model.pth')
        ]

    # 加载模型
    model = load_model(model_path)

    # 评估
    results = evaluate_model(model, val_loader)

    # 保存结果到文本文件
    result_file = os.path.join(config['save_dir'], 'test_evaluation_results.txt')
    with open(result_file, 'w', encoding='utf-8') as f:
        f.write("测试集评估结果\n")
        f.write("="*40 + "\n")
        f.write(f"模型: {model_path}\n\n")
        f.write(f"严格准确率: {results['strict_accuracy']:.4f}\n")
        f.write(f"宏平均F1: {results['macro_f1']:.4f}\n")
        f.write(f"微平均F1: {results['micro_f1']:.4f}\n")
        f.write(f"平均推理时间 (每batch): {results['mean_inference_time']*1000:.2f} ms\n")
        f.write("\n各类别F1:\n")
        for i, name in enumerate(config['class_names']):
            f.write(f"  {name}: {results['per_class_f1'][i]:.4f}\n")

    print(f"\n评估结果已保存至: {result_file}")