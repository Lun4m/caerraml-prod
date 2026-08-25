import hashlib
import json
import os
import subprocess
from pathlib import Path

from .cli import Args, Domain

DEFAULT_NAMESPACE = "production-v1"
DEFAULT_ALGORITHM = "sha256"


def sample_seed(
    date: str,
    member: int,
    domain: Domain,
    namespace: str = DEFAULT_NAMESPACE,
    algorithm: str = DEFAULT_ALGORITHM,
) -> int:
    """Derive a stable seed.

    The default identity deliberately excludes run ID, checkpoint, schedule,
    chunk end and task kind. This keeps reruns and model/config comparisons
    paired while giving each domain/date/member initialization fresh noise.
    """
    identity = {
        "algorithm": algorithm,
        "domain": domain,
        "member": str(member),
        "namespace": namespace,
        "timestamp": date,
    }

    encoded = json.dumps(identity, sort_keys=True, separators=(",", ":")).encode()
    seed = int.from_bytes(hashlib.sha256(encoded).digest()[:8], "big")
    seed &= (1 << 63) - 1
    # stay positive and above small seeds
    return seed | (1 << 62)


def run_inference(args: Args):
    os.environ["ANEMOI_START"] = args.start
    os.environ["ANEMOI_END"] = args.end
    os.environ["N_MEMBERS"] = str(args.members)

    namespace = os.environ.get("CAERRA_NAMESPACE", DEFAULT_NAMESPACE)

    recipes = Path.cwd() / "recipes"
    base_conf = recipes / "inference.yaml"
    post_proc = recipes / "defaults/post_processors.yaml"
    var_conf = recipes / "defaults/typed_variables.yaml"

    # NOTE: these are run sequentially, but could be parallelized
    for domain in Domain:
        run_conf = recipes / f"defaults/{domain}.yaml"

        for member in range(args.members):
            seed = sample_seed(args.start, member, domain, namespace=namespace)

            env = os.environ.copy()
            env["CAERRA_REGION"] = domain
            env["ANEMOI_BASE_SEED"] = str(seed)
            env["PERTURBATION_NUM"] = str(member)

            subprocess.run(
                f"uv run --frozen \
                    anemoi-inference run {base_conf} \
                    --defaults {run_conf} \
                    --defaults {var_conf} \
                    --defaults {post_proc}",
                check=True,
                shell=True,
                env=env,
            )
