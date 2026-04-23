from rest_framework import serializers
from .models import Resume


class ResumeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Resume
        fields = ['id', 'filename', 'parsed_text', 'file_path', 'word_count', 'created_at']
        read_only_fields = ['id', 'file_path', 'word_count', 'created_at']


class ResumeUploadSerializer(serializers.Serializer):
    file = serializers.FileField()


class ResumeDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Resume
        fields = ['id', 'filename', 'parsed_text', 'word_count', 'created_at']
        read_only_fields = ['id', 'filename', 'parsed_text', 'word_count', 'created_at']