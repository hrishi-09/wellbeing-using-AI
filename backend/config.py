"""
Shared configuration for all services.
"""
import os

# Generated PDFs are transient — write them to /tmp rather than under the
# app directory. /tmp is reliably writable on constrained hosts like
# Render's free tier, even if the app's own directory tree isn't (or gets
# reset oddly on redeploy).
OUT_DIR = os.path.join("/tmp", "auro_generated")
os.makedirs(OUT_DIR, exist_ok=True)
