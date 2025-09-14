import React from "react";
import { BookOpen, Zap, BarChart3 } from "lucide-react"; // ✅ Import icons

const Transformative = () => {
  return (
    <div className="min-h-screen bg-gray-100 py-12 px-4">
      <div className="max-w-6xl mx-auto">
        {/* Header Section */}
        <div className="text-center mb-16">
          <h1 className="text-5xl font-bold text-gray-800 mb-6">
            Transformative <span className="text-teal-500">Mentorship</span>
          </h1>
          <div className="w-16 h-1 bg-teal-500 mx-auto mb-8"></div>
          <p className="text-lg text-gray-600 italic max-w-3xl mx-auto leading-relaxed">
            "Mentorship is not about creating followers, but about nurturing
            leaders who will transform tomorrow." – Mukesh Mohan Gupta
          </p>
        </div>

        {/* Services Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 items-stretch">
          {/* MSME Advisory Card */}
          <div className="bg-white rounded-2xl p-8 shadow-sm hover:shadow-md transition-shadow duration-300 h-full flex flex-col">
            <div className="flex flex-col items-center text-center flex-grow">
              <div className="w-16 h-16 bg-blue-500 rounded-2xl flex items-center justify-center mb-6">
                <BookOpen className="w-8 h-8 text-white" />
              </div>
              <h3 className="text-2xl font-bold text-gray-800 mb-4">
                MSME Advisory
              </h3>
              <p className="text-gray-600 mb-8 leading-relaxed">
                Comprehensive business advisory through Swavalamban Digital
                Center, providing strategic guidance to thousands of MSMEs
              </p>
            </div>
            <button className="bg-blue-500 hover:bg-blue-600 text-white font-semibold px-8 py-3 rounded-lg transition-colors duration-200 mt-auto">
              Get Advisory
            </button>
          </div>

          {/* Startup Incubation Card */}
          <div className="bg-white rounded-2xl p-8 shadow-sm hover:shadow-md transition-shadow duration-300 h-full flex flex-col">
            <div className="flex flex-col items-center text-center flex-grow">
              <div className="w-16 h-16 bg-orange-500 rounded-2xl flex items-center justify-center mb-6">
                <Zap className="w-8 h-8 text-white" />
              </div>
              <h3 className="text-2xl font-bold text-gray-800 mb-4">
                Startup Incubation
              </h3>
              <p className="text-gray-600 mb-8 leading-relaxed">
                Partnering with SBI Foundation to incubate and mentor promising
                startups in the MSME ecosystem
              </p>
            </div>
            <button className="bg-blue-500 hover:bg-blue-600 text-white font-semibold px-8 py-3 rounded-lg transition-colors duration-200 mt-auto">
              Join Incubation
            </button>
          </div>

          {/* Growth Consulting Card */}
          <div className="bg-white rounded-2xl p-8 shadow-sm hover:shadow-md transition-shadow duration-300 h-full flex flex-col">
            <div className="flex flex-col items-center text-center flex-grow">
              <div className="w-16 h-16 bg-green-500 rounded-2xl flex items-center justify-center mb-6">
                <BarChart3 className="w-8 h-8 text-white" />
              </div>
              <h3 className="text-2xl font-bold text-gray-800 mb-4">
                Growth Consulting
              </h3>
              <p className="text-gray-600 mb-8 leading-relaxed">
                Specialized consulting for SME IPOs, business scaling, and
                strategic growth planning
              </p>
            </div>
            <button className="bg-blue-500 hover:bg-blue-600 text-white font-semibold px-8 py-3 rounded-lg transition-colors duration-200 mt-auto">
              Start Consulting
            </button>
          </div>
        </div>

        {/* Call-to-Action Section */}
        <div className="mt-20">
          <div className="bg-white rounded-3xl p-12 shadow-lg max-w-6xl mx-auto text-center">
            <h2 className="text-4xl font-bold text-gray-800 mb-6">
              Ready to Transform Your Business?
            </h2>
            <p className="text-lg text-gray-600 mb-10 max-w-2xl mx-auto leading-relaxed">
              Join thousands of successful entrepreneurs who have transformed
              their businesses with expert mentorship and strategic guidance
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
              <button className="bg-blue-500 hover:bg-blue-600 text-white font-semibold px-8 py-4 rounded-xl transition-colors duration-200 text-lg">
                Start Your Journey
              </button>
              <button className="bg-orange-400 hover:bg-orange-500 text-white font-semibold px-8 py-4 rounded-xl transition-colors duration-200 text-lg">
                Download Success Guide
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Transformative;
