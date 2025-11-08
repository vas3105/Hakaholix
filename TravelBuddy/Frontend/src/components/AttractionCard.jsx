import React from 'react';
import './Cards.css';

const AttractionCard = ({ attraction }) => {
  return (
    <div className="card attraction-card">
      <div className="card-content">
        <h3>{attraction.name}</h3>
        <p className="type">Type: {attraction.details.type}</p>
        <p className="location">City: {attraction.location.city}</p>
        <p className="duration">Duration: {attraction.details.duration_hours} hours</p>
        <p className="fee">Entry Fee: ₹{attraction.details.entry_fee_inr}</p>
        <p className="timing">Hours: {attraction.details.operating_hours}</p>
        <div className="tips">
          <h4>Insider Tips:</h4>
          <ul>
            {attraction.insider_tips.map((tip, index) => (
              <li key={index}>{tip}</li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
};

export default AttractionCard;