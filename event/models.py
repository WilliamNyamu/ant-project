from django.db import models
from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver
from accounts.models import Roles, UserRole


User = get_user_model()

# Create your models here.
class Event(models.Model):
    name = models.CharField(max_length=150)
    description = models.TextField()
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    location = models.CharField()
    is_virtual = models.BooleanField(default=False)
    image = models.ImageField(upload_to='events_image/')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    organizer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='events')
    reg_link = models.URLField(blank=True, null=True)
    instagram_link = models.URLField(blank=True, null=True)

    def __str__(self):
        return self.name

@receiver(post_save, sender=Event)
def create_event(sender, instance, created, **kwargs):
    if created:
        # Get or create the organizer role
        organizer_role, created = Roles.objects.get_or_create(name='organizer')
        # Add the organizer role to the user if they don't already have it
        UserRole.objects.get_or_create(user=instance.organizer, role=organizer_role)

class EventInterest(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='interested_events')
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='interests')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'event')

    def __str__(self):
        return f'{self.user.email} is interested in {self.event.name}'
    
