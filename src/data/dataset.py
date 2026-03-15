import torch
import pandas as pd
import numpy as np
from torch.utils.data import Dataset
from torchvision import transforms
from PIL import Image
import os


# 数据增强
def transform(is_training=True):
    if is_training:  # 是否用训练集
        return transforms.Compose([
            # 意义是让模型记住特征而不是固定的位置，创造更多样的训练数据
            transforms.Resize((224, 224)),  # 强制缩放到224x224
            transforms.RandomHorizontalFlip(p=0.5),  # 50%概率随机翻转图片
            transforms.RandomRotation(10),  # 在10度内随机旋转图片
            transforms.ColorJitter(brightness=0.2, contrast=0.2),  # 改变亮度和对比度在1+正负0.2范围内随机
            transforms.ToTensor(),  # 改变维度和数值(像素值)范围到[0,1]
            transforms.Normalize(  # 将像素值标准化到均值为0，标准差为1的分布，公式：output = (input - mean) / std
                mean=[0.485, 0.456, 0.406],  # RGB三个通道的均值
                std=[0.229, 0.224, 0.225]  # RGB三个通道的标准差
            )  # 标准化后使数据更接近正态分布，让所有特征在同一尺度，避免梯度爆炸，让数值计算稳定
        ])
    else:  # 测试集和验证集
        return transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225]
            )
        ])

# 针对少数类的强数据增强
def strong_transform():
    return transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.RandomHorizontalFlip(p=0.5),
        transforms.RandomVerticalFlip(p=0.3),  # 增加垂直翻转
        transforms.RandomRotation(30),  # 增大旋转角度
        transforms.ColorJitter(brightness=0.3, contrast=0.3, saturation=0.3, hue=0.1),  # 更强的颜色抖动
        transforms.RandomAffine(degrees=0, translate=(0.1, 0.1), scale=(0.8, 1.2)),  # 仿射变换
        transforms.RandomResizedCrop(size=(224, 224), scale=(0.7, 1.0)),  # 随机裁剪
        transforms.GaussianBlur(kernel_size=3, sigma=(0.1, 1.0)),  # 高斯模糊
        transforms.ToTensor(),
        transforms.Normalize(
            mean=[0.485, 0.456, 0.406],
            std=[0.229, 0.224, 0.225]
        )
    ])


# dataset的作用是来如何从文件夹中加载和预处理数据，然后让dataloader读取数据去训练模型
class FundusDataset(Dataset):

    def __init__(self, img_dir, excel_path, is_training=True):
        self.img_dir = img_dir
        self.transform = transform(is_training)
        self.strong_transform = strong_transform() if is_training else None
        self.is_training = is_training
        self.diseases = ['N', 'D', 'G', 'C', 'A', 'H', 'M', 'O']
        self.disease_names = {
            'N': '正常',
            'D': '糖尿病视网膜病变',
            'G': '青光眼',
            'C': '白内障',
            'A': '年龄相关性黄斑变性',
            'H': '高血压视网膜病变',
            'M': '病理性近视',
            'O': '其他疾病'
        }
        # 少数类索引（根据你的统计：类别2-6样本少）
        self.minority_classes = [2, 3, 4, 5, 6]

        # 获取所有图片
        self.image_files = os.listdir(img_dir)

        self.df = pd.read_excel(excel_path)
        self.label_map = self._create_label_map()

        # 预计算每个图片的少数类标记，避免每次重复计算
        self.is_minority_cache = {}
        self._precompute_minority_flags()

    def _precompute_minority_flags(self):
        """预计算每个样本是否为少数类"""
        for img_name in self.image_files:
            if img_name in self.label_map:
                labels = self.label_map[img_name]
                is_minority = False
                for class_idx in self.minority_classes:
                    if class_idx < len(labels) and labels[class_idx] == 1:
                        is_minority = True
                        break
                self.is_minority_cache[img_name] = is_minority
            else:
                self.is_minority_cache[img_name] = False

    def __len__(self):
        return len(self.image_files)

    def _create_label_map(self):
        label_map = {}  # 创建一个标签字典

        for index, row in self.df.iterrows():  # iterrows()遍历Excel的每一行，给出索引和这一行的数据
            # 处理左眼
            if pd.notna(row['Left-Fundus']):  # row['Left-Fundus']意思为获取这一行的 Left-Fundus 列的值，即为左眼的图片名。notna检查是否为空
                labels = []  # 先建一个空列表
                for disease in self.diseases:  # 遍历8种疾病
                    value = row[disease]  # 获取这一行这种疾病的值
                    labels.append(value)  # 添加到列表中
                label_map[row['Left-Fundus']] = np.array(labels)  # labels 转换成 numpy 数组

            # 处理右眼
            if pd.notna(row['Right-Fundus']):
                labels = []  # 先建一个空列表
                for disease in self.diseases:  # 遍历8种疾病
                    value = row[disease]  # 获取这一行这种疾病的值
                    labels.append(value)  # 添加到列表中
                label_map[row['Right-Fundus']] = np.array(labels)

        return label_map

    def __getitem__(self, idx):
        img_name = self.image_files[idx]
        img_path = os.path.join(self.img_dir, img_name)
        image = Image.open(img_path).convert('RGB')  # 打开图片
        # 获取标签
        if img_name in self.label_map:
            labels = self.label_map[img_name]
        else:
            # 若图片无对应标签，则使用全零向量（表示无任何疾病）
            labels = np.zeros(len(self.diseases), dtype=np.float32)
            print(f"警告: {img_name} 在标签映射中未找到，使用全零标签。")

        # 数据增强 - 针对少数类应用更强的增强
        if self.is_training:
            is_minority = self.is_minority_cache.get(img_name, False)
            if is_minority and self.strong_transform is not None:
                # 少数类应用强增强
                image = self.strong_transform(image)
            else:
                # 多数类应用普通增强
                image = self.transform(image)
        else:
            # 验证/测试集用普通变换
            image = self.transform(image)

        # 转换为tensor
        labels = torch.FloatTensor(labels)

        return image, labels, img_name