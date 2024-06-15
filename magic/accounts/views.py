from datetime import date, datetime
import logging

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.db import IntegrityError, transaction
from django.db.models import Sum
from django.http import HttpResponse, JsonResponse, HttpRequest
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse

from django.utils.dateparse import parse_date
from django.utils.safestring import mark_safe
from django.views.decorators.http import require_http_methods

from .forms import LoginForm, MealForm, RegistrationForm, UserProfileForm, UserForm
from .models import Meal, UserProfile, RelatedData
from django.http import HttpResponseRedirect

logger = logging.getLogger('accounts')
# 最初のページ
def index(request):
    return render(request, 'index.html')
# 新規登録画面

def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            try:
                user = form.save()
                # UserProfileが確実に作成されることを確認
                UserProfile.objects.get_or_create(user=user)
                username = form.cleaned_data.get('username')
                raw_password = form.cleaned_data.get('password1')
                user = authenticate(username=username, password=raw_password)
                if user is not None:
                    login(request, user)
                messages.success(request, '登録が完了しました。')
                return redirect('registration_complete')
            except IntegrityError as e:
                logger.error(f'IntegrityError: {e}')
                messages.error(request, 'ユーザー登録中にエラーが発生しました。')
        else:
            messages.error(request, '入力に問題があります。詳細を確認してください。')
            logger.debug(form.errors)
    else:
        form = RegistrationForm()
    return render(request, 'registration/register.html', {'form': form})

def registration_complete(request):
    return render(request, 'registration/registration_complete.html')

# ホーム画面
@login_required
def home(request):
    # ログインしている場合はユーザー情報を取得
    user_info = request.user
    meals = Meal.objects.all()

    # 最新の食事データを取得
    latest_meals = Meal.objects.filter(user=request.user).order_by('-eaten_at')[:5]

    context = {
        'user_info': user_info,
        'latest_meals': latest_meals,
    }
    return render(request, 'home.html', context)
# カロリー計算式
def calculate_target_calories(age, gender):
    if gender == 'M':
        if age <= 30:
            return 2400
        elif age <= 50:
            return 2200
        else:
            return 2000
    else:  # 女性の場合
        if age <= 30:
            return 2000
        elif age <= 50:
            return 1800
        else:
            return 1600

# アカウント削除確認画面
@login_required
def delete_confirmation(request):
    if request.method == 'POST':
        return redirect('delete_account')
    return render(request, 'delete_confirmation.html')


# アカウント削除
@login_required
def delete_account(request):
    if request.method == 'POST':
        return redirect('delete_in_progress')
    else:
        return redirect('delete_confirmation')
# アカウント削除進行画面
@login_required
def delete_in_progress(request):
    user = request.user

    # ユーザーの削除前に関連する UserProfile を削除
    try:
        if hasattr(user, 'userprofile'):
            user.userprofile.delete()
            logger.debug(f'UserProfile deleted for user: {user.username}')
    except Exception as e:
        logger.error(f'Error deleting UserProfile for user: {user.username}. Error: {e}')

    user.delete()
    logger.debug(f'User deleted: {user.username}')
    request.session['account_deleted'] = True
    redirect_url = reverse('delete_completed')
    return render(request, 'delete_in_progress.html', {
        'redirect_url': mark_safe(redirect_url)
    })
# アカウント削除完了画面
def delete_completed(request):
    if request.session.pop('account_deleted', None):
        return render(request, 'delete_completed.html')
    else:
        return redirect('home')
 # ログアウト画面
@login_required
def user_logout(request):
    logout(request)
    return redirect('logout_complete')

def logout_complete(request):
    # 'log_out.html'を指定してレンダリング
    return render(request, 'logout_complete.html')

