"""Verify an unsigned GeoAlibi evidence packet without contacting any API."""
import argparse
from pathlib import Path
from geoalibi.dossier import verify_packet

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('packet',type=Path)
args=parser.parse_args()
manifest=verify_packet(args.packet.read_bytes())
print('Content checksums verified for',len(manifest['files']),'files. This does not establish authenticity or correctness.')
