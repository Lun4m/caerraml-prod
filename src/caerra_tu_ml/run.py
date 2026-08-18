import hashlib
import json
import os
import subprocess

from .cli import Args, Domain

DEFAULT_NAMESPACE = "production-v1"
DEFAULT_ALGORITHM = "sha256"
N_MEMBERS = 11


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
    # stay positive and above the runner's small-seed special case
    return seed | (1 << 62)


def run_inference(args: Args):
    # Set start and end date env vars
    os.environ["ANEMOI_START"] = args.start
    os.environ["ANEMOI_END"] = args.end

    # NOTE: these are run sequentially, but could be parallelized
    for domain in Domain:
        for member in range(N_MEMBERS):
            env = os.environ.copy()
            seed = sample_seed(args.start, member, domain)

            env["CAERRA_REGION"] = domain
            env["ANEMOI_BASE_SEED"] = str(seed)
            env["PERTURBATION_NUM"] = str(member)

            # TODO: need shell because uv is not installed system-wide
            res = subprocess.run(
                f"uv run --frozen \
                    anemoi-inference run config.yaml \
                    --defaults defaults/post_processors.yaml \
                    --defaults defaults/{domain}.yaml \
                    --defaults defaults/typed_variables.yaml",
                check=False,
                shell=True,
                env=env,
            )

            if res.returncode != 0:
                print("ERROR: run with the following env failed:")
                print(f"   ANEMOI_START = {args.start}")
                print(f"   ANEMOI_END = {args.end}")
                print(f"   CAERRA_REGION = {domain}")
                print(f"   PERTURBATION_NUM = {member}")
                print(f"   ANEMOI_BASE_SEED = {seed}")

    print(args)
