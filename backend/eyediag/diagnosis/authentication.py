import jwt
from django.conf import settings
from django.contrib.auth.models import User
from rest_framework import authentication, exceptions


class JWTAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        auth_header = request.headers.get('Authorization')

        if not auth_header:
            return None

        try:
            # 提取token (格式: "Bearer <token>")
            token = auth_header.split(' ')[1]
            # 解码token
            payload = jwt.decode(
                token,
                settings.JWT_SECRET,
                algorithms=['HS256']
            )
            # 获取用户
            user = User.objects.get(id=payload['user_id'])
            return (user, None)
        except jwt.ExpiredSignatureError:
            raise exceptions.AuthenticationFailed('Token已过期')
        except jwt.InvalidTokenError:
            raise exceptions.AuthenticationFailed('无效的Token')
        except User.DoesNotExist:
            raise exceptions.AuthenticationFailed('用户不存在')