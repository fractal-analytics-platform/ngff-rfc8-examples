"""We use an existing v0.5 OME-Zarr plate to load OME-Zarr metadata
and use it to build an RFC8 plate.
We write a multi-document RFC8 collection, with each well as a separate document
and a separate RFC8 collection.json for the plate itself.

Run with: uv run python ./src/rfc8_examples/e08_v05_big_plate_to_multi_doc.py
"""

import functools
import shutil
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

import ngio_collections as ngc
import requests
import requests.adapters

from rfc8_examples import BASE_PATH

# Use smaller numbers if you want to convert fewer wells for testing
MAX_ROWS = 100
MAX_COLS = 100

plate_url = "https://livingobjects.ebi.ac.uk/idr/share/ome2024-ngff-challenge/idr0036/20591.ome.zarr/"


def build_multiscale(
    prefix: str,
    paths: list[str],
    scales: list[list[float]],
    axes: list[ngc.Axis],
) -> ngc.Node:

    arrays = [
        ngc.MultiscaleArray(
            path=ngc.ZarrPath(
                format="http",
                href=paths[level_index],
            ),
            downsamplingTransformations=([ngc.ScaleDownsampling(scale=factor_list)]),
        )
        for level_index, factor_list in enumerate(scales)
    ]

    node = ngc.new_multiscale(
        id=prefix,
        name=prefix,
        # The multiscale defines the coordinate system its single scales map into.
        coordinate_systems=[ngc.CoordinateSystem(id=f"{prefix}_space", axes=axes)],
        coordinate_transformations=[],
        arrays=arrays,
    )

    return node


def process_single_well(
    well_json: dict[str, Any],
    *,
    row_names: list[str],
    col_names: list[str],
    base_path: Path,
) -> ngc.Node | None:
    t_start = time.perf_counter()
    well_path = well_json["path"]
    rowname, colname = well_path.split("/")[-2:]
    print(f"[Well {rowname}/{colname}] START")
    if rowname not in row_names or colname not in col_names:
        return None
    write_path = str(base_path / "wells" / (well_path + ".zarr"))
    well_id = f"well{well_path.replace('/', '')}"
    well_collection_node = ngc.new_node("collection", id=well_id, name=well_id)
    well_url = plate_url + well_path + "/"
    # Optimization: Re-use the same session for all requests
    with requests.Session() as session:
        # Add retries, since this script may take long
        session.mount("https://", requests.adapters.HTTPAdapter(max_retries=3))

        well_json = requests.get(well_url + "zarr.json").json()
        ome_attrs = well_json["attributes"]["ome"]
        img_paths = [img["path"] for img in ome_attrs["well"]["images"]]

        for img_path in img_paths:
            img_url = well_url + img_path + "/"
            ome_json = session.get(img_url + "zarr.json").json()["attributes"]["ome"]
            ms_json = ome_json["multiscales"][0]
            axes = [
                ngc.Axis(name=ax["name"], type=ax["type"], unit=ax.get("unit"))
                for ax in ms_json["axes"]
            ]
            # paths are http URLs to the datasets within the multiscale image
            ds_paths = [img_url + ds["path"] for ds in ms_json["datasets"]]

            scales = [
                ds["coordinateTransformations"][0]["scale"]
                for ds in ms_json["datasets"]
            ]
            multiscale_node = build_multiscale(
                f"{rowname}{colname}_field{img_path}",
                ds_paths,
                scales,
                axes,
            )
            well_collection_node = well_collection_node.add(multiscale_node)

    rf_well = ngc.create(write_path, well_collection_node, overwrite=True)
    elapsed = time.perf_counter() - t_start
    print(f"[Well {rowname}/{colname}] END - elapsed {elapsed:.2f} s - {write_path=}")
    return rf_well


def build_collection(base_path: Path) -> ngc.Node:
    """The in-memory tree, detached until `create` writes it."""

    # load json from image_url
    json_rsp = requests.get(plate_url + "zarr.json").json()
    plate_json = json_rsp["attributes"]["ome"]["plate"]
    cols_json = plate_json["columns"][:MAX_COLS]
    rows_json = plate_json["rows"][:MAX_ROWS]
    row_names = [row["name"] for row in rows_json]
    col_names = [col["name"] for col in cols_json]

    # FIXME: Re-include HCS attributes through traits
    # plate_attrs = {"plate": {"columns": cols_json, "rows": rows_json}}
    plate = ngc.new_collection(id="plate", name="plate")

    wells_json = plate_json["wells"]
    # sort wells by columnIndex and rowIndex
    wells_json.sort(key=lambda w: (w["rowIndex"], w["columnIndex"]))

    # Optimization: process multiple wells in parallel
    partial_function = functools.partial(
        process_single_well,
        row_names=row_names,
        col_names=col_names,
        base_path=base_path,
    )
    with ThreadPoolExecutor() as executor:
        well_nodes = executor.map(partial_function, wells_json)
    for well_node in well_nodes:
        plate = plate.add_external(well_node)

    return plate


def main() -> None:
    EXAMPLE_DIR = BASE_PATH / Path(__file__).with_suffix("").name
    print(f"Running {Path(__file__).name}, {EXAMPLE_DIR}")
    shutil.rmtree(EXAMPLE_DIR, ignore_errors=True)
    EXAMPLE_DIR.mkdir(parents=True, exist_ok=True)
    plate = build_collection(EXAMPLE_DIR)

    url = str(EXAMPLE_DIR / "collection.json")
    ngc.create(url, plate, overwrite=True)

    print(f"Wrote {url}\n")


if __name__ == "__main__":
    main()
