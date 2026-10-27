"""Download one pinned author checkpoint with size/hash verification. No API credit used."""
from pathlib import Path
import os
import httpx
from geoalibi.pretrained import checkpoint_path, verify, URL, SIZE


def main():
    path = checkpoint_path()
    if path.exists():
        verify(path)
        print("Pinned detector already verified.")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".download")
    try:
        with httpx.stream("GET", URL, timeout=120, follow_redirects=True) as response:
            response.raise_for_status()
            count = 0
            with temporary.open("wb") as out:
                for chunk in response.iter_bytes(1024 * 1024):
                    count += len(chunk)
                    if count > SIZE:
                        raise ValueError("Checkpoint download exceeds expected size.")
                    out.write(chunk)
        verify(temporary)
        os.replace(temporary, path)
        print("Author checkpoint verified and installed. Weights: CC-BY-4.0; attribution in README.")
    finally:
        temporary.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
