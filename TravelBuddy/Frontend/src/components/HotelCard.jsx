import React from 'react';
import './Cards.css';

const HotelCard = ({ hotel }) => {
  return (
    <div className="card hotel-card">
      <div className="card-content">
        <h3>{hotel.name}</h3>
        <div className="rating">
          <span>⭐ {hotel.reviews.avg_rating}</span>
          <span>({hotel.reviews.total_reviews} reviews)</span>
        </div>
        <p className="location">
          {hotel.location.city}, {hotel.location.district}
        </p>
        <p className="price">From ₹{hotel.pricing.base_price_inr} per night</p>
        <div className="amenities">
          <h4>Key Amenities:</h4>
          <ul>
            {hotel.features.amenities.slice(0, 4).map((amenity, index) => (
              <li key={index}>{amenity.replace(/_/g, ' ')}</li>
            ))}
          </ul>
        </div>
        <div className="tags">
          {hotel.best_for.slice(0, 3).map((tag, index) => (
            <span key={index} className="tag">
              {tag.replace(/_/g, ' ')}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
};

export default HotelCard;