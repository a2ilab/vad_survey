import random
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import UserProfile, WordTuple, UserWordTuple, Rating


@receiver(post_save, sender=UserProfile)
def assign_alternating_dimension_wordtuples(sender, instance, created, **kwargs):
    """회원가입 시 V, A 차원을 번갈아가며 순차적으로 100개 튜플 할당"""
    if not created:
        return

    user = instance.user
    target_count = 100

    # 기존 유저 수를 기반으로 차원 결정 (V, A 번갈아)
    user_count = UserProfile.objects.count()
    dimension = 'V' if user_count % 2 == 1 else 'A'

    # 해당 차원의 튜플 중 랜덤 100개 선택
    tuples = list(WordTuple.objects.filter(dimension=dimension))
    random.shuffle(tuples)
    selected_tuples = tuples[:target_count]

    for word_tuple in selected_tuples:
        UserWordTuple.objects.get_or_create(user=user, word_tuple=word_tuple)


@receiver(post_delete, sender=Rating)
def update_gold_accuracy_on_rating_delete(sender, instance, **kwargs):
    """Rating 삭제 시 정확도 및 평가 수 재계산"""
    try:
        profile = instance.user.userprofile
        all_ratings = Rating.objects.filter(user=instance.user)
        gold_ratings = all_ratings.filter(word_tuple__is_gold=True)

        if gold_ratings.exists():
            correct = 0
            for r in gold_ratings:
                if r.best_word_id == r.word_tuple.gold_best_word_id and \
                   r.worst_word_id == r.word_tuple.gold_worst_word_id:
                    correct += 1
            profile.gold_accuracy = (correct / gold_ratings.count()) * 100
        else:
            profile.gold_accuracy = 0.0

        profile.total_ratings = all_ratings.values('word_tuple').distinct().count()
        profile.is_active = profile.gold_accuracy >= 80
        profile.save()

    except UserProfile.DoesNotExist:
        pass
