import React, { useEffect, useRef } from 'react';

export const AbundanceBackground: React.FC = () => {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let width = window.innerWidth;
    let height = window.innerHeight;
    let animationFrameId: number;
    let time = 0;

    // Particle State
    let particles: Array<{
      x: number;
      y: number;
      size: number;
      speedY: number;
      alpha: number;
      oscillationOffset: number;
    }> = [];

    const init = () => {
      width = window.innerWidth;
      height = window.innerHeight;
      canvas.width = width;
      canvas.height = height;

      // Initialize Particles
      const PARTICLE_COUNT = Math.min(width * 0.15, 120);
      particles = [];
      for (let i = 0; i < PARTICLE_COUNT; i++) {
        particles.push({
          x: Math.random() * width,
          y: Math.random() * height,
          size: Math.random() * 1.5 + 0.5,
          speedY: Math.random() * 0.2 + 0.05,
          alpha: Math.random() * 0.5 + 0.1,
          oscillationOffset: Math.random() * Math.PI * 2,
        });
      }
    };

    const drawSoftWave = (
      yBase: number,
      frequency: number,
      amplitude: number,
      speed: number,
      colorStart: string,
      colorEnd: string,
      alpha: number
    ) => {
      if (!ctx) return;
      ctx.beginPath();
      
      // Draw smooth curve across the screen
      for (let x = 0; x <= width; x += 5) {
        // Complex sine combinations for organic, "cerebral" flow
        const y = yBase + 
                  Math.sin(x * frequency + time * speed) * amplitude + 
                  Math.sin(x * frequency * 0.5 + time * speed * 1.5) * (amplitude * 0.5) +
                  Math.cos(x * frequency * 2 + time * speed * 0.5) * (amplitude * 0.2); // Added harmonic
        
        if (x === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
      }

      // Gradient Stroke for fading effect at edges
      const gradient = ctx.createLinearGradient(0, 0, width, 0);
      gradient.addColorStop(0, 'transparent');
      gradient.addColorStop(0.1, colorStart); // Start fading in late
      gradient.addColorStop(0.5, colorEnd);   // Center color
      gradient.addColorStop(0.9, colorStart); // Start fading out early
      gradient.addColorStop(1, 'transparent');

      ctx.strokeStyle = gradient;
      ctx.lineWidth = 2;
      ctx.globalAlpha = alpha;
      
      // Soft blur to make it "indistinct"
      ctx.shadowBlur = 20;
      ctx.shadowColor = colorEnd;
      
      ctx.stroke();
      
      // Reset context
      ctx.shadowBlur = 0;
      ctx.globalAlpha = 1;
    };

    const animate = () => {
      if (!ctx) return;
      
      // Clear background
      const bgGradient = ctx.createLinearGradient(0, 0, 0, height);
      bgGradient.addColorStop(0, '#0a1628'); // Navy 950
      bgGradient.addColorStop(1, '#000000'); // Black
      ctx.fillStyle = bgGradient;
      ctx.fillRect(0, 0, width, height);

      time += 0.0015;

      const centerY = height * 0.55;

      // 1. Draw "Cerebral" Waves
      drawSoftWave(centerY, 0.0012, 50, 1, '#6366f1', '#818cf8', 0.04);
      drawSoftWave(centerY + 30, 0.0008, 40, 0.8, '#4338ca', '#6366f1', 0.03);
      drawSoftWave(centerY - 20, 0.0015, 60, 1.1, '#ca8a04', '#eab308', 0.02);
      drawSoftWave(centerY, 0.0005, 90, 0.5, '#ffffff', '#cbd5e1', 0.015);

      // 2. Draw Floating Particles
      particles.forEach(p => {
        p.y -= p.speedY;
        // Loop particles when they go off screen
        if (p.y < -10) {
            p.y = height + 10;
            p.x = Math.random() * width;
        }

        // Gentle side-to-side oscillation
        const x = p.x + Math.sin(time * 0.5 + p.oscillationOffset) * 10;
        
        ctx.beginPath();
        ctx.arc(x, p.y, p.size, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(255, 215, 0, ${p.alpha})`; // Gold particles
        ctx.fill();
      });

      animationFrameId = requestAnimationFrame(animate);
    };

    init();
    window.addEventListener('resize', init);
    animate();

    return () => {
      window.removeEventListener('resize', init);
      cancelAnimationFrame(animationFrameId);
    };
  }, []);

  return <canvas ref={canvasRef} className="absolute inset-0 w-full h-full pointer-events-none" />;
};