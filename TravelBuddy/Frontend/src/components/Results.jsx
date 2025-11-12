import React from 'react';
import HotelCard from './HotelCard';
import AttractionCard from './AttractionCard';
import './Cards.css';

const Results = ({ hotels, attractions, activeTab = 'hotels' }) => {
  return (
    <div className="results-container">
      <div className="tab-buttons">
        <button 
          className={`tab-button ${activeTab === 'hotels' ? 'active' : ''}`}
          onClick={() => activeTab = 'hotels'}
        >
          Hotels
        </button>
        <button 
          className={`tab-button ${activeTab === 'attractions' ? 'active' : ''}`}
          onClick={() => activeTab = 'attractions'}
        >
          Attractions
        </button>
      </div>

      <div className="cards-grid">
        {activeTab === 'hotels' && hotels?.map(hotel => (
          <HotelCard key={hotel.id} hotel={hotel} />
        ))}
        
        {activeTab === 'attractions' && attractions?.map(attraction => (
          <AttractionCard key={attraction.id} attraction={attraction} />
        ))}
      </div>
    </div>
  );
};

export default Results;