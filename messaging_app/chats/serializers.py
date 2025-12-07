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
            'last_name',
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
        if not request or not request.user.is_authenticated:
            raise serializers.ValidationError("User musst be logged in.")
        sender_id=data.get('sender_id')
        if str(request.user.user_id) != str(sender_id):
            raise serializers.ValidationError("You cannot send messages as someone else!")
        conversation=data.get('conversation')
        if request and request.method in ['POST', 'PUT', 'PATCH']:
            if not conversation.participants.filter(user_id=sender_id).exists():
                raise serializers.ValidationError("Sender must be a participant in the conversation.")
        return data
class ConversationListSerializer(serializers.ModelSerializer):
    participants =UserSerializer(many=True, read_only=True)
    participant_id=serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        many=True,
        write_only=True,
        required=False,
        source='participants'
    )
    last_message=serializers.SerializerMethodField()
    unread_count=serializers.SerializerMethodField()
    class Meta:
        model=Conversation
        fields=[
            'conversation_id',
            'participants',
            'participant_id',
            'created_at',
            'last_message',
            'unread_count',
        ]
        read_only_fields = ['conversation_id', 'created_at']
    def get_last_message(self, obj):
        msg=obj.messages.select_related('sender').order_by('-sent_at').first()
        return MessageSerializer(msg, context=self.context).data if msg else None
    def get_unread_count(self, obj):
        request=self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.messages.filter(
                sent_at__gte=timezone.now() - timezone.timedelta(days=30)
            ).exclude(sender=request.user).count()
        return 0
class converssationDetailSerializer(serializers.ModelSerializer):
    participants=UserSerializer(many=True, read_only=True)
    messages=MessageSerializer(many=True, read_only=True)
    class Meta:
        model=Conversation
        fields=[
            'conversation_id',
            'participants',
            'created_at',
            'messages',
        ]
        read_only_fields = ['conversation_id', 'created_at', 'participants', 'messages']