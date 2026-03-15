import jwt
import datetime
import os
import numpy as np
from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .models import DiagnosisRecord
from .serializers import DiagnosisRecordSerializer
from .utils import predict_image, predict_batch  # 导入预测函数

from .gradcam import generate_and_save_heatmaps, generate_gradcam, generate_layercam
from .utils import load_model, transform
import os


def generate_token(user):
    """生成JWT token"""
    payload = {
        'user_id': user.id,
        'username': user.username,
        'is_admin': user.username == 'admin',
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=settings.JWT_EXPIRY_HOURS),
        'iat': datetime.datetime.utcnow()
    }
    token = jwt.encode(payload, settings.JWT_SECRET, algorithm='HS256')
    return token


# ==================== 认证相关视图 ====================

@api_view(['POST'])
def register(request):
    """用户注册"""
    try:
        username = request.data.get('username')
        password = request.data.get('password')

        if not username or not password:
            return Response({
                'success': False,
                'message': '用户名和密码不能为空'
            }, status=status.HTTP_400_BAD_REQUEST)

        if User.objects.filter(username=username).exists():
            return Response({
                'success': False,
                'message': '用户名已存在'
            }, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.create_user(
            username=username,
            password=password
        )

        return Response({
            'success': True,
            'message': '注册成功'
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response({
            'success': False,
            'message': f'注册失败: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def login(request):
    """用户登录"""
    try:
        username = request.data.get('username')
        password = request.data.get('password')

        if not username or not password:
            return Response({
                'success': False,
                'message': '用户名和密码不能为空'
            }, status=status.HTTP_400_BAD_REQUEST)

        user = authenticate(username=username, password=password)

        if user:
            token = generate_token(user)

            return Response({
                'success': True,
                'token': token,
                'username': user.username,
                'is_admin': user.username == 'admin',
                'message': '登录成功'
            })
        else:
            return Response({
                'success': False,
                'message': '用户名或密码错误'
            }, status=status.HTTP_401_UNAUTHORIZED)

    except Exception as e:
        return Response({
            'success': False,
            'message': f'登录失败: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def check_username(request):
    """检查用户名是否存在"""
    username = request.query_params.get('username')
    if not username:
        return Response({
            'exists': False,
            'message': '请提供用户名'
        })

    exists = User.objects.filter(username=username).exists()
    return Response({
        'exists': exists,
        'message': '用户名已存在' if exists else '用户名可用'
    })


# ==================== 诊断相关视图 ====================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_image(request):
    """上传单张图片进行诊断"""
    try:
        print(f"收到上传请求，用户: {request.user.username}")

        image_file = request.FILES.get('image')
        if not image_file:
            print("没有图片文件")
            return Response({
                'success': False,
                'message': '请选择图片'
            }, status=status.HTTP_400_BAD_REQUEST)

        print(f"文件名: {image_file.name}, 类型: {image_file.content_type}, 大小: {image_file.size} bytes")

        # 检查文件类型
        allowed_types = ['image/jpeg', 'image/png', 'image/jpg']
        if image_file.content_type not in allowed_types:
            print(f"文件类型不支持: {image_file.content_type}")
            return Response({
                'success': False,
                'message': '只支持 JPG、PNG 格式的图片'
            }, status=status.HTTP_400_BAD_REQUEST)

        # 检查文件大小（限制 10MB）
        if image_file.size > 10 * 1024 * 1024:
            print(f"文件太大: {image_file.size} bytes")
            return Response({
                'success': False,
                'message': '图片大小不能超过 10MB'
            }, status=status.HTTP_400_BAD_REQUEST)

        # 创建记录
        print("创建数据库记录...")
        record = DiagnosisRecord.objects.create(
            user=request.user,
            image=image_file
        )
        print(f"记录创建成功，ID: {record.id}, 路径: {record.image.path}")

        # 调用模型预测
        try:
            print("开始调用预测函数...")
            result, confidence, probabilities = predict_image(record.image.path)
            print(f"预测结果: {result}, 置信度: {confidence}")
            record.result = result
            record.confidence = confidence
            record.probabilities = {f'class_{i}': p for i, p in enumerate(probabilities)}
            record.save()
        except Exception as e:
            print(f"预测失败: {str(e)}")
            import traceback
            traceback.print_exc()
            # 预测失败时设置默认值
            record.result = "诊断失败"
            record.confidence = 0
            record.save()

        serializer = DiagnosisRecordSerializer(record, context={'request': request})

        return Response({
            'success': True,
            'message': '上传成功',
            'record': serializer.data
        })

    except Exception as e:
        print(f"上传过程异常: {str(e)}")
        import traceback
        traceback.print_exc()
        return Response({
            'success': False,
            'message': f'上传失败: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def batch_upload(request):
    """批量上传图片"""
    try:
        images = request.FILES.getlist('images')
        if not images:
            return Response({
                'success': False,
                'message': '请选择图片'
            }, status=status.HTTP_400_BAD_REQUEST)

        if len(images) > 20:
            return Response({
                'success': False,
                'message': '一次最多上传20张图片'
            }, status=status.HTTP_400_BAD_REQUEST)

        results = []

        for image_file in images:
            # 检查文件类型
            allowed_types = ['image/jpeg', 'image/png', 'image/jpg']
            if image_file.content_type not in allowed_types:
                continue

            # 创建记录
            record = DiagnosisRecord.objects.create(
                user=request.user,
                image=image_file
            )

            # 调用模型预测
            try:
                result, confidence, probabilities = predict_image(record.image.path)
                record.result = result
                record.confidence = confidence
                record.probabilities = {f'class_{i}': p for i, p in enumerate(probabilities)}
                record.save()
            except Exception as e:
                print(f"预测失败: {e}")
                record.result = "诊断失败"
                record.confidence = 0
                record.save()

            serializer = DiagnosisRecordSerializer(record, context={'request': request})
            results.append(serializer.data)

        return Response({
            'success': True,
            'message': f'成功上传 {len(results)} 张图片',
            'records': results
        })

    except Exception as e:
        return Response({
            'success': False,
            'message': f'批量上传失败: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ==================== 记录管理视图 ====================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_records(request):
    """获取用户的诊断记录"""
    records = request.user.records.all()
    serializer = DiagnosisRecordSerializer(records, many=True, context={'request': request})
    return Response({
        'success': True,
        'records': serializer.data
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_favorites(request):
    """获取用户的收藏记录"""
    records = request.user.records.filter(is_favorite=True)
    serializer = DiagnosisRecordSerializer(records, many=True, context={'request': request})
    return Response({
        'success': True,
        'records': serializer.data
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def toggle_favorite(request, record_id):
    """切换收藏状态"""
    try:
        record = DiagnosisRecord.objects.get(id=record_id, user=request.user)
        record.is_favorite = not record.is_favorite
        record.save()

        return Response({
            'success': True,
            'is_favorite': record.is_favorite,
            'message': '已添加收藏' if record.is_favorite else '已取消收藏'
        })
    except DiagnosisRecord.DoesNotExist:
        return Response({
            'success': False,
            'message': '记录不存在'
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_record(request, record_id):
    """删除诊断记录"""
    try:
        record = DiagnosisRecord.objects.get(id=record_id, user=request.user)
        # 删除图片文件
        if record.image:
            if os.path.isfile(record.image.path):
                os.remove(record.image.path)
        record.delete()

        return Response({
            'success': True,
            'message': '删除成功'
        })
    except DiagnosisRecord.DoesNotExist:
        return Response({
            'success': False,
            'message': '记录不存在'
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_record_detail(request, record_id):
    """获取单条记录的详细信息"""
    try:
        record = DiagnosisRecord.objects.get(id=record_id, user=request.user)
        serializer = DiagnosisRecordSerializer(record, context={'request': request})
        return Response({
            'success': True,
            'record': serializer.data
        })
    except DiagnosisRecord.DoesNotExist:
        return Response({
            'success': False,
            'message': '记录不存在'
        }, status=status.HTTP_404_NOT_FOUND)


# ==================== 管理员功能 ====================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_users(request):
    """获取所有用户（仅管理员）"""
    if request.user.username != 'admin':
        return Response({
            'success': False,
            'message': '无权限访问'
        }, status=status.HTTP_403_FORBIDDEN)

    users = User.objects.all().order_by('id')
    user_list = []
    for user in users:
        user_list.append({
            'id': user.id,
            'username': user.username,
            'is_admin': user.username == 'admin',
            'date_joined': user.date_joined.strftime('%Y-%m-%d %H:%M'),
            'last_login': user.last_login.strftime('%Y-%m-%d %H:%M') if user.last_login else None,
            'records_count': user.records.count()
        })

    return Response({
        'success': True,
        'users': user_list
    })


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_user(request, user_id):
    """删除用户（仅管理员）"""
    if request.user.username != 'admin':
        return Response({
            'success': False,
            'message': '无权限访问'
        }, status=status.HTTP_403_FORBIDDEN)

    try:
        user_to_delete = User.objects.get(id=user_id)

        if user_to_delete.username == 'admin':
            return Response({
                'success': False,
                'message': '不能删除管理员账户'
            }, status=status.HTTP_400_BAD_REQUEST)

        username = user_to_delete.username
        user_to_delete.delete()

        return Response({
            'success': True,
            'message': f'用户 {username} 已成功删除'
        })
    except User.DoesNotExist:
        return Response({
            'success': False,
            'message': '用户不存在'
        }, status=status.HTTP_404_NOT_FOUND)


# ==================== Grad-CAM 可视化 ====================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_heatmap(request, record_id):
    """为指定的诊断记录生成热力图"""
    try:
        record = DiagnosisRecord.objects.get(id=record_id, user=request.user)

        # 检查图片是否存在
        if not os.path.exists(record.image.path):
            return Response({
                'success': False,
                'message': '图片文件不存在'
            }, status=status.HTTP_404_NOT_FOUND)

        # 加载模型
        model = load_model()
        if model is None:
            return Response({
                'success': False,
                'message': '模型加载失败'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # 创建输出目录 - 使用你的实际路径
        heatmap_dir = os.path.join(settings.BASE_DIR, 'heatmaps', str(record.user.id))
        os.makedirs(heatmap_dir, exist_ok=True)

        # 生成热力图
        methods = request.data.get('methods', ['gradcam', 'layercam'])
        heatmap_paths = generate_and_save_heatmaps(
            model,
            record.image.path,
            heatmap_dir,
            methods
        )

        # 构建URL - 修改这里，使用你的实际路径
        request_obj = request._request
        base_url = f"{request_obj.scheme}://{request_obj.get_host()}"
        heatmap_urls = {}

        for method, path in heatmap_paths.items():
            # 获取文件名
            filename = os.path.basename(path)
            # 构建URL，指向你的实际路径
            # 注意：这里需要配置静态文件服务来访问 heatmaps 目录
            full_url = f"{base_url}/heatmaps/{record.user.id}/{filename}"
            print(f"{method} 热力图URL: {full_url}")
            heatmap_urls[method] = full_url

        return Response({
            'success': True,
            'heatmaps': heatmap_urls,
            'message': '热力图生成成功'
        })

    except DiagnosisRecord.DoesNotExist:
        return Response({
            'success': False,
            'message': '记录不存在'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        print(f"热力图生成错误: {e}")
        import traceback
        traceback.print_exc()
        return Response({
            'success': False,
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# ==================== 统计功能 ====================
import datetime
from django.db.models import Count
from django.utils import timezone


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_statistics(request):
    """获取系统统计信息"""
    try:
        user = request.user

        # 基础统计
        stats = {
            'user': {
                'total_diagnoses': user.records.count(),
                'favorites': user.records.filter(is_favorite=True).count(),
            }
        }

        # 如果是管理员，获取全局统计
        if user.username == 'admin':
            # 总诊断次数
            total_diagnoses = DiagnosisRecord.objects.count()

            # 今日诊断
            today = timezone.now().date()
            today_diagnoses = DiagnosisRecord.objects.filter(
                created_at__date=today
            ).count()

            # 本周诊断
            week_ago = timezone.now() - datetime.timedelta(days=7)
            week_diagnoses = DiagnosisRecord.objects.filter(
                created_at__gte=week_ago
            ).count()

            # 本月诊断
            month_ago = timezone.now() - datetime.timedelta(days=30)
            month_diagnoses = DiagnosisRecord.objects.filter(
                created_at__gte=month_ago
            ).count()

            # 疾病分布
            disease_stats = []
            from .utils import CLASS_NAMES
            for name in CLASS_NAMES:
                count = DiagnosisRecord.objects.filter(result=name).count()
                if count > 0:
                    disease_stats.append({
                        'name': name,
                        'count': count
                    })

            # 按结果分组统计
            result_stats = DiagnosisRecord.objects.values('result') \
                .annotate(count=Count('id')) \
                .order_by('-count')

            # 每日诊断趋势（最近30天）
            daily_trend = []
            for i in range(30):
                date = today - datetime.timedelta(days=i)
                count = DiagnosisRecord.objects.filter(
                    created_at__date=date
                ).count()
                daily_trend.append({
                    'date': date.strftime('%Y-%m-%d'),
                    'count': count
                })
            daily_trend.reverse()

            # 用户排名
            user_rank = []
            users = User.objects.annotate(
                diagnose_count=Count('records')
            ).order_by('-diagnose_count')[:10]

            for u in users:
                user_rank.append({
                    'username': u.username,
                    'diagnoses': u.diagnose_count,
                    'is_admin': u.username == 'admin'
                })

            stats['admin'] = {
                'total_diagnoses': total_diagnoses,
                'today_diagnoses': today_diagnoses,
                'week_diagnoses': week_diagnoses,
                'month_diagnoses': month_diagnoses,
                'total_users': User.objects.count(),
                'disease_distribution': disease_stats,
                'result_stats': list(result_stats),
                'daily_trend': daily_trend,
                'user_rank': user_rank
            }

        return Response({
            'success': True,
            'statistics': stats
        })

    except Exception as e:
        return Response({
            'success': False,
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_daily_stats(request):
    """获取每日诊断统计（图表用）"""
    try:
        days = int(request.query_params.get('days', 7))

        end_date = timezone.now().date()
        start_date = end_date - datetime.timedelta(days=days - 1)

        dates = []
        counts = []

        for i in range(days):
            date = start_date + datetime.timedelta(days=i)
            count = DiagnosisRecord.objects.filter(
                created_at__date=date
            ).count()
            dates.append(date.strftime('%m-%d'))
            counts.append(count)

        return Response({
            'success': True,
            'dates': dates,
            'counts': counts
        })

    except Exception as e:
        return Response({
            'success': False,
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


