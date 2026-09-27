import React from 'react';
import { Polygon } from 'react-leaflet';

export default function SwathOverlay({ polygon, color = '#38bdf8', fillOpacity = 0.35 }) {
  if (!polygon || !Array.isArray(polygon) || polygon.length === 0) {
    return null;
  }

  return (
    <Polygon
      positions={polygon}
      pathOptions={{
        color,
        weight: 2,
        fillColor: color,
        fillOpacity,
        dashArray: '4, 4',
      }}
    />
  );
}
