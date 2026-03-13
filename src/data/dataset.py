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


# dataset的作用是来如何从文件夹中加载和预处理数据，然后让dataloader读取数据去训练模型
class FundusDataset(Dataset):

    def __init__(self, img_dir, excel_path, is_training=True):
        self.img_dir = img_dir
        self.transform = transform(is_training)
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

        # 获取所有图片
        self.image_files = os.listdir(img_dir)

        self.df = pd.read_excel(excel_path)
        self.label_map = self._create_label_map()




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

        # 数据增强
        if self.transform:
            image = self.transform(image)  # 应用transform来增强图像

        # 转换为tensor
        labels = torch.FloatTensor(labels)

        return image, labels, img_name
