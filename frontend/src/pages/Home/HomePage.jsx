// src/pages/Home/HomePage.jsx
// src/pages/Home/HomePage.jsx
import { useNavigate } from "react-router-dom";
import { useState, useEffect } from "react";  // useState, useEffect 추가
import BottomNav from "@/components/BottomNav";
import weatherComments from "@/data/weatherComments.json";
import "./HomePage.css";

export default function HomePage() {
  const navigate = useNavigate();
  const API_URL = import.meta.env.VITE_API_URL || "http://211.188.62.72:8080";  // 추가
  
  // 날씨 상태 추가
  const [weather, setWeather] = useState({
    temp: "3°",
    desc: "약간흐림",
    icon: "/main-weather.png"
  });
  
  const [loading, setLoading] = useState(true);
  const [myRecipeCount, setMyRecipeCount] = useState(0);
  const [speechBubble, setSpeechBubble] = useState({
    comment: "날이 많이 쌀쌀하네요!\n오늘은 김이 모락모락 나는 국물 요리 어떠세요?",
    recommendation: ""
  });
  const [isBirthday, setIsBirthday] = useState(false);

  const memberStr = localStorage.getItem("member");
  const member = memberStr ? JSON.parse(memberStr) : null;
  const memberId = member?.id || 0;

  // 날씨 데이터 가져오기
  useEffect(() => {
    const init = async () => {
      const isBirthdayToday = await checkBirthday(); // 생일 체크를 먼저 실행하고 결과 받기
      fetchWeather(isBirthdayToday); // 생일 여부를 전달하며 날씨 정보 가져오기
      fetchMyRecipeCount();
    };
    init();
  }, []);

  // 날씨 상태에 따른 아이콘 매핑 함수
  const getWeatherIcon = (weatherDesc) => {
    const desc = weatherDesc.toLowerCase();

    if (desc.includes('맑') || desc.includes('clear') || desc.includes('sunny')) {
      return '/sun.png';
    } else if (desc.includes('비') || desc.includes('rain')) {
      return '/rain.png';
    } else if (desc.includes('눈') || desc.includes('snow')) {
      return '/snow.png';
    } else if (desc.includes('번개') || desc.includes('thunder') || desc.includes('storm')) {
      return '/storm.png';
    } else if (desc.includes('바람') || desc.includes('wind')) {
      return '/wind.png';
    } else if (desc.includes('흐') || desc.includes('구름') || desc.includes('cloud')) {
      return '/cloud.png';
    } else {
      return '/main-weather.png';
    }
  };

  // 날씨 설명 짧게 변환하는 함수
  const getShortWeatherDesc = (weatherDesc) => {
    const desc = weatherDesc.toLowerCase();

    if (desc.includes('맑')) return '맑음';
    if (desc.includes('비')) return '비';
    if (desc.includes('눈')) return '눈';
    if (desc.includes('번개') || desc.includes('storm')) return '천둥번개';
    if (desc.includes('바람')) return '바람';
    if (desc.includes('흐') || desc.includes('구름')) return '흐림';

    return weatherDesc;
  };

  // 시간대 계산 함수
  const getTimeOfDay = () => {
    const hour = new Date().getHours();
    if (hour >= 6 && hour < 12) return '아침';
    if (hour >= 12 && hour < 18) return '점심';
    if (hour >= 18 && hour < 24) return '저녁';
    return '새벽';
  };

  // 온도 범주 계산 함수
  const getTempCategory = (temp) => {
    if (temp < 10) return '추움';
    if (temp > 25) return '더움';
    return '쾌적';
  };

  // 날씨 카테고리 매핑 함수
  const getWeatherCategory = (weatherDesc) => {
    const desc = weatherDesc.toLowerCase();
    if (desc.includes('맑') || desc.includes('clear')) return '맑음';
    if (desc.includes('비') || desc.includes('rain')) return '비옴';
    if (desc.includes('눈') || desc.includes('snow')) return '눈옴';
    return '구름 낌';
  };

  // 날씨 기반 코멘트 가져오기
  const getWeatherComment = (temp, weatherDesc) => {
    const timeOfDay = getTimeOfDay();
    const tempCategory = getTempCategory(temp);
    const weatherCategory = getWeatherCategory(weatherDesc);

    const matchedComment = weatherComments.find(
      (item) =>
        item.time === timeOfDay &&
        item.temp === tempCategory &&
        item.weather === weatherCategory
    );

    if (matchedComment) {
      return {
        comment: matchedComment.comment,
        recommendation: matchedComment.recommendation
      };
    }

    // 매칭 실패 시 기본값
    return {
      comment: "날이 많이 쌀쌀하네요!\n오늘은 김이 모락모락 나는 국물 요리 어떠세요?",
      recommendation: ""
    };
  };


  const fetchWeather = async (isBirthdayToday = false) => {
    try {
      if ("geolocation" in navigator) {
        navigator.geolocation.getCurrentPosition(
          async (position) => {
            const lat = position.coords.latitude;
            const lon = position.coords.longitude;

            const response = await fetch(
              `${API_URL}/api/weather/location?lat=${lat}&lon=${lon}`
            );

            if (response.ok) {
              const data = await response.json();
              const bubbleContent = getWeatherComment(data.temp, data.weather_desc);

              if (!isBirthdayToday) {
                setSpeechBubble(bubbleContent);
              }

              setWeather({
                temp: `${Math.round(data.temp)}°`,
                desc: getShortWeatherDesc(data.weather_desc),
                icon: getWeatherIcon(data.weather_desc)
              });
            }
            setLoading(false);
          },
          () => {
            fetchWeatherByCity("서울강남구", isBirthdayToday);
          },
          {
            enableHighAccuracy: false,
            timeout: 5000,
            maximumAge: 300000
          }
        );
      } else {
        fetchWeatherByCity("서울강남구", isBirthdayToday);
      }
    } catch (error) {
      console.error("날씨 API 에러:", error);
      setLoading(false);
    }
  };

  const fetchMyRecipeCount = async () => {
    try {
      const response = await fetch(`${API_URL}/api/recipe/list?member_id=${memberId}`);
      if (!response.ok) return;
      const data = await response.json();
      setMyRecipeCount((data.recipes || []).length);
    } catch (error) {
      console.error("마이 레시피 개수 불러오기 실패:", error);
    }
  };

const checkBirthday = async () => {
  try {
    // 디버깅용: 임시로 오늘을 생일로 가정
    const FORCE_BIRTHDAY_TEST = false;

    if (FORCE_BIRTHDAY_TEST) {
      setIsBirthday(true);
      setSpeechBubble({
        comment: "일 년 중 가장 소중한 생일을 진심으로 축하드려요!\n행복을 기원하며 따뜻한 미역국 한 그릇은 어떨까요?",
        recommendation: ""
      });
      return true;
    }

    if (memberId === 0) {
      return false;
    }

    const response = await fetch(`${API_URL}/api/user/profile?member_id=${memberId}`);

    if (!response.ok) {
      return false;
    }

    const data = await response.json();
    const birthday = data.birthday;

    if (!birthday) {
      return false;
    }

    const today = new Date();
    const todayMonth = String(today.getMonth() + 1).padStart(2, '0');
    const todayDay = String(today.getDate()).padStart(2, '0');
    const todayStr = `${todayMonth}-${todayDay}`;

    if (birthday === todayStr || birthday === `${todayMonth}${todayDay}`) {
      setIsBirthday(true);
      setSpeechBubble({
        comment: "일 년 중 가장 소중한 생일을 진심으로 축하드려요!\n행복을 기원하며 따뜻한 미역국 한 그릇은 어떨까요?",
        recommendation: ""
      });
      return true;
    } else {
      setIsBirthday(false);
      return false;
    }
  } catch (error) {
    console.error("생일 확인 실패:", error);
    return false;
  }
};


const fetchWeatherByCity = async (city, isBirthdayToday = false) => {
  try {
    const response = await fetch(`${API_URL}/api/weather/current?city=${city}`);

    if (response.ok) {
      const data = await response.json();
      const bubbleContent = getWeatherComment(data.temp, data.weather_desc);

      if (!isBirthdayToday) {
        setSpeechBubble(bubbleContent);
      }

      setWeather({
        temp: `${Math.round(data.temp)}°`,
        desc: getShortWeatherDesc(data.weather_desc),
        icon: getWeatherIcon(data.weather_desc)
      });
    }
  } catch (error) {
    console.error("폴백 날씨 API 에러:", error);
  } finally {
    setLoading(false);
  }
};

  return (
    <div className="home-container">
      <div className="home-bg" />

      {/* 날씨 박스 - 동적 데이터로 변경 */}
      <div className="weather-box">
        <img src={weather.icon} alt="날씨" />
        <span className="weather-temp">{weather.temp}</span>
        <span className="weather-desc">{weather.desc}</span>
      </div>

      <img
        src="/main-profile.png"
        alt="프로필"
        className="profile-icon"
        onClick={() => navigate("/mypage")}
        style={{ cursor: "pointer" }}
      />

      <div className="speech-bubble">
          {speechBubble.comment.split('\n').map((line, i) => (
          <span key={i}>
            {line}
            {i < speechBubble.comment.split('\n').length - 1 && <br />}
          </span>
        ))}
      </div>

      <img
        src={isBirthday ? "/birthday-main-character.png" : "/main-character.png"}
        alt="캐릭터"
        className="main-character"
      />

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
              <span className="highlight">{myRecipeCount}개</span>
            </div>

            <h3>마이 레시피</h3>
            <p>
              이전에 함께 만들었던,
              <br />
              레시피를 확인해요!
            </p>
          </div>

          {/* TOP 100 레시피 */}
          <div
            className="card small"
            onClick={() => navigate("/recipes")}
            style={{ cursor: "pointer" }}
          >
            <div className="card-small-top">
              <img src="/main-profile.png" className="card-icon" alt="감자" />
            </div>

            <h3>TOP 100 레시피</h3>
            <p>
              인기 있는 다른 레시피가
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
