from django.urls import path
from . import api_views

urlpatterns = [
    # 认证相关
    path('register/', api_views.register, name='api_register'),
    path('login/', api_views.login, name='api_login'),
    path('check-username/', api_views.check_username, name='api_check_username'),

    # 记录相关
    path('upload/', api_views.upload_image, name='api_upload'),
    path('batch-upload/', api_views.batch_upload, name='api_batch_upload'),
    path('records/', api_views.get_records, name='api_records'),
    path('records/<int:record_id>/', api_views.get_record_detail, name='api_record_detail'),
    path('records/<int:record_id>/toggle-favorite/', api_views.toggle_favorite, name='api_toggle_favorite'),
    path('records/<int:record_id>/delete/', api_views.delete_record, name='api_delete_record'),
    path('records/<int:record_id>/heatmap/', api_views.generate_heatmap, name='api_generate_heatmap'),  # 确保这行存在
    path('favorites/', api_views.get_favorites, name='api_favorites'),

    # 统计相关
    path('statistics/', api_views.get_statistics, name='api_statistics'),
    path('statistics/daily/', api_views.get_daily_stats, name='api_daily_stats'),

    # 管理员相关
    path('users/', api_views.get_users, name='api_get_users'),
    path('users/<int:user_id>/', api_views.delete_user, name='api_delete_user'),
]