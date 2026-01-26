import { useNavigate } from "react-router-dom";
import Button from "@/components/Button";

export default function SplashPage() {
  const navigate = useNavigate();

  const goHome = () => {
    navigate("/home");
  };

  return (
    <div className="splash-container">
      <div className="splash-content">
        <Button onClick={goHome}>로그인 없이 사용해보기</Button>
      </div>
    </div>
  );
}
