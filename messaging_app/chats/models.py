from django.db import models
import uuid
from django.utils import timezone
from django.contrib.auth.models import AbstractUser,BaseUserManager
from django.contrib.auth import get_user_model

# Create your models here.
class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email field must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.username = email                     # username = email
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")
        return self.create_user(email, password, **extra_fields)

class User(AbstractUser):
    user_id=models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    phone_number=models.CharField(max_length=20,null=True, blank=True)
    ROLE_CHOICES=[
        ('guest', 'Guest'),
        ('host','Host'),
        ('admin', 'Admin'),
    ]
    role=models.CharField(
        max_length=10,
        choices=ROLE_CHOICES,
        default='guest',
    )
    created_at=models.DateTimeField(default=timezone.now)
    USERNAME_FIELD='email'
    REQUIRED_FIELDS=['first_name', 'last_name']
    objects=CustomUserManager()
    def save(self, *args, **kwargs):
        if not self.username:
            self.username=self.email
        super().save(*args, **kwargs)
    def __str__(self):
        return f"{self.get_full_name()} ({self.email})-{self.role.capitalize()}"
    class Meta:
        db_table='user'
        indexes=[models.Index(fields=['email'])]
        verbose_name='User'
        verbose_name_plural='Users'
        constraints=[
            models.UniqueConstraint(fields=['email'], name='unique_email_constraint')
        ]
User=get_user_model()
class Conversation(models.Model):
    conversation_id=models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    participants=models.ManyToManyField(
        to=User,
        related_name='conversations',
        help_text="Users particpating in this conversation"
    )
    created_at=models.DateTimeField(default=timezone.now)
    def __str__(self):
        participants_names=', '.join([p.get_full_name() for p in self.participants.all()[:3]])
        if self.participants.count()>3:
             participants_names += f" and {self.participants.count() - 3} more"
        return f"Conversation between {participants_names}"
    class Meta:
        db_table='conversation'
        ordering=['-created_at']
        verbose_name='Conversation'
        verbose_name_plural='Conversations'

class  Property(models.Model):
    property_id=models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    host_id=models.ForeignKey(
        to=User,
        on_delete=models.CASCADE,
        related_name='hosted_properties'
    )
    title=models.CharField(max_length=255, null=False, blank=False)
    description=models.TextField(null=True, blank=True)
    location=models.CharField(max_length=500, null=False, blank=False)
    price_per_night=models.DecimalField(max_digits=10, decimal_places=2)
    created_at=models.DateTimeField(default=timezone.now)
    updated_at=models.DateTimeField(auto_now=True)
    def __str__(self):
        return f"Property: {self.title} owned by {self.host_id.get_full_name()}"
    class Meta:
        db_table='property'
        ordering=['-created_at']
        verbose_name='Property'
        verbose_name_plural='Properties'
        indexes=[
            models.Index(fields=['property_id']),
        ]
        constraints=[
            models.CheckConstraint(
                check=models.Q(price_per_night__gte=0),
                name='price_per_night_non_negative'
            )
        ]
class Booking(models.Model):
    booking_id=models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    property_id=models.ForeignKey(
        to=Property,
        on_delete=models.CASCADE,
        related_name='bookings'
    )
    user_id=models.ForeignKey(
        to=User,
        on_delete=models.CASCADE,
        related_name='booking'
    )
    check_in=models.DateField(null=False, blank=False)
    check_out=models.DateField(null=False, blank=False)
    total_price=models.DecimalField(max_digits=10, decimal_places=2)
    created_at=models.DateTimeField(default=timezone.now)
    status_choices=[
        ('pending','Pending'),
        ('confirmed','Confirmed'),
        ('canceled','Canceled'),
    ]
    status=models.CharField(
        max_length=10,
        choices=status_choices,
        default='pending',
    )
    def __str__(self):
        return f"Booking by {self.user_id.get_full_name()} for {self.property_id.title} from {self.check_in} to {self.check_out}"
    class Meta:
        db_table='booking'
        ordering=['-created_at']
        verbose_name='Booking'
        verbose_name_plural='Bookings'
        indexes=[
            models.Index(fields=['property_id', 'check_in', 'check_out']),
        ]
        constraints=[
            models.CheckConstraint(
                check=models.Q(check_out__gt=models.F('check_in')),
                name='check_out_after_check_in'
            )
        ]
class Payment(models.Model):
    payment_id=models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    booking_id=models.ForeignKey(
        to=Booking,
        on_delete=models.CASCADE,
        related_name='payments'
    )
    user_id=models.ForeignKey(
        to=User,
        on_delete=models.CASCADE,
        related_name='payments'
    )
    amount=models.DecimalField(max_digits=10, decimal_places=2)
    payment_date=models.DateTimeField(default=timezone.now)
    payment_method_choices=[
        ('credit_card','Credit Card'),
        ('paypal','PayPal'),
        ('bank_transfer','Bank Transfer'),
    ]
    payment_method=models.CharField(
        max_length=20,
        choices=payment_method_choices,
        default='credit_card',
    )
 
    def __str__(self):
        return f"Payment of {self.amount} by {self.user_id.get_full_name()} for booking {self.booking_id}"
    class Meta:
        db_table='payment'
        ordering=['-payment_date']
        verbose_name='Payment'
        verbose_name_plural='Payments'
        indexes=[
            models.Index(fields=['booking_id']),
        ]
        constraints=[
            models.CheckConstraint(
                check=models.Q(amount__gte=0),
                name='payment_amount_non_negative'
            )
        ]
class Review(models.Model):
    review_id=models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    property_id=models.ForeignKey(
        to=Property,
        on_delete=models.CASCADE,
        related_name='reviews'
    )
    user_id=models.ForeignKey(
        to=User,
        on_delete=models.CASCADE,
        related_name='reviews'
    )
    rating=models.IntegerField(null=False, blank=False)
    comment=models.TextField(null=True, blank=True)
    created_at=models.DateTimeField(default=timezone.now)
    def __str__(self):
        return f"Review by {self.user_id.get_full_name()} for {self.property_id.title} - Rating: {self.rating}"
    class Meta:
        db_table='review'
        ordering=['-created_at']
        verbose_name='Review'
        verbose_name_plural='Reviews'
        indexes=[
            models.Index(fields=['property_id', 'rating']),
        ]
        constraints=[
            models.CheckConstraint(
                check=models.Q(rating__gte=1) & models.Q(rating__lte=5),
                name='rating_between_1_and_5'
            )
        ]
class Message(models.Model):
    message_id=models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    sender=models.ForeignKey(
        to=User,
        on_delete=models.CASCADE,
        related_name='sent_messages'
    )
    
    conversation=models.ForeignKey(
        to=Conversation,
        on_delete=models.CASCADE,
        related_name='messages'
    )
    message_body=models.TextField(null=False, blank=False)
    sent_at=models.DateTimeField(default=timezone.now)
    def __str__(self):
        return f"Message from {self.sender.get_full_name()} in {self.conversation_id}"
    class Meta:
        db_table = 'message'
        ordering = ['sent_at']
        indexes = [
            models.Index(fields=['conversation', 'sent_at']),
        ]
        verbose_name = "Message"
        verbose_name_plural = "Messages"
        constraints=[
            models.CheckConstraint(
            check=~models.Q(message_body=''),
            name='non_empty_message_body'
            )
    
        ]