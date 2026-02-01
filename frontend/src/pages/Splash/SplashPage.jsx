import { useNavigate } from "react-router-dom";
import "./SplashPage.css";

export default function SplashPage() {
  const navigate = useNavigate();

  const goHome = () => {
    navigate("/home");
  };

  const goNaverLogin = () => {
    // TODO: 네이버 로그인 구현
  };

  return (
    <div className="splash-container">
      {/* RecipeU */}
      <p className="splash-recipeu">RecipeU</p>

      {/* 레시퓨 */}
      <div className="splash-title-row">
        <span className="splash-title-char splash-title-char--reo">레</span>
        <span className="splash-title-char splash-title-char--si">시</span>
        <span className="splash-title-char splash-title-char--pyu">퓨</span>
      </div>

      {/* 캐릭터 이미지 */}
      <img
        src="/splash-potato.png"
        alt="레시퓨 캐릭터"
        className="splash-character-img"
      />

      {/* 네이버 로그인 */}
      <button className="splash-naver-btn" onClick={goNaverLogin}>
        <img
          src="/login-naver.png"
          alt="네이버 로그인"
          className="splash-naver-btn-img"
        />
      </button>

      {/* 로그인 없이 사용해보기 */}
      <button className="splash-guest-btn" onClick={goHome}>
        로그인 없이 사용해보기
      </button>
    </div>
  );
}
