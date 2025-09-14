import React from "react";
import { User } from "lucide-react";

function App() {
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {/* Hero Section */}
        <div className="text-center mb-16">
          <h2 className="text-5xl font-bold text-gray-900 mb-4">
            Inspiring <span className="text-orange-500">Conversations</span>
          </h2>
          <div className="w-24 h-1 bg-orange-500 mx-auto mb-6"></div>
          <p className="text-xl text-gray-600 max-w-4xl mx-auto leading-relaxed">
            Sharing insights and expertise at prestigious forums, conferences,
            and
            <br />
            institutions across India and globally
          </p>
        </div>

        {/* Two Column Layout */}
        <div className="flex gap-8 p-8 bg-gray-50 min-h-screen">
      {/* Speaking Expertise Section */}
      <div className="flex-1">
        <h2 className="text-3xl font-bold text-gray-900 mb-8">Speaking Expertise</h2>
        
        <div className="space-y-4">
          {/* MSME Growth Strategies */}
          <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100 flex items-center gap-4">
            <div className="w-3 h-3 bg-blue-500 rounded-full flex-shrink-0"></div>
            <p className="text-gray-700 font-medium">MSME Growth Strategies & Business Development</p>
          </div>
          
          {/* Financial Management */}
          <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100 flex items-center gap-4">
            <div className="w-3 h-3 bg-yellow-500 rounded-full flex-shrink-0"></div>
            <p className="text-gray-700 font-medium">Financial Management & Investment Planning</p>
          </div>
          
          {/* Digital Transformation - Highlighted */}
          <div className="bg-gradient-to-r from-green-100 to-blue-100 rounded-2xl p-6 shadow-sm border border-green-200 flex items-center gap-4">
            <div className="w-3 h-3 bg-green-500 rounded-full flex-shrink-0"></div>
            <p className="text-gray-700 font-medium">Digital Transformation & Technology Adoption</p>
          </div>
          
          {/* Policy Reforms */}
          <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100 flex items-center gap-4">
            <div className="w-3 h-3 bg-purple-500 rounded-full flex-shrink-0"></div>
            <p className="text-gray-700 font-medium">Policy Reforms & Government Initiatives</p>
          </div>
          
          {/* Entrepreneurship */}
          <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100 flex items-center gap-4">
            <div className="w-3 h-3 bg-blue-600 rounded-full flex-shrink-0"></div>
            <p className="text-gray-700 font-medium">Entrepreneurship & Leadership Development</p>
          </div>
        </div>
      </div>
      
      {/* Speaking Partners Section */}
      <div className="w-96">
        <div className="bg-gradient-to-br from-purple-100 via-blue-50 to-green-50 rounded-3xl p-8 shadow-lg">
          {/* Header */}
          <h2 className="text-2xl font-bold text-gray-800 mb-8">Speaking Partners</h2>
          
          {/* Partners Grid */}
          <div className="grid grid-cols-2 gap-4 mb-8">
            {/* Ministry of MSME */}
            <div className="bg-white bg-opacity-70 backdrop-blur-sm rounded-2xl p-4 shadow-sm border border-white border-opacity-50">
              <p className="text-gray-700 font-medium text-center">Ministry of MSME</p>
            </div>
            
            {/* SIDBI */}
            <div className="bg-white bg-opacity-70 backdrop-blur-sm rounded-2xl p-4 shadow-sm border border-white border-opacity-50">
              <p className="text-gray-700 font-medium text-center">SIDBI</p>
            </div>
            
            {/* SBI Foundation */}
            <div className="bg-white bg-opacity-70 backdrop-blur-sm rounded-2xl p-4 shadow-sm border border-white border-opacity-50">
              <p className="text-gray-700 font-medium text-center">SBI Foundation</p>
            </div>
            
            {/* SEBI */}
            <div className="bg-white bg-opacity-70 backdrop-blur-sm rounded-2xl p-4 shadow-sm border border-white border-opacity-50">
              <p className="text-gray-700 font-medium text-center">SEBI</p>
            </div>
            
            {/* RBI */}
            <div className="bg-white bg-opacity-70 backdrop-blur-sm rounded-2xl p-4 shadow-sm border border-white border-opacity-50">
              <p className="text-gray-700 font-medium text-center">RBI</p>
            </div>
            
            {/* CII */}
            <div className="bg-white bg-opacity-70 backdrop-blur-sm rounded-2xl p-4 shadow-sm border border-white border-opacity-50">
              <p className="text-gray-700 font-medium text-center">CII</p>
            </div>
          </div>
          
          {/* Book Speaking Engagement Button */}
          <button className="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-4 px-6 rounded-2xl shadow-md transition duration-200 ease-in-out transform hover:scale-105">
            Book Speaking Engagement
          </button>
        </div>
      </div>
    </div>
      </main>
    </div>
  );
}

export default App;
