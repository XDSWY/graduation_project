from django.contrib.auth import authenticate,login,logout
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.models import User
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import DiagnosisRecord
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
import pandas as pd
from django.db.models import Count
from django.utils import timezone
from datetime import timedelta

# 检查是否为admin用户的辅助函数
def is_admin(user):
    return user.username == 'admin'  # 或者使用 user.is_superuser

def index(request):
    # 如果用户已登录，根据身份跳转到对应主页
    if request.user.is_authenticated:
        if request.user.username == 'admin':
            return redirect('admin_home')
        else:
            return redirect('home')
    # 未登录用户显示index页面（登录表单）
    return render(request, 'index.html')


def login_view(request):
    # 如果用户已登录，直接跳转到对应主页
    if request.user.is_authenticated:
        if request.user.username == 'admin':
            return redirect('admin_home')
        else:
            return redirect('home')

    # 处理POST请求
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            if username == 'admin':  # admin用户跳转到admin_home
                return redirect('admin_home')
            else:
                return redirect('home')  # 普通用户跳转到普通home
        else:
            messages.error(request, '用户名或密码错误')
            return redirect('index')

    # GET请求时显示index页面
    return render(request, 'index.html')


def register_view(request):
    # 如果用户已登录，直接跳转到对应主页
    if request.user.is_authenticated:
        if request.user.username == 'admin':
            return redirect('admin_home')
        else:
            return redirect('home')

    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        confirm_password = request.POST['confirm_password']

        if password != confirm_password:
            messages.error(request, '两次密码不一致')
        elif User.objects.filter(username=username).exists():
            messages.error(request, '用户名已存在')
        else:
            user = User.objects.create_user(username=username, password=password)
            login(request, user)
            # 注册成功后根据身份跳转
            if username == 'admin':
                return redirect('admin_home')
            else:
                return redirect('home')

    # GET请求时显示注册页面
    return render(request, 'register.html')

# 添加退出视图
def logout_view(request):
    logout(request)
    return redirect('index')  # 退出后重定向到首页（登录页）


# 上传照片页面
@login_required
def upload(request):
    if request.method == 'POST' and request.FILES.get('image'):
        # 这里添加你的模型预测逻辑
        # 临时创建一个测试记录
        from .utils import predict_image  # 如果有预测函数

        image_file = request.FILES['image']
        record = DiagnosisRecord(user=request.user, image=image_file)
        record.save()

        try:
            # 如果有模型预测功能
            # result, confidence, probs = predict_image(record.image.path)
            # record.result = result
            # record.confidence = confidence
            # record.save()

            # 临时用测试数据
            record.result = "正常"
            record.confidence = 95.5
            record.save()

            return redirect('result', pk=record.pk)
        except Exception as e:
            messages.error(request, f'预测失败: {str(e)}')
            record.delete()
            return redirect('upload')

    return render(request, 'upload.html')


# 批量上传
@login_required
def batch_upload(request):
    if request.method == 'POST' and request.FILES.getlist('images'):
        images = request.FILES.getlist('images')
        results = []

        for img_file in images:
            record = DiagnosisRecord(user=request.user, image=img_file)
            record.save()
            try:
                # 临时用测试数据
                record.result = "正常"
                record.confidence = 95.5
                record.save()
                results.append({
                    'filename': img_file.name,
                    'result': record.result,
                    'confidence': f'{record.confidence:.2f}%'
                })
            except Exception as e:
                record.delete()
                results.append({
                    'filename': img_file.name,
                    'result': '失败',
                    'confidence': str(e)
                })

        # 生成CSV报告
        df = pd.DataFrame(results)
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="batch_results.csv"'
        df.to_csv(response, index=False)
        return response

    return render(request, 'batch_upload.html')


# 我的收藏
@login_required
def favorites(request):
    records = request.user.records.filter(is_favorite=True)
    return render(request, 'favorites.html', {'records': records})


# 历史记录
@login_required
def history(request):
    records = request.user.records.all()
    return render(request, 'history.html', {'records': records})


# 统计信息
@login_required
def statistics(request):
    user = request.user
    total = user.records.count()

    # 按结果分组统计
    result_stats = user.records.values('result').annotate(count=Count('id'))

    # 最近7天诊断数量
    last_week = timezone.now() - timedelta(days=7)
    daily_stats = user.records.filter(created_at__gte=last_week) \
        .extra({'date': "date(created_at)"}) \
        .values('date') \
        .annotate(count=Count('id')) \
        .order_by('date')

    context = {
        'total': total,
        'result_stats': result_stats,
        'daily_stats': list(daily_stats),
    }
    return render(request, 'statistics.html', context)


# 查看结果
@login_required
def result(request, pk):
    record = get_object_or_404(DiagnosisRecord, pk=pk, user=request.user)
    return render(request, 'result.html', {'record': record})


# 切换收藏状态
@login_required
def toggle_favorite(request, pk):
    record = get_object_or_404(DiagnosisRecord, pk=pk, user=request.user)
    record.is_favorite = not record.is_favorite
    record.save()
    return redirect(request.META.get('HTTP_REFERER', 'history'))

# admin专属的home页面
@login_required
@user_passes_test(is_admin, login_url='home')  # 非admin用户访问会跳转到普通home
def admin_home(request):
    return render(request, 'admin_home.html')


# 普通用户的home页面（保持不变）
@login_required
def home(request):
    return render(request, 'home.html')


# 管理用户页面
@login_required
@user_passes_test(is_admin, login_url='home')
def manage_users(request):
    users = User.objects.all().order_by('username')  # 获取所有用户，按用户名排序
    return render(request, 'manage_users.html', {'users': users})


# 删除用户功能
@login_required
@user_passes_test(is_admin, login_url='home')
def delete_user(request, user_id):
    if request.method == 'POST':
        user_to_delete = get_object_or_404(User, id=user_id)

        # 防止admin删除自己
        if user_to_delete.username == 'admin':
            messages.error(request, '不能删除admin账户')
        else:
            username = user_to_delete.username
            user_to_delete.delete()
            messages.success(request, f'用户 {username} 已成功删除')

    return redirect('manage_users')