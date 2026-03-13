import os
import pandas as pd
import numpy as np
import shutil


def split_training_set(
        processed_train_dir,  # 处理后的训练集图片目录
        data_excel_path,  # data.xlsx 文件路径
        output_base_dir,  # 输出基础目录
        val_size=1400,  # 验证集图片数
        random_seed=42  # 随机种子
):

    print("=" * 70)
    print("数据集划分（从训练集中分出验证集）")
    print("=" * 70)

    # 1. 读取数据表格
    print("\n📁 读取数据表格...")
    df = pd.read_excel(data_excel_path)

    # 获取所有患者ID
    patient_ids = df['ID'].unique()

    # 计算需要多少患者才能得到1400张图片
    # 每个患者平均有2张图片，所以大约需要700个患者
    val_patients_needed = val_size // 2

    # 随机打乱患者ID
    np.random.seed(random_seed)
    shuffled_ids = np.random.permutation(patient_ids)

    # 划分患者
    val_patient_ids = shuffled_ids[:val_patients_needed]
    train_patient_ids = shuffled_ids[val_patients_needed:]


    # 7. 创建输出目录
    new_train_dir = r"/data/new/Training Images"
    new_val_dir = r"/data/new/validation images"

    # 复制训练集图片
    train_copied = 0
    for patient_id in train_patient_ids:
        patient_records = df[df['ID'] == patient_id]
        for _, row in patient_records.iterrows():
            for eye in ['Left-Fundus', 'Right-Fundus']:
                if pd.notna(row[eye]):
                    img_name = row[eye]
                    src = os.path.join(processed_train_dir, img_name)
                    dst = os.path.join(new_train_dir, img_name)
                    if os.path.exists(src):
                        shutil.copy2(src, dst)
                        train_copied += 1

    # 复制验证集图片
    val_copied = 0
    for patient_id in val_patient_ids:
        patient_records = df[df['ID'] == patient_id]
        for _, row in patient_records.iterrows():
            for eye in ['Left-Fundus', 'Right-Fundus']:
                if pd.notna(row[eye]):
                    img_name = row[eye]
                    src = os.path.join(processed_train_dir, img_name)
                    dst = os.path.join(new_val_dir, img_name)
                    if os.path.exists(src):
                        shutil.copy2(src, dst)
                        val_copied += 1

    # 保存患者划分
    patient_split = []
    for pid in train_patient_ids:
        patient_split.append({'patient_id': pid, 'split': 'train'})
    for pid in val_patient_ids:
        patient_split.append({'patient_id': pid, 'split': 'val'})

    patient_df = pd.DataFrame(patient_split)
    patient_df.to_csv(os.path.join(output_base_dir, 'patient_split.csv'), index=False)

    # 保存图片划分
    image_split = []
    for pid in train_patient_ids:
        patient_records = df[df['ID'] == pid]
        for _, row in patient_records.iterrows():
            for eye in ['Left-Fundus', 'Right-Fundus']:
                if pd.notna(row[eye]):
                    image_split.append({
                        'patient_id': pid,
                        'image_name': row[eye],
                        'split': 'train'
                    })

    for pid in val_patient_ids:
        patient_records = df[df['ID'] == pid]
        for _, row in patient_records.iterrows():
            for eye in ['Left-Fundus', 'Right-Fundus']:
                if pd.notna(row[eye]):
                    image_split.append({
                        'patient_id': pid,
                        'image_name': row[eye],
                        'split': 'val'
                    })

    image_df = pd.DataFrame(image_split)
    image_df.to_csv(os.path.join(output_base_dir, 'image_split.csv'), index=False)

    return train_df, val_df


# 主程序
if __name__ == "__main__":
    # 设置路径
    processed_train_dir = r"/data/processed/Training Images"  # 处理后的训练集图片
    data_excel_path = r"/data/raw/ODIR-5K/data.xlsx"  # 数据表格
    output_base_dir = r"/data/new"  # 新的输出目录

    train_df, val_df = split_training_set(
        processed_train_dir=processed_train_dir,
        data_excel_path=data_excel_path,
        output_base_dir=output_base_dir,
        val_size=1400  # 验证集1400张图片
    )
