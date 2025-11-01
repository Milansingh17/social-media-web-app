from django.urls import path
from .import views
from mainproject import settings
from django.conf.urls.static import static
from django.contrib.auth.views import LoginView,LogoutView
urlpatterns = [
  path('', views.home, name='home'), 
  path('signup/',views.signup),
  path('loginn/', views.loginn, name='loginn'),
  path('logout/', views.logout_view, name='logout'),

  path('upload', views.upload, name='upload'),
  path('like-post/<str:id>/', views.likes, name='like-post'),
  path('explore/', views.explore ,name= 'explore'),
  path('profile/<str:username>/', views.profile, name='profile'),

  path('delete/<str:id>/', views.delete, name='delete'),
  path('search/', views.search_results, name='search_results'),
  path('follow/', views.follow, name='follow'),

  path('#/<str:id>/', views.home_post),
  
  
  
  path('lobby/', views.lobby, name='lobby'),                   # Lobby page
  path('room/', views.room, name='room'),                # Room page
  path('get_token/', views.getToken, name='getToken'),   # Get Agora token
  path('create_member/', views.createMember, name='createMember'),  # Create member
  path('get_member/', views.getMember, name='getMember'),          # Get member info
  path('delete_member/', views.deleteMember, name='deleteMember')
]
