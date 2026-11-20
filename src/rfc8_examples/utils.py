import hashlib
import json
import random
import uuid
from pathlib import Path

import ngio_collections as ngc
import numpy as np
import zarr

_RND = random.Random()
_RND.seed(1234567)


AXES_YX = [
    ngc.Axis(name="y", type="space", unit="micrometer"),
    ngc.Axis(name="x", type="space", unit="micrometer"),
]

def get_uuid(source: str | bytes | dict | None = None) -> str:
    if source is None:
        kwargs = {"int": _RND.getrandbits(128)}
    elif isinstance(source, bytes):
        kwargs = {"hex": hashlib.shake_128(source).hexdigest(16)}
    elif isinstance(source, str):
        kwargs = {
            "hex": hashlib.shake_128(bytes(source, encoding="utf-8")).hexdigest(16)
        }
    elif isinstance(source, dict):
        kwargs = {
            "hex": hashlib.shake_128(
                bytes(json.dumps(source), encoding="utf-8")
            ).hexdigest(16)
        }
    else:
        raise NotImplementedError(f"{type(source)=} is not supported")
    return str(uuid.UUID(**kwargs))


def create_zarr_array(path: str | Path, seed: int = 1234567) -> None:
    np.random.seed(seed=seed)
    z = zarr.create_array(
        store=path,
        shape=(100, 100),
        chunks=(100, 100),
        dtype="f4",
        overwrite=True,
        dimension_names=["y", "x"]
    )
    z[:, :] = np.random.random((100, 100))
