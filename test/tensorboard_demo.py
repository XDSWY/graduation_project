"""
from torch.utils.tensorboard import SummaryWriter
path = "C:\\Users\\lenovo\\Desktop\\graduation_project\\logs"
writer = SummaryWriter(path)
for i in range(100):
    writer.add_scalar("y=2x", 3*i, i)

writer.close()
# tensorboard --logdir=logs --port=6007  指定端口，打开图像
"""


from torch.utils.tensorboard import SummaryWriter
import numpy as np
from PIL import Image

writer = SummaryWriter("./logs")
image_path = r"C:\Users\lenovo\Desktop\graduation_project\test\hymenoptera_data\hymenoptera_data\train\ants\0013035.jpg"
img_PIL = Image.open(image_path)
img_array = np.array(img_PIL)
print(type(img_array))
print(img_array.shape)

writer.add_image("demo", img_array, 4, dataformats='HWC')
for i in range(100):
    writer.add_scalar("y=2x", 3*i, i)

writer.close()

