from django.db import models
from django.contrib.auth.models import User
import os

def user_directory_path(instance, filename):
    # 文件将上传到 MEDIA_ROOT/user_<id>/<filename>
    return f'user_{instance.user.id}/{filename}'

class DiagnosisRecord(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='records')
    image = models.ImageField(upload_to=user_directory_path)
    result = models.CharField(max_length=100, blank=True, null=True)  # 诊断结果
    confidence = models.FloatField(default=0.0)  # 置信度
    probabilities = models.JSONField(default=dict, blank=True)  # 各类别概率
    created_at = models.DateTimeField(auto_now_add=True)
    is_favorite = models.BooleanField(default=False)  # 收藏标记

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.created_at} - {self.result}"