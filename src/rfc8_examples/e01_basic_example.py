from pathlib import Path

import ngio_collections as ngc

from rfc8_examples import BASE_PATH, get_uuid
from rfc8_examples.utils import create_zarr_array

EXAMPLE_DIR = BASE_PATH / Path(__file__).with_suffix("").name


def main():

    coord_sys_id = get_uuid("coord-sys-id")
    multiscale_id = get_uuid("multiscale")
    collection_id = get_uuid("collection")
    axes_czyx = [
        ngc.Axis(name="y", type="space", unit="micrometer"),
        ngc.Axis(name="x", type="space", unit="micrometer"),
    ]
    arrays = [
        ngc.MultiscaleArray(
            path=ngc.ZarrPath(href="./s0"),
            downsamplingTransformations=None,
        ),
        ngc.MultiscaleArray(
            path=ngc.ZarrPath(href="./s1"),
            downsamplingTransformations=([ngc.ScaleDownsampling(scale=[2, 2])]),
        ),
    ]
    multiscale = ngc.new_multiscale(
        id=multiscale_id,
        name="My Multiscale",
        coordinate_systems=[
            ngc.CoordinateSystem(id=coord_sys_id, name="physical", axes=axes_czyx)
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

    EXAMPLE_DIR.mkdir(parents=True, exist_ok=True)
    collection = ngc.new_collection(
        id=collection_id, name="My Collection", traits=[]
    ).add(multiscale)

    ngc.create(str(EXAMPLE_DIR / "zarr.json"), collection, overwrite=True)

    create_zarr_array(EXAMPLE_DIR / "0", seed=0)
    create_zarr_array(EXAMPLE_DIR / "1", seed=1)


if __name__ == "__main__":
    main()
