import random
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db.models import F
from .models import UserProfile, WordTuple, UserWordTuple, Rating


@receiver(post_save, sender=UserProfile)
def assign_alternating_dimension_wordtuples(sender, instance, created, **kwargs):
    """회원가입 시 V, A 차원을 번갈아가며 순차적으로 100개 튜플 할당"""
    if not created:
        return

    user = instance.user
    target_count = 100
    user_count = UserProfile.objects.count()
    dimension = 'V' if user_count % 2 == 1 else 'A'

    tuples = list(WordTuple.objects.filter(dimension=dimension))
    random.shuffle(tuples)
    selected_tuples = tuples[:target_count]

    for word_tuple in selected_tuples:
        UserWordTuple.objects.get_or_create(user=user, word_tuple=word_tuple)


def recalculate_gold_accuracy(user):
    """골든 정확도 재계산 함수"""
    profile = user.userprofile

    # 평가 완료된 골든 튜플 수
    rated_gold = Rating.objects.filter(user=user, word_tuple__is_gold=True).values('word_tuple').distinct().count()

    # 할당된 골든 튜플 수
    assigned_gold = UserWordTuple.objects.filter(user=user, word_tuple__is_gold=True).count()

    if rated_gold == 0 or rated_gold < assigned_gold:
        # 평가 미완료이거나 평가 0개이면 정확도 계산하지 않음
        return

    # 정확히 일치하는 골든 평가 수
    correct_count = Rating.objects.filter(
        user=user,
        word_tuple__is_gold=True,
        best_word_id=F('word_tuple__gold_best_word_id'),
        worst_word_id=F('word_tuple__gold_worst_word_id'),
    ).count()

    # 정확도 계산
    accuracy = (correct_count / rated_gold) * 100
    profile.gold_accuracy = accuracy

    # 정확도에 따라 활성/비활성 설정
    if accuracy < 80:
        profile.is_active = False
        Rating.objects.filter(user=user).update(is_active=False)
    else:
        profile.is_active = True
        Rating.objects.filter(user=user).update(is_active=True)

    profile.save()


@receiver(post_save, sender=Rating)
def handle_rating_save(sender, instance, **kwargs):
    """Rating 저장 시 골든 정확도 재계산"""
    if instance.word_tuple.is_gold:
        recalculate_gold_accuracy(instance.user)


@receiver(post_delete, sender=Rating)
def handle_rating_delete(sender, instance, **kwargs):
    """Rating 삭제 시 골든 정확도 재계산"""
    if instance.word_tuple.is_gold:
        recalculate_gold_accuracy(instance.user)
