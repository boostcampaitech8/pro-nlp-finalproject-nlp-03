// src/pages/Home/HomePage.jsx
import { useNavigate } from "react-router-dom";
import BottomNav from "@/components/BottomNav";
import "./HomePage.css";

export default function HomePage() {
  const navigate = useNavigate();

  return (
    <div className="home-container">
      <div className="home-bg" />

      <div className="weather-box">
        <img src="/main-weather.png" alt="날씨" />
        <span className="weather-temp">3°</span>
        <span className="weather-desc">약간흐림</span>
      </div>

      <img
        src="/main-profile.png"
        alt="프로필"
        className="profile-icon"
        onClick={() => navigate("/mypage")}
        style={{ cursor: "pointer" }}
      />

      <div className="speech-bubble">
        날이 많이 쌀쌀하네요!
        <br />
        오늘은 김이 모락모락 나는 국물 요리 어떠세요?
      </div>

      <img src="/main-character.png" alt="캐릭터" className="main-character" />

      <div className="home-scroll">
        {/* 메인 카드 - 채팅으로 이동 */}
        <div
          className="card card-large"
          onClick={() => navigate("/cook-start")}
          style={{ cursor: "pointer" }}
        >
          <img src="/main-profile.png" className="card-icon" alt="감자" />

          <div className="card-text">
            <h3>오늘의 맞춤 레시피는?</h3>
            <p>
              오늘 뭐 먹어야할지 모르겠다면?
              <br />
              지금 바로 맞춤 레시피를 알아보세요!
            </p>
          </div>

          <img src="/main-next.png" className="card-action" alt="이동" />
        </div>

        {/* 챗봇 카드 - 채팅으로 이동 */}
        <div
          className="card"
          onClick={() => navigate("/chat")}
          style={{ cursor: "pointer" }}
        >
          <img src="/main-profile.png" className="card-icon" alt="감자" />
          <div className="card-text">
            <h3>요리하다가 궁금한게 있으신가요?</h3>
            <p>요리 도우미 챗봇에게 언제든지 물어보세요!</p>
          </div>
        </div>

        <div className="card-row">
          {/* 마이 레시피 */}
          <div
            className="card small"
            onClick={() => navigate("/recipes/my")}
            style={{ cursor: "pointer" }}
          >
            <div className="card-small-top">
              <img src="/main-profile.png" className="card-icon" alt="감자" />
              <span className="highlight">N개</span>
            </div>

            <h3>마이 레시피</h3>
            <p>
              이전에 함께 만들었던,
              <br />
              레시피를 확인해요!
            </p>
          </div>

          {/* 전체 레시피 */}
          <div
            className="card small"
            onClick={() => navigate("/recipes")}
            style={{ cursor: "pointer" }}
          >
            <div className="card-small-top">
              <img src="/main-profile.png" className="card-icon" alt="감자" />
            </div>

            <h3>전체 레시피</h3>
            <p>
              또 다른 레시피가
              <br />
              궁금하다면?
            </p>
          </div>
        </div>
      </div>

      <BottomNav />
    </div>
  );
}
