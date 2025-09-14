import React from 'react';
import { Zap, Users, Monitor, CheckCircle, Building, BookOpen, Menu, X } from 'lucide-react';

function App() {
  const [isMenuOpen, setIsMenuOpen] = React.useState(false);

  const achievementCards = [
    {
      icon: <Zap className="w-8 h-8 text-white" />,
      iconBg: "bg-blue-500",
      title: "LinkedIn Top Creator",
      description: "Selected among Top 200 LinkedIn Creators in India for exceptional MSME content and thought leadership",
      statistic: "#200",
      statisticColor: "text-blue-600"
    },
    {
      icon: <Users className="w-8 h-8 text-white" />,
      iconBg: "bg-orange-500",
      title: "MSME Network Leader",
      description: "Built India's largest MSME advisory network connecting 32,000+ advisors and entrepreneurs nationwide",
      statistic: "32K+",
      statisticColor: "text-orange-600"
    },
    {
      icon: <Monitor className="w-8 h-8 text-white" />,
      iconBg: "bg-teal-500",
      title: "YouTube Pioneer",
      description: "Created MSME Helpline - India's largest business education platform with over 1 million subscribers",
      statistic: "1M+",
      statisticColor: "text-teal-600"
    },
    {
      icon: <CheckCircle className="w-8 h-8 text-white" />,
      iconBg: "bg-purple-500",
      title: "Innovation Platform",
      description: "Launched NoDefaulters.com - India's first comprehensive MSME payment and credit platform",
      statistic: "#1",
      statisticColor: "text-purple-600"
    },
    {
      icon: <Building className="w-8 h-8 text-white" />,
      iconBg: "bg-blue-600",
      title: "Corporate Leadership",
      description: "Former Director at prestigious institutions including Dena Bank, Hindustan Fertilizers, and more",
      statistic: "Director",
      statisticColor: "text-blue-700"
    },
    {
      icon: <BookOpen className="w-8 h-8 text-white" />,
      iconBg: "bg-red-500",
      title: "Policy Advisor",
      description: "Trusted advisor to the Prime Minister's Office on MSME policies, reforms, and strategic initiatives",
      statistic: "PMO",
      statisticColor: "text-red-600"
    }
  ];

  return (
    <div className="min-h-screen bg-gray-50">

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        {/* Hero Section */}
        <div className="text-center mb-16">
          <h2 className="text-4xl md:text-5xl font-bold text-gray-900 mb-4">
            Remarkable <span className="text-blue-600">Achievements</span>
          </h2>
          <div className="w-16 h-1 bg-green-500 mx-auto mb-6"></div>
          <p className="text-lg text-gray-600 max-w-3xl mx-auto leading-relaxed">
            Transforming India's MSME landscape through innovation, leadership, and 
            unwavering commitment to excellence
          </p>
        </div>

        {/* Achievement Cards Container */}
        <div className="bg-white rounded-2xl shadow-xl p-8 md:p-12">
          {/* First Row of Cards */}
          <div className="grid md:grid-cols-3 gap-8 mb-12">
            {achievementCards.slice(0, 3).map((card, index) => (
              <div 
                key={index} 
                className="bg-white rounded-xl shadow-lg p-6 border border-gray-100 hover:shadow-xl transition-shadow duration-300"
              >
                <div className="flex flex-col items-center text-center">
                  <div className={`${card.iconBg} w-16 h-16 rounded-xl flex items-center justify-center mb-6`}>
                    {card.icon}
                  </div>
                  <h3 className="text-xl font-bold text-gray-900 mb-4">{card.title}</h3>
                  <p className="text-gray-600 text-sm leading-relaxed mb-6">{card.description}</p>
                  <div className={`text-3xl font-bold ${card.statisticColor}`}>
                    {card.statistic}
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* Second Row of Cards */}
          <div className="grid md:grid-cols-3 gap-8">
            {achievementCards.slice(3, 6).map((card, index) => (
              <div 
                key={index + 3} 
                className="bg-white rounded-xl shadow-lg p-6 border border-gray-100 hover:shadow-xl transition-shadow duration-300"
              >
                <div className="flex flex-col items-center text-center">
                  <div className={`${card.iconBg} w-16 h-16 rounded-xl flex items-center justify-center mb-6`}>
                    {card.icon}
                  </div>
                  <h3 className="text-xl font-bold text-gray-900 mb-4">{card.title}</h3>
                  <p className="text-gray-600 text-sm leading-relaxed mb-6">{card.description}</p>
                  <div className={`text-3xl font-bold ${card.statisticColor}`}>
                    {card.statistic}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;