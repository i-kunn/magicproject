from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, UserChangeForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from .models import Meal, Food, UserProfile
from django.forms import inlineformset_factory

class RegistrationForm(UserCreationForm):
    GENDER_CHOICES = (
        ('M', '男性'),
        ('F', '女性'),
    )
    username = forms.CharField(max_length=150, label="ユーザー名")
    gender = forms.ChoiceField(choices=GENDER_CHOICES, label="性別")
    age = forms.IntegerField(label="年齢", min_value=0)  # min_valueを設定して、マイナスの値を禁止
    email = forms.EmailField(label="メールアドレス")
    password1 = forms.CharField(label="パスワード", widget=forms.PasswordInput)
    password2 = forms.CharField(label="パスワード確認", widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['username', 'email', 'gender', 'age', 'password1', 'password2']

    def clean_age(self):
        age = self.cleaned_data.get('age')
        if age is not None and age < 0:
            raise forms.ValidationError("年齢は0歳以上でなければなりません。")
        return age

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError('同じユーザー名が既に登録済みです。')
        return username

    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
            # UserProfileはpost_saveシグナルで作成される
            UserProfile.objects.filter(user=user).update(
                age=self.cleaned_data['age'],
                gender=self.cleaned_data['gender']
            )
        return user

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['age', 'gender']
        labels = {
            'age': '年齢',
            'gender': '性別',
        }

    def clean_age(self):
        age = self.cleaned_data.get('age')
        if age is not None and age < 0:
            raise forms.ValidationError("年齢は0歳以上でなければなりません。")
        return age


# ログイン画面
class LoginForm(AuthenticationForm):
    class Meta:
        fields = ['username', 'password']

# User の情報を編集するためのフォーム
class UserForm(forms.ModelForm):
    email = forms.EmailField(
        required=True,
        error_messages={
            'required': 'メールアドレスを入力してください。',
        },
        label='メールアドレス'  # ラベルを日本語に変更
    )
    class Meta:
        model = User
        fields = ['username', 'email']
        labels = {
            'username': 'ユーザー名',
            'email': 'メールアドレス',
        }

class MealForm(forms.ModelForm):
    class Meta:
        model = Meal
        fields = ['meal_type', 'food_name', 'calories', 'eaten_at']
        widgets = {
            'meal_type': forms.Select(attrs={'title': '食事の種類'}),
            'date': forms.DateInput(attrs={'type': 'date', 'title': '日付', 'placeholder': '日付を選択'}),
            'food_name': forms.TextInput(attrs={'placeholder': '食べた食品の名前を入力', 'title': '食事内容'}),
            'calories': forms.NumberInput(attrs={'title': 'カロリー', 'placeholder': 'カロリーを入力'}),
            'eaten_at': forms.TimeInput(attrs={'type': 'time', 'title': '摂取時間', 'placeholder': '食べた時間を入力'})
        }



class MealEditForm(forms.ModelForm):
    class Meta:
        model = Meal
        fields = ['meal_type', 'date', 'food_name', 'calories']  # 編集可能なフィールドを指定
        labels = {
            'meal_type': '食事の種類',
            'food_name': '食事内容',  # ここでフィールドのラベルを変更
            'calories': 'カロリー',
            'date': '日付',

        }
FoodFormSet = inlineformset_factory(Meal, Food, fields=('name',), extra=1, can_delete=True)

