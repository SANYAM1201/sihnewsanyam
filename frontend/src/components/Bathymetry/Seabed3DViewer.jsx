import React, { useEffect, useRef, useState } from 'react';

export default function Seabed3DViewer({ altitude = 12.0, depth = 25.0 }) {
  const canvasRef = useRef(null);
  const [rotation, setRotation] = useState({ x: 35, y: -45 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });

  const handleMouseDown = (e) => {
    setIsDragging(true);
    setDragStart({ x: e.clientX, y: e.clientY });
  };

  const handleMouseMove = (e) => {
    if (!isDragging) return;
    const dx = e.clientX - dragStart.x;
    const dy = e.clientY - dragStart.y;
    setRotation((prev) => ({
      x: Math.max(10, Math.min(80, prev.x + dy * 0.5)),
      y: prev.y + dx * 0.5,
    }));
    setDragStart({ x: e.clientX, y: e.clientY });
  };

  const handleMouseUp = () => setIsDragging(false);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animId;
    const rows = 20;
    const cols = 28;
    const spacing = 14;

    const render = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      const cx = canvas.width / 2;
      const cy = canvas.height / 2 + 20;

      const radX = (rotation.x * Math.PI) / 180;
      const radY = (rotation.y * Math.PI) / 180;

      const project = (x, y, z) => {
        // Rotate Y
        const x1 = x * Math.cos(radY) + z * Math.sin(radY);
        const z1 = -x * Math.sin(radY) + z * Math.cos(radY);

        // Rotate X
        const y2 = y * Math.cos(radX) - z1 * Math.sin(radX);
        const z2 = y * Math.sin(radX) + z1 * Math.cos(radX);

        // Orthographic/Isometric projection
        const px = cx + x1;
        const py = cy + y2;
        return { px, py, depth: z2 };
      };

      const points = [];
      for (let r = 0; r < rows; r++) {
        points[r] = [];
        for (let c = 0; c < cols; c++) {
          const x = (c - cols / 2) * spacing;
          const z = (r - rows / 2) * spacing;

          // Realistic undulating seafloor with a target mound in center
          const distCenter = Math.hypot(c - cols / 2, r - rows / 2);
          let elevation = Math.sin(r * 0.4 + c * 0.3) * 6;
          if (distCenter < 4) {
            elevation += (4 - distCenter) * 8; // Target bump
          }

          const y = -elevation;
          points[r][c] = project(x, y, z);
        }
      }

      // Draw grid lines
      ctx.lineWidth = 1.2;

      // Rows
      for (let r = 0; r < rows; r++) {
        for (let c = 0; c < cols - 1; c++) {
          const p1 = points[r][c];
          const p2 = points[r][c + 1];
          const depthRatio = Math.max(0, Math.min(1, (p1.px + 200) / 400));
          ctx.strokeStyle = `rgba(2, 132, 199, ${0.4 + depthRatio * 0.4})`;
          ctx.beginPath();
          ctx.moveTo(p1.px, p1.py);
          ctx.lineTo(p2.px, p2.py);
          ctx.stroke();
        }
      }

      // Columns
      for (let c = 0; c < cols; c++) {
        for (let r = 0; r < rows - 1; r++) {
          const p1 = points[r][c];
          const p2 = points[r + 1][c];
          ctx.strokeStyle = 'rgba(14, 165, 233, 0.45)';
          ctx.beginPath();
          ctx.moveTo(p1.px, p1.py);
          ctx.lineTo(p2.px, p2.py);
          ctx.stroke();
        }
      }

      // Draw target highlight beacon at center
      const centerP = points[Math.floor(rows / 2)][Math.floor(cols / 2)];
      ctx.fillStyle = '#ef4444';
      ctx.beginPath();
      ctx.arc(centerP.px, centerP.py, 5, 0, Math.PI * 2);
      ctx.fill();

      // Beacon pulse ring
      ctx.strokeStyle = 'rgba(239, 68, 68, 0.75)';
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.arc(centerP.px, centerP.py, 10, 0, Math.PI * 2);
      ctx.stroke();
    };

    render();
  }, [rotation, altitude, depth]);

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        background: '#0a0f18',
        borderRadius: '8px',
        padding: '12px',
        color: '#e2e8f0',
        cursor: isDragging ? 'grabbing' : 'grab',
        userSelect: 'none',
      }}
      onMouseDown={handleMouseDown}
      onMouseMove={handleMouseMove}
      onMouseUp={handleMouseUp}
      onMouseLeave={handleMouseUp}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', width: '100%', marginBottom: '8px', fontSize: '12px' }}>
        <span style={{ fontWeight: 700, color: '#38bdf8' }}>🏔️ 3D SEABED TOPOGRAPHY MESH</span>
        <span style={{ color: '#94a3b8' }}>Click &amp; Drag to Rotate 3D Terrain</span>
      </div>
      <canvas
        ref={canvasRef}
        width={540}
        height={260}
        style={{ width: '100%', height: '260px', display: 'block' }}
      />
      <div style={{ display: 'flex', gap: '16px', marginTop: '8px', fontSize: '11px', color: '#94a3b8' }}>
        <span>Seafloor Depth: <strong>{depth}m</strong></span>
        <span>Relief Variation: <strong>±3.2m</strong></span>
        <span>Vehicle Altitude: <strong>{altitude}m</strong></span>
        <span>Elevation Target: <strong style={{ color: '#ef4444' }}>● Active Anomaly</strong></span>
      </div>
    </div>
  );
}
