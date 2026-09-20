/**
 * Click Effects — Originkit
 * Ported for browser / Swooped Studio
 * Modes: 'sniper' | 'rings' | 'burst' | 'particles' | 'crosshair' | 'wavy'
 */

(() => {
  // Configuration with Originkit preset props
  const config = {
    interactionMode: 'particles', // 'rings' | 'burst' | 'particles' | 'crosshair' | 'wavy' | 'sniper'
    color: '#ffffff',
    duration: 0.3,
    strokeWidth: 2,
    effectSize: 45,
    rotation: 0
  };

  // Create overlay container
  let container = document.getElementById('click-effects-container');
  if (!container) {
    container = document.createElement('div');
    container.id = 'click-effects-container';
    container.style.cssText = 'position:fixed;inset:0;pointer-events:none;z-index:9999;overflow:visible;';
    document.body.appendChild(container);
  }

  // Ensure GSAP is loaded
  function ensureGsap(callback) {
    if (window.gsap) {
      callback();
      return;
    }
    const script = document.createElement('script');
    script.src = 'https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/gsap.min.js';
    script.onload = callback;
    document.head.appendChild(script);
  }

  function createSvgElement(tag, attrs = {}) {
    const el = document.createElementNS('http://www.w3.org/2000/svg', tag);
    for (const [key, val] of Object.entries(attrs)) {
      el.setAttribute(key, val);
    }
    return el;
  }

  function getSvgStyle(x, y, effectSize, rotation) {
    return `position:absolute;left:${x - effectSize / 2}px;top:${y - effectSize / 2}px;width:${effectSize}px;height:${effectSize}px;pointer-events:none;overflow:visible;transform:rotate(${rotation}deg);transform-origin:center;`;
  }

  // Effect Renderers
  function renderRings(x, y) {
    const { color, duration, strokeWidth, effectSize, rotation } = config;
    const svg = createSvgElement('svg');
    svg.style.cssText = getSvgStyle(x, y, effectSize, rotation);

    const circle = createSvgElement('circle', {
      cx: effectSize / 2,
      cy: effectSize / 2,
      r: effectSize / 4,
      fill: 'none',
      stroke: color,
      'stroke-width': strokeWidth
    });
    svg.appendChild(circle);
    container.appendChild(svg);

    gsap.set(svg, { scale: 0.5 });
    gsap.timeline({ onComplete: () => svg.remove() })
      .to(svg, { scale: 2, duration, ease: 'power3.out' }, 0)
      .to(circle, { attr: { 'stroke-width': 0 }, duration, ease: 'power3.out' }, 0)
      .to(svg, { opacity: 0, duration: duration * 0.2, ease: 'linear' }, duration * 0.8);
  }

  function renderBurst(x, y) {
    const { color, duration, strokeWidth, effectSize, rotation } = config;
    const svg = createSvgElement('svg');
    svg.style.cssText = getSvgStyle(x, y, effectSize, rotation);

    const centerX = effectSize / 2;
    const centerY = effectSize / 2;
    const angles = [45, 80, 115, 150];

    angles.forEach((deg) => {
      const angle = deg * (Math.PI / 180);
      const startX = centerX + effectSize * 0.1 * Math.cos(angle);
      const startY = centerY - effectSize * 0.1 * Math.sin(angle);
      const endX = centerX + effectSize * 0.25 * Math.cos(angle);
      const endY = centerY - effectSize * 0.25 * Math.sin(angle);

      const line = createSvgElement('line', {
        x1: startX,
        y1: startY,
        x2: endX,
        y2: endY,
        stroke: color,
        'stroke-width': strokeWidth,
        'stroke-linecap': 'square'
      });
      svg.appendChild(line);

      gsap.timeline()
        .to(line, {
          translateX: (effectSize / 4) * Math.cos(angle),
          translateY: (-effectSize / 4) * Math.sin(angle),
          duration,
          ease: 'power2.out'
        }, 0)
        .to(line, {
          attr: { 'stroke-width': 0 },
          duration: duration * 0.4,
          ease: 'linear'
        }, duration * 0.6);
    });

    container.appendChild(svg);
    gsap.delayedCall(duration, () => svg.remove());
  }

  function renderParticles(x, y) {
    const { color, duration, strokeWidth, effectSize, rotation } = config;
    const group = document.createElement('div');
    container.appendChild(group);

    for (let i = 0; i < 8; i++) {
      const angle = i * 45 * (Math.PI / 180);
      const distance = effectSize * 0.2 + Math.random() * (effectSize * 0.3);
      const finalX = x + Math.cos(angle) * distance;
      const finalY = y + Math.sin(angle) * distance;

      const dot = document.createElement('div');
      dot.style.cssText = `position:absolute;left:${x - strokeWidth / 2}px;top:${y - strokeWidth / 2}px;width:0px;height:0px;background-color:${color};border-radius:50%;pointer-events:none;transform:rotate(${rotation}deg);transform-origin:center;`;
      group.appendChild(dot);

      gsap.timeline()
        .to(dot, {
          width: strokeWidth * 2,
          height: strokeWidth * 2,
          duration: duration * 0.2,
          ease: 'power1.out'
        }, 0)
        .to(dot, {
          left: finalX - strokeWidth,
          top: finalY - strokeWidth,
          duration: duration * 0.4,
          ease: 'power1.out'
        }, duration * 0.2)
        .to(dot, {
          width: 0,
          height: 0,
          left: finalX,
          top: finalY,
          duration: duration * 0.4,
          ease: 'linear'
        }, duration * 0.6);
    }

    gsap.delayedCall(duration, () => group.remove());
  }

  function renderCrosshair(x, y) {
    const { color, duration, strokeWidth, effectSize, rotation } = config;
    const svg = createSvgElement('svg');
    svg.style.cssText = getSvgStyle(x, y, effectSize, rotation);

    const centerX = effectSize / 2;
    const centerY = effectSize / 2;
    const angles = [0, 90, 180, 270];
    const lineLength = effectSize * 0.3;

    angles.forEach((deg) => {
      const angle = deg * (Math.PI / 180);
      const startX = centerX + 20 * Math.cos(angle);
      const startY = centerY - 20 * Math.sin(angle);
      const endX = centerX + (20 + lineLength) * Math.cos(angle);
      const endY = centerY - (20 + lineLength) * Math.sin(angle);

      const line = createSvgElement('line', {
        x1: startX,
        y1: startY,
        x2: centerX,
        y2: centerY,
        stroke: color,
        'stroke-width': strokeWidth,
        'stroke-linecap': 'square'
      });
      svg.appendChild(line);

      gsap.timeline()
        .to(line, {
          attr: { x1: endX, y1: endY, x2: endX, y2: endY },
          duration: duration * 0.8,
          ease: 'power1.out'
        }, 0)
        .to(line, {
          attr: { 'stroke-width': 0 },
          duration: duration * 0.6,
          ease: 'linear'
        }, duration * 0.4);
    });

    container.appendChild(svg);
    gsap.delayedCall(duration, () => svg.remove());
  }

  function renderWavy(x, y) {
    const { color, duration, strokeWidth, effectSize, rotation } = config;
    const svg = createSvgElement('svg');
    svg.style.cssText = getSvgStyle(x, y, effectSize, rotation);

    const centerX = effectSize / 2;
    const centerY = effectSize / 2;
    const angles = [45, 90, 135, 180];

    angles.forEach((angle) => {
      const startRadius = effectSize * 0.1;
      const endRadius = effectSize * 0.5;
      const rad = (angle * Math.PI) / 180;
      const startX = centerX + startRadius * Math.cos(rad);
      const startY = centerY - startRadius * Math.sin(rad);
      const endX = centerX + endRadius * Math.cos(rad);
      const endY = centerY - endRadius * Math.sin(rad);
      const midX = (startX + endX) / 2;
      const midY = (startY + endY) / 2;
      const waveOffset = effectSize * 0.05;
      const control1X = midX + waveOffset * Math.cos(rad + Math.PI / 2);
      const control1Y = midY - waveOffset * Math.sin(rad + Math.PI / 2);
      const wavyPath = `M ${startX} ${startY} Q ${control1X} ${control1Y} ${midX} ${midY} T ${endX} ${endY}`;

      const path = createSvgElement('path', {
        d: wavyPath,
        stroke: color,
        'stroke-width': strokeWidth,
        'stroke-linecap': 'round',
        fill: 'none'
      });
      svg.appendChild(path);

      const pathLength = path.getTotalLength ? path.getTotalLength() || 40 : 40;
      gsap.set(path, {
        strokeDasharray: `1, ${pathLength}`,
        strokeDashoffset: 0
      });

      gsap.timeline()
        .to(path, {
          strokeDasharray: `${pathLength}, ${pathLength}`,
          strokeDashoffset: -pathLength,
          duration,
          ease: 'power1.out'
        }, 0)
        .to(path, {
          attr: { 'stroke-width': 0 },
          duration: duration * 0.4,
          ease: 'linear'
        }, duration * 0.6);
    });

    container.appendChild(svg);
    gsap.delayedCall(duration, () => svg.remove());
  }

  function renderSniper(x, y) {
    const { color, duration, strokeWidth, effectSize, rotation } = config;
    const group = document.createElement('div');
    container.appendChild(group);

    // Crosshair lines
    const svg = createSvgElement('svg');
    svg.style.cssText = getSvgStyle(x, y, effectSize, rotation);

    const centerX = effectSize / 2;
    const centerY = effectSize / 2;
    const angles = [0, 90, 180, 270];
    const lineLength = effectSize * 0.2;

    angles.forEach((deg) => {
      const angle = deg * (Math.PI / 180);
      const startX = centerX + 5 * Math.cos(angle);
      const startY = centerY - 5 * Math.sin(angle);
      const endX = centerX + (5 + lineLength) * Math.cos(angle);
      const endY = centerY - (5 + lineLength) * Math.sin(angle);

      const line = createSvgElement('line', {
        x1: startX,
        y1: startY,
        x2: endX,
        y2: endY,
        stroke: color,
        'stroke-width': strokeWidth,
        'stroke-linecap': 'square'
      });
      svg.appendChild(line);

      gsap.timeline()
        .to(line, {
          translateX: (5 + lineLength) * Math.cos(angle),
          translateY: -(5 + lineLength) * Math.sin(angle),
          duration,
          ease: 'power2.out'
        }, 0)
        .to(line, {
          attr: { 'stroke-width': 0 },
          duration: duration * 0.4,
          ease: 'linear'
        }, duration * 0.6);
    });
    group.appendChild(svg);

    // 8 Sub-radial sparks
    const sparkAngles = [
      Math.PI / 3,
      (2 * Math.PI) / 3,
      (4 * Math.PI) / 3,
      (5 * Math.PI) / 3,
      Math.PI / 6,
      (5 * Math.PI) / 6,
      (7 * Math.PI) / 6,
      (11 * Math.PI) / 6
    ];

    sparkAngles.forEach((angle) => {
      const spark = document.createElement('div');
      spark.style.cssText = `position:absolute;left:${x - strokeWidth / 2}px;top:${y - strokeWidth / 2}px;width:${strokeWidth}px;height:${strokeWidth}px;background-color:${color};pointer-events:none;transform-origin:center;transform:rotate(${rotation}deg);border-radius:50%;`;
      group.appendChild(spark);

      gsap.timeline()
        .to(spark, {
          x: Math.cos(angle) * (effectSize * 0.4),
          y: Math.sin(angle) * (effectSize * 0.4),
          duration,
          ease: 'power2.out'
        }, 0)
        .to(spark, {
          width: 0,
          height: 0,
          duration: duration * 0.4,
          ease: 'linear'
        }, duration * 0.6);
    });

    gsap.delayedCall(duration, () => group.remove());
  }

  // Trigger effect dispatcher
  function triggerEffect(x, y) {
    if (!window.gsap) return;
    switch (config.interactionMode) {
      case 'rings':
        renderRings(x, y);
        break;
      case 'burst':
        renderBurst(x, y);
        break;
      case 'particles':
        renderParticles(x, y);
        break;
      case 'crosshair':
        renderCrosshair(x, y);
        break;
      case 'wavy':
        renderWavy(x, y);
        break;
      case 'sniper':
      default:
        renderSniper(x, y);
        break;
    }
  }

  // Click listener
  document.addEventListener('click', (e) => {
    // Avoid triggering when clicking within inputs or file selectors if focused
    triggerEffect(e.clientX, e.clientY);
  });

  // Global API to change mode or trigger programmatically
  window.MouseEffects = {
    setMode: (mode) => {
      if (['rings', 'burst', 'particles', 'crosshair', 'wavy', 'sniper'].includes(mode)) {
        config.interactionMode = mode;
      }
    },
    setColor: (color) => { config.color = color; },
    trigger: triggerEffect,
    config
  };

  // Initialize GSAP
  ensureGsap(() => {
    console.log('[Originkit] MouseEffects initialized with mode:', config.interactionMode);
  });
})();
