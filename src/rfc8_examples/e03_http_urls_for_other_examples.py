import json
import shutil
from pathlib import Path

from rfc8_examples import BASE_PATH
from rfc8_examples.utils import get_uuid


def main():
    EXAMPLE_DIR = BASE_PATH / Path(__file__).with_suffix("").name
    print(f"Running {Path(__file__).name}, {EXAMPLE_DIR}")
    shutil.rmtree(EXAMPLE_DIR, ignore_errors=True)
    EXAMPLE_DIR.mkdir(parents=True, exist_ok=True)

    E01_ZARR_JSON = BASE_PATH / "e01_inlined_multiscale/zarr.json"
    E02_ZARR_JSON = BASE_PATH / "e02_distributed_multiscales/zarr.json"
    e01_ome = json.loads(E01_ZARR_JSON.read_text())["attributes"]["ome"]
    e02_ome = json.loads(E02_ZARR_JSON.read_text())["attributes"]["ome"]

    DATA = {
        "ome": {
            "version": "0.9dev4",
            "type": "collection",
            "name": "Parent Collection",
            "id": get_uuid("e03-collection"),
            "nodes": [
                {
                    "type": "collection",
                    "id": e01_ome["id"],
                    "name": e01_ome["name"],
                    "path": {
                        "type": "zarr",
                        "format": "http",
                        "href": "https://raw.githubusercontent.com/fractal-analytics-platform/ngff-rfc8-examples/main/data/e01_inlined_multiscale",
                    },
                },
                {
                    "type": "collection",
                    "id": e02_ome["id"],
                    "name": e02_ome["name"],
                    "path": {
                        "type": "zarr",
                        "format": "http",
                        "href": "https://raw.githubusercontent.com/fractal-analytics-platform/ngff-rfc8-examples/main/data/e02_distributed_multiscales",
                    },
                },
            ],
        }
    }
    root_path = EXAMPLE_DIR / "root.json"
    if root_path.parent.exists():
        shutil.rmtree(root_path.parent)
    root_path.parent.mkdir(parents=True, exist_ok=True)
    with open(root_path, "w") as f:
        json.dump(DATA, f, indent=2)


if __name__ == "__main__":
    main()
