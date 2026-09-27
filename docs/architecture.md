# Sonar Sentry — System Architecture & Physics Specifications

## 1. System Overview

```
 ┌────────────────────────────────────────────────────────────────────────┐
 │                              FRONTEND                                  │
 │   React 18 · Vite · CSS Modules · Real-Time Canvas Waterfall · Leaflet │
 └───────────────────────────────────┬────────────────────────────────────┘
                                     │ HTTP (REST) / WSS (WebSocket)
                                     ▼
 ┌────────────────────────────────────────────────────────────────────────┐
 │                           FASTAPI BACKEND                              │
 │                                                                        │
 │   ┌──────────────────────┐  ┌────────────────────┐  ┌──────────────┐   │
 │   │ Triton XTF Parser    │  │ SSS DSP Pipeline   │  │ YOLOv8s Head │   │
 │   │ (0xFACE / 0x7B)      │  │ BAC + Stripe + FFT │  │ + SADH Eval  │   │
 │   └──────────┬───────────┘  └─────────┬──────────┘  └──────┬───────┘   │
 │              │                        │                    │           │
 │              ▼                        ▼                    ▼           │
 │   ┌────────────────────────────────────────────────────────────────┐   │
 │   │             SADH Acoustic Shadow Physics Estimator             │   │
 │   │      H_t = (L_s · H_s) / R_s  ·  Confidence Fusion Engine      │   │
 │   └───────────────────────────────┬────────────────────────────────┘   │
 │                                   │                                    │
 └───────────────────────────────────┼────────────────────────────────────┘
                                     ▼
 ┌────────────────────────────────────────────────────────────────────────┐
 │                      STORAGE & TELEMETRY LAYER                         │
 │     SQLite (Local) · Supabase (Cloud Sync) · Prometheus Metrics        │
 └────────────────────────────────────────────────────────────────────────┘
```

## 2. DSP Pipeline Stages

1. **Beam Angle Correction (BAC)**: Normalizes across-range acoustic gain drop-off caused by spherical spreading and acoustic attenuation in seawater.
2. **Homomorphic / Stripe Filtering**: Attenuates horizontal and vertical sonar striping caused by vessel heave, roll, and transducer ringing.
3. **Slant Range Correction (SRC)**: Reprojects slant-range travel times ($R_s$) to true seafloor ground-range coordinates ($R_g = \sqrt{R_s^2 - H_s^2}$).
4. **Adaptive Boundary Preservation**: Prevents over-smoothing of fine target edges using high-gradient bilateral weighting.

## 3. SADH Acoustic Shadow Physics Formulation

Target height above the seabed ($H_t$) is derived geometrically from acoustic shadow length ($L_s$), towfish altitude ($H_s$), and slant range ($R_s$):

$$H_t = \frac{L_s \cdot H_s}{R_s}$$

The **Physics Confidence Score** fuses:
- Neural detector probability ($C_{yolo}$)
- Expected physical dimensions for the detected marine debris class
- Contrast ratio between the acoustic highlight and acoustic shadow
- Non-zero shadow verification:

$$C_{physics} = \alpha C_{yolo} + \beta \min\left(1.0, \frac{H_t}{H_{expected}}\right) + \gamma S_{contrast}$$
