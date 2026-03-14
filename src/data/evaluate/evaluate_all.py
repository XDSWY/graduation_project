# evaluate_all.py
from torch import device
import torch

from src.data.evaluate.evaluate import evaluate_model, val_loader

models_to_evaluate = {
    'vit': 'checkpoints/best_vit.pth',
    'resnet50': 'checkpoints/best_resnet50.pth',
    'swin': 'checkpoints/best_swin.pth',
    'maxvit': 'checkpoints/best_maxvit.pth'
}

results = {}
for name, path in models_to_evaluate.items():
    print(f"\n{'=' * 50}")
    print(f"评估 {name}")
    print(f"{'=' * 50}")

    # 根据模型名选择对应的创建函数
    if name == 'vit':
        from transformers import ViTForImageClassification

        model = ViTForImageClassification.from_pretrained(...)
    elif name == 'swin':
        from transformers import SwinForImageClassification

        model = SwinForImageClassification.from_pretrained(...)
    elif name == 'maxvit':
        import timm

        model = timm.create_model('maxvit_tiny_tf_224', pretrained=False)

    # 加载权重
    checkpoint = torch.load(path)
    model.load_state_dict(checkpoint['model_state_dict'])
    model = model.to(device)
    model.eval()

    # 评估（用你之前写的evaluate函数）
    results[name] = evaluate_model(model, val_loader)

# 打印对比表格
print("\n📊 模型对比结果")
print("-" * 60)
print(f"{'模型':<10} {'准确率':<10} {'精确率':<10} {'召回率':<10} {'推理时间(ms)':<15}")
print("-" * 60)
for name, res in results.items():
    print(
        f"{name:<10} {res['accuracy']:<10.4f} {res['precision']:<10.4f} {res['recall']:<10.4f} {res['mean_inference_time'] * 1000:<15.2f}")