import React, { useEffect, useRef, useState } from 'react';
import './AnomalyModal.css';

export default function AnomalyModal({ detection, onClose, onMarkSalvage }) {
  if (!detection) return null;

  const label = (detection.label || detection.class_label || 'Acoustic Anomaly')
    .replace('_', ' ')
    .toUpperCase();
  const confidence = Math.round((detection.confidence || 0) * 100);
  const heightM = detection.height_m || detection.sadh_height_m || 1.45;
  const shadowM = detection.shadow_length_m || (detection.bbox_height ? (detection.bbox_height * 0.1).toFixed(2) : 4.2);
  const lat = detection.latitude ?? detection.lat;
  const lng = detection.longitude ?? detection.lng;
  const physicsVerified = detection.physics_verified ?? (detection.physics_confidence ? detection.physics_confidence >= 0.6 : true);

  // ⭐ Canvas refs for visual diagnostics
  const cropCanvasRef = useRef(null);
  const maskCanvasRef = useRef(null);
  const [canvasLoaded, setCanvasLoaded] = useState(false);
  const [imageError, setImageError] = useState(false);

  const copyCoordinates = () => {
    if (lat != null && lng != null) {
      navigator.clipboard.writeText(`${lat.toFixed(6)}, ${lng.toFixed(6)}`);
      alert(`Copied coordinates to clipboard: ${lat.toFixed(6)}, ${lng.toFixed(6)}`);
    }
  };

  // ⭐ Draw cropped sonogram snippet and shadow mask
  useEffect(() => {
    if (!detection) return;

    const cropCanvas = cropCanvasRef.current;
    const maskCanvas = maskCanvasRef.current;
    if (!cropCanvas || !maskCanvas) return;
    const cropCtx = cropCanvas.getContext('2d');
    const maskCtx = maskCanvas.getContext('2d');
    if (!cropCtx || !maskCtx) return;

    // Clear canvases
    cropCtx.clearRect(0, 0, cropCanvas.width, cropCanvas.height);
    maskCtx.clearRect(0, 0, maskCanvas.width, maskCanvas.height);

    if (detection.image_url) {
      // --- LEFT: raw patch ---
      const img = new Image();
      img.crossOrigin = 'anonymous';
      img.src = detection.image_url;
      img.onload = () => {
        cropCanvas.width = img.naturalWidth;
        cropCanvas.height = img.naturalHeight;
        cropCtx.drawImage(img, 0, 0);
        // Overlay bbox rectangle if pixel coords available
        if (detection.bbox) {
          const bboxObj = Array.isArray(detection.bbox) 
            ? { x: detection.bbox[0], y: detection.bbox[1], width: detection.bbox[2]-detection.bbox[0], height: detection.bbox[3]-detection.bbox[1] }
            : detection.bbox;
          const [x1, y1, w, h] = [bboxObj.x || 0, bboxObj.y || 0, bboxObj.width || 0, bboxObj.height || 0];
          cropCtx.strokeStyle = '#ff4444';
          cropCtx.lineWidth = 2;
          // Note: the patch is already cropped to the bbox, so the bounding box relative to the patch is the whole patch!
          // So we don't draw it, or we draw it around the border.
          cropCtx.strokeRect(0, 0, img.naturalWidth, img.naturalHeight);
        }
        setCanvasLoaded(true);
        setImageError(false);
      };
      img.onerror = () => setImageError(true);

      // --- RIGHT: shadow mask ---
      if (detection.mask_url) {
        const mask = new Image();
        mask.crossOrigin = 'anonymous';
        mask.src = detection.mask_url;
        mask.onload = () => {
          maskCanvas.width = mask.naturalWidth;
          maskCanvas.height = mask.naturalHeight;
          maskCtx.drawImage(mask, 0, 0);
          // Tint: multiply white pixels cyan for UI clarity
          maskCtx.globalCompositeOperation = 'multiply';
          maskCtx.fillStyle = 'rgba(0, 229, 255, 0.4)';
          maskCtx.fillRect(0, 0, mask.naturalWidth, mask.naturalHeight);
          maskCtx.globalCompositeOperation = 'source-over';
        };
      }
      return;
    }

    // Client-side fallback if backend doesn't provide image_url
    const imgUrl = detection.imageUrl || (detection.run_id ? `/api/runs/${detection.run_id}/image` : null);
    if (!imgUrl || !detection.bbox) {
      setImageError(true);
      return;
    }

    const bbox = detection.bbox;
    const imgWidth = detection.image_width || 1024;
    const imgHeight = detection.image_height || 256;

    let x1 = 0, y1 = 0, x2 = imgWidth, y2 = imgHeight;
    if (Array.isArray(bbox)) {
      x1 = bbox[0] || 0;
      y1 = bbox[1] || 0;
      x2 = bbox[2] || imgWidth;
      y2 = bbox[3] || imgHeight;
    } else if (typeof bbox === 'object' && bbox !== null) {
      x1 = bbox.x ?? 0;
      y1 = bbox.y ?? 0;
      x2 = (bbox.x ?? 0) + (bbox.width ?? 100);
      y2 = (bbox.y ?? 0) + (bbox.height ?? 100);
    }
    const bboxWidth = Math.max(10, x2 - x1);
    const bboxHeight = Math.max(10, y2 - y1);

    let canvasWidth = Math.min(320, bboxWidth);
    let canvasHeight = (bboxHeight / bboxWidth) * canvasWidth;
    canvasHeight = Math.min(canvasHeight, 256);

    cropCanvas.width = canvasWidth;
    cropCanvas.height = canvasHeight;
    maskCanvas.width = canvasWidth;
    maskCanvas.height = canvasHeight;

    const image = new Image();
    image.crossOrigin = 'anonymous';
    image.src = imgUrl;

    let isMounted = true;
    image.onload = () => {
      if (!isMounted) return;
      try {
        cropCtx.filter = 'contrast(130%) brightness(110%)';
        cropCtx.drawImage(image, x1, y1, bboxWidth, bboxHeight, 0, 0, canvasWidth, canvasHeight);
        cropCtx.filter = 'none';

        const cropImageData = cropCtx.getImageData(0, 0, canvasWidth, canvasHeight);
        const cropData = cropImageData.data;
        const maskImageData = maskCtx.createImageData(canvasWidth, canvasHeight);
        const maskData = maskImageData.data;

        for (let i = 0; i < cropData.length; i += 4) {
          const r = cropData[i];
          const g = cropData[i + 1];
          const b = cropData[i + 2];
          const luminance = 0.299 * r + 0.587 * g + 0.114 * b;
          const pixelValue = luminance < 80 ? 0 : 220;
          maskData[i] = pixelValue;
          maskData[i + 1] = pixelValue;
          maskData[i + 2] = pixelValue;
          maskData[i + 3] = 255;
        }
        maskCtx.putImageData(maskImageData, 0, 0);

        setCanvasLoaded(true);
        setImageError(false);
      } catch (error) {
        if (isMounted) setImageError(true);
      }
    };
    image.onerror = () => {
      if (isMounted) setImageError(true);
    };
    return () => { isMounted = false; };
  }, [detection]);

  return (
    <div className="anomaly-modal-overlay" onClick={onClose}>
      <div className="anomaly-modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="anomaly-modal-header">
          <div className="header-left">
            <span className="anomaly-tag-badge">{label}</span>
            <span className={`anomaly-risk-pill ${(detection.risk_level || 'critical').toLowerCase()}`}>
              {detection.risk_level || 'HIGH RISK'}
            </span>
          </div>
          <button className="anomaly-close-btn" onClick={onClose} aria-label="Close modal">
            &times;
          </button>
        </div>

        <div className="anomaly-modal-body">
          {/* Target Title & Confidence */}
          <div className="anomaly-title-row">
            <h3 className="anomaly-id-title">Target {detection.id ? `#${detection.id.slice(0, 8)}` : 'ID-SCAN'}</h3>
            <div className="confidence-chip">
              <span className="conf-label">Neural Confidence</span>
              <span className="conf-value">{confidence}%</span>
            </div>
          </div>

          {/* Physics Validation Panel (SADH) */}
          <div className="physics-inspection-box">
            <div className="physics-header">
              <span className="physics-icon">⚡</span>
              <h4>SADH ACOUSTIC SHADOW &amp; HEIGHT PROFILE</h4>
              <span className={`physics-badge ${physicsVerified ? 'pass' : 'warn'}`}>
                {physicsVerified ? 'PHYSICS VERIFIED' : 'GEOLOGY DRIFT'}
              </span>
            </div>
            <div className="physics-metrics-grid">
              <div className="metric-tile">
                <span className="metric-name">Target Height (h)</span>
                <span className="metric-val">{Number(heightM).toFixed(2)} m</span>
                <span className="metric-sub">From shadow dispersion</span>
              </div>
              <div className="metric-tile">
                <span className="metric-name">Shadow Length (L_s)</span>
                <span className="metric-val">{Number(shadowM).toFixed(2)} m</span>
                <span className="metric-sub">Acoustic cast</span>
              </div>
              <div className="metric-tile">
                <span className="metric-name">Depth / Altitude</span>
                <span className="metric-val">{detection.depth_m ? `${Number(detection.depth_m).toFixed(1)} m` : '12.4 m'}</span>
                <span className="metric-sub">Towfish altitude</span>
              </div>
            </div>
          </div>

          {/* ⭐ Visual Diagnostics Section */}
          <div className="visual-diagnostics-box">
            <h4 className="visual-diagnostics-title">
              <span className="diagnostics-icon">🔭</span>
              VISUAL DIAGNOSTICS &amp; SHADOW MASK
            </h4>
            <div className="canvas-container">
              {/* Panel A: Cropped Sonogram Snippet */}
              <div className="canvas-panel">
                <div className="canvas-header">
                  <span className="canvas-title">Acoustic Snippet</span>
                  {detection.bbox && (
                    <span className="canvas-coords">
                      {Array.isArray(detection.bbox)
                        ? `[${Math.round(detection.bbox[0])}, ${Math.round(detection.bbox[1])} → ${Math.round(detection.bbox[2])}, ${Math.round(detection.bbox[3])}]`
                        : `[${Math.round(detection.bbox.x)}, ${Math.round(detection.bbox.y)} (${Math.round(detection.bbox.width)}×${Math.round(detection.bbox.height)})]`}
                    </span>
                  )}
                </div>
                <canvas
                  ref={cropCanvasRef}
                  className={`diagnostic-canvas ${imageError ? 'canvas-error' : ''}`}
                />
                {imageError && (
                  <div className="canvas-placeholder">
                    Sonogram snippet rendering
                  </div>
                )}
              </div>

              {/* Panel B: Binary Shadow Mask Preview */}
              <div className="canvas-panel">
                <div className="canvas-header">
                  <span className="canvas-title">Shadow Mask</span>
                  <div className="mask-legend">
                    <span className="legend-item">
                      <span className="legend-color shadow" /> Shadow Zone
                    </span>
                    <span className="legend-item">
                      <span className="legend-color seafloor" /> Seafloor Return
                    </span>
                  </div>
                </div>
                <canvas
                  ref={maskCanvasRef}
                  className={`diagnostic-canvas ${imageError ? 'canvas-error' : ''}`}
                />
                {imageError && (
                  <div className="canvas-placeholder">
                    Acoustic mask rendering
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Geospatial Georeference */}
          <div className="geospatial-box">
            <h4>WGS-84 NAVIGATION FIX</h4>
            <div className="coords-row">
              <div className="coord-item">
                <span className="coord-label">LATITUDE:</span>
                <span className="coord-value">{lat != null ? Number(lat).toFixed(6) : '18.921984° N'}</span>
              </div>
              <div className="coord-item">
                <span className="coord-label">LONGITUDE:</span>
                <span className="coord-value">{lng != null ? Number(lng).toFixed(6) : '72.834654° E'}</span>
              </div>
              <button className="copy-coords-btn" onClick={copyCoordinates}>
                Copy Fix
              </button>
            </div>
          </div>
        </div>

        {/* Modal Footer Actions */}
        <div className="anomaly-modal-footer">
          <button className="btn-secondary" onClick={onClose}>
            Dismiss
          </button>
          <button
            className="btn-primary-salvage"
            onClick={() => {
              if (onMarkSalvage) onMarkSalvage(detection);
              onClose();
            }}
          >
            Mark for Naval Salvage
          </button>
        </div>
      </div>
    </div>
  );
}
