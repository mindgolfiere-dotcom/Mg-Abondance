import React from 'react';

export const Logo: React.FC<{ className?: string }> = ({ className = '' }) => {
  return (
    <div className={`flex items-center gap-1.5 select-none ${className}`}>
      {/* MG - Gradient Blue, Extra Bold */}
      <span className="font-sans font-extrabold text-2xl md:text-3xl bg-clip-text text-transparent bg-gradient-to-b from-blue-500 to-blue-950 tracking-tight">
        MG
      </span>
      {/* ABONDANCE - White, Bold */}
      <span className="font-sans font-bold text-2xl md:text-3xl text-white tracking-tight">
        ABONDANCE
      </span>
    </div>
  );
};