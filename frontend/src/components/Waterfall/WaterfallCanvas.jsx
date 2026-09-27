import React, { useRef, useEffect } from 'react';

export default function WaterfallCanvas({ pings = [], width = 800, height = 400 }) {
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Draw background / grid
    ctx.fillStyle = '#0a0f1d';
    ctx.fillRect(0, 0, width, height);

    // If pings are present, draw acoustic scanlines
    if (pings.length > 0) {
      const pingHeight = Math.max(1, Math.floor(height / Math.min(pings.length, height)));

      pings.slice(-height).forEach((ping, rowIdx) => {
        const y = rowIdx * pingHeight;
        if (Array.isArray(ping)) {
          const colWidth = width / ping.length;
          ping.forEach((val, colIdx) => {
            const intensity = Math.min(255, Math.max(0, val));
            // Sonar color palette (deep copper / gold)
            ctx.fillStyle = `rgb(${intensity}, ${Math.floor(intensity * 0.75)}, ${Math.floor(intensity * 0.2)})`;
            ctx.fillRect(colIdx * colWidth, y, colWidth + 0.5, pingHeight);
          });
        }
      });
    } else {
      // Synthetic demo waterfall sweep pattern
      const imgData = ctx.createImageData(width, height);
      for (let y = 0; y < height; y++) {
        for (let x = 0; x < width; x++) {
          const idx = (y * width + x) * 4;
          // Nadir blank line in center
          const distFromCenter = Math.abs(x - width / 2);
          if (distFromCenter < 12) {
            imgData.data[idx] = 10;
            imgData.data[idx + 1] = 15;
            imgData.data[idx + 2] = 25;
            imgData.data[idx + 3] = 255;
          } else {
            // Simulated acoustic backscatter
            const noise = (Math.sin(x * 0.05 + y * 0.08) + Math.cos(x * 0.02 - y * 0.04)) * 30 + 110;
            const r = Math.min(255, Math.floor(noise + Math.random() * 20));
            imgData.data[idx] = r;
            imgData.data[idx + 1] = Math.floor(r * 0.7);
            imgData.data[idx + 2] = Math.floor(r * 0.2);
            imgData.data[idx + 3] = 255;
          }
        }
      }
      ctx.putImageData(imgData, 0, 0);

      // Overlay center nadir line indicator
      ctx.strokeStyle = '#38bdf8';
      ctx.setLineDash([4, 4]);
      ctx.beginPath();
      ctx.moveTo(width / 2, 0);
      ctx.lineTo(width / 2, height);
      ctx.stroke();

      // Legend overlay
      ctx.fillStyle = 'rgba(0,0,0,0.6)';
      ctx.fillRect(10, 10, 180, 50);
      ctx.fillStyle = '#38bdf8';
      ctx.font = '11px monospace';
      ctx.fillText('PORT SWATH | NADIR | STBD SWATH', 15, 28);
      ctx.fillStyle = '#ffffff';
      ctx.fillText('STATUS: STREAMING ACTIVE', 15, 46);
    }
  }, [pings, width, height]);

  return (
    <div style={{ position: 'relative', width: '100%', overflow: 'hidden', borderRadius: '8px', border: '1px solid #1e293b' }}>
      <canvas
        ref={canvasRef}
        width={width}
        height={height}
        style={{ width: '100%', height: 'auto', display: 'block' }}
      />
    </div>
  );
}
