from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout as auth_logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from .models import Profile, Post, Followers, LikePost,RoomMember



from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import random
import time

# Assuming you are using Agora's RtcTokenBuilder
from agora_token_builder import RtcTokenBuilder  

# Your RoomMember model
from .models import RoomMember



# -----------------------------
# SIGNUP
# -----------------------------
def signup(request):
    if request.method == 'POST':
        fnm = request.POST.get('fnm')
        emailid = request.POST.get('emailid')
        password = request.POST.get('password')

        try:
            # Create the user
            my_user = User.objects.create_user(username=fnm, email=emailid, password=password)
            my_user.save()

            # Create a profile for this user
            Profile.objects.create(user=my_user)

            # Log in the new user
            login(request, my_user)
            return redirect('home')

        except Exception as e:
            invalid = f"User already exists or error: {e}"
            return render(request, 'signup.html', {'invalid': invalid})

    return render(request, 'signup.html')


# -----------------------------
# LOGIN
# -----------------------------
def loginn(request):
    if request.method == 'POST':
        fnm = request.POST.get('fnm')
        pwd = request.POST.get('pwd')

        user = authenticate(request, username=fnm, password=pwd)
        if user is not None:
            login(request, user)
            return redirect('home')

        invalid = "Invalid Credentials"
        return render(request, 'loginn.html', {'invalid': invalid})

    return render(request, 'loginn.html')


# -----------------------------
# LOGOUT
# -----------------------------
def logout_view(request):
    auth_logout(request)
    return redirect('loginn') 

# -----------------------------
# HOME PAGE (feed)
@login_required
def home(request):
    # Get IDs of users the current user is following
    following_user_ids = Followers.objects.filter(follower=request.user).values_list('followed_id', flat=True)

    # Get posts from the current user and followed users
    posts = Post.objects.filter(Q(user=request.user) | Q(user__id__in=following_user_ids)).order_by('-created_at')

    # Safely get user profile
    try:
        profile = Profile.objects.get(user=request.user)
    except Profile.DoesNotExist:
        profile = Profile.objects.create(user=request.user)

    context = {
        'posts': posts,
        'profile': profile
    }
    return render(request, 'main.html', context)

# -----------------------------
# UPLOAD POST
# -----------------------------
@login_required
def upload(request):
    if request.method == 'POST':
        user = request.user
        image = request.FILES.get('image_upload')
        caption = request.POST.get('caption', '')

        if image:  # ensure file is uploaded
            Post.objects.create(user=user, image=image, caption=caption)

        return redirect('home')

    return redirect('home')


# -----------------------------
# LIKE POST
# -----------------------------
@login_required
def likes(request, id):
    post = get_object_or_404(Post, id=id)
    user = request.user  # this is the User object

    # check if this user already liked the post
    like_filter = LikePost.objects.filter(post=post, user=user).first()

    if like_filter is None:
        # create a new like
        LikePost.objects.create(post=post, user=user)
        post.no_of_likes += 1
    else:
        # remove like
        like_filter.delete()
        post.no_of_likes -= 1

    post.save()
    return redirect(f'/#{id}')


# -----------------------------
# EXPLORE
# -----------------------------
@login_required
def explore(request):
    posts = Post.objects.all().order_by('-created_at')
    profile = Profile.objects.get(user=request.user)

    context = {
        'posts': posts,
        'profile': profile
    }

    return render(request, 'explore.html', context)


