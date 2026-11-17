from pathlib import Path

import ngio_collections as ngc

from rfc8_examples import BASE_PATH, get_uuid
from rfc8_examples.utils import AXES_YX, create_zarr_array

NUM_MULTISCALES = 10
NUM_SINGLESCALES = 5


def main():
    EXAMPLE_DIR = BASE_PATH / Path(__file__).with_suffix("").name
    EXAMPLE_DIR.mkdir(parents=True, exist_ok=True)

    coord_sys_id = get_uuid("coord-system")
    collection_id = get_uuid("collection")
    multiscales_refs = []
    for ind_multiscale in range(NUM_MULTISCALES):
        rel_path_multiscale = f"image-{ind_multiscale:02d}"
        multiscale_id = get_uuid(f"multiscale-{ind_multiscale}")
        arrays = []
        for ind_singlescale in range(NUM_SINGLESCALES):
            arrays.append(
                ngc.MultiscaleArray(
                    path=ngc.ZarrPath(href=f".{rel_path_multiscale}/s{ind_singlescale}"),
                    downsamplingTransformations=(
                        None
                        if ind_singlescale == 0
                        else [
                            ngc.ScaleDownsampling(
                                scale=[2**ind_singlescale, 2**ind_singlescale]
                            )
                        ]
                    ),
                )
            )
            

        multiscale_node = ngc.new_multiscale(
            id=multiscale_id,
            name=f"Multiscale {ind_multiscale}",
            coordinate_systems=[
                ngc.CoordinateSystem(id=coord_sys_id, name="physical", axes=AXES_YX)
            ],
            coordinate_transformations=[
                ngc.ScaleTransformation(
                    scale=[0.1, 0.1],
                    input=ngc.ReferenceObj(type="multiscale", ref=multiscale_id),
                    output=ngc.ReferenceObj(type="coordinate_system", ref=coord_sys_id),
                )
            ],
            arrays=arrays,
        )

        multiscale_link = ngc.create(
            str(EXAMPLE_DIR / rel_path_multiscale / "zarr.json"),
            multiscale_node,
        )
        multiscales_refs.append(multiscale_link)
        for ind_singlescale in range(NUM_SINGLESCALES):
            create_zarr_array(
                EXAMPLE_DIR / rel_path_multiscale / f"s{ind_singlescale}",
                seed=(ind_multiscale * 100 + ind_singlescale),
            )

    collection = ngc.new_collection(
        id=collection_id,
        name="My Collection",
        traits=[],
    ).add_external(*multiscales_refs)

    url = str(EXAMPLE_DIR / "zarr.json")
    ngc.create(url, collection, overwrite=True)


if __name__ == "__main__":
    main()
