/**
 * Generates an authentic simulated side-scan sonar swath image (PNG File)
 * with seafloor backscatter, nadir track, acoustic highlight, and cast shadow geometry.
 */

export function createDemoSonarFile() {
  const width = 640;
  const height = 360;
  const canvas = document.createElement('canvas');
  canvas.width = width;
  canvas.height = height;
  const ctx = canvas.getContext('2d');

  const imgData = ctx.createImageData(width, height);
  const data = imgData.data;

  // 1. Generate seabed backscatter background
  for (let y = 0; y < height; y++) {
    for (let x = 0; x < width; x++) {
      const idx = (y * width + x) * 4;
      // Distance from nadir (center)
      const distFromCenter = Math.abs(x - width / 2);
      
      // Nadir water column is dark
      let baseIntensity = distFromCenter < 20 ? 15 : 120 + (Math.random() * 45 - 22);

      // Range attenuation & seafloor ripples
      if (distFromCenter >= 20) {
        baseIntensity += Math.sin(y * 0.15 + x * 0.05) * 15;
      }

      baseIntensity = Math.max(0, Math.min(255, baseIntensity));

      // Thermal bronze / amber sonar palette
      data[idx] = Math.min(255, baseIntensity * 1.15);     // R
      data[idx + 1] = Math.min(255, baseIntensity * 0.85); // G
      data[idx + 2] = Math.min(255, baseIntensity * 0.4);  // B
      data[idx + 3] = 255;                                // A
    }
  }

  ctx.putImageData(imgData, 0, 0);

  // 2. Draw Simulated Target 1 (Sunken Shipwreck with Shadow)
  // Target acoustic highlight (bright white/yellow)
  ctx.fillStyle = '#ffea9f';
  ctx.fillRect(180, 120, 36, 16);
  // Cast acoustic shadow behind it (pure dark zero return)
  ctx.fillStyle = '#08090c';
  ctx.fillRect(216, 118, 52, 20);

  // 3. Draw Simulated Target 2 (Discarded Ghost Net / Cable)
  ctx.strokeStyle = '#fff0b3';
  ctx.lineWidth = 3;
  ctx.beginPath();
  ctx.moveTo(420, 200);
  ctx.bezierCurveTo(440, 220, 460, 190, 480, 230);
  ctx.stroke();
  // Shadow for net
  ctx.fillStyle = '#0a0d10';
  ctx.fillRect(482, 205, 30, 28);

  // Convert canvas to Blob -> File
  return new Promise((resolve) => {
    canvas.toBlob((blob) => {
      const file = new File([blob], 'demo_sonar_swath_arabian_sea.png', {
        type: 'image/png',
        lastModified: Date.now(),
      });
      resolve(file);
    }, 'image/png');
  });
}
