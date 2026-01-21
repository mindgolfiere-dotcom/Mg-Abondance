import React from 'react';
import { Hero } from './components/Hero';
import { Features } from './components/Features';
import { Testimonials } from './components/Testimonials';
import { Footer } from './components/Footer';

function App() {
  return (
    <main className="min-h-screen bg-navy-950 text-white selection:bg-gold-500/30 selection:text-gold-200">
      <Hero />
      <Features />
      <Testimonials />
      <Footer />
    </main>
  );
}

export default App;