import os
import yaml
import pandas as pd
import numpy as np
from PIL import Image


# 加载配置文件
def load_config(config_path=r'C:\Users\lenovo\Desktop\graduation_project\config\preprocessing.yaml'):
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)  # 只加载基本python对象
    return config


#加载配置
config = load_config()

input_dir = config['preprocessing']['input_dir']
output_dir = config['preprocessing']['output_dir']
target_size = tuple(config['preprocessing']['target_size'])
remove_black_border = config['preprocessing']['remove_black_border']
clahe_clip_limit = config['preprocessing']['clahe_clip_limit']
clahe_grid_size = tuple(config['preprocessing']['clahe_grid_size'])


# 1.去除黑边
def remove_black_borders(image, percentile=2, min_threshold=5):
    # 转换为灰度图
    gray = np.array(image.convert('L'))
    gray_mask = gray > 0  # 将灰度图像数组中大于0的改为true，小于0为false,创建布尔掩码
    non_black = gray[gray_mask]  # 提取为true的灰度值(提取非黑像素)

    if len(non_black) == 0:  # 整张图都是黑的
        return image

        # 取亮度最低的percentile%像素的上限值作为阈值(作用是阈值可以随不用亮度的图像调整)
    auto_threshold = np.percentile(non_black, percentile)

    # 确保阈值不低于最小值
    threshold = max(min_threshold, auto_threshold)

    mask = gray > threshold  # 创建一个布尔掩码，大于threshold的为true，否则反之
    # any()：如果有true，则会返回true，如果都为false，则返回false
    if not mask.any():  # 若 掩码矩阵全为false，则为全黑图像
        return image  # 没有找到内容

    rows = np.any(mask, axis=1)  # 按行检查，每行是否有true值
    cols = np.any(mask, axis=0)  # 按列检查，每行是否有true值

    # 找上下左右边界
    rmin, rmax = np.where(rows)[0][[0, -1]]  # 找rows中true值的索引，然后取第一个后最后一个元素(上下边界)
    cmin, cmax = np.where(cols)[0][[0, -1]]  # 找cols中true值的索引，然后取第一个后最后一个元素(左右边界)

    # 裁剪图片
    result = image.crop((cmin, rmin, cmax, rmax))  # crop(left,upper,right,lower)

    return result


# 2.调整尺寸
def resize(image, target_size=(512, 512)):

    target_width, target_height = target_size
        # 获取处理黑边之后的尺寸
    w, h = image.size

    # 计算两种比例
    width_ratio = target_width / w
    height_ratio = target_height / h

    # 取较小的比例
    scale = min(width_ratio, height_ratio)

    # 计算新尺寸
    new_w = int(w * scale)
    new_h = int(h * scale)

    # 缩放图片
    resized_img = image.resize((new_w, new_h), Image.Resampling.LANCZOS)

    # 创建黑色画布并粘贴
    final_img = Image.new('RGB', (target_width, target_height), 'black')
    paste_x = (target_width - new_w) // 2
    paste_y = (target_height - new_h) // 2
    final_img.paste(resized_img, (paste_x, paste_y))

    return final_img

# 批量处理所有图片
def batch_process(input_dir, output_dir):
    os.makedirs(output_dir, exist_ok=True)  # 若此目录位置不存在会自动创建

    # 获取所有图片
    all_files = os.listdir(input_dir)
    image_files = []
    for f in all_files:
        image_files.append(f)

    for filename in image_files:
        input_path = os.path.join(input_dir, filename)
        output_path = os.path.join(output_dir, filename)

        # 1. 打开图片
        img = Image.open(input_path)

        # 2. 去除黑边
        img = remove_black_borders(img)

        # 3. 调整尺寸
        img = resize(img, target_size=(512, 512))

        # 4. 保存
        img.save(output_path)
        img.close()



if __name__ == "__main__":
    # 处理训练集
    batch_process(
        input_dir="data/raw/ODIR-5K/Training Images",
        output_dir="data/processed/training"
    )

    # 处理测试集
    batch_process(
        input_dir="data/raw/ODIR-5K/Testing Images",
        output_dir="data/processed/testing"
    )
