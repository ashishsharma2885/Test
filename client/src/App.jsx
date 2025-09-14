import React from 'react'
import Header from './components/Header'
import HeroSection from './components/HeroSection'
import About from './components/About'
import Remarkable from './components/Remarkable'
import Inspiring  from './components/Inspiring'
import Presence from './components/Presence'
import Transformative from './components/Transformative'
import Contact from './components/Contact'

const App = () => {
  return (
   <div>
    <Header />
    <HeroSection />
   <About />
   <Remarkable />
   <Inspiring />
   <Presence />
   <Transformative />
   <Contact />
   </div>
  )
}

export default App