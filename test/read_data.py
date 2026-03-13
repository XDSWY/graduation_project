from torch.utils.data import Dataset
import torch
from PIL import Image
import os


class MyDataSet(Dataset):
    def __init__(self, root_dir, label_dir):
        self.root_dir = root_dir  # 要的是根目录文件的路径
        self.label_dir = label_dir  # 只需给出根目录文件下的文件夹名
        self.path = os.path.join(self.root_dir, self.label_dir)
        self.img_path = os.listdir(self.path)  # 获取img的一个列表

    def __getitem__(self, idx):
        img_name = self.img_path[idx]
        image_item_path = os.path.join(self.path, img_name)
        img = Image.open(image_item_path)
        label = self.label_dir
        return img, label

    def __len__(self):
        return len(self.img_path)


root_dir = 'hymenoptera_data/hymenoptera_data/train'
ants_label_dir = 'ants'  # 相对路径
bees_label_dir = 'bees'  # 文件夹名
ants_dataset = MyDataSet(root_dir, ants_label_dir)
bees_dataset = MyDataSet(root_dir, bees_label_dir)

train_dataset = ants_dataset + bees_dataset # 拼接数据集


print(len(train_dataset))