import subprocess

from .cli import Action, Args
from .pre import PreProcessor
from .run import run_inference


# TODO: not sure if this is needed
def load_modules():
    subprocess.run(["module", "purge"], check=True)

    modules = ("uv", "cuda/12.8", "ecmwf-toolbox", "python3/3.12.11")
    for module in modules:
        subprocess.run(["module", "load", module], check=True)


def main():
    args = Args.parse()

    match args.action:
        case Action.PREPARE:
            processor = PreProcessor()
            processor.prepare_datasets(args)

        case Action.RUN:
            run_inference(args)


if __name__ == "__main__":
    main()
