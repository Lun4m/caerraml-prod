import subprocess

from .cli import Action, Args
from .pre import PreProcessor
from .run import run_inference


def load_modules():
    subprocess.run(["module", "purge"], check=True)
    subprocess.run(["module", "load", "uv"], check=True)
    subprocess.run(["module", "load", "cuda/12.8"], check=True)
    subprocess.run(["module", "load", "ecmwf-toolbox"], check=True)
    subprocess.run(["module", "load", "python3/3.12.11"], check=True)


def main():
    args = Args.parse()

    load_modules()

    match args.action:
        case Action.PREPARE:
            processor = PreProcessor()
            processor.prepare_datasets(args)

        case Action.RUN:
            run_inference(args)


if __name__ == "__main__":
    main()