@login_required
def profile(request, username):
    user_object = User.objects.get(username=username)
    profile = Profile.objects.get(user=request.user)
    user_profile = Profile.objects.get(user=user_object)

    user_posts = Post.objects.filter(user=user_object).order_by('-created_at')
    user_post_length = user_posts.count()

    follower = request.user
    followed = user_object

    # follow/unfollow logic
    if Followers.objects.filter(follower=follower, followed=followed).exists():
        follow_unfollow = 'Unfollow'
    else:
        follow_unfollow = 'Follow'

    # counts
    user_followers = Followers.objects.filter(followed=followed).count()
    user_following = Followers.objects.filter(follower=followed).count()

    context = {
        'user_object': user_object,
        'user_profile': user_profile,
        'user_posts': user_posts,
        'user_post_length': user_post_length,
        'profile': profile,
        'follow_unfollow': follow_unfollow,
        'user_followers': user_followers,
        'user_following': user_following,
    }

    # Update profile info if owner edits their own profile
    if request.user.username == username and request.method == 'POST':
        if request.FILES.get('image') is not None:
            user_profile.profileimg = request.FILES['image']
        user_profile.bio = request.POST.get('bio', user_profile.bio)
        user_profile.location = request.POST.get('location', user_profile.location)
        user_profile.save()
        return redirect(f'/profile/{username}/')

    return render(request, 'profile.html', context)

# DELETE POST
# -----------------------------
@login_required
def delete(request, id):
    post = get_object_or_404(Post, id=id, user=request.user)
    post.delete()
    return redirect(f'/profile/{request.user.username}')


# -----------------------------
# SEARCH RESULTS
# -----------------------------
@login_required
def search_results(request):
    query = request.GET.get('q', '')
    users = Profile.objects.filter(user__username__icontains=query)
    posts = Post.objects.filter(caption__icontains=query)

    context = {
        'query': query,
        'users': users,
        'posts': posts
    }
    return render(request, 'search_user.html', context)

def home_post(request,id):
    post = Post.objects.get(id=id)
    profile = Profile.objects.get(user=request.user)
    context ={
        'post':post,
        'profile':profile
    }
    return render(request,'main.html',context)
# -----------------------------
# FOLLOW / UNFOLLOW
# -----------------------------
@login_required
def follow(request):
    if request.method == 'POST':
        followed_username = request.POST['user']  # the person being followed
        follower = request.user                   # the logged-in user

        try:
            followed = User.objects.get(username=followed_username)
        except User.DoesNotExist:
            return redirect('/')  # or handle the error gracefully

        follow_instance = Followers.objects.filter(follower=follower, followed=followed).first()

        if follow_instance:
            # Already following — so unfollow
            follow_instance.delete()
        else:
            # Not following yet — create a new follow record
            Followers.objects.create(follower=follower, followed=followed)

        return redirect(f'/profile/{followed_username}/')

    return redirect('/')




def lobby(request):
    return render(request,'lobby.html')


def room(request):
    return render(request,'room.html')

def getToken(request):
    appId = "b244d9283b894f628d97c870c1a8b049"
    appCertificate = "2ea76a95d21f4e83adda3543db75f08d"
    channelName = request.GET.get('channel')
    uid = random.randint(1, 230)
    expirationTimeInSeconds = 3600
    currentTimeStamp = int(time.time())
    privilegeExpiredTs = currentTimeStamp + expirationTimeInSeconds
    role = 1

    token = RtcTokenBuilder.buildTokenWithUid(appId, appCertificate, channelName, uid, role, privilegeExpiredTs)

    return JsonResponse({'token': token, 'uid': uid}, safe=False)


@csrf_exempt
def createMember(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        member, created = RoomMember.objects.get_or_create(   # ✅ fixed here
            name=data['name'],
            uid=data['UID'],
            room_name=data['room_name']
        )
        return JsonResponse({'name': member.name}, safe=False)
    else:
        return JsonResponse({'error': 'Invalid request method'}, status=400)

@csrf_exempt
def getMember(request):
    uid = request.GET.get('UID')
    room_name = request.GET.get('room_name')

    member = RoomMember.objects.get(
        uid=uid,
        room_name=room_name
    )
    name = member.name
    return JsonResponse({'name':member.name},safe=False)

@csrf_exempt
def deleteMember(request):
    data = json.loads(request.body)
    member = RoomMember.objects.get(
        name=data['name'],
        uid=data['UID'],
        room_name=data['room_name']
    )
    member.delete()
    return JsonResponse('Member deleted', safe=False)
