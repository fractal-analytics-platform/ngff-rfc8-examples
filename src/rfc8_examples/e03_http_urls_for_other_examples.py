import json
import shutil
from pathlib import Path

from rfc8_examples import BASE_PATH

EXAMPLE_DIR = BASE_PATH / Path(__file__).with_suffix("").name
DATA = {
    "ome": {
        "version": "0.9dev4",
        "type": "collection",
        "name": "Parent Collection",
        "id": "0e566578-f3f4-4129-af7c-17cfb586a877",
        "nodes": [
            {
                "type": "collection",
                "path": {
                    "type": "https://fractal-analytics-platform.github.io/ngff-extensions/node-path-http",
                    "href": "https://raw.githubusercontent.com/fractal-analytics-platform/ngff-rfc8-examples/main/data/e01_basic_example",
                    "document_type": "zarr",
                },
            },
            {
                "type": "collection",
                "path": {
                    "type": "https://fractal-analytics-platform.github.io/ngff-extensions/node-path-http",
                    "href": "https://raw.githubusercontent.com/fractal-analytics-platform/ngff-rfc8-examples/main/data/e02_basic_examples_many_images",
                    "document_type": "zarr",
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
