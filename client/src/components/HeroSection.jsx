import React from "react";
import { User, Trophy } from "lucide-react";

const HeroSection = () => {
  return (
    <section className="bg-slate-800 text-white py-16">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid lg:grid-cols-2 gap-12 items-center">
          {/* Left Content */}
          <div>
            <div className="flex items-center mb-6">
              <Trophy className="w-5 h-5 text-orange-400 mr-2" />
              <span className="text-sm font-medium text-gray-300">
                India's Leading MSME Expert
              </span>
            </div>

            <h1 className="text-5xl font-bold mb-6 leading-tight">
              Transforming <br />
              <span className="text-orange-400">India's</span> <br />
              MSME Future
            </h1>

            <p className="text-xl text-gray-300 mb-8 leading-relaxed">
              35+ Years of Excellence | 1M+ Digital Community <br /> | Top 200
              LinkedIn Creator | Policy Advisor to PM
            </p>

            <div className="flex flex-col sm:flex-row gap-4 mb-12">
              <button className="bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 px-8 rounded-lg transition-colors duration-200">
                Discover Journey
              </button>
              <button className="bg-orange-500 hover:bg-orange-600 text-white font-semibold py-3 px-8 rounded-lg transition-colors duration-200">
                Connect Now
              </button>
            </div>

            {/* Stats */}
            <div className="grid grid-cols-4 gap-6">
              <div>
                <div className="text-3xl font-bold text-gray-400">35+</div>
              </div>
              <div>
                <div className="text-3xl font-bold text-gray-400">1.0M+</div>
              </div>
              <div>
                <div className="text-3xl font-bold text-gray-400">32K+</div>
              </div>
              <div>
                <div className="text-3xl font-bold text-gray-400">200+</div>
              </div>
            </div>
          </div>

          {/* Right Profile Card */}
          <div className="flex justify-center lg:justify-end">
            <div className="bg-gray-100 rounded-2xl p-8 max-w-md w-full">
              {/* Profile Image */}
              <div className="flex justify-center mb-6">
                <div className="relative">
                  <div className="w-32 h-32 bg-gray-300 rounded-full flex items-center justify-center border-4 border-blue-600">
                    <User className="w-16 h-16 text-gray-500" />
                  </div>
                  <div className="absolute -bottom-2 left-1/2 transform -translate-x-1/2 bg-blue-600 text-white text-xs px-3 py-1 rounded-full">
                    CA • MSME Expert
                  </div>
                </div>
              </div>

              {/* Profile Info */}
              <div className="text-center mb-6">
                <h3 className="text-2xl font-bold text-gray-900 mb-2">
                  Mukesh Mohan Gupta
                </h3>
                <p className="text-gray-600 text-sm leading-relaxed">
                  India's Most Trusted MSME Advisor & Digital Transformation
                  Leader
                </p>
              </div>

              {/* Metrics */}
              <div className="grid grid-cols-2 gap-4">
                <div className="bg-white p-4 rounded-lg text-center shadow-sm">
                  <div className="text-2xl font-bold text-blue-600 mb-1">CA</div>
                  <div className="text-xs text-gray-500">
                    Chartered Accountant
                  </div>
                </div>
                <div className="bg-white p-4 rounded-lg text-center shadow-sm">
                  <div className="text-2xl font-bold text-orange-500 mb-1">
                    35+
                  </div>
                  <div className="text-xs text-gray-500">Years Excellence</div>
                </div>
                <div className="bg-white p-4 rounded-lg text-center shadow-sm">
                  <div className="text-2xl font-bold text-green-500 mb-1">
                    1M+
                  </div>
                  <div className="text-xs text-gray-500">Followers</div>
                </div>
                <div className="bg-white p-4 rounded-lg text-center shadow-sm">
                  <div className="text-2xl font-bold text-red-500 mb-1">
                    Top 200
                  </div>
                  <div className="text-xs text-gray-500">LinkedIn Creator</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default HeroSection;
