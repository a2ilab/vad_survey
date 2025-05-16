import random

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.shortcuts import render, redirect
from django.utils import timezone
from django.utils.safestring import mark_safe

from .form import SignUpForm
from .models import UserProfile
from .models import WordTuple, Rating, UserWordTuple  # UserWordTuple 추가


@login_required
# 안내 페이지 추가, 수정
def intro(request):
    """
    실험 시작 전 간략 안내 페이지를 보여주는 뷰.
    """

    current_tuple_id = request.session.get('current_rating_tuple_id')
    current_user_tuple = None

    if current_tuple_id:
        # 세션에 저장된 튜플이 있으면 해당 튜플 가져오기
        try:
            current_user_tuple = UserWordTuple.objects.get(
                id=current_tuple_id,
                user=request.user,
                completed=False
            )
        except UserWordTuple.DoesNotExist:
            # 세션에 저장된 튜플이 없거나 이미 완료된 경우 세션에서 제거
            if 'current_rating_tuple_id' in request.session:
                del request.session['current_rating_tuple_id']

    # 2. 사용자에게 할당된 미완료 튜플 가져오기 (현재 평가 중인 튜플이 없는 경우)
    if not current_user_tuple:
        user_tuples = UserWordTuple.objects.filter(
            user=request.user,
            completed=False
        ).select_related('word_tuple')

        # 평가할 수 있는 튜플 찾기
        available_tuples = []
        for user_tuple in user_tuples:
            word_tuple = user_tuple.word_tuple

            # 해당 튜플의 dimension 확인 (V, A, D 중 하나)
            tuple_dimension = word_tuple.dimension

            # dimension이 설정되지 않은 경우 건너뛰기
            if not tuple_dimension:
                continue

            # 이미 평가된 차원인지 확인
            already_rated = Rating.objects.filter(
                user=request.user,
                word_tuple=word_tuple,
                dimension=tuple_dimension
            ).exists()

            # 아직 평가되지 않은 경우에만 추가
            if not already_rated:
                available_tuples.append(user_tuple)

        # 평가할 튜플이 없는 경우
        if not available_tuples:
            # 모든 작업이 완료되었거나, 모든 할당된 튜플의 차원이 이미 평가된 경우
            for ut in user_tuples:
                # 차원이 정의된 튜플만 확인
                if not ut.word_tuple.dimension:
                    continue

                # 이미 평가되었는지 확인
                is_rated = Rating.objects.filter(
                    user=request.user,
                    word_tuple=ut.word_tuple,
                    dimension=ut.word_tuple.dimension
                ).exists()

                # 평가되었다면 완료 처리
                if is_rated:
                    ut.completed = True
                    ut.save()

            total_ratings = Rating.objects.filter(user=request.user).count()
            return render(request, 'vad_survey/complete.html', {
                'total_ratings': total_ratings
            })

        # 무작위로 평가할 튜플 선택
        current_user_tuple = random.choice(available_tuples)

        # 세션에 현재 평가 중인 튜플 저장
        request.session['current_rating_tuple_id'] = current_user_tuple.id

    # 3. 현재 평가할 튜플 및 차원 설정
    word_tuple = current_user_tuple.word_tuple
    dimension_code = word_tuple.dimension
    dimension_name = dict(Rating.DIMENSIONS)[dimension_code]


    return render(request, 'vad_survey/intro.html', {
        'dimension': {'code': dimension_code, 'name': dimension_name},
        'message_valence' : {'valence_pos': 
                             mark_safe('''<p>아래 4개의 단어 중 <span class="font-bold text-red-500">[ 행복 ], [ 기쁨 ], [ 긍정적인 것 ], [ 만족 ], [ 평온 ], [ 소망 ]</span>과 가장 관련성이 <span class="font-bold ">높은</span> 단어는 무엇인가요? <br><span class="font-bold text-red-500">또는</span> <span class="font-bold text-red-500"> [ 불행 ], [ 성가심 ], [ 부정적인 것 ],[ 불만 ], [ 우울감 ], [ 절망 ] </span>과 가장 관련성이 <span class="font-bold ">낮은</span> 단어는 무엇인가요?'''),
                             'valence_neg': 
                             mark_safe('''<p>아래 4개의 단어 중 <span class="font-bold text-red-500">[ 불행 ], [ 성가심 ], [ 부정적인 것 ],[ 불만 ], [ 우울감 ], [ 절망 ]</span>과 가장 관련성이 <span class="font-bold ">높은</span> 단어는 무엇인가요? <br><span class="font-bold text-red-500">또는</span> <span class="font-bold text-red-500">[ 행복 ], [ 기쁨 ], [ 긍정적인 것 ], [ 만족 ], [ 평온 ], [ 소망 ] </span>과 가장 관련성이 <span class="font-bold ">낮은</span> 단어는 무엇인가요?''')
                     },
        'message_arousal' : {'arousal_h':
                             mark_safe(''' <p>아래 4개의 단어 중<br>
                             <span class="font-bold text-red-500">[ 긴장하는 ], [ 적극적인 ], [ 자극적인 ], [ 흥분하는 ], [ 떨리는 ], [ 깨어있는 ]</span>과 가장 관련성이 <span class="font-bold ">높은</span> 단어는 무엇인가요?
                             <br>또는
                             <br><span class="font-bold text-red-500"> [ 긴장풀린 ], [ 소극적인 ], [ 이완된 ],[ 차분한 ], [ 느린 ], [ 둔한 ], [ 나른한 ] </span>과 가장 관련성이 <span class="font-bold ">낮은</span> 단어는 무엇인가요?'''),
                             'arousal_l':
                             mark_safe(''' <p>아래 4개의 단어 중<br>
                             <span class="font-bold text-red-500"> [ 긴장풀린 ], [ 소극적인 ], [ 이완된 ],[ 차분한 ], [ 느린 ], [ 둔한 ], [ 나른한 ] </span>과 가장 관련성이 <span class="font-bold ">높은</span> 단어는 무엇인가요?
                             <br>또는
                             <br><span class="font-bold text-red-500">[ 긴장하는 ], [ 적극적인 ], [ 자극적인 ], [ 흥분하는 ], [ 떨리는 ], [ 깨어있는 ]</span>과 가장 관련성이 <span class="font-bold ">낮은</span> 단어는 무엇인가요?''')
                             },
        'test_words' : ['a', 'b', 'c', 'd']
    })

