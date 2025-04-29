import random

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.shortcuts import render, redirect
from django.utils import timezone
from .form import SignUpForm
from .models import UserProfile
from .models import WordTuple, Rating, UserWordTuple


@login_required
def intro(request):
    tuple_id = request.session.get('current_rating_tuple_id')
    user_tuple = None

    if tuple_id:
        try:
            user_tuple = UserWordTuple.objects.get(
                id=tuple_id,
                user=request.user,
                completed=False
            )
        except UserWordTuple.DoesNotExist:
            user_tuple = None
            del request.session['current_rating_tuple_id']

    if not user_tuple:
        user_tuples = UserWordTuple.objects.filter(
            user=request.user,
            completed=False
        ).select_related('word_tuple')

        available = [
            ut for ut in user_tuples
            if ut.word_tuple.dimension and not Rating.objects.filter(
                user=request.user,
                word_tuple=ut.word_tuple,
                dimension=ut.word_tuple.dimension
            ).exists()
        ]

        if not available:
            messages.warning(request, '현재 할당된 평가 작업이 없습니다.')
            return redirect('vad_survey:rate_words')

        user_tuple = random.choice(available)
        request.session['current_rating_tuple_id'] = user_tuple.id

    word_tuple = user_tuple.word_tuple
    code = word_tuple.dimension
    name = dict(Rating.DIMENSIONS).get(code, '')

    return render(request, 'vad_survey/intro.html', {
        'dimension': {'code': code, 'name': name}
    })


@login_required
def rate_words(request):
    current_tuple_id = request.session.get('current_rating_tuple_id')
    current_user_tuple = None

    if current_tuple_id:
        try:
            current_user_tuple = UserWordTuple.objects.get(
                id=current_tuple_id,
                user=request.user,
                completed=False
            )
        except UserWordTuple.DoesNotExist:
            if 'current_rating_tuple_id' in request.session:
                del request.session['current_rating_tuple_id']

    if not current_user_tuple:
        user_tuples = UserWordTuple.objects.filter(
            user=request.user,
            completed=False
        ).select_related('word_tuple')

        if not user_tuples.exists():
            return render(request, 'vad_survey/no_assignments.html', {
                'message': '현재 할당된 평가 작업이 없습니다. 관리자에게 문의하세요.'
            })

        available_tuples = []
        for user_tuple in user_tuples:
            word_tuple = user_tuple.word_tuple
            tuple_dimension = word_tuple.dimension
            if not tuple_dimension:
                continue

            already_rated = Rating.objects.filter(
                user=request.user,
                word_tuple=word_tuple,
                dimension=tuple_dimension
            ).exists()

            if not already_rated:
                available_tuples.append(user_tuple)

        if not available_tuples:
            for ut in user_tuples:
                if not ut.word_tuple.dimension:
                    continue
                is_rated = Rating.objects.filter(
                    user=request.user,
                    word_tuple=ut.word_tuple,
                    dimension=ut.word_tuple.dimension
                ).exists()
                if is_rated:
                    ut.completed = True
                    ut.save()

            total_ratings = Rating.objects.filter(user=request.user).count()
            return render(request, 'vad_survey/complete.html', {
                'total_ratings': total_ratings
            })

        current_user_tuple = random.choice(available_tuples)
        request.session['current_rating_tuple_id'] = current_user_tuple.id

    word_tuple = current_user_tuple.word_tuple
    dimension_code = word_tuple.dimension
    dimension_name = dict(Rating.DIMENSIONS)[dimension_code]
    words = list(word_tuple.words.all().only('id', 'text'))

    if request.method == 'POST':
        best_word_id = request.POST.get('best_word')
        worst_word_id = request.POST.get('worst_word')

        if best_word_id and worst_word_id:
            if best_word_id == worst_word_id:
                messages.warning(request, '가장 높은 단어와 가장 낮은 단어는 달라야 합니다.')
            else:
                try:
                    tuple_word_ids = [str(w.id) for w in words]

                    if best_word_id not in tuple_word_ids or worst_word_id not in tuple_word_ids:
                        messages.error(request, f'선택한 단어가 현재 평가 중인 튜플에 속하지 않습니다.')
                    else:
                        existing_rating = Rating.objects.filter(
                            user=request.user,
                            word_tuple=word_tuple,
                            dimension=dimension_code
                        ).exists()

                        if existing_rating:
                            messages.warning(request, '이미 평가한 차원입니다.')
                        else:
                            best_word = next(w for w in words if str(w.id) == best_word_id)
                            worst_word = next(w for w in words if str(w.id) == worst_word_id)

                            Rating.objects.create(
                                user=request.user,
                                word_tuple=word_tuple,
                                dimension=dimension_code,
                                best_word=best_word,
                                worst_word=worst_word,
                                start_time=timezone.now()
                            )

                            current_user_tuple.completed = True
                            current_user_tuple.save()

                            if 'current_rating_tuple_id' in request.session:
                                del request.session['current_rating_tuple_id']

                            messages.success(request, '평가가 성공적으로 저장되었습니다.')

                            # ✅ 여기서 완료되었는지 확인하고 완료 화면으로 이동
                            remaining_assignments = UserWordTuple.objects.filter(
                                user=request.user,
                                completed=False
                            )
                            if not remaining_assignments.exists():
                                return render(request, 'vad_survey/complete.html', {
                                    'total_ratings': Rating.objects.filter(user=request.user).count()
                                })

                            return redirect('vad_survey:rate_words')

                except ValidationError as e:
                    error_msg = str(e.message_dict) if hasattr(e, 'message_dict') else str(e)
                    messages.error(request, f'평가 저장 중 오류: {error_msg}')
                except Exception as e:
                    messages.error(request, f'예상치 못한 오류 발생: {str(e)}')

    current_dimension = {
        'code': dimension_code,
        'name': dimension_name
    }

    return render(request, 'vad_survey/rate.html', {
        'words': words,
        'dimension': current_dimension,
        'word_tuple': word_tuple,
        'user_tuple_id': current_user_tuple.id,
        'ratings_left': UserWordTuple.objects.filter(
            user=request.user,
            completed=False
        ).count(),
        'total_ratings': UserWordTuple.objects.filter(user=request.user).count(),
        'completed_ratings': UserWordTuple.objects.filter(
            user=request.user,
            completed=True
        ).count(),
        'progress_rate': UserWordTuple.objects.filter(
            user=request.user,
            completed=True
        ).count() / UserWordTuple.objects.filter(user=request.user).count() * 100
    })


def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.username = str(form.cleaned_data.get('username'))
            user.save()

            if not UserProfile.objects.filter(user=user).exists():
                UserProfile.objects.create(
                    user=user,
                    sona_id=user.username,
                    age=form.cleaned_data.get('age'),
                    gender=form.cleaned_data.get('gender')
                )
            else:
                messages.error(request, "이미 해당 유저 프로필이 존재합니다.")
                return render(request, 'registration/signup.html', {'form': form})

            login(request, user)
            messages.success(request, '회원가입이 완료되었습니다.')
            return redirect('vad_survey:intro')
    else:
        form = SignUpForm()
    return render(request, 'registration/signup.html', {'form': form})
