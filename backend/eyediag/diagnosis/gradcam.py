import cv2
import numpy as np
import torch
import torch.nn.functional as F
import os
from PIL import Image
import matplotlib.pyplot as plt
from .utils import transform

# 全局变量记录设备
_device = None


def get_device():
    """获取可用设备，如果GPU出错则回退到CPU"""
    global _device
    if _device is not None:
        return _device

    if torch.cuda.is_available():
        try:
            # 测试CUDA是否可用
            torch.zeros(1).cuda()
            _device = torch.device('cuda')
            print("使用GPU设备")
        except:
            _device = torch.device('cpu')
            print("GPU不可用，回退到CPU")
    else:
        _device = torch.device('cpu')
        print("使用CPU设备")

    return _device


def find_last_conv_layer(model):
    """
    自动查找模型的最后一个卷积层
    """
    conv_layers = []
    for name, module in model.named_modules():
        if isinstance(module, torch.nn.Conv2d):
            conv_layers.append((name, module))

    if conv_layers:
        return conv_layers[-1][0]  # 返回最后一个卷积层的名称
    return None


def generate_gradcam(model, image_tensor, target_layer=None, target_class=None):
    """
    生成 Grad-CAM 热力图（CPU回退版本）
    """
    device = get_device()

    # 确保模型和输入在同一设备
    model = model.to(device)
    image_tensor = image_tensor.to(device)

    model.eval()

    # 如果没有指定目标层，自动查找
    if target_layer is None:
        target_layer = find_last_conv_layer(model)
        if target_layer is None:
            print("未找到卷积层，无法生成Grad-CAM")
            return None, None

    print(f"使用目标层: {target_layer}")

    # 注册钩子获取特征图和梯度
    features = []
    gradients = []

    def forward_hook(module, input, output):
        features.append(output.detach())

    def backward_hook(module, grad_input, grad_output):
        gradients.append(grad_output[0].detach())

    # 获取目标层
    layer = dict([*model.named_modules()]).get(target_layer)
    if layer is None:
        print(f"找不到层: {target_layer}")
        return None, None

    # 注册钩子
    forward_handle = layer.register_forward_hook(forward_hook)
    backward_handle = layer.register_full_backward_hook(backward_hook)

    try:
        # 前向传播
        output = model(image_tensor)

        # 获取logits
        if hasattr(output, 'logits'):
            logits = output.logits
        else:
            logits = output

        # 确定目标类别
        if target_class is None:
            target_class = logits.argmax(dim=1).item()

        print(f"目标类别: {target_class}")

        # 反向传播
        model.zero_grad()
        one_hot = torch.zeros_like(logits)
        one_hot[0, target_class] = 1
        logits.backward(gradient=one_hot, retain_graph=True)

        # 检查是否捕获到特征和梯度
        if not features or not gradients:
            print("未能捕获特征图或梯度")
            return None, None

        feature_map = features[0]
        gradient = gradients[0]

        # 计算权重
        weights = gradient.mean(dim=[2, 3], keepdim=True)

        # 生成热力图
        cam = (weights * feature_map).sum(dim=1, keepdim=True)
        cam = F.relu(cam)
        cam = cam.squeeze().cpu().numpy()

        # 归一化
        if cam.max() - cam.min() != 0:
            cam = (cam - cam.min()) / (cam.max() - cam.min() + 1e-8)
        else:
            cam = np.zeros_like(cam)

        return cam, target_class

    except Exception as e:
        print(f"Grad-CAM生成失败: {e}")
        import traceback
        traceback.print_exc()
        return None, None

    finally:
        # 移除钩子
        forward_handle.remove()
        backward_handle.remove()


