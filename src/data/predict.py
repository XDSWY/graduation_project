import torch
from PIL import Image
from torchvision import transforms
from transformers import ViTForImageClassification
import os
import matplotlib.pyplot as plt
from IPython.display import display

from config import config, device


# 预处理图片增加batch维度
def preprocess_image(image_path):
    image = Image.open(image_path).convert('RGB')
    transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(
            mean=[0.485, 0.456, 0.406],
            std=[0.229, 0.224, 0.225]
        )
    ])
    image_tensor = transform(image).unsqueeze(0)
    return image, image_tensor


def load_model_for_prediction(model_path):
    """加载用于预测的模型"""
    from transformers import ViTForImageClassification

    model = ViTForImageClassification.from_pretrained(
        config['pretrained_path'],
        num_labels=config['num_classes'],
        ignore_mismatched_sizes=True
    )

    if os.path.exists(model_path):
        checkpoint = torch.load(model_path, map_location=device)
        model.load_state_dict(checkpoint['model_state_dict'])
        print(f"✅ 模型加载成功！")
        if 'val_f1' in checkpoint:
            print(f"   验证集F1: {checkpoint['val_f1']:.4f}")
        if 'accuracy' in checkpoint:
            print(f"   训练准确率: {checkpoint['accuracy']:.4f}")
    else:
        print(f"❌ 模型文件不存在: {model_path}")

    model = model.to(device)
    model.eval()
    return model


# 简单预测图片
def predict_image(model, image_path, threshold=0.5):
    original_image, image_tensor = preprocess_image(image_path)
    image_tensor = image_tensor.to(device)

    with torch.no_grad():
        outputs = model(image_tensor)
        probabilities = torch.sigmoid(outputs.logits).cpu().numpy()[0]

    predictions = (probabilities > threshold).astype(int)

    # 显示图片
    plt.figure(figsize=(8, 8))
    plt.imshow(original_image)
    plt.title(f"测试图片: {os.path.basename(image_path)}")
    plt.axis('off')
    plt.show()

    # 打印结果
    print("\n" + "=" * 60)
    print("预测结果")
    print("=" * 60)

    detected = []
    for i, (name, prob) in enumerate(zip(config['class_names'], probabilities)):
        marker = "✓" if predictions[i] == 1 else "✗"
        print(f"{marker} {name:15}: {prob:.2%}")
        if predictions[i] == 1:
            detected.append(name)

    print("\n" + "=" * 60)
    if detected:
        print(f"检测到的疾病: {', '.join(detected)}")
    else:
        print("检测结果: 正常")
    print("=" * 60)

    return probabilities, predictions


if __name__ == '__main__':
    # 示例使用
    model_path = os.path.join(config['save_dir'], 'best_model_by_val_f1.pth')
    model = load_model_for_prediction(model_path)

    test_image_path = r'C:\Users\lenovo\Desktop\graduation_project\data\new\Validation Images\1024_left.jpg'
    if os.path.exists(test_image_path):
        probs, preds = predict_image(model, test_image_path)
    else:
        print(f"文件不存在: {test_image_path}")