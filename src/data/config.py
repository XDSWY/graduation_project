import torch

# 超参数配置
config = {
    'model_name': 'google/vit-base-patch16-224',
    'num_classes': 8,
    'class_names': ['正常', '糖尿病视网膜病变', '青光眼', '白内障',
                   '黄斑变性', '高血压视网膜病变', '近视', '其他'],
    'batch_size': 16,
    'epochs': 20,
    'learning_rate': 1e-5,
    'weight_decay': 0.05,
    'warmup_steps': 500,
    'gradient_accumulation_steps': 2,
    'max_grad_norm': 1.0,
    'save_dir': './checkpoints',
    'log_dir': './logs',
    'pretrained_path': r'C:/Users/lenovo/Desktop/graduation_project/models/vit-base-patch16-224',
}

# 设备配置
def get_device():
    if torch.cuda.is_available():
        return 'cuda'
    else:
        return 'cpu'

device = torch.device(get_device())