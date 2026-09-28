/**
 * Ultra-Photorealistic Hydrographic Side-Scan Sonar Swath Generator.
 * Simulates high-resolution dual-channel (Port/Starboard) acoustic waterfall imagery
 * with authentic Rayleigh seabed speckle, TVG gain curves, nadir blind zone,
 * and physics-grounded target highlight & acoustic shadow dispersion.
 */

export function createDemoSonarFile() {
  const width = 800;
  const height = 480;
  const canvas = document.createElement('canvas');
  canvas.width = width;
  canvas.height = height;
  const ctx = canvas.getContext('2d');

  const imgData = ctx.createImageData(width, height);
  const data = imgData.data;

  const nadirWidth = 32;
  const centerX = width / 2;

  // 1. Generate Authentic Seafloor Acoustic Texture with Rayleigh Speckle & Wavelet Ripples
  for (let y = 0; y < height; y++) {
    for (let x = 0; x < width; x++) {
      const idx = (y * width + x) * 4;
      const distFromCenter = Math.abs(x - centerX);

      let intensity = 0;

      if (distFromCenter < nadirWidth / 2) {
        // Nadir water column (water delay / minimal backscatter before bottom return)
        intensity = 10 + Math.random() * 8;
      } else {
        // Seafloor first bottom return boundary pulse
        const isFirstReturn = Math.abs(distFromCenter - nadirWidth / 2) < 4;
        const returnBoost = isFirstReturn ? 45 : 0;

        // Slant-range Time Variable Gain (TVG) curve simulation
        const rangeRatio = (distFromCenter - nadirWidth / 2) / (centerX - nadirWidth / 2);
        const tvgGain = 1.0 + Math.sin(rangeRatio * Math.PI) * 0.25;

        // Seafloor sedimentary sand ripples & micro-ridges
        const ripple1 = Math.sin(y * 0.08 + x * 0.03) * 14;
        const ripple2 = Math.cos(y * 0.03 - x * 0.06) * 10;
        const ripple3 = Math.sin(y * 0.2 + (x % 30) * 0.1) * 6;

        // Rayleigh acoustic speckle noise
        const u1 = Math.max(1e-6, Math.random());
        const u2 = Math.random();
        const rayleigh = Math.sqrt(-2.0 * Math.log(u1)) * Math.cos(2.0 * Math.PI * u2) * 18;

        const baseSeabed = 105 + ripple1 + ripple2 + ripple3 + rayleigh + returnBoost;
        intensity = Math.max(0, Math.min(255, baseSeabed * tvgGain));
      }

      // Copper/Bronze high-definition acoustic thermal palette
      data[idx] = Math.min(255, Math.floor(intensity * 1.18));      // R
      data[idx + 1] = Math.min(255, Math.floor(intensity * 0.88));  // G
      data[idx + 2] = Math.min(255, Math.floor(intensity * 0.42));  // B
      data[idx + 3] = 255;                                          // A
    }
  }

  ctx.putImageData(imgData, 0, 0);

  // 2. Draw Target 1: Sunken Shipwreck Hull (Starboard Channel)
  const wreckX = 220;
  const wreckY = 160;

  // Acoustic Cast Shadow (Starboard sound casts shadow away from nadir towards the left)
  ctx.fillStyle = '#06080b';
  ctx.beginPath();
  ctx.moveTo(wreckX - 8, wreckY - 12);
  ctx.lineTo(wreckX - 78, wreckY - 18);
  ctx.lineTo(wreckX - 84, wreckY + 44);
  ctx.lineTo(wreckX - 6, wreckY + 38);
  ctx.closePath();
  ctx.fill();

  // Shipwreck Hull & Bulkheads (High Backscatter Reflection)
  ctx.fillStyle = '#fffae0';
  ctx.beginPath();
  ctx.ellipse(wreckX + 16, wreckY + 12, 34, 14, 0.2, 0, Math.PI * 2);
  ctx.fill();

  // Shipwreck structural ribs (Acoustic scattering stripes)
  ctx.strokeStyle = '#fff3bf';
  ctx.lineWidth = 2.5;
  for (let i = -24; i <= 24; i += 8) {
    ctx.beginPath();
    ctx.moveTo(wreckX + 16 + i, wreckY);
    ctx.lineTo(wreckX + 16 + i + 4, wreckY + 24);
    ctx.stroke();
  }

  // 3. Draw Target 2: Ghost Fishing Net & Rigging Array (Port Channel)
  const netX = 560;
  const netY = 280;

  // Ghost Net irregular acoustic shadow (Casts shadow towards right on Port channel)
  ctx.fillStyle = '#080a0e';
  ctx.beginPath();
  ctx.moveTo(netX + 15, netY - 20);
  ctx.lineTo(netX + 75, netY - 14);
  ctx.bezierCurveTo(netX + 85, netY + 20, netX + 70, netY + 50, netX + 60, netY + 65);
  ctx.lineTo(netX + 10, netY + 45);
  ctx.closePath();
  ctx.fill();

  // Ghost net woven filament mesh & weights (Bright acoustic web)
  ctx.strokeStyle = '#fff8db';
  ctx.lineWidth = 1.8;
  ctx.beginPath();
  ctx.moveTo(netX - 25, netY - 15);
  ctx.bezierCurveTo(netX + 5, netY + 5, netX - 10, netY + 35, netX + 20, netY + 40);
  ctx.stroke();

  ctx.strokeStyle = '#ffeaa7';
  ctx.lineWidth = 1.2;
  for (let j = 0; j < 5; j++) {
    ctx.beginPath();
    ctx.arc(netX - 15 + j * 8, netY - 10 + j * 9, 6 + (j % 2) * 4, 0, Math.PI * 2);
    ctx.stroke();
  }

  // 4. Draw Target 3: Subsea Pipeline / Cylinder Section (Port Channel)
  const pipeX = 500;
  const pipeY = 100;

  // Pipeline shadow
  ctx.fillStyle = '#05070a';
  ctx.fillRect(pipeX + 8, pipeY - 6, 42, 14);

  // Pipeline specular linear reflection
  ctx.fillStyle = '#fffbe6';
  ctx.fillRect(pipeX - 14, pipeY - 4, 20, 10);
  ctx.strokeStyle = '#ffffff';
  ctx.lineWidth = 2;
  ctx.strokeRect(pipeX - 14, pipeY - 4, 20, 10);

  // 5. Nadir Track Marker & Channel Indicator Lines
  ctx.strokeStyle = 'rgba(255, 255, 255, 0.4)';
  ctx.setLineDash([4, 4]);
  ctx.lineWidth = 1;
  ctx.beginPath();
  ctx.moveTo(centerX, 0);
  ctx.lineTo(centerX, height);
  ctx.stroke();
  ctx.setLineDash([]);

  // Telemetry HUD overlay in top corner
  ctx.fillStyle = 'rgba(10, 15, 24, 0.75)';
  ctx.fillRect(10, 10, 270, 42);
  ctx.strokeStyle = 'rgba(2, 132, 199, 0.5)';
  ctx.strokeRect(10, 10, 270, 42);

  ctx.fillStyle = '#38bdf8';
  ctx.font = 'bold 11px monospace';
  ctx.fillText('PORT CH [◄] │ NADIR │ [►] STBD CH', 18, 26);
  ctx.fillStyle = '#94a3b8';
  ctx.font = '10px monospace';
  ctx.fillText('FREQ: 450 kHz · ALT: 12.5m · R_MAX: 75m', 18, 42);

  // Convert canvas to Blob -> File
  return new Promise((resolve) => {
    canvas.toBlob((blob) => {
      const file = new File([blob], 'demo_sonar_swath_highres_450khz.png', {
        type: 'image/png',
        lastModified: Date.now(),
      });
      resolve(file);
    }, 'image/png');
  });
}
