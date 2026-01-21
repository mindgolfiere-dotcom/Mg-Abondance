import React from 'react';
import { BrainCircuit, TrendingUp, Users } from 'lucide-react';

const FeatureItem = ({ icon: Icon, title, description }: { icon: any, title: string, description: string }) => (
  <div className="flex flex-col items-center text-center p-6 rounded-2xl bg-white/5 border border-white/10 backdrop-blur-sm hover:bg-white/10 transition-colors duration-300">
    <div className="mb-4 p-3 rounded-full bg-gradient-to-br from-slate-800 to-black border border-white/10 shadow-lg">
      <Icon className="w-8 h-8 text-gold-400" />
    </div>
    <h3 className="text-xl font-medium text-white mb-2 font-sans">{title}</h3>
    <p className="text-slate-400 font-light leading-relaxed">
      {description}
    </p>
  </div>
);

export const Features: React.FC = () => {
  return (
    <section className="py-24 px-4 bg-navy-950 relative z-20">
      <div className="max-w-6xl mx-auto">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          <FeatureItem 
            icon={BrainCircuit}
            title="Reprogrammation Subconsciente"
            description="Accède à des sessions audio neuro-acoustiques conçues pour dissoudre les blocages financiers et aligner ton esprit sur l'abondance."
          />
          <FeatureItem 
            icon={TrendingUp}
            title="Visualisation de Croissance"
            description="Utilise nos outils immersifs pour visualiser tes objectifs, suivre ta valeur nette et manifester tes résultats avec précision."
          />
          <FeatureItem 
            icon={Users}
            title="Cercle d'Initiés"
            description="Rejoins une communauté exclusive d'entrepreneurs et de créateurs qui partagent tes ambitions et accélèrent ta réussite."
          />
        </div>
      </div>
    </section>
  );
};