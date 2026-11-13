# 🏆 RecipeU (레시퓨)

**AI 기반 개인화 레시피 추천 및 조리 가이드 서비스**

## ✏️ 프로젝트 소개

| 특징 | 설명 |
|------|------|
| **프로젝트 주제** | 네이버 부스트캠프 AI-Tech 8기 NLP 트랙 Final Project |
| **프로젝트 설명** | 사용자의 신체 조건과 선호도, 조리 환경을 반영해 레시피를 실시간으로 맞춤 설계하고, 요리 전 과정을 음성으로 가이드하는 개인화 대화형 AI 요리 Agent |
| **진행 기간** | 2026년 1월 19일 ~ 2026년 2월 11일 (3주) |
| **테크 스택** | Github Action, Airflow, Milvus, MongoDB, MySQL, FastAPI, Docker, ClovaStudio, LangChain, LangGraph, React, Nginx vLLM, Qwen, GPT-SoVITS |
| **서비스 URL** | [https://recipeu.site](https://recipeu.site) |

## 👨‍💻 Contributors

<table align='center'>
  <tr>
    </td>
        <td align="center">
      <img src="https://github.com/choijunho-AIDeveloper.png" alt="최준호" width="100" height="100" style="border-radius: 50%;"/><br>
      <a href="https://github.com/choijunho-AIDeveloper">
        <img src="https://img.shields.io/badge/최준호-grey?style=for-the-badge&logo=github" alt="badge 최준호"/>
      </a>
    </td>
    <td align="center">
      <img src="https://github.com/kyunhui.png" alt="김윤희" width="100" height="100" style="border-radius: 50%;"/><br>
      <a href="https://github.com/kyunhui">
        <img src="https://img.shields.io/badge/김윤희-grey?style=for-the-badge&logo=github" alt="badge 김윤희"/>
      </a>
    </td>
    <td align="center">
      <img src="https://github.com/Parkseojin2001.png" alt="박서진" width="100" height="100" style="border-radius: 50%;"/><br>
      <a href="https://github.com/Parkseojin2001">
        <img src="https://img.shields.io/badge/박서진-grey?style=for-the-badge&logo=github" alt="badge 박서진"/>
      </a>
    </td>
    <td align="center">
      <img src="https://github.com/nay0ng.png" alt="곽나영" width="100" height="100" style="border-radius: 50%;"/><br>
      <a href="https://github.com/nay0ng">
        <img src="https://img.shields.io/badge/곽나영-grey?style=for-the-badge&logo=github" alt="badge 곽나영"/>
      </a>
    </td>
    <td align="center">
      <img src="https://github.com/2sseul.png" alt="김이슬" width="100" height="100" style="border-radius: 50%;"/><br>
      <a href="https://github.com/2sseul">
        <img src="https://img.shields.io/badge/김이슬-grey?style=for-the-badge&logo=github" alt="badge 김이슬"/>
      </a>
    </td>
    <td align="center">
      <img src="https://github.com/hyejinw.png" alt="우혜진" width="100" height="100" style="border-radius: 50%;"/><br>
      <a href="https://github.com/hyejinw">
        <img src="https://img.shields.io/badge/우혜진-grey?style=for-the-badge&logo=github" alt="badge 우혜진"/>
      </a>
  </tr>
</table>

## 👼 역할 분담

| 이름   | 역할                                                                                                         |
| ------ | ------------------------------------------------------------------------------------------------------------ |
| 최&#8288;준&#8288;호 | LLM 모델링 및 양자화, 프롬프트 엔지니어링, 프론트엔드, 요리 Agent 구축 및 최적화, 요리 관련 학습 데이터셋 구성 |
| 김&#8288;윤&#8288;희 | 음성 파이프라인 구축, 음성 VAD 고도화, 서비스 비용/속도 최적화, 프롬프트 엔지니어링, Streamlit 기반 테스트 환경 구축, Fast API/React 개발 |
| 박&#8288;서&#8288;진 | 레시피 데이터 DB & VectorDB 구축, 프론트엔드, 데이터 수집 및 임베딩 자동화(Airflow), 레시피 Agent 구축, 데이터 파이프라인 CI/CD 구축, 데이터 서버 인프라 구축(GCP) |
| 곽&#8288;나&#8288;영 | 레시피 Agent 설계 및 최적화, Agent 평가, MySQL DB 구축 및 CRUD 구성, Fast API/React 개발 |
| 김&#8288;이&#8288;슬 | 레시피 Agent 구축 및 최적화, 프롬프트 엔지니어링, 서버 인프라 구축 및 CI/CD 자동화, HCX API 및 FastAPI 백엔드 개발, WebSocket 기반 실시간 스트리밍 구현, React 개발 |
| 우&#8288;혜&#8288;진 | RunPod GPU 환경 구성, 모델 서빙 (Qwen LLM, GPT-SoVITS 기반 커스텀 TTS), 음성 (STT/LLM/TTS) 파이프라인 설계, SSE 기반 실시간 청크 스트리밍, FastAPI/React 개발 |

## ✍🏻 프로젝트 개요

- 사용자의 신체 조건(알레르기, 비건 등)과 주방 환경(보유 조리 도구), 그리고 실시간 선호(매운게 먹고싶어 등)까지 이해하는 **개인화 AI 요리 에이전트**
- 고정된 DB의 결과물만 보여주는 것이 아니라, 사용자와의 대화를 통해 레시피를 실시간으로 재구성하고, 요리 중에도 음성으로 상호작용하며 마치 나만의 개인 쉐프가 옆에 있는 듯한 경험 제공

## 🏗 시스템 아키텍처
![alt text](<Architecture.png>)

## 📁 프로젝트 구조

```
recipeu/
├── airflow
│   ├── dags
│   │   ├── lib
│   │   │   ├── chunking.py
│   │   │   ├── embed_and_upsert.py
│   │   │   ├── embedding_pipeline.py
│   │   │   ├── mongo_utils.py
│   │   │   ├── page_crawling.py
│   │   │   ├── ranking_crawling.py
│   │   │   └── recipe_to_doc.py
│   │   ├── recipe_collection.py
│   │   ├── recipe_embedding.py
│   │   └── recipe_ranking.py
│   ├── .env.example
│   ├── docker-compose.yml
│   └── Dockerfile
├── Architecture.png
├── backend
│   ├── app
│   │   ├── config.py
│   │   └── main.py
│   ├── core
│   │   ├── dependencies.py
│   │   ├── exceptions.py
│   │   └── websocket.py
│   ├── Dockerfile
│   ├── features
│   │   ├── auth
│   │   │   ├── __init__.py
│   │   │   └── router.py
│   │   ├── chat
│   │   │   ├── agent.py
│   │   │   ├── prompts.py
│   │   │   ├── router.py
│   │   │   └── schemas.py
│   │   ├── chat_external
│   │   │   └── router.py
│   │   ├── cooking
│   │   │   ├── agent.py
│   │   │   ├── router.py
│   │   │   ├── schemas.py
│   │   │   └── session.py
│   │   ├── mypage
│   │   │   ├── __init__.py
│   │   │   └── router.py
│   │   ├── ranking
│   │   │   ├── router.py
│   │   │   └── schemas.py
│   │   ├── recipe
│   │   │   ├── __init__.py
│   │   │   ├── prompts.py
│   │   │   ├── router.py
│   │   │   ├── schemas.py
│   │   │   └── service.py
│   │   ├── user
│   │   │   ├── router.py
│   │   │   └── schemas.py
│   │   ├── voice
│   │   │   ├── __init__.py
│   │   │   ├── clova_speech_client.py
│   │   │   ├── router.py
│   │   │   ├── service.py
│   │   │   └── text_analyzer.py
│   │   ├── weather
│   │   │   ├── korea_lat_lon.csv
│   │   │   └── router.py
│   │   └── whether
│   │       └── router.py
│   ├── models
│   │   └── mysql_db.py
│   ├── new_token_summary.py
│   ├── recipe_token_summary_func.py
│   ├── requirements.txt
│   ├── run.py
│   ├── services
│   │   ├── __init__.py
│   │   ├── audio.py
│   │   ├── llm.py
│   │   ├── rag.py
│   │   └── search.py
│   ├── temp_token_summary.py
│   ├── test_hcx_token.py
│   ├── token_validation_report.md
│   └── utils
│       ├── helpers.py
│       ├── intent.py
│       └── parser.py
├── frontend
│   ├── directory_structure.txt
│   ├── Dockerfile
│   ├── index.html
│   ├── nginx.conf
│   ├── package-lock.json
│   ├── package.json
│   ├── public
│   │   ├── favicon.ico
│   │   ├── loading-bg-phone.png
│   │   ├── loading-motion.gif
│   │   ├── peu_banjuk.png
│   │   ├── peu_chicken.png
│   │   ├── peu_cook.png
│   │   ├── peu_gimbab.png
│   │   ├── peu_hurai.png
│   │   ├── peu_icecream.png
│   │   ├── peu_pizza.png
│   │   ├── peu_ramen.png
│   │   ├── peu_salad.png
│   │   └── peu_wink.png
│   ├── src
│   │   ├── app
│   │   │   ├── App.jsx
│   │   │   └── main.jsx
│   │   ├── components
│   │   │   ├── BottomNav.css
│   │   │   ├── BottomNav.jsx
│   │   │   ├── Button.jsx
│   │   │   ├── ButtonRed.css
│   │   │   ├── ButtonRed.jsx
│   │   │   ├── ButtonWhite.css
│   │   │   ├── ButtonWhite.jsx
│   │   │   ├── Header.jsx
│   │   │   ├── Modal.jsx
│   │   │   ├── PageTransition.jsx
│   │   │   ├── RecipeBottomSheet.css
│   │   │   └── RecipeBottomSheet.jsx
│   │   ├── data
│   │   │   └── weatherComments.json
│   │   ├── features
│   │   │   └── chat
│   │   │       ├── components
│   │   │       │   ├── ChatAvatar.jsx
│   │   │       │   ├── ChatBubble.jsx
│   │   │       │   ├── ChatInput.jsx
│   │   │       │   └── ChatList.jsx
│   │   │       └── hooks
│   │   │           ├── useChatAgent.js
│   │   │           ├── useChatSocket.js
│   │   │           └── useCookingAgent.js
│   │   ├── images.js
│   │   ├── layouts
│   │   │   ├── FixedLayout.jsx
│   │   │   ├── MobileLayout.jsx
│   │   │   ├── RecipeLayout.css
│   │   │   ├── RecipeLayout.jsx
│   │   │   └── ScrollLayout.jsx
│   │   ├── pages
│   │   │   ├── Chat
│   │   │   │   ├── ChatPage.css
│   │   │   │   ├── ChatPage.jsx
│   │   │   │   ├── ChatPageOut.css
│   │   │   │   └── ChatPageOut.jsx
│   │   │   ├── Cook
│   │   │   │   ├── CookCompletePage.css
│   │   │   │   ├── CookCompletePage.jsx
│   │   │   │   ├── CookModeAudioPage.css
│   │   │   │   ├── CookModeAudioPage.jsx
│   │   │   │   ├── CookModePage.css
│   │   │   │   ├── CookModePage.jsx
│   │   │   │   ├── CookStartPage.css
│   │   │   │   └── CookStartPage.jsx
│   │   │   ├── Home
│   │   │   │   ├── HomePage.css
│   │   │   │   └── HomePage.jsx
│   │   │   ├── Loading
│   │   │   │   ├── LoadingPage.css
│   │   │   │   └── LoadingPage.jsx
│   │   │   ├── MyPages
│   │   │   │   ├── MyPage.css
│   │   │   │   └── MyPage.jsx
│   │   │   ├── MyRecipes
│   │   │   │   ├── MyRecipesPage.css
│   │   │   │   ├── MyRecipesPage.jsx
│   │   │   │   ├── RecipeDetailModal.css
│   │   │   │   └── RecipeDetailModal.jsx
│   │   │   ├── NaverCallback
│   │   │   │   └── NaverCallbackPage.jsx
│   │   │   ├── Rankings
│   │   │   │   ├── RankingRecipesPage.css
│   │   │   │   └── RankingRecipesPage.jsx
│   │   │   ├── Recipes
│   │   │   │   ├── RecipeResultPage.css
│   │   │   │   └── RecipeResultPage.jsx
│   │   │   └── Splash
│   │   │       ├── SplashPage.css
│   │   │       └── SplashPage.jsx
│   │   ├── routes
│   │   │   ├── __root.jsx
│   │   │   ├── chat.jsx
│   │   │   ├── cook-audio.jsx
│   │   │   ├── cook-complete.jsx
│   │   │   ├── cook-start.jsx
│   │   │   ├── cook.jsx
│   │   │   ├── home.jsx
│   │   │   ├── index.jsx
│   │   │   ├── loading.jsx
│   │   │   ├── mypage.jsx
│   │   │   ├── naver-callback.jsx
│   │   │   ├── out-chat.jsx
│   │   │   ├── recipe-result.jsx
│   │   │   ├── recipes.index.jsx
│   │   │   └── recipes.my.jsx
│   │   ├── routeTree.gen.ts
│   │   ├── style
│   │   │   └── global.css
│   │   └── utils
│   │       └── textFormatter.js
│   ├── tree.txt
│   └── vite.config.js
├── README.md
└── voice_module
    ├── README.md
    └── voice_module
        ├── 1_ready_vllm.sh
        ├── 2_go_others.sh
        ├── agents
        │   └── cooking_session.py
        ├── config
        │   ├── prompts.yaml
        │   └── settings.py
        ├── core
        │   ├── api_client.py
        │   ├── llm_engine.py
        │   ├── text_processor.py
        │   ├── types.py
        │   └── vad_audio.py
        ├── main.py
        ├── MSA_GUIDE.md
        ├── QUICKSTART.md
        ├── README.md
        ├── recipe_sample.jsonl
        ├── servers
        │   ├── llm_server.py
        │   ├── stt_server.py
        │   ├── tts_inference.py
        │   └── tts_server.py
        ├── start_servers.sh
        ├── start_servers(expired).sh
        ├── test_tts_endpoints.py
        ├── test_vllm_stream.py
        ├── test_vllm.py
        ├── utils
        │   └── audio_utils.py
        └── venv_llm_requirements.txt
```

## 🎯 주요 서비스

### 1. Chat Service (WebSocket)
**엔드포인트**: `/api/chat/ws/{session_id}`

**기능:**
- 실시간 대화형 레시피 검색 및 추천
- 사용자 의도 감지 (레시피 검색, 조리 질문, 레시피 수정, 비요리 질문)
- 적응형 RAG (쿼리 재작성 및 문서 랭킹)
- 레시피 수정 처리 (재료 추가/제거/대체)
- 알레르기 및 선호도 관리
- AI 안전 필터 (개인정보 탐지, 유해 표현 차단)
- 수정 이력 추적

**주요 인텔리전스:**
- 사용자가 기존 레시피를 수정하고 싶을 때 감지
- 레시피 생성 전 알레르기 검증
- 싫어하는 재료 포함 시 확인 요청
- 세션 전반에 걸친 수정 이력 추적

### 2. Recipe Service (REST API)
**주요 엔드포인트:**
- `POST /api/recipe/generate` - 채팅 히스토리로부터 레시피 생성
- `POST /api/recipe/generate-from-chat` - 조리 세션 내 레시피 생성
- `GET /api/recipe/list` - 저장된 레시피 목록 조회
- `GET /api/recipe/{recipe_id}` - 레시피 상세 조회
- `POST /api/recipe/save-my-recipe` - "마이 레시피"에 저장
- `PUT /api/recipe/{recipe_id}` - 레시피 업데이트 (평점, 제목, 이미지)
- `DELETE /api/recipe/{recipe_id}` - 저장된 레시피 삭제

**기능:**
- RAG 기반 레시피 생성 (LLM 활용)
- 토큰 사용량 추적 (input/output/total)
- 단계별 성능 분석
- 조리 세션 데이터 통합
- MySQL 데이터베이스에 메타데이터 저장

### 3. Cooking Mode (Voice + Text)
**엔드포인트**: `/api/cook/ws/{session_id}`

**기능:**
- 음성 가이드 단계별 조리 지침
- 실시간 TTS (Text-to-Speech) 핸즈프리 작동
- 조리 세션 관리
- MySQL에 음성 데이터 저장
- 에이전트 기반 지침 생성
- 대화형 조리 진행 상황 추적

**지원 기능:**
- 각 단계별 조리 가이드 제공
- 지침을 위한 음성 오디오 생성
- 향후 참조를 위한 음성 상호작용 저장
- 상황별 도움을 위한 레시피 통합

### 4. User Management (REST API)
**주요 엔드포인트:**
- `GET /api/user/profile` - 사용자 프로필 조회 (MySQL)
- 사용자 개인화 (알레르기, 선호도)
- 가족 구성원 관리
- 조리 도구/주방 기구 선호도
- 종합 프로필 데이터 로드

**기능:**
- MySQL 기반 영구 저장
- 다중 사용자 지원 (로그인 + 게스트)
- 가족 프로필 관리
- 개별 알레르기/선호도 추적
- 주방 장비 추적

### 5. Authentication (Naver OAuth)
**엔드포인트**: `/api/auth/*`

**기능:**
- Naver OAuth 2.0 통합
- 첫 로그인 시 자동 회원 생성/업데이트
- State 기반 CSRF 보호
- 프로필 동기화 (이메일, 닉네임, 생일, 사진)

### 6. Ranking System (Cache-based)
**엔드포인트**: `/api/rankings/*`

**기능:**
- 실시간 인기 레시피 랭킹
- MongoDB 기반 랭킹 데이터
- 성능을 위한 인메모리 캐싱
- 날짜 기반 랭킹 (KST 타임존)
- 레시피 프리뷰 카드 (제목, 작성자, 이미지)

### 7. Voice Service (STT + TTS)
**주요 엔드포인트:**
- `POST /api/voice/stt` - 완전성 분석을 통한 음성-텍스트 변환
- `POST /api/voice/process-text` - 텍스트-LLM-TTS 파이프라인
- `POST /api/voice/process` - 전체 음성 파이프라인
- `POST /api/voice/session` - 음성 세션 생성
- `POST /api/voice/save-history` - 음성 대화 저장
- `GET /api/voice/history/{id}` - 음성 히스토리 조회

**기능:**
- Naver CLOVA Speech STT
- 음성 완전성 감지
- LLM 응답 생성
- TTS 오디오 스트리밍
- 음성 데이터 영속성

### 8. MyPage (Personalization)
**엔드포인트**: `/api/mypage/*`

**기능:**
- 통합 프로필 로드
- 가족 관리 (CRUD)
- 개인화 설정 (알레르기/선호도)
- 조리 도구 선택
- 게스트 vs 등록 사용자 처리
- 조리 도구 마스터 데이터 시딩

## 🚀 설치 및 실행

### 사전 요구사항
- **Node.js**: 18.x 이상
- **Python**: 3.11
- **Docker**: 최신 버전
- **MySQL**: 8.x
- **Milvus**: 2.6.9
- **MongoDB**: 최신 버전

### Frontend 설치 및 실행

```bash
cd frontend

# 의존성 설치
npm install

# 개발 서버 실행 (localhost:5173)
npm run dev

# 프로덕션 빌드
npm run build

# 프리뷰 모드
npm run preview
```

### Backend 설치 및 실행

```bash
cd backend

# 가상환경 생성
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# 환경 변수 설정
cp .env.example .env
# .env 파일 편집 (아래 "환경 변수" 섹션 참고)

# 개발 서버 실행 (localhost:8080)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8080

# 프로덕션 모드
uvicorn app.main:app --host 0.0.0.0 --port 8080
```

### Docker로 실행 (권장)

```bash
# Frontend Docker 실행
cd frontend
docker build -t recipeu-frontend .
docker run -p 5173:80 recipeu-frontend

# Backend Docker 실행
cd backend
docker build -t recipeu-backend .
docker run -p 8080:8080 recipeu-backend
```

## 📝 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 자세한 내용은 [LICENSE](LICENSE) 파일을 참조하세요.

<div align="center">

**Made with ❤️ by RecipeU Team**

*네이버 부스트캠프 AI Tech 8기 NLP 트랙*

**[Website](https://recipeu.site)** • **[Report](docs/final_report.pdf)**

</div>
