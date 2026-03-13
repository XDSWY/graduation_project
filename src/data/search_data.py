# 在notebook中检查数据集
import os

# 1. 查看Training Images有多少张
train_count = len(os.listdir(r"C:\Users\lenovo\Desktop\graduation_project\data\raw\ODIR-5K\Training Images"))
print(f"Training Images: {train_count} 张")

# 2. 查看Testing Images有多少张
test_count = len(os.listdir(r"C:\Users\lenovo\Desktop\graduation_project\data\raw\ODIR-5K\Testing Images"))
print(f"Testing: {test_count} 张")

# 3. 计算划分比例
val_ratio = 0.2
new_train = int(train_count * (1 - val_ratio))
val = int(train_count * val_ratio)

print(f"\n建议划分:")
print(f"  新训练集: {new_train} 张 ({new_train/(new_train+val+test_count):.1%})")
print(f"  验证集: {val} 张 ({val/(new_train+val+test_count):.1%})")
print(f"  测试集: {test_count} 张 ({test_count/(new_train+val+test_count):.1%})")

print("--------------------------------------------------")
print("--------------------------------------------------")

# 1. 查看新Training Images有多少张
train_new_count = len(os.listdir(r"C:\Users\lenovo\Desktop\graduation_project\data\new\Training Images"))
print(f"Training Images: {train_new_count} 张")

# 2. 查看新Testing Images有多少张
test_new_count = len(os.listdir(r"C:\Users\lenovo\Desktop\graduation_project\data\new\Testing Images"))
print(f"Testing: {test_new_count} 张")

# 2. 查看新validation Images有多少张
valid_new_count = len(os.listdir(r"C:\Users\lenovo\Desktop\graduation_project\data\new\Validation Images"))
print(f"validation: {valid_new_count} 张")


print(f"\n建议划分:")
print(f"  新训练集: {train_new_count} 张 ({train_new_count/(train_new_count+valid_new_count+test_new_count):.1%})")
print(f"  验证集: {valid_new_count} 张 ({valid_new_count/(train_new_count+valid_new_count+test_new_count):.1%})")
print(f"  测试集: {test_new_count} 张 ({test_new_count/(train_new_count+valid_new_count+test_new_count):.1%})")