def generate_layercam(model, image_tensor, target_layer=None, target_class=None):
    """
    生成 LayerCAM 热力图（CPU回退版本）
    """
    device = get_device()

    # 确保模型和输入在同一设备
    model = model.to(device)
    image_tensor = image_tensor.to(device)

    model.eval()

    if target_layer is None:
        target_layer = find_last_conv_layer(model)
        if target_layer is None:
            return None, None

    # 注册钩子获取特征图和梯度
    features = []
    gradients = []

    def forward_hook(module, input, output):
        features.append(output.detach())

    def backward_hook(module, grad_input, grad_output):
        gradients.append(grad_output[0].detach())

    layer = dict([*model.named_modules()]).get(target_layer)
    if layer is None:
        return None, None

    forward_handle = layer.register_forward_hook(forward_hook)
    backward_handle = layer.register_full_backward_hook(backward_hook)

    try:
        output = model(image_tensor)

        if hasattr(output, 'logits'):
            logits = output.logits
        else:
            logits = output

        if target_class is None:
            target_class = logits.argmax(dim=1).item()

        model.zero_grad()
        one_hot = torch.zeros_like(logits)
        one_hot[0, target_class] = 1
        logits.backward(gradient=one_hot, retain_graph=True)

        if not features or not gradients:
            return None, None

        feature_map = features[0]  # (1, C, H, W)
        gradient = gradients[0]  # (1, C, H, W)

        # LayerCAM: 对每个空间位置独立加权
        weights = F.relu(gradient)

        # 逐元素相乘并求和
        cam = (weights * feature_map).sum(dim=1, keepdim=True)
        cam = F.relu(cam)
        cam = cam.squeeze().cpu().numpy()

        # 归一化
        if cam.max() - cam.min() != 0:
            cam = (cam - cam.min()) / (cam.max() - cam.min() + 1e-8)
        else:
            cam = np.zeros_like(cam)

        return cam, target_class

    except Exception as e:
        print(f"LayerCAM生成失败: {e}")
        import traceback
        traceback.print_exc()
        return None, None

    finally:
        forward_handle.remove()
        backward_handle.remove()


def overlay_heatmap(image_path, heatmap, output_path, alpha=0.5):
    """
    将热力图叠加到原图上
    """
    try:
        # 读取原图
        img = cv2.imread(image_path)
        if img is None:
            # 尝试用 PIL 读取
            pil_img = Image.open(image_path).convert('RGB')
            img = np.array(pil_img)
            img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

        # 调整大小
        h, w = img.shape[:2]
        heatmap = cv2.resize(heatmap, (w, h))

        # 转换为彩色热力图
        heatmap = np.uint8(255 * heatmap)
        heatmap_color = cv2.applyColorMap(heatmap, cv2.COLORMAP_JET)

        # 叠加
        superimposed = cv2.addWeighted(img, 1 - alpha, heatmap_color, alpha, 0)

        # 保存
        cv2.imwrite(output_path, superimposed)

        # 同时也保存单独的热力图
        heatmap_only_path = output_path.replace('.jpg', '_heatmap.jpg').replace('.png', '_heatmap.png')
        cv2.imwrite(heatmap_only_path, heatmap_color)

        return output_path

    except Exception as e:
        print(f"叠加热力图失败: {e}")
        return None


def generate_and_save_heatmaps(model, image_path, output_dir, methods=['gradcam', 'layercam']):
    """
    生成并保存多种热力图
    """
    os.makedirs(output_dir, exist_ok=True)

    # 加载并预处理图像
    image = Image.open(image_path).convert('RGB')
    input_tensor = transform(image).unsqueeze(0)

    results = {}

    if 'gradcam' in methods:
        try:
            cam, target_class = generate_gradcam(model, input_tensor)
            if cam is not None:
                output_path = os.path.join(output_dir, f'gradcam_{os.path.basename(image_path)}')
                overlay_heatmap(image_path, cam, output_path)
                results['gradcam'] = output_path
                print(f"Grad-CAM生成成功: {output_path}")
            else:
                print("Grad-CAM生成失败")
        except Exception as e:
            print(f"Grad-CAM处理失败: {e}")

    if 'layercam' in methods:
        try:
            cam, target_class = generate_layercam(model, input_tensor)
            if cam is not None:
                output_path = os.path.join(output_dir, f'layercam_{os.path.basename(image_path)}')
                overlay_heatmap(image_path, cam, output_path)
                results['layercam'] = output_path
                print(f"LayerCAM生成成功: {output_path}")
            else:
                print("LayerCAM生成失败")
        except Exception as e:
            print(f"LayerCAM处理失败: {e}")

    return results