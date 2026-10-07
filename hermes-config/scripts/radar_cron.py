#!/usr/bin/env python3
"""
Cron Runner Script: Hermes AI Tech Radar Daily Digest
Dijalankan secara terjadwal untuk mengumpulkan rilis teknologi terbaru,
memverifikasi, dan mencetak pesan digest untuk dikirim ke WhatsApp Zulfi.
"""
import sys
import os

# Tambahkan /opt/data ke sys.path
sys.path.insert(0, "/opt/data")

from radar.service import RadarService

def run_radar():
    service = RadarService()
    # 1. Jalankan pipeline pengumpulan & analisis
    pipeline_res = service.run_pipeline()
    
    # 2. Format digest untuk WhatsApp
    digest_text = service.format_whatsapp_digest(min_tier="INTERESTING", limit=6)
    
    # Cetak digest ke stdout (ini yang akan diteruskan oleh Hermes cron delivery ke WhatsApp)
    print(digest_text)

if __name__ == "__main__":
    run_radar()
