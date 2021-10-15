from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    followers = models.ManyToManyField("User", blank=True, related_name="following")
    profile = models.TextField()
    def followed_by(self, user):
        return (user in self.followers.all())

class Post(models.Model):
    user = models.ForeignKey("User", on_delete=models.CASCADE, related_name="posts")
    content = models.TextField(blank=False)
    timestamp = models.DateTimeField(auto_now_add=True)
    #likes = models.PositiveIntegerField(default=0)
    likers = models.ManyToManyField("User", related_name="like_posts")
    def __str__(self):
        return self.user.username + ': ' + self.content
    
    def liked(self, user):
        return (user in self.likers.all())

    def serialize(self, user):
        return {
            "id": self.id,
            "user": self.user.username,
            "content": self.content,
            "timestamp": self.timestamp.strftime("%b %d %Y, %I:%M %p"),
            "likes": len(self.likers.all()),
            "liked": self.liked(user)
        }


