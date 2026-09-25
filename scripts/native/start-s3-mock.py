"""Starts moto's S3-compatible mock server on port 9000 (MinIO's usual
port) and creates the finpulse-raw bucket, standing in for MinIO on
this machine (see constitution v1.1.0's Deployment Environment
Exception -- MinIO stopped shipping Windows binaries).

Run this once, leave it running in its own terminal, then run
scripts/run_pipeline.py in another terminal.
"""
from __future__ import annotations

import threading

import boto3
from moto.server import ThreadedMotoServer

PORT = 9000


def main() -> None:
    server = ThreadedMotoServer(port=PORT, ip_address="127.0.0.1")
    server.start()
    print(f"S3-compatible mock server running at http://localhost:{PORT}")

    client = boto3.client(
        "s3",
        endpoint_url=f"http://localhost:{PORT}",
        aws_access_key_id="finpulse",
        aws_secret_access_key="finpulse123",
        region_name="us-east-1",
    )
    client.create_bucket(Bucket="finpulse-raw")
    print("bucket 'finpulse-raw' created")
    print("Ctrl+C to stop.")

    threading.Event().wait()


if __name__ == "__main__":
    main()
