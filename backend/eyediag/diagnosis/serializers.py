from rest_framework import serializers
from .models import DiagnosisRecord


class DiagnosisRecordSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = DiagnosisRecord
        fields = ['id', 'image', 'image_url', 'result', 'confidence', 'created_at', 'is_favorite']

    def get_image_url(self, obj):
        request = self.context.get('request')
        if request and obj.image:
            return request.build_absolute_uri(obj.image.url)
        return None
