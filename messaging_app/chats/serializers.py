from rest_framework import serializers
from django.contrib.auth import get_user_model
from models import Conversation , Message
from django.utils import timezone
User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    fullname=serializers.CharField(source='get_full_name', read_only=True)
    role_display=serializers.CharField(source='get_role_display', read_only=True)
    class Meta:
        model = User
        fields = [
            'user_id', 
            'email',
            'first_name', 
            'last_name'
            'fullname',
            'role',
            'role_display',
            'phone_number',
            'created_at',
            ]
        read_only_fields = ['user_id', 'created_at']
class MessageSerializer(serializers.ModelSerializer):
    sender=UserSerializer(read_only=True)
    sender_id=serializers.UUIDField(write_only=True)
    class Meta:
        model=Message
        fields=[
            'message_id',
            'sender',
            'sender_id',
            'message_body',
            'sent_at',
        ]
        read_only_fields = ['message_id', 'sent_at']
    def validate(self, data):
        request=self.context.get('request')
        if request and request.method in ['POST', 'PUT', 'PATCH']:
            conversation=data.get('conversation')
            sender_id=data.get('sender_id')
            if not conversation.participants.filter(user_id=sender_id).exists():
                raise serializers.ValidationError("Sender must be a participant in the conversation.")
        return data
class ConversationSerializer(serializers.ModelSerializer):
    parcicipants =UserSerializer(many=True, read_only=True)
    parcicipant_id=serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        many=True,
        Write_only=True,
        required=False
    )
    last_message=serializers.SerializerMethodField()
    unread_count=serializers.SerializerMethodField()
    class Meta:
        model=Conversation
        fields=[
            'conversation_id',
            'parcicipants',
            'parcicipant_id',
            'created_at',
            'last_message',
            'unread_count',
        ]
        read_only_fields = ['conversation_id', 'created_at']
    def get_last_message(self, obj):
        request=self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.messages.filter(
                sent_at__get=timezone.now() - timezone.timedelta(days=7)
            )