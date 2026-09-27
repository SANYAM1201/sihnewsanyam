import React from 'react';
import { Polyline } from 'react-leaflet';

export default function VesselTrack({ track, color = '#22c55e', weight = 3 }) {
  if (!track || !Array.isArray(track) || track.length < 2) {
    return null;
  }

  return (
    <Polyline
      positions={track}
      pathOptions={{
        color,
        weight,
        opacity: 0.9,
        lineCap: 'round',
        lineJoin: 'round',
      }}
    />
  );
}
