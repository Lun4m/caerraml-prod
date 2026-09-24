import hashlib
import json
import os
import subprocess
from collections.abc import Iterable

import click
from caerra_prep import Date, Domain, common_cli_params, get_recipes_path
from click_extra import EnumChoice

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
    # stay positive and above small seeds
    return seed | (1 << 62)


def run_inference(
    n_members: int,
    domains: Iterable[Domain] | None,
    members: list[int] | None,
    date: Date,
):
    domains = set(domains) if domains is not None else set(Domain)
    members = members if members is not None else list(range(n_members))

    os.environ["CAERRA_DATE"] = date.str
    os.environ["N_MEMBERS"] = str(n_members)

    namespace = os.environ.get("CAERRA_NAMESPACE", DEFAULT_NAMESPACE)
    print("Using namespace:", namespace, flush=True)

    # recipes dir lives in the root of the repo
    recipes = get_recipes_path(__file__, "../../recipes")
    base_conf = recipes / "inference.yaml"
    post_proc = recipes / "defaults/post_processors.yaml"
    var_conf = recipes / "defaults/typed_variables.yaml"

    # NOTE: these are run sequentially, but could be parallelized
    for domain in domains:
        run_conf = recipes / f"defaults/{domain}.yaml"

        for member in members:
            seed = sample_seed(date.start, member, domain, namespace=namespace)

            env = os.environ.copy()
            env["CAERRA_REGION"] = domain
            env["ANEMOI_BASE_SEED"] = str(seed)
            env["PERTURBATION_NUM"] = str(member)
            env["GRIB_OUTNAME"] = f"{date.str}/{domain}_m{member:02}"

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


@click.command(context_settings={"show_default": True})
@click.option(
    "--n_members",
    type=int,
    default=N_MEMBERS,
    help="Number of members",
)
@click.option(
    "--domains",
    multiple=True,
    type=EnumChoice(Domain),
    default=None,
    help="Only operate on the given domains [default: all]",
)
@click.option(
    "-m",
    "--members",
    multiple=True,
    type=int,
    default=None,
    help="Only generate the given members. Can be specified multiple times. [default: all]",
)
@common_cli_params
def cli(*args, **kwargs):
    run_inference(*args, **kwargs)
