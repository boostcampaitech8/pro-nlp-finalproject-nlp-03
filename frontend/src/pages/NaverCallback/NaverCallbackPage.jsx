import { useEffect, useState } from "react";
import { useNavigate, useSearch } from "@tanstack/react-router";

const API_URL = import.meta.env.VITE_API_URL || "";

export default function NaverCallbackPage() {
  const navigate = useNavigate();
  const searchParams = useSearch({ from: '/naver-callback' });
  const [error, setError] = useState(null);

  useEffect(() => {
    const handleNaverCallback = async () => {
      const code = searchParams.code;
      const state = searchParams.state;

      if (!code || !state) {
        setError("인증 정보가 없습니다.");
        return;
      }

      try {
        const response = await fetch(`${API_URL}/api/auth/naver/callback`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ code, state }),
        });

        const data = await response.json();

        if (response.ok) {
          localStorage.setItem("token", data.token);
          localStorage.setItem("userId", data.userId);
          navigate({ to: "/home" });
        } else {
          setError(data.message || "로그인 실패");
        }
      } catch (err) {
        console.error("네이버 로그인 에러:", err);
        setError("로그인 처리 중 오류가 발생했습니다.");
      }
    };

    handleNaverCallback();
  }, [searchParams, navigate]);

  if (error) {
    return <div>에러: {error}</div>;
  }

  return <div>네이버 로그인 처리 중...</div>;
}
