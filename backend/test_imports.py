#!/usr/bin/env python
"""Test which module is causing the hang during import."""
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("Loading .env...")
from dotenv import load_dotenv
load_dotenv()
print("✓ .env loaded")

print("Importing FastAPI...")
from fastapi import FastAPI
print("✓ FastAPI imported")

print("Importing pricing router...")
try:
    from src.api.pricing import router as pricing_router
    print("✓ pricing router imported")
except Exception as e:
    print(f"✗ pricing router failed: {e}")

print("Importing news router...")
try:
    from src.api.news import router as news_router
    print("✓ news router imported")
except Exception as e:
    print(f"✗ news router failed: {e}")

print("Importing oil_factors router...")
try:
    from src.api.oil_factors import router as oil_factors_router
    print("✓ oil_factors router imported")
except Exception as e:
    print(f"✗ oil_factors router failed: {e}")

print("Importing ctp router...")
try:
    from src.api.ctp import router as ctp_router
    print("✓ ctp router imported")
except Exception as e:
    print(f"✗ ctp router failed: {e}")

print("\nAll imports completed successfully!")
