from django.urls import path
from django.contrib.auth import views as auth_views
from . import views




urlpatterns = [
    path('', views.index, name='index'),
    path('register/', views.register, name='register'),
    path('registration_complete/', views.registration_complete, name='registration_complete'),
    path('home/', views.home, name='home'),
    path('edit_profile/', views.edit_profile, name='edit_profile'),
    path('add_meal/', views.add_meal, name='add_meal'),
    path('edit-meal/', views.edit_meal, name='edit_meal'),
    path('delete_completed/', views.delete_completed, name='delete_completed'),
    path('delete_in_progress/', views.delete_in_progress, name='delete_in_progress'),
    path('delete_confirmation/', views.delete_confirmation, name='delete_confirmation'),
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html', next_page='home'), name='login'),
    path('logout/', views.user_logout, name='logout'), 
    path('selected_date/', views.selected_date, name='selected_date'),
    path('enter_meal_data/', views.enter_meal_data, name='enter_meal_data'),
    path('success/', views.success, name='success'),
    path('login/', views.user_login, name='user_login'),  
    path('delete_account/', views.delete_account, name='delete_account'),
    path('update_profile/', views.update_profile, name='update_profile'),
    path('change-password/', views.change_password, name='change_password'),
    path('update-complete/', views.update_complete, name='update-complete'),
    path('edit-complete/', views.edit_complete, name='edit-complete'),
    path('calorie_warning/', views.calorie_warning, name='calorie_warning'),
    path('logout_complete/', views.logout_complete, name='logout_complete'),
    path('submit_meal_data/', views.submit_meal_data, name='submit_meal_data'),
    path('edit-meal/<int:meal_id>/', views.edit_meal, name='edit_meal'),
    path('api/calories/<int:year>/', views.calories_by_year, name='calories_by_year'),
    path('password_changed/', views.password_changed, name='password_changed'),
    path('meal/confirm-delete/<int:meal_id>/', views.confirm_delete_meal, name='confirm_delete_meal'),
    path('meal/delete/<int:meal_id>/', views.delete_meal, name='delete_meal'),
    path('meal/delete/complete/', views.delete_meal_complete, name='delete_meal_complete'),
]

