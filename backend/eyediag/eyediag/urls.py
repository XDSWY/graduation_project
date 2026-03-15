"""
URL configuration for eyediag project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include
from diagnosis import views
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve
from django.urls import re_path
import os

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('diagnosis.api_urls')),  # API路由
    # 原来的HTML路由可以保留，也可以注释掉
    # path('', views.index, name='index'),
    # path('login/', views.login_view, name='login'),
    # path('register/', views.register_view, name='register'),
]

# 开发环境下的静态文件服务
if settings.DEBUG:
    # 媒体文件服务（用于上传的图片）
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

    # 添加 heatmaps 的路由
    urlpatterns += [
        re_path(r'^heatmaps/(?P<path>.*)$', serve, {
            'document_root': os.path.join(settings.BASE_DIR, 'heatmaps'),
        }),
    ]

    if settings.DEBUG:
        urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
        urlpatterns += static(settings.HEATMAPS_URL, document_root=settings.HEATMAPS_ROOT)