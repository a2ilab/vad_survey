# 한국어 VAD Lexicon 워크벤치

한국어 단어의 Valence(가치), Arousal(각성), Dominance(지배) 특성을 평가하고 어휘 사전을 구축하기 위한 워크벤치입니다.

## 프로젝트 소개

이 프로젝트는 한국어 단어들의 감정적 특성을 평가하고 어휘 사전을 구축하기 위한 워크벤치입니다. NRC VAD Lexicon을 참고하여, 한국어 단어들의 Valence(긍정-부정), Arousal(흥분-평온), Dominance(강력-약함) 특성을 평가하고 어휘 사전을 구축할 수 있는 도구를 제공합니다.

## 주요 기능

- 단어 목록 업로드 및 관리
- Valence, Arousal, Dominance 평가 인터페이스
- 평가 결과 시각화 및 분석
- 어휘 사전 구축 및 편집
- 데이터 내보내기/가져오기

## 설치 방법

1. 저장소를 클론합니다:
```bash
git clone [repository-url]
cd vad_survey
```

2. 필요한 패키지를 설치합니다:
```bash
pip install -r requirements.txt
```

## 사용 방법

1. 서버 실행:
```bash
python app.py
```

2. 웹 브라우저에서 다음 주소로 접속:
```
http://3.105.215.3:8000/
```

## 기술 스택

- Python
- Flask
- HTML/CSS
- JavaScript
- Data Processing Libraries

## 데이터 형식

- 단어 목록: JSON, CSV 등 지원
- 평가 결과: JSON, CSV 형식 지원
- 어휘 사전: JSON 형식으로 저장

## 라이선스

이 프로젝트는 MIT 라이선스를 따릅니다.

## 기여하기

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 참고 사이트

- [NRC VAD Lexicon](https://saifmohammad.com/WebPages/nrc-vad.html) 