def practice(request):
    # 1. 세션에 저장된 현재 튜플 ID 확인
    tuple_id = request.session.get('current_rating_tuple_id')
    user_tuple = UserWordTuple.objects.get(
                id=tuple_id,
                user=request.user,
                completed=False
            )
    word_tuple = user_tuple.word_tuple
    code = word_tuple.dimension
    name = dict(Rating.DIMENSIONS).get(code, '')
    
    if code == 'A':
        words = ('편안한', '귀한', '우스운', '두려운')
        correct_best = '두려운'
        correct_worst = '편안한'
    elif code == 'V':
        words = ('욕설','의무','책임','자유')
        correct_best = '자유'
        correct_worst = '욕설'
    message = ''

    if request.method == 'POST':
        best = request.POST.get('best_word')
        worst = request.POST.get('worst_word')
        if best == correct_best and worst == correct_worst:
            message = '정답입니다!'
        else:
            message = '틀렸습니다. 다시 시도해주세요.'
    # 고정된 단어 튜플
    # 정답 기준

    return render(request, 'vad_survey/practice.html', {
        'words': words,
        'message': message,
        'dimension': {'code': code, 'name': name},
        'message_valence' : {'valence_pos': 
                             mark_safe('''<p>아래 4개의 단어 중 <span class="font-bold text-red-500">[ 행복 ], [ 기쁨 ], [ 긍정적인 것 ], [ 만족 ], [ 평온 ], [ 소망 ]</span>과 가장 관련성이 <span class="font-bold ">높은</span> 단어는 무엇인가요? <br><span class="font-bold text-red-500">또는</span> <span class="font-bold text-red-500"> [ 불행 ], [ 성가심 ], [ 부정적인 것 ],[ 불만 ], [ 우울감 ], [ 절망 ] </span>과 가장 관련성이 <span class="font-bold ">낮은</span> 단어는 무엇인가요?'''),
                             'valence_neg': 
                             mark_safe('''<p>아래 4개의 단어 중 <span class="font-bold text-red-500">[ 불행 ], [ 성가심 ], [ 부정적인 것 ],[ 불만 ], [ 우울감 ], [ 절망 ]</span>과 가장 관련성이 <span class="font-bold ">높은</span> 단어는 무엇인가요? <br><span class="font-bold text-red-500">또는</span> <span class="font-bold text-red-500">[ 행복 ], [ 기쁨 ], [ 긍정적인 것 ], [ 만족 ], [ 평온 ], [ 소망 ] </span>과 가장 관련성이 <span class="font-bold ">낮은</span> 단어는 무엇인가요?''')
                     },
        'message_arousal' : {'arousal_h':
                             mark_safe(''' <p>아래 4개의 단어 중<br>
                             <span class="font-bold text-red-500">[ 긴장하는 ], [ 적극적인 ], [ 자극적인 ], [ 흥분하는 ], [ 떨리는 ], [ 깨어있는 ]</span>과 가장 관련성이 <span class="font-bold ">높은</span> 단어는 무엇인가요?
                             <br>또는
                             <br><span class="font-bold text-red-500"> [ 긴장풀린 ], [ 소극적인 ], [ 이완된 ],[ 차분한 ], [ 느린 ], [ 둔한 ], [ 나른한 ] </span>과 가장 관련성이 <span class="font-bold ">낮은</span> 단어는 무엇인가요?'''),
                             'arousal_l':
                             mark_safe(''' <p>아래 4개의 단어 중<br>
                             <span class="font-bold text-red-500"> [ 긴장풀린 ], [ 소극적인 ], [ 이완된 ],[ 차분한 ], [ 느린 ], [ 둔한 ], [ 나른한 ] </span>과 가장 관련성이 <span class="font-bold ">높은</span> 단어는 무엇인가요?
                             <br>또는
                             <br><span class="font-bold text-red-500">[ 긴장하는 ], [ 적극적인 ], [ 자극적인 ], [ 흥분하는 ], [ 떨리는 ], [ 깨어있는 ]</span>과 가장 관련성이 <span class="font-bold ">낮은</span> 단어는 무엇인가요?''')
                             },
    })
