import "./ButtonRed.css";

export default function CookStartButton({
  onClick,
  children = "레시피 생성하기",
}) {
  return (
    <button className="cook-start-btn" onClick={onClick}>
      {children}
    </button>
  );
}
