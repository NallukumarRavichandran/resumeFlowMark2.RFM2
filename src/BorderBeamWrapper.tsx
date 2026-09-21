import React from 'react';
import { createRoot } from 'react-dom/client';
import { BorderBeam } from 'border-beam';

/**
 * Attaches a BorderBeam effect to a target DOM element.
 * It does this by creating a wrapper container around the target element's 
 * physical space, rendering BorderBeam behind it.
 */
export function attachBorderBeam(targetId, options = {}) {
  const targetEl = document.getElementById(targetId);
  if (!targetEl) {
    console.error(`attachBorderBeam: Element #${targetId} not found.`);
    return null;
  }

  // Create a container for the React root, positioned exactly like the target
  const container = document.createElement('div');
  container.className = 'border-beam-overlay';
  
  // Style container to match target's size and position
  container.style.position = 'absolute';
  container.style.top = '0';
  container.style.left = '0';
  container.style.width = '100%';
  container.style.height = '100%';
  container.style.pointerEvents = 'none'; // let clicks pass through to textarea
  container.style.zIndex = '0'; // Behind the text
  container.style.borderRadius = getComputedStyle(targetEl).borderRadius;

  // We need the parent of targetEl to be relative so we can position absolute inside it
  const parent = targetEl.parentElement;
  if (getComputedStyle(parent).position === 'static') {
    parent.style.position = 'relative';
  }

  // Also ensure the target itself has a higher z-index and is transparent so the beam shows underneath
  targetEl.style.position = 'relative';
  targetEl.style.zIndex = '1';
  targetEl.style.background = 'transparent';
  // Let's remove its default border so the beam is the only border
  targetEl.style.border = 'none';

  // Insert the container before the target element or inside parent
  parent.insertBefore(container, targetEl);

  const root = createRoot(container);
  
  const size = options.size || 'md';
  const colorVariant = options.colorVariant || 'ocean';
  const strength = options.strength !== undefined ? options.strength : 0.8;

  // We render BorderBeam with an empty 100% 100% div as child
  root.render(
    <BorderBeam size={size} colorVariant={colorVariant} strength={strength}>
      <div style={{ 
        width: '100%', 
        height: '100%', 
        borderRadius: 'inherit',
        backgroundColor: getComputedStyle(targetEl).backgroundColor || 'var(--input-bg)'
      }}></div>
    </BorderBeam>
  );

  return {
    destroy: () => {
      root.unmount();
      if (container.parentNode) {
        container.parentNode.removeChild(container);
      }
      // Restore styles if needed
      targetEl.style.background = '';
      targetEl.style.border = '';
    }
  };
}

// Expose globally
window.attachBorderBeam = attachBorderBeam;