def intro2(request):
    return render(request, 'vad_survey/intro2.html')


def rate_words(request):
    """특정 차원(V, A, D)의 단어 튜플을 평가하는 뷰"""

    # 1. 현재 세션에 평가 중인 튜플이 있는지 확인
    current_tuple_id = request.session.get('current_rating_tuple_id')
    current_user_tuple = None

    if current_tuple_id:
        # 세션에 저장된 튜플이 있으면 해당 튜플 가져오기
        try:
            current_user_tuple = UserWordTuple.objects.get(
                id=current_tuple_id,
                user=request.user,
                completed=False
            )
        except UserWordTuple.DoesNotExist:
            # 세션에 저장된 튜플이 없거나 이미 완료된 경우 세션에서 제거
            if 'current_rating_tuple_id' in request.session:
                del request.session['current_rating_tuple_id']

    # 2. 사용자에게 할당된 미완료 튜플 가져오기 (현재 평가 중인 튜플이 없는 경우)
    if not current_user_tuple:
        user_tuples = UserWordTuple.objects.filter(
            user=request.user,
            completed=False
        ).select_related('word_tuple')

        # 모든 튜플 평가 완료 시 complete.html로 이동
        if not user_tuples.exists():
            total_ratings = Rating.objects.filter(user=request.user).count()
            return render(request, 'vad_survey/complete.html', {
                'total_ratings': total_ratings
            })

        # 평가할 수 있는 튜플 찾기
        available_tuples = []
        for user_tuple in user_tuples:
            word_tuple = user_tuple.word_tuple

            # 해당 튜플의 dimension 확인 (V, A, D 중 하나)
            tuple_dimension = word_tuple.dimension

            # dimension이 설정되지 않은 경우 건너뛰기
            if not tuple_dimension:
                continue

            # 이미 평가된 차원인지 확인
            already_rated = Rating.objects.filter(
                user=request.user,
                word_tuple=word_tuple,
                dimension=tuple_dimension
            ).exists()

            # 아직 평가되지 않은 경우에만 추가
            if not already_rated:
                available_tuples.append(user_tuple)

        # 평가할 튜플이 없는 경우
        if not available_tuples:
            # 모든 작업이 완료되었거나, 모든 할당된 튜플의 차원이 이미 평가된 경우
            for ut in user_tuples:
                # 차원이 정의된 튜플만 확인
                if not ut.word_tuple.dimension:
                    continue

                # 이미 평가되었는지 확인
                is_rated = Rating.objects.filter(
                    user=request.user,
                    word_tuple=ut.word_tuple,
                    dimension=ut.word_tuple.dimension
                ).exists()

                # 평가되었다면 완료 처리
                if is_rated:
                    ut.completed = True
                    ut.save()

            total_ratings = Rating.objects.filter(user=request.user).count()
            return render(request, 'vad_survey/complete.html', {
                'total_ratings': total_ratings
            })

        # 무작위로 평가할 튜플 선택
        current_user_tuple = random.choice(available_tuples)

        # 세션에 현재 평가 중인 튜플 저장
        request.session['current_rating_tuple_id'] = current_user_tuple.id

        # 평가 시작 시간 기록
        request.session['rating_start_time'] = timezone.now().isoformat()

    # 3. 현재 평가할 튜플 및 차원 설정
    word_tuple = current_user_tuple.word_tuple
    dimension_code = word_tuple.dimension
    dimension_name = dict(Rating.DIMENSIONS)[dimension_code]

    # 현재 튜플에 속한 단어들 (미리 로드)
    words = list(word_tuple.words.all().only('id', 'text'))

    # 4. POST 요청 처리
    if request.method == 'POST':
        best_word_id = request.POST.get('best_word')
        worst_word_id = request.POST.get('worst_word')

        if best_word_id and worst_word_id:
            if best_word_id == worst_word_id:
                messages.warning(request, '가장 높은 단어와 가장 낮은 단어는 달라야 합니다.')
            else:
                try:
                    # 선택된 단어들이 현재 튜플에 속하는지 확인
                    tuple_word_ids = [str(w.id) for w in words]

                    if best_word_id not in tuple_word_ids or worst_word_id not in tuple_word_ids:
                        messages.error(request,
                                       f'선택한 단어가 현재 평가 중인 튜플에 속하지 않습니다. '
                                       f'선택됨: {best_word_id}, {worst_word_id}, '
                                       f'가능한 ID들: {", ".join(tuple_word_ids)}')
                    else:
                        # 이미 평가된 차원인지 한번 더 확인
                        existing_rating = Rating.objects.filter(
                            user=request.user,
                            word_tuple=word_tuple,
                            dimension=dimension_code
                        ).exists()

                        if existing_rating:
                            messages.warning(request, '이미 평가한 차원입니다.')
                        else:
                            # 평가 생성 - 직접 객체를 가져와서 사용
                            best_word = next(w for w in words if str(w.id) == best_word_id)
                            worst_word = next(w for w in words if str(w.id) == worst_word_id)

                            # 세션에서 평가 시작 시간 가져오기
                            start_time_str = request.session.get('rating_start_time')
                            if start_time_str:
                                try:
                                    start_time = timezone.datetime.fromisoformat(start_time_str)
                                except (ValueError, TypeError):
                                    start_time = timezone.now()
                            else:
                                start_time = timezone.now()

                            # Rating 객체 생성 부분
                            rating = Rating.objects.create(
                                user=request.user,
                                word_tuple=word_tuple,
                                dimension=dimension_code,
                                best_word=best_word,
                                worst_word=worst_word,
                                start_time=start_time
                            )

                            # response_time이 너무 짧으면 최소값으로 설정
                            if not rating.response_time or rating.response_time < 500:
                                rating.response_time = 500  # 최소 0.5초
                                rating.save(update_fields=['response_time'])

                            # 완료 처리
                            current_user_tuple.completed = True
                            current_user_tuple.save()

                            # 세션에서 현재 평가 중인 튜플과 시작 시간 제거
                            if 'current_rating_tuple_id' in request.session:
                                del request.session['current_rating_tuple_id']
                            if 'rating_start_time' in request.session:
                                del request.session['rating_start_time']

                            messages.success(request, '평가가 성공적으로 저장되었습니다.')

                except ValidationError as e:
                    error_msg = str(e.message_dict) if hasattr(e, 'message_dict') else str(e)
                    messages.error(request, f'평가 저장 중 오류: {error_msg}')
                except Exception as e:
                    messages.error(request, f'예상치 못한 오류 발생: {str(e)}')

        return redirect('vad_survey:rate_words')

    # 5. 평가 화면 표시
    current_dimension = {
        'code': dimension_code,
        'name': dimension_name
    }

    # 새로운 평가를 시작할 때 시작 시간 설정
    if 'rating_start_time' not in request.session:
        request.session['rating_start_time'] = timezone.now().isoformat()

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
        ).count() / UserWordTuple.objects.filter(user=request.user).count() * 100,
        'message_valence': {'valence_pos':
                                mark_safe(
                                    '''<p>아래 4개의 단어 중 <span class="font-bold text-red-500">[ 행복 ], [ 기쁨 ], [ 긍정적인 것 ], [ 만족 ], [ 평온 ], [ 소망 ]</span>과 가장 관련성이 <span class="font-bold ">높은</span> 단어는 무엇인가요? <br><span class="font-bold text-red-500">또는</span> <span class="font-bold text-red-500"> [ 불행 ], [ 성가심 ], [ 부정적인 것 ],[ 불만 ], [ 우울감 ], [ 절망 ] </span>과 가장 관련성이 <span class="font-bold ">낮은</span> 단어는 무엇인가요?'''),
                            'valence_neg':
                                mark_safe(
                                    '''<p>아래 4개의 단어 중 <span class="font-bold text-red-500">[ 불행 ], [ 성가심 ], [ 부정적인 것 ],[ 불만 ], [ 우울감 ], [ 절망 ]</span>과 가장 관련성이 <span class="font-bold ">높은</span> 단어는 무엇인가요? <br><span class="font-bold text-red-500">또는</span> <span class="font-bold text-red-500">[ 행복 ], [ 기쁨 ], [ 긍정적인 것 ], [ 만족 ], [ 평온 ], [ 소망 ] </span>과 가장 관련성이 <span class="font-bold ">낮은</span> 단어는 무엇인가요?''')
                            },
        'message_arousal': {'arousal_h':
                                mark_safe(''' <p>아래 4개의 단어 중<br>
                             <span class="font-bold text-red-500">[ 긴장하는 ], [ 적극적인 ], [ 자극적인 ], [ 흥분하는 ], [ 떨리는 ], [ 깨어있는 ]</span>과 가장 관련성이 <span class="font-bold ">높은</span> 단어는 무엇인가요?
                             <br>또는
                             <br><span class="font-bold text-red-500"> [ 긴장풀린 ], [ 소극적인 ], [ 이완된 ],[ 차분한 ], [ 느린 ], [ 둔한 ], [ 나른한 ] </span>과 가장 관련성이 <span class="font-bold ">낮은</span> 단어는 무엇인가요?'''),
                            'arousal_l':
                                mark_safe(''' <p>아래 4개의 단어 중<br>
                             <span class="font-bold text-red-500"> [ 긴장풀린 ], [ 소극적인 ], [ 이완된 ],[ 차분한 ], [ 느린 ], [ 둔한 ], [ 나른한 ] </span>과 가장 관련성이 <span class="font-bold ">높은</span> 단어는 무엇인가요?
                             <br>또는
                             <br><span class="font-bold text-red-500">[ 긴장하는 ], [ 적극적인 ], [ 자극적인 ], [ 흥분하는 ], [ 떨리는 ], [ 깨어있는 ]</span>과 가장 관련성이 <span class="font-bold ">낮은</span> 단어는 무엇인가요?''')
                            }
    })

def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.username = str(form.cleaned_data.get('username'))  # 숫자 입력 대비 문자열로 변환
            user.save()

            # ⭐ UserProfile 중복 체크 후 생성
            if not UserProfile.objects.filter(user=user).exists():
                UserProfile.objects.create(
                    user=user,
                    sona_id=user.username,  # 소다 ID를 따로 지정
                    age=form.cleaned_data.get('age'),
                    gender=form.cleaned_data.get('gender')
                )
            else:
                messages.error(request, "이미 해당 유저 프로필이 존재합니다.")
                return render(request, 'registration/signup.html', {'form': form})

            login(request, user)
            messages.info(request, '회원가입이 완료되었습니다. 관리자가 평가 작업을 할당할 때까지 기다려주세요.')
            return redirect('vad_survey:intro') # 수정
    else:
        form = SignUpForm()
    return render(request, 'registration/signup.html', {'form': form})