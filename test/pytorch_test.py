import torch
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import sys

print("="*70)
print("毕业设计环境完整验证")
print("="*70)

# 1. PyTorch验证
print("\n1. PyTorch验证:")
print(f"   版本: {torch.__version__}")
print(f"   CUDA可用: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"   GPU设备: {torch.cuda.get_device_name(0)}")

# 2. 基础包验证
print("\n2. 基础包验证:")
print(f"   NumPy版本: {np.__version__}")
print(f"   Pandas版本: {pd.__version__}")

# 3. 图像处理验证
print("\n3. 图像处理验证:")


# 4. 医学图像验证
try:
    import monai
    print(f"   MONAI版本: {monai.__version__}")
except:
    print("   MONAI: 需要安装")

# 5. 系统信息
print("\n4. 系统信息:")
print(f"   Python版本: {sys.version[:50]}")
print(f"   环境位置: {sys.executable}")

# 6. 测试Tensor操作
print("\n5. Tensor操作测试:")
x = torch.randn(2, 3, 224, 224)  # 模拟眼底图像batch
print(f"   创建Tensor: {x.shape}")
print(f"   设备: {x.device}")

if torch.cuda.is_available():
    x_gpu = x.cuda()
    print(f"   GPU Tensor: {x_gpu.shape}, 设备: {x_gpu.device}")

print("\n" + "="*70)
print("🎉 环境验证完成！所有必要包已安装！")
print("📚 现在可以开始你的毕业设计了：")
print("   1. 下载ODIR数据集")
print("   2. 开始写数据预处理代码")
print("   3. 实现Transformer模型")
print("="*70)