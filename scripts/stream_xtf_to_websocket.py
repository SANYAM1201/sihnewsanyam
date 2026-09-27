"""Stream acoustic pings from a local or simulated XTF file to the Sonar Sentry WebSocket server."""

import argparse
import asyncio
import json
import sys
from pathlib import Path

# Add backend directory
backend_path = Path(__file__).resolve().parent.parent / "backend"
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

import websockets
from app.services.xtf_parser import create_synthetic_xtf, parse_xtf_bytes


async def stream_xtf(file_path: str = "", ws_url: str = "ws://localhost:8000/ws/waterfall", delay_ms: int = 100):
    print(f"Connecting to live vessel waterfall stream: {ws_url}...")

    if file_path and Path(file_path).is_file():
        data = Path(file_path).read_bytes()
    else:
        print("Generating compliant Triton XTF synthetic survey track...")
        data = create_synthetic_xtf(num_pings=64, samples_per_channel=256)

    waterfall_np, meta = parse_xtf_bytes(data)
    total_pings = len(waterfall_np)
    print(f"Loaded {total_pings} acoustic pings (width: {waterfall_np.shape[1]} px).")

    async with websockets.connect(ws_url) as ws:
        print("Connected! Streaming live sonar pings to server...")
        for i in range(total_pings):
            chunk = waterfall_np[i].tolist()
            message = {
                "type": "ping",
                "ping_number": i + 1,
                "waterfall_chunk": chunk,
                "detections": [],
                "timestamp": f"Ping #{i+1:04d}",
            }
            await ws.send(json.dumps(message))
            print(f"Streamed ping {i+1}/{total_pings}", end="\r")
            await asyncio.sleep(delay_ms / 1000.0)

    print("\nStreaming mission completed successfully!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", default="")
    parser.add_argument("--url", default="ws://localhost:8000/ws/waterfall")
    parser.add_argument("--delay", type=int, default=80)
    args = parser.parse_args()

    asyncio.run(stream_xtf(args.file, args.url, args.delay))