# ログイン画面
def user_login(request):
    if request.method == 'POST':
        form = LoginForm(data=request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user:
                login(request, user)
                return redirect('home')  # ログイン後にホームページにリダイレクト
            else:
                # 認証失敗時のメッセージを追加
                return render(request, 'login.html', {'form': form, 'error': 'ユーザー名またはパスワードが間違っています。'})
        else:
            # フォームが無効の場合の処理
            return render(request, 'login.html', {'form': form, 'error': '入力内容に誤りがあります。'})
    else:
        form = LoginForm()
        return render(request, 'login.html', {'form': form})


# 食事追加画面
@login_required
def add_meal(request):
    user_profile = UserProfile.objects.get(user=request.user)
    target_calories = calculate_target_calories(user_profile.age, user_profile.gender)

    today = date.today()  # 今日の日付を取得
    selected_date = today  # デフォルト日付を今日に設定

    if request.method == 'POST':
        meal_form = MealForm(request.POST)
        if meal_form.is_valid():
            meal = meal_form.save(commit=False)
            meal.user = request.user
            selected_date = meal_form.cleaned_data.get('date', today)  # フォームから日付を取得
            meal.date = selected_date
            try:
                with transaction.atomic():
                    meal.save()
                    # 選択された日付での食事を取得してカロリーを計算
                    meals_on_date = Meal.objects.filter(date=selected_date, user=request.user)
                    total_calories = sum(meal.calories for meal in meals_on_date)

                    if total_calories > target_calories:
                        return redirect('calorie_warning')
                    else:
                        return redirect('success')
            except Exception as e:
                messages.error(request, f'食事の保存中にエラーが発生しました: {e}')
        else:
            messages.error(request, 'フォームの送信に失敗しました。以下のエラーを修正してください')
    else:
        meal_form = MealForm(initial={'date': today})  # 初期値として今日の日付を設定

    meals_on_date = Meal.objects.filter(date=selected_date, user=request.user)
    total_calories = sum(meal.calories for meal in meals_on_date)

    context = {
        'meal_form': meal_form,
        'target_calories': target_calories,
        'total_calories': total_calories,
        'selected_date': selected_date
    }
    return render(request, 'add_meal.html', context)


# カロリー警告画面
@login_required
def calorie_warning(request):
    return render(request, 'calorie_warning.html')
# 食事追加成功画面
@login_required
def success(request):
    return render(request, 'success.html')

# プロフィール編集画面
@login_required
def edit_profile(request):
    user = request.user
    profile, created = UserProfile.objects.get_or_create(user=user)

    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            return redirect('update_profile')
    else:
        form = UserProfileForm(instance=profile)

    # ユーザー情報、メールアドレス、フォームをコンテキストにまとめて渡す
    context = {
        'form': form,
        'username': user.username,
        'user_profile': profile,
        'email': user.email,  # メールアドレスを追加
    }
    return render(request, 'edit_profile.html', context)

# プロフィール更新
@login_required
def update_profile(request):
    user = request.user
    user_profile = user.profile  # related_name='profile' で設定しているため

    if request.method == 'POST':
        user_form = UserForm(request.POST, instance=user)
        profile_form = UserProfileForm(request.POST, instance=user_profile)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            return redirect('update-complete')
    else:
        user_form = UserForm(instance=user)
        profile_form = UserProfileForm(instance=user_profile)

    return render(request, 'update_profile.html', {
        'user_form': user_form,
        'profile_form': profile_form,
    })

# パスワード変更画面
@login_required
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # セッションの更新
            messages.success(request, 'パスワードが正常に更新されました。')
            return redirect('password_changed')  # 成功時のリダイレクト先
        else:
            messages.error(request, 'エラーが発生しました。パスワード変更に失敗しました。')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'change_password.html', {'form': form})
# パスワード変更完了画面
@login_required
def password_changed(request):
    return render(request, 'password_changed.html')


# プロフィール更新完了画面
@login_required
def update_complete(request):
    return render(request, 'update_complete.html')

def selected_date(request):
    # 選択された日付を取得する
    selected_date = request.GET.get('selected_date')
    # 選択された日付をコンテキストに渡してテンプレートをレンダリングする
    return render(request, 'selected_date.html', {'selected_date': selected_date})

# 食事編集画面
@login_required
def edit_meal(request, meal_id):
    try:
        meal = Meal.objects.get(id=meal_id, user=request.user)
        request.session['updated_meal_id'] = meal.id
        form = MealForm(instance=meal)
        return render(request, 'edit_meal.html', {'form': form, 'meal': meal})
    except Meal.DoesNotExist:
        messages.error(request, "該当する食事が見つかりません。")
        return redirect('home')
