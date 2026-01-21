import React from 'react';
import { Logo } from './Logo';
import { SubscribeForm } from './SubscribeForm';
import { AbundanceBackground } from './AbundanceBackground';

export const Hero: React.FC = () => {
  return (
    <section className="relative min-h-screen flex flex-col items-center justify-center pt-20 pb-32 overflow-hidden bg-black text-center px-4">
      
      {/* 1. Animated Canvas Background */}
      <div className="absolute inset-0 z-0">
        <AbundanceBackground />
      </div>

      {/* 2. Optional: Subtle radial vignette to focus center */}
      <div className="absolute inset-0 z-0 bg-[radial-gradient(circle_at_center,transparent_0%,rgba(0,0,0,0.4)_100%)] pointer-events-none"></div>

      {/* Header / Logo Positioned Absolutely at Top */}
      <div className="absolute top-12 left-0 w-full z-20 flex justify-center pointer-events-none">
        <Logo />
      </div>

      {/* 3. Content */}
      <div className="relative z-10 flex flex-col items-center max-w-4xl mx-auto space-y-8 mt-8 md:mt-0">
        
        <h1 className="text-5xl md:text-[64px] font-sans font-light tracking-tight leading-[1.1] text-transparent bg-clip-text bg-gradient-to-b from-white via-white to-white/70 drop-shadow-sm">
          Un espace où l'abondance <br className="hidden md:block"/> financière devient naturelle
        </h1>
        
        <p className="text-lg md:text-xl text-slate-300 max-w-2xl font-light leading-relaxed">
          MG Abondance est le meilleur endroit pour manifester <br className="hidden md:block"/> tes objectifs financiers en toute facilité.
        </p>

        <div className="w-full pt-8">
          <SubscribeForm />
          <p className="text-xs text-slate-400 mt-4 font-light tracking-wide opacity-80">
            Inscris-toi pour un accès anticipé. Pas de spam. Que de l'abondance.
          </p>
        </div>
      </div>

      {/* 4. Bottom Fade to blend with next section */}
      <div className="absolute bottom-0 left-0 w-full h-24 bg-gradient-to-t from-navy-950 to-transparent z-10 pointer-events-none"></div>
    </section>
  );
};