from django.db import models
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
import os

# Create your models here.
User = get_user_model()

def validate_video_extension(value):
    """Validate video file extensions"""
    valid_extensions = ['.mp4', '.mov', '.avi', '.wmv']
    ext = os.path.splitext(value.name)[1]
    if ext.lower() not in valid_extensions:
        raise ValidationError('Unsupported video format. Please use MP4, MOV, AVI, or WMV.')

class Post(models.Model):
    POST_TYPES = [
        ('text', 'Text Only'),
        ('image', 'Image'),
        ('video', 'Video'),
        ('mixed', 'Mixed Content')
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts')
    content = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='post_images/', blank=True, null=True)
    video = models.FileField(
        upload_to='post_videos/', 
        validators=[validate_video_extension],
        blank=True, 
        null=True,
        help_text='Supported formats: MP4, MOV, AVI, WMV'
    )
    post_type = models.CharField(
        max_length=10, 
        choices=POST_TYPES, 
        default='text'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        """Validate post content based on type"""
        if not self.content and not self.image and not self.video:
            raise ValidationError('Post must have either text, image, or video content.')
        
        # Set post type based on content
        if self.video and (self.image or self.content):
            self.post_type = 'mixed'
        elif self.video:
            self.post_type = 'video'
        elif self.image and self.content:
            self.post_type = 'mixed'
        elif self.image:
            self.post_type = 'image'
        else:
            self.post_type = 'text'

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.post_type.capitalize()} post by {self.user.email} on {self.created_at}"
        
    class Meta:
        ordering = ['-created_at']


class Like(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='likes')
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='likes')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'post')

    def __str__(self):
        return f"{self.user.email} liked post #{self.post.id} on {self.created_at}"