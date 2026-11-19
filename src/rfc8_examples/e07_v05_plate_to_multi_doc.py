"""We use an existing v0.5 OME-Zarr plate to load OME-Zarr metadata
and use it to build an RFC8 plate.
We write a multi-document RFC8 collection, with each well as a separate document
and a separate RFC8 collection.json for the plate itself.

Run with: uv run src/rfc8_examples/e07_v05_plate_to_multi_doc.py
"""

import shutil
from pathlib import Path

import ngio_collections as ngc
import requests

from rfc8_examples import BASE_PATH

MAX_ROWS = 2
MAX_COLS = 3

plate_url = "https://livingobjects.ebi.ac.uk/idr/zarr/v0.5/idr0010/76-45.ome.zarr/"


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

    # Only process the first 3 wells for demonstration purposes.
    wells_json = plate_json["wells"]
    # sort wells by columnIndex and rowIndex
    wells_json.sort(key=lambda w: (w["rowIndex"], w["columnIndex"]))

    for well_json in wells_json:
        well_path = well_json["path"]
        rowname, colname = well_path.split("/")[-2:]
        if rowname not in row_names:
            continue
        if colname not in col_names:
            continue

        write_path = str(base_path / "wells" / (well_path + ".zarr"))

        well_id = f"well{well_path.replace('/', '')}"
        well_collection_node = ngc.new_node("collection", id=well_id, name=well_id)

        well_url = plate_url + well_path + "/"
        well_json = requests.get(well_url + "zarr.json").json()

        img_paths = [
            img["path"] for img in well_json["attributes"]["ome"]["well"]["images"]
        ]
        for img_path in img_paths:
            img_url = well_url + img_path + "/"
            ms_json = requests.get(img_url + "zarr.json").json()["attributes"]["ome"][
                "multiscales"
            ][0]
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
                f"{rowname}{colname}_field{img_path}", ds_paths, scales, axes
            )
            well_collection_node = well_collection_node.add(multiscale_node)

        print("write_path", write_path)
        rf_well = ngc.create(write_path, well_collection_node, overwrite=True)
        # well_ref = ngc.open(write_path).ref()  # ReferenceObj(id="image", path=image.zarr)

        # plate = plate.add(well_collection_node)
        plate = plate.add_external(rf_well)

    return plate


def main() -> None:
    EXAMPLE_DIR = BASE_PATH / Path(__file__).with_suffix("").name
    print(f"Running {Path(__file__).name}, {EXAMPLE_DIR}")
    shutil.rmtree(EXAMPLE_DIR, ignore_errors=True)
    EXAMPLE_DIR.mkdir(parents=True, exist_ok=True)

    plate = build_collection(EXAMPLE_DIR)

    url = str(EXAMPLE_DIR / "collection.json")
    ngc.create(url, plate, overwrite=True)

    print(f"wrote {url}\n")
    print(Path(url).read_text())


if __name__ == "__main__":
    main()
