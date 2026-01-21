import React, { useState } from 'react';
import { Loader2 } from 'lucide-react';

interface SubscribeFormProps {
  className?: string;
  variant?: 'light' | 'dark';
}

export const SubscribeForm: React.FC<SubscribeFormProps> = ({ className, variant = 'dark' }) => {
  const [email, setEmail] = useState('');
  const [status, setStatus] = useState<'idle' | 'loading' | 'success' | 'error'>('idle');
  const [errorMessage, setErrorMessage] = useState('');

  // 🔌 CONFIGURATION WEBHOOK ZAPIER
  const WEBHOOK_URL = 'https://hooks.zapier.com/hooks/catch/22386736/uqhetq2/';

  const validateEmail = (email: string) => {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage('');
    
    if (!email) {
      setErrorMessage('Entre ton adresse email');
      setStatus('error');
      return;
    }

    if (!validateEmail(email)) {
      setErrorMessage('Entre une adresse email valide');
      setStatus('error');
      return;
    }

    setStatus('loading');

    try {
      // 1. Envoi des données au Webhook Zapier
      // Nous utilisons 'no-cors' ou text/plain pour garantir que la requête part sans être bloquée par le navigateur,
      // même si cela signifie que nous ne pouvons pas lire la réponse JSON détaillée.
      await fetch(WEBHOOK_URL, {
        method: 'POST',
        headers: {
          'Content-Type': 'text/plain;charset=utf-8',
        },
        body: JSON.stringify({ 
          email,
          source: 'landing-page-mg-abondance',
          date: new Date().toISOString()
        }),
      });

      setStatus('success');
      
      // 2. Redirection vers Skool
      // Utilisation de window.location.href pour une navigation standard (pas d'iframe, pas d'embed).
      // Cela garantit que la page Skool se charge comme un nouveau site.
      setTimeout(() => {
        window.location.href = 'https://www.skool.com/mgabondance/about';
      }, 500); // Petit délai pour laisser l'utilisateur voir le succès visuel

    } catch (error) {
      console.error('Submission error:', error);
      // En cas d'erreur technique (rare avec no-cors/text-plain), on redirige quand même pour ne pas bloquer l'utilisateur
      window.location.href = 'https://www.skool.com/mgabondance/about';
    }
  };

  return (
    <div className={`w-full max-w-[580px] mx-auto ${className}`}>
      <form 
        onSubmit={handleSubmit}
        className="flex flex-col md:flex-row items-center gap-3 w-full"
      >
        <div className="relative w-full md:flex-1">
          <input
            type="email"
            value={email}
            onChange={(e) => {
              setEmail(e.target.value);
              if (status === 'error') setStatus('idle');
            }}
            placeholder="Ton adresse email"
            disabled={status === 'loading' || status === 'success'}
            className={`
              w-full h-[56px] px-6 rounded-xl text-base outline-none transition-all duration-300
              placeholder:text-slate-400 text-slate-900 font-sans
              ${status === 'error' ? 'ring-2 ring-red-500 bg-red-50' : 'focus:ring-2 focus:ring-blue-500/50 shadow-[0_4px_16px_rgba(0,0,0,0.1)]'}
              bg-white border-none
              disabled:opacity-70 disabled:cursor-not-allowed
            `}
          />
        </div>

        {/* Bouton avec effet "boule de lumière bleutée" */}
        <div className="relative group w-full md:w-auto h-[56px] rounded-xl overflow-hidden p-[1px]">
          {/* Fond animé (Trainée lumineuse) */}
          <div className="absolute inset-[-100%] animate-[spin_3s_linear_infinite] bg-[conic-gradient(from_90deg_at_50%_50%,#000000_0%,#000000_50%,#3b82f6_75%,#60a5fa_100%)] opacity-70" />
          
          <button
            type="submit"
            disabled={status === 'loading' || status === 'success'}
            className="
              relative w-full md:w-[160px] h-full rounded-[11px] bg-black text-white font-semibold font-sans
              flex items-center justify-center overflow-hidden transition-all duration-300
              hover:bg-slate-950 disabled:opacity-90 disabled:cursor-not-allowed z-10
            "
          >
            {status === 'loading' ? (
              <span className="flex items-center gap-2">
                <Loader2 className="w-5 h-5 animate-spin text-blue-400" />
                <span>Envoi...</span>
              </span>
            ) : status === 'success' ? (
              <span className="text-green-400 font-medium">Redirection...</span>
            ) : (
              <span className="group-hover:text-blue-50 transition-colors">Rejoindre</span>
            )}
            
            {/* Petit effet de reflet interne */}
            <div className="absolute inset-0 bg-gradient-to-t from-blue-900/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none" />
          </button>
        </div>
      </form>

      {/* Messages d'erreur */}
      <div className={`mt-3 text-center transition-all duration-300 ${status === 'error' ? 'opacity-100 translate-y-0' : 'opacity-0 -translate-y-2 pointer-events-none absolute w-full'}`}>
        <p className="text-[#FF6B6B] text-[13px] font-medium bg-red-950/30 inline-block px-3 py-1 rounded-full border border-red-900/50">
          {errorMessage}
        </p>
      </div>
    </div>
  );
};