import React from 'react';
import { Play } from 'lucide-react';

const MediaPresence = () => {
  const videoCards = [
    {
      id: 1,
      title: "Exclusive Interview with",
      speaker: "Shri Piyush Goyal",
      position: "Minister of Commerce & Industry",
      description: "Export Opportunities for MSMEs",
      details: "Exploring global market opportunities and export strategies for small and medium enterprises in the post-pandemic world.",
      buttonText: "Watch Interview",
      gradient: "from-blue-600 to-purple-600"
    },
    {
      id: 2,
      title: "In Conversation with",
      speaker: "Shri Giriraj Singh",
      position: "Minister of MSME",
      description: "Future of MSME Sector",
      details: "Discussing government initiatives, policy reforms, and the roadmap for MSME growth in India's developing economy.",
      buttonText: "Watch Discussion",
      gradient: "from-emerald-500 to-teal-600"
    },
    {
      id: 3,
      title: "Banking Insights with",
      speaker: "Smt. Arundhati Bhattacharya",
      position: "Former SBI Chairperson",
      description: "MSME Banking Solutions",
      details: "Insights on banking innovations, credit solutions, and financial inclusion strategies for small businesses.",
      buttonText: "Watch Insights",
      gradient: "from-orange-500 to-amber-500"
    }
  ];

  const guestCategories = [
    "Cabinet Ministers",
    "Banking Leaders", 
    "Industry Experts",
    "Policy Makers"
  ];

  return (
    <div className="bg-gray-200 min-h-screen py-8 md:py-16">
      <div className="container mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header Section */}
        <div className="text-center mb-12 md:mb-16">
          <h1 className="text-3xl sm:text-4xl lg:text-5xl font-bold text-gray-900 mb-4">
            Media <span className="text-blue-600">Presence</span>
          </h1>
          <div className="w-16 h-1 bg-blue-600 mx-auto mb-6"></div>
          <p className="text-gray-600 text-lg sm:text-xl max-w-4xl mx-auto leading-relaxed">
            Engaging conversations with India's top leaders, ministers, and industry experts on 'Positive Talk'
          </p>
        </div>

        {/* Video Cards Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 lg:gap-8 mb-16 md:mb-20">
          {videoCards.map((card) => (
            <div key={card.id} className="bg-white rounded-2xl shadow-lg hover:shadow-xl transition-all duration-300 overflow-hidden group">
              {/* Video Thumbnail with Gradient */}
              <div className={`relative h-48 sm:h-56 bg-gradient-to-br ${card.gradient} flex items-center justify-center`}>
                <div className="absolute inset-0 bg-black bg-opacity-10"></div>
                <div className="relative z-10 text-center text-white px-4">
                  <div className="w-16 h-16 bg-white bg-opacity-20 rounded-full flex items-center justify-center mb-4 mx-auto group-hover:bg-opacity-30 transition-all duration-300">
                    <Play className="w-8 h-8 text-white ml-1" />
                  </div>
                  <p className="text-sm font-medium opacity-90 mb-2">{card.title}</p>
                  <h3 className="text-xl sm:text-2xl font-bold mb-1">{card.speaker}</h3>
                  <p className="text-sm opacity-80">{card.position}</p>
                </div>
              </div>

              {/* Card Content */}
              <div className="p-6">
                <h4 className="text-xl font-bold text-gray-900 mb-3">
                  {card.description}
                </h4>
                <p className="text-gray-600 text-sm leading-relaxed mb-6">
                  {card.details}
                </p>
                <button className="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 px-6 rounded-lg transition-colors duration-300">
                  {card.buttonText}
                </button>
              </div>
            </div>
          ))}
        </div>

        {/* Distinguished Guests Section */}
        <div className=" rounded-2xl shadow-lg p-8 md:p-12">
          <h2 className="text-2xl sm:text-3xl lg:text-4xl font-bold text-gray-900 text-center mb-8 md:mb-12">
            Distinguished Guests on Positive Talk
          </h2>

          {/* Category Tabs */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8 md:mb-12">
            {guestCategories.map((category, index) => (
              <div
                key={index}
                className="bg-gray-100 hover:bg-gray-200 text-gray-700 font-medium py-4 px-4 sm:px-6 rounded-lg text-center transition-colors duration-300 cursor-pointer"
              >
                <span className="text-sm sm:text-base">{category}</span>
              </div>
            ))}
          </div>

          {/* Explore Button */}
          <div className="text-center">
            <button className="bg-orange-500 hover:bg-orange-600 text-white font-semibold py-4 px-8 rounded-lg transition-colors duration-300 text-lg">
              Explore All Episodes
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MediaPresence;