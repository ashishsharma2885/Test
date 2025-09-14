import React from "react";

const About = () => {
  return (
    <section className="bg-gray-50 py-20">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section Header */}
        <div className="text-center mb-16">
          <h2 className="text-4xl md:text-5xl font-bold text-gray-900 mb-4">
            The Visionary Behind <span className="text-blue-600">MSME</span>{" "}
            <span className="text-orange-500">Revolution</span>
          </h2>
          <div className="w-16 h-1 bg-blue-600 mx-auto mb-6"></div>
          <p className="text-xl text-gray-600 max-w-4xl mx-auto leading-relaxed">
            A pioneering force in India's MSME ecosystem, bridging traditional
            business wisdom with cutting-edge innovation
          </p>
        </div>

        <div className="grid lg:grid-cols-2 gap-12 items-start">
          {/* Left Content */}
          <div className="bg-white rounded-2xl p-8 shadow-lg">
            <h3 className="text-2xl font-bold text-gray-900 mb-6">
              Journey of Excellence
            </h3>
            <p className="text-gray-600 leading-relaxed mb-8">
              Mukesh Mohan Gupta stands as India's most trusted MSME advisor,
              with an extraordinary 35-year journey that has transformed
              countless small and medium enterprises. His unique blend of
              traditional chartered accountancy expertise and modern digital
              innovation has made him the go-to mentor for India's
              entrepreneurial ecosystem.
            </p>

            <div className="flex items-center">
              <div className="w-3 h-3 bg-blue-600 rounded-full mr-3"></div>
              <span className="text-lg font-semibold text-gray-900">
                Chartered Accountant Excellence
              </span>
            </div>
          </div>

          {/* Right Content - Stats Cards */}
          <div className="grid grid-cols-2 gap-4">
            {[
              {
                title: "Expertise",
                desc: "35+ Years of MSME Excellence",
                color: "bg-blue-600",
                icon: (
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                  />
                ),
              },
              {
                title: "Network",
                desc: "32,000+ MSME Advisors",
                color: "bg-orange-500",
                icon: (
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"
                  />
                ),
              },
              {
                title: "Media",
                desc: "1M+ YouTube Subscribers",
                color: "bg-green-500",
                icon: (
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z"
                  />
                ),
              },
              {
                title: "Recognition",
                desc: "Top 200 LinkedIn Creator",
                color: "bg-red-500",
                icon: (
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M13 10V3L4 14h7v7l9-11h-7z"
                  />
                ),
              },
            ].map((card, index) => (
              <div
                key={index}
                className="bg-white rounded-2xl p-6 shadow-lg hover:shadow-xl transition-all duration-300 hover:-translate-y-1 text-center"
              >
                <div
                  className={`${card.color} w-12 h-12 rounded-2xl flex items-center justify-center mx-auto mb-4`}
                >
                  <svg
                    className="w-6 h-6 text-white"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    {card.icon}
                  </svg>
                </div>
                <h4 className="text-lg font-bold text-gray-900 mb-2">
                  {card.title}
                </h4>
                <p className="text-sm text-gray-600 leading-relaxed">
                  {card.desc}
                </p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
};

export default About;
