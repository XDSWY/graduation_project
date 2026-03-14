"""
类别分布分析脚本
使用方法：python analyze_class_distribution.py
"""

import numpy as np
import os
import pickle
import argparse
from collections import Counter


def check_class_distribution(y_train, y_val, class_names=None):
    """
    分析训练集和验证集的类别分布

    Args:
        y_train: 训练集标签 (one-hot编码或整数编码)
        y_val: 验证集标签 (one-hot编码或整数编码)
        class_names: 类别名称列表，可选
    """
    # 判断标签格式
    if len(y_train.shape) > 1 and y_train.shape[1] > 1:
        # one-hot 编码
        train_dist = np.mean(y_train, axis=0)
        val_dist = np.mean(y_val, axis=0)

        # 计算每个类别的样本数
        train_counts = np.sum(y_train, axis=0)
        val_counts = np.sum(y_val, axis=0)

        n_classes = y_train.shape[1]
    else:
        # 整数编码
        n_classes = len(np.unique(np.concatenate([y_train, y_val])))
        train_dist = np.array([np.mean(y_train == i) for i in range(n_classes)])
        val_dist = np.array([np.mean(y_val == i) for i in range(n_classes)])

        train_counts = np.array([np.sum(y_train == i) for i in range(n_classes)])
        val_counts = np.array([np.sum(y_val == i) for i in range(n_classes)])

    # 如果没有提供类别名称，创建默认名称
    if class_names is None:
        class_names = [f"类别{i}" for i in range(n_classes)]

    print("=" * 60)
    print("类别分布分析报告")
    print("=" * 60)

    print("\n📊 各类别在训练集中的比例:")
    print("-" * 40)
    for i, name in enumerate(class_names):
        print(f"  {name}: {train_dist[i]:.3f} ({int(train_counts[i])} 样本)")

    print("\n📊 各类别在验证集中的比例:")
    print("-" * 40)
    for i, name in enumerate(class_names):
        print(f"  {name}: {val_dist[i]:.3f} ({int(val_counts[i])} 样本)")

    # 计算分布差异
    diff = np.abs(train_dist - val_dist)
    print("\n📈 分布差异 (训练集比例 - 验证集比例):")
    print("-" * 40)
    for i, name in enumerate(class_names):
        print(f"  {name}: {diff[i]:.3f}")

    # 统计信息
    print("\n📉 统计摘要:")
    print("-" * 40)
    print(f"  训练集总样本数: {int(np.sum(train_counts))}")
    print(f"  验证集总样本数: {int(np.sum(val_counts))}")
    print(f"  类别数量: {n_classes}")
    print(f"  平均分布差异: {np.mean(diff):.3f}")
    print(f"  最大分布差异: {np.max(diff):.3f} (类别: {class_names[np.argmax(diff)]})")

    # 检查不平衡情况
    imbalance_ratio = np.max(train_counts) / np.min(train_counts)
    print(f"\n⚠️  不平衡比率 (最多/最少): {imbalance_ratio:.2f}")
    if imbalance_ratio > 2:
        print("  警告: 数据集存在明显不平衡！")
    elif imbalance_ratio > 5:
        print("  严重警告: 数据集高度不平衡！")

    return {
        'train_dist': train_dist,
        'val_dist': val_dist,
        'diff': diff,
        'train_counts': train_counts,
        'val_counts': val_counts,
        'imbalance_ratio': imbalance_ratio
    }


def load_labels_from_file(train_file, val_file, format='numpy'):
    """
    从文件加载标签数据
    """
    if format == 'numpy':
        y_train = np.load(train_file)
        y_val = np.load(val_file)
    elif format == 'pickle':
        with open(train_file, 'rb') as f:
            y_train = pickle.load(f)
        with open(val_file, 'rb') as f:
            y_val = pickle.load(f)
    else:
        raise ValueError(f"不支持的文件格式: {format}")

    return y_train, y_val


def generate_sample_data(n_samples=1000, n_classes=5, save=False):
    """
    生成示例数据用于测试
    """
    np.random.seed(42)

    # 生成不平衡的训练集
    train_probs = np.array([0.4, 0.25, 0.15, 0.12, 0.08])  # 不平衡分布
    y_train = np.random.choice(n_classes, size=n_samples, p=train_probs)

    # 生成验证集（稍微不同的分布）
    val_probs = np.array([0.35, 0.25, 0.18, 0.12, 0.10])
    y_val = np.random.choice(n_classes, size=n_samples // 5, p=val_probs)

    # 转换为 one-hot 编码（可选）
    y_train_onehot = np.eye(n_classes)[y_train]
    y_val_onehot = np.eye(n_classes)[y_val]

    if save:
        np.save('y_train_sample.npy', y_train_onehot)
        np.save('y_val_sample.npy', y_val_onehot)
        print("示例数据已保存为 y_train_sample.npy 和 y_val_sample.npy")

    return y_train_onehot, y_val_onehot, ['A', 'B', 'C', 'D', 'E']


def main():
    parser = argparse.ArgumentParser(description='分析训练集和验证集的类别分布')
    parser.add_argument('--train_file', type=str, help='训练集标签文件 (.npy)')
    parser.add_argument('--val_file', type=str, help='验证集标签文件 (.npy)')
    parser.add_argument('--class_names', type=str, nargs='+', help='类别名称列表')
    parser.add_argument('--generate_sample', action='store_true', help='生成示例数据并运行')

    args = parser.parse_args()

    if args.generate_sample:
        print("生成示例数据...")
        y_train, y_val, class_names = generate_sample_data(n_samples=2000, save=True)
        check_class_distribution(y_train, y_val, class_names)

    elif args.train_file and args.val_file:
        print(f"加载训练标签: {args.train_file}")
        print(f"加载验证标签: {args.val_file}")

        # 加载数据
        y_train = np.load(args.train_file)
        y_val = np.load(args.val_file)

        # 获取类别名称
        class_names = args.class_names if args.class_names else None

        # 分析分布
        results = check_class_distribution(y_train, y_val, class_names)

        # 可选：保存结果到文件
        output_file = 'class_distribution_results.txt'
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("类别分布分析结果\n")
            f.write("=" * 50 + "\n")
            f.write(f"训练集分布: {results['train_dist']}\n")
            f.write(f"验证集分布: {results['val_dist']}\n")
            f.write(f"分布差异: {results['diff']}\n")

        print(f"\n结果已保存到 {output_file}")

    else:
        print("请指定标签文件或使用 --generate_sample 生成示例数据")
        print("\n使用示例:")
        print("  python analyze_class_distribution.py --generate_sample")
        print(
            "  python analyze_class_distribution.py --train_file y_train.npy --val_file y_val.npy --class_names 正常 DR 青光眼")


if __name__ == "__main__":
    main()