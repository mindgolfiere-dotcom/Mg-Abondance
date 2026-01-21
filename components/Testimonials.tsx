import React from 'react';

export const Testimonials: React.FC = () => {
  return (
    <section className="py-24 px-4 bg-navy-950 relative z-20 border-t border-white/5">
      <div className="max-w-4xl mx-auto flex flex-col md:flex-row items-center gap-12">
        {/* Image Side */}
        <div className="w-full md:w-1/2 relative group">
          <div className="absolute inset-0 bg-gold-500/20 blur-2xl rounded-full transform group-hover:scale-105 transition-transform duration-700"></div>
          <div className="relative rounded-2xl overflow-hidden aspect-[4/5] border border-white/10 shadow-2xl">
             <img 
              src="https://images.unsplash.com/photo-1618519764620-7403abdbdfe9?q=80&w=2670&auto=format&fit=crop" 
              alt="Person using the app in a peaceful setting"
              className="w-full h-full object-cover opacity-80 group-hover:opacity-100 transition-opacity duration-500"
            />
            <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent"></div>
          </div>
        </div>

        {/* Text Side */}
        <div className="w-full md:w-1/2 space-y-6">
           <div className="inline-flex items-center space-x-1">
             {[1, 2, 3, 4, 5].map((star) => (
               <svg key={star} className="w-5 h-5 text-gold-400 fill-current" viewBox="0 0 20 20">
                 <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
               </svg>
             ))}
           </div>
           
           <h2 className="text-3xl font-serif italic leading-tight text-white/90">
             "Avant MG Abondance, je voyais l'argent comme une source de stress. Aujourd'hui, c'est une énergie fluide que je maîtrise avec calme et certitude."
           </h2>
           
           <div>
             <p className="text-white font-medium">Camille Laurent</p>
             <p className="text-slate-500 text-sm">Entrepreneure & Artiste</p>
           </div>
        </div>
      </div>
    </section>
  );
};