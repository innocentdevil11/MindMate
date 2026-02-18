"use client";

import { useEffect, useRef } from "react";
import { usePathname } from "next/navigation";

/* =======================
   Particle Class
======================= */
class Particle {
  constructor(canvas) {
    this.canvas = canvas;

    // Original position
    this.baseX = Math.random() * canvas.width;
    this.baseY = Math.random() * canvas.height;

    // Current position
    this.x = this.baseX;
    this.y = this.baseY;

    this.size = Math.random() * 3 + 0.75;

    this.speedX = 0;
    this.speedY = 0;

    this.opacity = Math.random() * 0.5 + 0.3;
  }

  update(pointer) {
    // Cursor interaction
    if (pointer.active) {
      const dx = this.x - pointer.x;
      const dy = this.y - pointer.y;
      const dist = Math.hypot(dx, dy);
      const radius = 160;

      if (dist > 0 && dist < radius) {
        const force = (1 - dist / radius) * 0.25;
        this.speedX += (dx / dist) * force;
        this.speedY += (dy / dist) * force;
      }
    }

    // Return to original position
    const returnStrength = 0.02;
    this.speedX += (this.baseX - this.x) * returnStrength;
    this.speedY += (this.baseY - this.y) * returnStrength;

    // Damping
    this.speedX *= 0.92;
    this.speedY *= 0.92;

    this.x += this.speedX;
    this.y += this.speedY;
  }

  draw(ctx) {
    ctx.fillStyle = `rgba(147, 51, 234, ${this.opacity})`;
    ctx.beginPath();
    ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
    ctx.fill();
  }
}

/* =======================
   Main Component
======================= */
export default function AnimatedBackground() {
  const pathname = usePathname();
  
  // Don't render on chat pages
  if (pathname?.includes("/chat")) return null;
  
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext("2d");
    let animationFrameId;
    let particles = [];

    const pointer = { x: 0, y: 0, active: false };

    /* =======================
       Canvas Resize
    ======================= */
    const resizeCanvas = () => {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
      initParticles();
    };

    window.addEventListener("resize", resizeCanvas);
    resizeCanvas();

    /* =======================
       Init Particles
    ======================= */
    function initParticles() {
      particles = [];
      const count = Math.min(
        Math.floor((canvas.width * canvas.height) / 15000),
        100
      );

      for (let i = 0; i < count; i++) {
        particles.push(new Particle(canvas));
      }
    }

    /* =======================
       Pointer Events
    ======================= */
    const onMove = (e) => {
      pointer.active = true;
      pointer.x = e.clientX;
      pointer.y = e.clientY;
    };

    const onLeave = () => {
      pointer.active = false;
    };

    const onTouch = (e) => {
      const t = e.touches?.[0];
      if (!t) return;
      pointer.active = true;
      pointer.x = t.clientX;
      pointer.y = t.clientY;
    };

    window.addEventListener("mousemove", onMove, { passive: true });
    window.addEventListener("mouseleave", onLeave, { passive: true });
    window.addEventListener("touchstart", onTouch, { passive: true });
    window.addEventListener("touchmove", onTouch, { passive: true });

    /* =======================
       Draw Connecting Lines
    ======================= */
    function drawLines() {
      const maxDist = 140;

      for (let i = 0; i < particles.length; i++) {
        for (let j = i + 1; j < particles.length; j++) {
          const dx = particles[i].x - particles[j].x;
          const dy = particles[i].y - particles[j].y;
          const dist = Math.hypot(dx, dy);

          if (dist < maxDist) {
            const opacity = 0.35 * (1 - dist / maxDist);
            ctx.strokeStyle = `rgba(0, 0, 0, ${opacity})`; // subtle black
            ctx.lineWidth = 0.7;
            ctx.beginPath();
            ctx.moveTo(particles[i].x, particles[i].y);
            ctx.lineTo(particles[j].x, particles[j].y);
            ctx.stroke();
          }
        }
      }
    }

    /* =======================
       Animation Loop
    ======================= */
    const animate = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      drawLines();

      particles.forEach((p) => {
        p.update(pointer);
        p.draw(ctx);
      });

      animationFrameId = requestAnimationFrame(animate);
    };

    animate();

    /* =======================
       Cleanup
    ======================= */
    return () => {
      window.removeEventListener("resize", resizeCanvas);
      window.removeEventListener("mousemove", onMove);
      window.removeEventListener("mouseleave", onLeave);
      window.removeEventListener("touchstart", onTouch);
      window.removeEventListener("touchmove", onTouch);
      cancelAnimationFrame(animationFrameId);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      className="fixed inset-0 pointer-events-none z-0 opacity-60"
      style={{ background: "transparent" }}
    />
  );
}
