"""
Main Document Ingestion Pipeline.
Orchestrates parsing of Constitution of India and BNSS 2023.
Produces unified active legal corpus: data/processed/all_chunks.json.
"""

import json
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from pipeline.parse_constitution import run_ingestion as parse_constitution
from pipeline.parse_bnss import parse_bnss
from pipeline.parse_bns import parse_bns
from pipeline.parse_cpa import parse_cpa
from pipeline.parse_rti import parse_rti
PROCESSED_DIR = BASE_DIR / "data" / "processed"


def run_ingestion():
    """Run all document parsers and produce consolidated corpus."""
    const_chunks = parse_constitution()
    bnss_chunks = parse_bnss()
    bns_chunks = parse_bns()
    cpa_chunks = parse_cpa()
    rti_chunks = parse_rti()

    all_chunks = const_chunks + bnss_chunks + bns_chunks + cpa_chunks + rti_chunks
    out_path = PROCESSED_DIR / "all_chunks.json"
    out_path.write_text(json.dumps(all_chunks, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"\n[Ingest Complete]")
    print(f"  Constitution Chunks: {len(const_chunks)}")
    print(f"  BNSS 2023 Chunks:    {len(bnss_chunks)}")
    print(f"  BNS 2023 Chunks:     {len(bns_chunks)}")
    print(f"  CPA 2019 Chunks:     {len(cpa_chunks)}")
    print(f"  RTI 2005 Chunks:     {len(rti_chunks)}")
    print(f"  Total Active Chunks: {len(all_chunks)} -> {out_path}")
    return all_chunks


if __name__ == "__main__":
    run_ingestion()
