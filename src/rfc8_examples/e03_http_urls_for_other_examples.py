import json
import shutil
from pathlib import Path

from rfc8_examples import BASE_PATH

EXAMPLE_DIR = BASE_PATH / Path(__file__).with_suffix("").name
DATA = {
    "ome": {
        "version": "0.x",
        "type": "collection",
        "name": "http_collection",
        "id": "http_collection",
        "nodes": [
            {
                "type": "collection",
                "name": "example1",
                "id": "example1",
                "path": {
                    "type": "json",
                    "path": "https://raw.githubusercontent.com/fractal-analytics-platform/ngff-rfc8-examples/main/data/e01_basic_example/root.json",
                },
            },
            {
                "type": "collection",
                "name": "example2",
                "id": "example2",
                "path": {
                    "type": "json",
                    "path": "https://raw.githubusercontent.com/fractal-analytics-platform/ngff-rfc8-examples/main/data/e02_basic_examples_many_images/root.json",
                },
            },
            {
                "type": "collection",
                "name": "example4",
                "id": "example4",
                "path": {
                    "type": "json",
                    "path": "https://raw.githubusercontent.com/fractal-analytics-platform/ngff-rfc8-examples/main/data/e04_plate_multiple_fields/root.json",
                },
            },
        ],
    }
}

def main():
    root_path = EXAMPLE_DIR / "root.json"
    if root_path.parent.exists():
        shutil.rmtree(root_path.parent)
    root_path.parent.mkdir(parents=True, exist_ok=True)
    with open(root_path, "w") as f:
        json.dump(DATA, f, indent=2)

if __name__ == "__main__":
    main()