import os
import pandas as pd
import numpy as np
import shutil
from collections import Counter


def split_dataset(
        processed_train_dir,  # 处理后的图片目录（所有图片）
        data_excel_path,  # data.xlsx 文件路径
        output_base_dir,  # 输出基础目录
        train_ratio=0.7,  # 训练集比例
        val_ratio=0.15,  # 验证集比例
        test_ratio=0.15,  # 测试集比例
        random_seed=42  # 随机种子
):


    # 检查比例之和是否为1
    assert abs(train_ratio + val_ratio + test_ratio - 1.0) < 1e-10, "比例之和必须为1"

    # 1. 读取数据表格
    print("\n📁 读取数据表格...")
    df = pd.read_excel(data_excel_path)
    print(f"总患者数: {df['ID'].nunique()}")
    print(f"总记录数: {len(df)}")

    # 2. 获取疾病列
    disease_cols = ['N', 'D', 'G', 'C', 'A', 'H', 'M', 'O']
    disease_names = {
        'N': '正常',
        'D': '糖尿病视网膜病变',
        'G': '青光眼',
        'C': '白内障',
        'A': '黄斑变性',
        'H': '高血压视网膜病变',
        'M': '近视',
        'O': '其他'
    }

    # 3. 计算原始数据集的疾病分布

    total_patients = df['ID'].nunique()
    original_dist = {}

    for col in disease_cols:
        # 计算有多少患者患有该疾病（左眼或右眼）
        patients_with_disease = df[df[col] == 1]['ID'].nunique()
        percentage = (patients_with_disease / total_patients) * 100
        original_dist[col] = {
            'patients': patients_with_disease,
            'percentage': percentage
        }
        print(f"{disease_names[col]:<20} {patients_with_disease:<10} {percentage:>6.2f}%")

    # 4. 获取所有患者ID并打乱
    patient_ids = df['ID'].unique()
    np.random.seed(random_seed)
    shuffled_ids = np.random.permutation(patient_ids)

    # 5. 分层抽样函数
    def get_patient_disease_vector(patient_df):
        """获取患者的疾病向量（多标签）"""
        # 取该患者所有记录中疾病标签的最大值（只要有1就算1）
        return patient_df[disease_cols].max().values

    # 6. 分层抽样划分患者
    print("\n🔄 正在进行分层抽样划分...")

    train_patients = []
    val_patients = []
    test_patients = []

    # 按疾病类型分组患者
    disease_groups = {}
    for pid in shuffled_ids:
        patient_records = df[df['ID'] == pid]
        disease_vector = get_patient_disease_vector(patient_records)
        # 将疾病向量转换为字符串作为分组键
        group_key = ''.join([str(int(x)) for x in disease_vector])
        if group_key not in disease_groups:
            disease_groups[group_key] = []
        disease_groups[group_key].append(pid)

    # 从每个组中按比例抽取
    for group_key, pids in disease_groups.items():
        group_size = len(pids)
        n_train = int(round(group_size * train_ratio))
        n_val = int(round(group_size * val_ratio))

        # 确保总数为group_size
        if n_train + n_val > group_size:
            n_train = group_size - n_val

        train_patients.extend(pids[:n_train])
        val_patients.extend(pids[n_train:n_train + n_val])
        test_patients.extend(pids[n_train + n_val:])


    # 7. 创建输出目录
    new_train_dir = r'C:\Users\lenovo\Desktop\graduation_project\data\latest\Training Images'
    new_val_dir = r'C:\Users\lenovo\Desktop\graduation_project\data\latest\validation images'
    new_test_dir = r'C:\Users\lenovo\Desktop\graduation_project\data\latest\Testing Images'

    os.makedirs(new_train_dir, exist_ok=True)
    os.makedirs(new_val_dir, exist_ok=True)
    os.makedirs(new_test_dir, exist_ok=True)


    def copy_patient_images(patient_ids, target_dir, split_name):
        """复制指定患者的所有图片"""
        copied = 0
        image_list = []

        for pid in patient_ids:
            patient_records = df[df['ID'] == pid]
            for _, row in patient_records.iterrows():
                for eye in ['Left-Fundus', 'Right-Fundus']:
                    if pd.notna(row[eye]):
                        img_name = row[eye]
                        src = os.path.join(processed_train_dir, img_name)
                        dst = os.path.join(target_dir, img_name)
                        if os.path.exists(src):
                            shutil.copy2(src, dst)
                            copied += 1
                            image_list.append({
                                'patient_id': pid,
                                'image_name': img_name,
                                'split': split_name
                            })
                        else:
                            print(f"  警告: 图片不存在 {img_name}")

        return copied, image_list

    # 复制训练集
    train_copied, train_images = copy_patient_images(train_patients, new_train_dir, 'train')
    print(f"  训练集: {train_copied} 张图片")

    # 复制验证集
    val_copied, val_images = copy_patient_images(val_patients, new_val_dir, 'val')
    print(f"  验证集: {val_copied} 张图片")

    # 复制测试集
    test_copied, test_images = copy_patient_images(test_patients, new_test_dir, 'test')
    print(f"  测试集: {test_copied} 张图片")



    # 患者划分
    patient_split = []
    for pid in train_patients:
        patient_split.append({'patient_id': pid, 'split': 'train'})
    for pid in val_patients:
        patient_split.append({'patient_id': pid, 'split': 'val'})
    for pid in test_patients:
        patient_split.append({'patient_id': pid, 'split': 'test'})

    patient_df = pd.DataFrame(patient_split)
    patient_df.to_csv(os.path.join(output_base_dir, 'patient_split.csv'), index=False)

    # 图片划分
    all_images = train_images + val_images + test_images
    image_df = pd.DataFrame(all_images)
    image_df.to_csv(os.path.join(output_base_dir, 'image_split.csv'), index=False)


    return {
        'train_patients': len(train_patients),
        'val_patients': len(val_patients),
        'test_patients': len(test_patients),
        'train_images': train_copied,
        'val_images': val_copied,
        'test_images': test_copied,
        'distribution_report': os.path.join(output_base_dir, 'distribution_report.txt')
    }


# 主程序
if __name__ == "__main__":
    # 设置路径
    processed_train_dir = r"C:\Users\lenovo\Desktop\graduation_project\data\processed\Training Images"  # 处理后的所有图片目录
    data_excel_path = r"C:\Users\lenovo\Desktop\graduation_project\data\raw\ODIR-5K\data.xlsx"  # 数据表格
    output_base_dir = r"C:\Users\lenovo\Desktop\graduation_project\data\latest"  # 新的输出目录


    # 执行划分
    results = split_dataset(
        processed_train_dir=processed_train_dir,
        data_excel_path=data_excel_path,
        output_base_dir=output_base_dir,
        train_ratio=0.7,  # 训练集70%
        val_ratio=0.15,  # 验证集15%
        test_ratio=0.15,  # 测试集15%
        random_seed=42
    )

    print("\n📊 划分结果汇总:")
    print(f"训练集: {results['train_patients']} 患者, {results['train_images']} 图片")
    print(f"验证集: {results['val_patients']} 患者, {results['val_images']} 图片")
    print(f"测试集: {results['test_patients']} 患者, {results['test_images']} 图片")