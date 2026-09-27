"""Compile best.onnx to TensorRT FP16 / INT8 execution engine for NVIDIA edge hardware."""

import argparse
import sys
from pathlib import Path


def build_tensorrt_engine(onnx_path: str = "best.onnx", engine_path: str = "models/best_int8.engine", fp16: bool = True, int8: bool = False):
    try:
        import tensorrt as trt
    except ImportError:
        print("TensorRT Python package is not available on this platform.")
        print("On NVIDIA Jetson (Orin/Xavier), install with: sudo apt-get install tensorrt python3-libnvinfer")
        print("Alternatively, use the trtexec CLI:")
        print(f"  trtexec --onnx={onnx_path} --saveEngine={engine_path} {'--fp16' if fp16 else ''} {'--int8' if int8 else ''}")
        return

    logger = trt.Logger(trt.Logger.WARNING)
    builder = trt.Builder(logger)
    network = builder.create_network(1 << int(trt.NetworkDefinitionCreationFlag.EXPLICIT_BATCH))
    parser = trt.OnnxParser(network, logger)

    with open(onnx_path, "rb") as f:
        if not parser.parse(f.read()):
            for error in range(parser.num_errors):
                print(parser.get_error(error))
            raise ValueError("ONNX parsing failed")

    config = builder.create_builder_config()
    config.set_memory_pool_limit(trt.MemoryPoolType.WORKSPACE, 1 << 30)  # 1GB

    if fp16 and builder.platform_has_fast_fp16:
        config.set_flag(trt.BuilderFlag.FP16)
        print("Enabled FP16 precision")

    if int8 and builder.platform_has_fast_int8:
        config.set_flag(trt.BuilderFlag.INT8)
        print("Enabled INT8 quantization")

    print(f"Building serialized TensorRT engine from {onnx_path}...")
    serialized_engine = builder.build_serialized_network(network, config)

    Path(engine_path).parent.mkdir(parents=True, exist_ok=True)
    with open(engine_path, "wb") as f:
        f.write(serialized_engine)
    print(f"TensorRT engine compiled to {engine_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--onnx", default="best.onnx")
    parser.add_argument("--engine", default="models/best_int8.engine")
    parser.add_argument("--fp16", action="store_true", default=True)
    parser.add_argument("--int8", action="store_true", default=False)
    args = parser.parse_args()
    build_tensorrt_engine(args.onnx, args.engine, fp16=args.fp16, int8=args.int8)
