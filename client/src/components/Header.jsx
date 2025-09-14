import React from "react";

const Header = () => {
  return (
    <header className="bg-white shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo and Brand */}
          <div className="flex items-center">
            <div className="bg-blue-600 text-white font-bold text-lg px-3 py-1 rounded-lg mr-3">
              MMG
            </div>
            <div>
              <h1 className="text-xl font-bold text-gray-900">
                Mukesh Mohan Gupta
              </h1>
              <p className="text-sm text-gray-600">MSME Visionary</p>
            </div>
          </div>

          {/* Navigation */}
          <nav className="hidden md:flex space-x-8">
            {["Home", "About", "Achievements", "Speaking", "Media", "Mentorship", "Contact"].map(
              (item, index) => (
                <a
                  key={index}
                  href="#"
                  className="text-gray-700 hover:text-blue-600 font-medium"
                >
                  {item}
                </a>
              )
            )}
          </nav>
        </div>
      </div>
    </header>
  );
};

export default Header;
