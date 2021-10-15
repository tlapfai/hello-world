from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django import forms
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt, csrf_protect
import json

from .models import User, Post


class PostForm(forms.Form):
    content = forms.CharField(widget=forms.Textarea(attrs={'rows':'4', 'cols':'150', 'id':'input-area'}), label='New Post', required=True)

#@login_required
def index(request):
    return render(request, "network/index.html", {'post_form': PostForm().as_table()})


def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "network/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "network/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "network/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "network/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "network/register.html")


@login_required
def load_posts(request, scope):

    # Filter emails returned based on mailbox
    if scope == 'all':
        posts = Post.objects.all()
    elif scope == "following":
        posts = Post.objects.filter(user__in=request.user.following.all())
    else:
        return JsonResponse({"error": "Invalid mailbox."}, status=400)

    # Return emails in reverse chronologial order
    posts = posts.order_by("-timestamp").all()
    return JsonResponse([post.serialize(request.user) for post in posts], safe=False)


@login_required
@csrf_exempt
def new_post(request):

    # Composing a new email must be via POST
    if request.method != "POST":
        return JsonResponse({"error": "POST request required."}, status=400)

    # Get contents of email
    data = json.loads(request.body)
    content = data.get("body", "")
    post = Post(user=request.user, content=content)
    post.save()
    return JsonResponse({"message": "Posted successfully."}, status=201)

@login_required
@csrf_exempt
def like_post(request, post_id):
    if request.method == "GET":
        post = Post.objects.get(pk=post_id)
        user = request.user
        if post.liked(user):
            post.likers.remove(user)
        else:
            post.likers.add(user)

        return HttpResponse(status=204)
    

@login_required
@csrf_exempt
def follow_user(request, user):
    if request.method == "GET":
        target_user = User.objects.get(username=user)
        iam = request.user
        if target_user ==  iam:
            pass
        else:
            if target_user.followed_by(iam):
                target_user.followers.remove(iam)
                return JsonResponse({"message": f"You unfollowed {target_user.username}."}, status=204)
            else:
                target_user.followers.add(iam)
                return JsonResponse({"message": f"You unfollowed {target_user.username}."}, status=204)
    else:
        return HttpResponse(status=403)

        
