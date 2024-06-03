from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.conf import settings
# プロフィール
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    age = models.PositiveIntegerField(default=0,verbose_name='年齢')
    gender = models.CharField(max_length=1, choices=[('M', '男性'), ('F', '女性')], verbose_name='性別')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self):
        return f"{self.user.username} - {self.gender} - Age: {self.age}"

# 食事
class Meal(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='ユーザー')
    food_name = models.CharField(max_length=100, verbose_name='食事内容')
    calories = models.IntegerField(verbose_name='カロリー')
    date = models.DateField(verbose_name='日付')
    eaten_at = models.TimeField(verbose_name='摂取時間')
    id = models.AutoField(primary_key=True)
    MEAL_TYPES = [
        ('breakfast', '朝食'),
        ('lunch', '昼食'),
        ('dinner', '夕食'),
    ]
    meal_type = models.CharField(max_length=10, choices=MEAL_TYPES, verbose_name='食事の種類')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.food_name} - {self.calories} kcal "

    class Meta:
        ordering = ['-date', '-eaten_at']
        verbose_name = '食事'
        verbose_name_plural = '食事'



class Food(models.Model):
    meal = models.ForeignKey(Meal, on_delete=models.CASCADE, verbose_name='食事')
    name = models.CharField(max_length=100, verbose_name='食事内容')


class TotalCalories(models.Model):
    total = models.IntegerField(default=0)  # 合計カロリーを表すフィールド

    def __str__(self):
        return f"Total Calories: {self.total}"

class RelatedData(models.Model):
    meal = models.ForeignKey(Meal, on_delete=models.CASCADE, related_name='related_data')
    additional_info = models.CharField(max_length=255)

    def __str__(self):
        return self.additional_info











