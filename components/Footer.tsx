import React from 'react';
import { SubscribeForm } from './SubscribeForm';

export const Footer: React.FC = () => {
  return (
    <footer className="py-32 px-4 bg-navy-950 relative z-20 border-t border-white/5 overflow-hidden">
      {/* Background glow for footer */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-blue-900/10 blur-[100px] rounded-full pointer-events-none"></div>

      <div className="relative z-10 max-w-2xl mx-auto text-center space-y-8">
        <h2 className="text-4xl md:text-5xl font-sans font-light text-white tracking-tight">
          Prêt à transformer ta réalité ?
        </h2>
        <p className="text-slate-400 text-lg font-light">
          Rejoins la liste d'attente et sois le premier informé du lancement.
        </p>
        
        <div className="pt-4">
           <SubscribeForm />
        </div>
        
        <div className="pt-12 flex justify-center space-x-6 text-slate-600 text-sm">
          <a href="#" className="hover:text-white transition-colors">Mentions Légales</a>
          <a href="#" className="hover:text-white transition-colors">Confidentialité</a>
          <a href="#" className="hover:text-white transition-colors">Twitter</a>
        </div>
        
        <p className="text-slate-700 text-xs">
          © 2025 MG Abondance. Tous droits réservés.
        </p>
      </div>
    </footer>
  );
};