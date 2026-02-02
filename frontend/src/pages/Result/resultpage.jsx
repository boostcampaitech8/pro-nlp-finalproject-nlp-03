import React, { useState } from 'react';
import './FoodReview.css';

const FoodReview = () => {
  const [rating, setRating] = useState(0);

  const handleStarClick = (index) => {
    setRating(index + 1);
  };

  return (
    <div className="food-review-container">
      {/* Header */}
      <div className="header">
        <div className="time">9:41</div>
        <div className="status-icons">
          <span className="signal">📶</span>
          <span className="wifi">📡</span>
          <span className="battery">🔋</span>
        </div>
      </div>

      {/* Logo */}
      <div className="logo">
        <img src="/logo.png" alt="조리포트 로고" />
      </div>

      {/* Main Content */}
      <div className="content-card">
        <h2 className="title">오늘의 요리가 끝났어요</h2>
        <p className="subtitle">
          맛있게 잘먹었는지~.~?<br />
          <span className="highlight">마스터리얼 낙지볶음 ≥</span>
        </p>

        <div className="order-info">
          총 3.3시간 00:14:34
        </div>

        {/* Food Image */}
        <div className="food-image">
          <img src="/food-sample.jpg" alt="낙지볶음" />
        </div>

        {/* Star Rating */}
        <div className="star-rating">
          {[0, 1, 2].map((index) => (
            <span
              key={index}
              className={`star ${index < rating ? 'filled' : ''}`}
              onClick={() => handleStarClick(index)}
            >
              ⭐
            </span>
          ))}
        </div>

        {/* Action Buttons */}
        <div className="button-group">
          <button className="btn btn-share">
            메이킹 사진과<br />동영상보기
          </button>
          <button className="btn btn-review">
            연달콩레모
          </button>
        </div>
      </div>
    </div>
  );
};

export default FoodReview;