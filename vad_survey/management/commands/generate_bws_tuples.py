# vad_survey/management/commands/generate_bws_tuples.py
import random
import statistics
from typing import List, Set, Dict
from django.core.management.base import BaseCommand, CommandError
from vad_survey.models import Word, WordTuple


class Command(BaseCommand):
    help = 'Generate Best-Worst Scaling tuples without dimension info'

    def add_arguments(self, parser):
        parser.add_argument('--items-per-tuple', type=int, default=4)
        parser.add_argument('--scaling-factor', type=float, default=2.0)
        parser.add_argument('--iterations', type=int, default=100)
        parser.add_argument('--random-seed', type=int, default=1234)
        parser.add_argument('--word-ids', type=str, default=None)
        parser.add_argument('--dimension', type=str, default=None, help='Optional dimension to save with tuples')
        parser.add_argument('--word-texts', type=str, default=None)  # 추가 가능

    def handle(self, *args, **options):
        word_ids_opt = options.get('word_ids')
        word_texts_opt = options.get('word_texts')

        # word ID 또는 텍스트 기반 조회
        if word_ids_opt:
            id_list = [int(pk) for pk in word_ids_opt.split(',') if pk]
            words_qs = Word.objects.filter(id__in=id_list)
        elif word_texts_opt:
            text_list = [t.strip() for t in word_texts_opt.split(',') if t.strip()]
            words_qs = Word.objects.filter(text__in=text_list)
        else:
            raise CommandError("단어 ID 또는 텍스트를 제공해야 합니다 (--word-ids 또는 --word-texts)")

        words = list(words_qs)
        if len(words) < options['items_per_tuple']:
            self.stderr.write("단어 수가 tuple 크기보다 적습니다.")
            return

        self.stdout.write(f"{len(words)}개 단어로 튜플 생성 시작...")

        generator = BWSTupleGenerator(
            items_per_tuple=options['items_per_tuple'],
            scaling_factor=options['scaling_factor'],
            num_iterations=options['iterations'],
            random_seed=options['random_seed']
        )

        tuples = generator.generate_tuples(words)

        tuples_created = 0
        for tuple_words in tuples:
            word_tuple = WordTuple.objects.create(dimension=options['dimension'])
            word_tuple.words.set(tuple_words)
            word_tuple.save()
            tuples_created += 1

        self.stdout.write(self.style.SUCCESS(f"{tuples_created}개 WordTuple 생성 완료"))

class BWSTupleGenerator:
    def __init__(
            self,
            items_per_tuple: int = 4,
            scaling_factor: float = 2.0,
            num_iterations: int = 100,
            random_seed: int = 1234
    ):
        """Best-Worst Scaling 튜플 생성기 초기화"""
        self.items_per_tuple = items_per_tuple
        self.scaling_factor = scaling_factor
        self.num_iterations = num_iterations
        random.seed(random_seed)

    def generate_tuples(self, items: List[str]) -> List[List[str]]:
        """BWS 평가를 위한 최적의 튜플 세트 생성"""
        num_items = len(items)
        num_unique_pairs = (num_items * (num_items - 1)) // 2
        num_tuples = round(self.scaling_factor * num_items)

        if num_items < self.items_per_tuple:
            raise ValueError("The number of unique items is less than the number of items requested per tuple")

        best_score = float('inf')
        best_tuples = []

        for iter_num in range(1, self.num_iterations + 1):
            print(f"iteration {iter_num}")

            # 현재 반복에서의 튜플 생성
            tuples = []
            ranlist = items.copy()
            random.shuffle(ranlist)  # 아이템 순서를 무작위로 섞음
            freq_pair: Dict[str, int] = {}  # 아이템 쌍의 등장 빈도를 저장할 딕셔너리

            j = 0  # 현재 랜덤 리스트에서의 인덱스
            for _ in range(num_tuples):
                tuple_items = []

                # 현재 랜덤 리스트에 충분한 아이템이 남아있는 경우
                if j + self.items_per_tuple <= len(ranlist):
                    tuple_items = ranlist[j:j + self.items_per_tuple]
                    j += self.items_per_tuple
                else:
                    # 남은 아이템들을 사용하고 새로운 랜덤 리스트 시작
                    current_items = set()
                    while j < len(ranlist):
                        tuple_items.append(ranlist[j])
                        current_items.add(ranlist[j])
                        j += 1

                    # 새로운 랜덤 리스트 생성
                    need_more = self.items_per_tuple - len(tuple_items)
                    ranlist = items.copy()
                    random.shuffle(ranlist)
                    j = 0

                    # 필요한 만큼 새로운 아이템 추가 (중복 방지)
                    while need_more > 0:
                        while j < len(ranlist) and ranlist[j] in current_items:
                            j += 1
                        if j < len(ranlist):
                            tuple_items.append(ranlist[j])
                            need_more -= 1
                            j += 1

                tuples.append(tuple_items)

                # 현재 튜플에서 모든 가능한 아이템 쌍의 빈도 계산
                for i in range(len(tuple_items)):
                    for k in range(i + 1, len(tuple_items)):
                        # 쌍을 정렬하여 저장 (A,B와 B,A를 같은 것으로 처리)
                        pair = tuple(sorted([tuple_items[i],tuple_items[k]], key=lambda w: w.id))
                        freq_pair[str(pair)] = freq_pair.get(str(pair), 0) + 1

            # 투웨이 밸런스 점수 계산 (쌍 빈도의 표준편차)
            freq_values = list(freq_pair.values())
            if len(freq_values) > 1:
                score = statistics.stdev(freq_values)
                # 더 좋은 밸런스(낮은 표준편차)를 가진 경우 저장
                if score < best_score:
                    best_score = score
                    best_tuples = tuples

        return best_tuples