# 食事編集完了画面
@login_required
def edit_complete(request):
    meal_id = request.session.get('updated_meal_id')
    if not meal_id:
        messages.error(request, "更新された食事情報の取得に失敗しました。")
        return redirect('home')

    try:
        meal = Meal.objects.get(id=meal_id, user=request.user)
    except Meal.DoesNotExist:
        messages.error(request, "該当する食事が見つかりません。")
        return redirect('home')

    if request.method == 'POST':
        form = MealForm(request.POST, instance=meal)
        if form.is_valid():
            form.save()
            meal.refresh_from_db()  # データベースから最新のデータを取得
            messages.success(request, "食事情報が更新されました。")

            # 関連データの更新
            related_data_qs = RelatedData.objects.filter(meal=meal)
            for related_data in related_data_qs:
                related_data.additional_info = '更新された情報'
                related_data.save()

            # redirect_url の生成
            redirect_url = reverse('enter_meal_data') + f'?selected_date={meal.date.isoformat()}'

            # 完了画面をレンダリングし、履歴画面へのリンクを提供
            return render(request, 'edit_complete.html', {
                'new_data': {
                    'meal_type': meal.meal_type,
                    'food_name': meal.food_name,
                    'calories': meal.calories,
                    'eaten_at': meal.eaten_at,
                    'date': meal.date
                },
                'meal': meal,
                'redirect_url': redirect_url
            })
        else:
            messages.error(request, "フォームの入力にエラーがあります。")
            return render(request, 'edit_meal.html', {'form': form, 'meal': meal})
    else:
        form = MealForm(instance=meal)
        return render(request, 'edit_meal.html', {'meal': meal, 'form': form})

# 食事削除確認
@login_required
def confirm_delete_meal(request, meal_id):
    # meal_idに基づいてMealオブジェクトを取得し、存在しない場合はエラーメッセージを表示しリダイレクトする
    meal = get_object_or_404(Meal, id=meal_id, user=request.user)

    return render(request, 'confirm_delete_meal.html', {'meal': meal})
# 食事削除画面
@login_required
def delete_meal(request, meal_id):
    meal = get_object_or_404(Meal, id=meal_id, user=request.user)
    if request.method == 'POST':
        meal.delete()
        messages.success(request, "食事データが削除されました。")
        return redirect('delete_meal_complete')  # 削除完了画面にリダイレクト
    return redirect('confirm_delete_meal', meal_id=meal_id)

# 食事削除完了画面
@login_required
def delete_meal_complete(request):
    return render(request, 'delete_meal_complete.html')

# 追加したデータを確認する画面
@login_required
def enter_meal_data(request):
    selected_date_str = request.GET.get('selected_date', None)
    selected_date = parse_date(selected_date_str) if selected_date_str else None

    if request.method == 'POST':
        form = MealForm(request.POST)
        if form.is_valid():
            meal = form.save(commit=False)
            meal.date = selected_date
            meal.user = request.user
            meal.save()
            return redirect('home')
    else:
        form = MealForm(initial={'date': selected_date})

    meals = Meal.objects.filter(date=selected_date, user=request.user) if selected_date else []
    total_calories = sum(meal.calories for meal in meals)  # 合計カロリーを計算


    return render(request, 'enter_meal_data.html', {
        'selected_date': selected_date,
        'form': form,
        'meals': meals,
        'total_calories': total_calories  # 合計カロリーをテンプレートに渡す
    })



@require_http_methods(["POST"])
def submit_meal_data(request: HttpRequest) -> HttpResponse:
    if request.method == 'POST':
        meal_type = request.POST.get('meal_type')
        date = request.POST.get('date')
        food_name = request.POST.get('food_name')
        calories = request.POST.get('calories')

        try:
            meal = Meal(
                meal_type=meal_type,
                date=date,
                food_name=food_name,
                calories=calories,
            )
            meal.save()
            messages.success(request, '食事情報が正常に保存されました。')
            return redirect('home')
        except Exception as e:
            messages.error(request, '保存中にエラーが発生しました。')
            return render(request, 'meal_form.html', {'error': str(e)})

    return HttpResponse("Invalid request", status=400)


# カロリー超過場合カレンダーに色をつける
def calories_by_year(request, year):
    start_date = parse_date(f"{year}-01-01")
    end_date = parse_date(f"{year}-12-31")
    meals = Meal.objects.filter(date__range=(start_date, end_date), user=request.user)

    # ユーザープロファイルから年齢と性別を直接取得
    user_profile = UserProfile.objects.get(user=request.user)
    age = user_profile.age  # 年齢フィールドの名前は仮定
    gender = user_profile.gender  # 性別

    required_calories = calculate_target_calories(age, gender)

    calories_data = meals.values('date').annotate(total_calories=Sum('calories')).order_by('date')

    response_data = {
        meal['date'].strftime('%Y-%m-%d'): {
            'calories': meal['total_calories'],
            'requiredCalories': required_calories
        } for meal in calories_data
    }

    return JsonResponse(response_data)



