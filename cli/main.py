"""CLI to interact with the OpenSearch database and SageMaker models."""

# Author: Georgios Douzas <gdouzas@icloud.com>
# License: MIT

import warnings

import click
from database import database
from models import models

warnings.filterwarnings('ignore')


@click.group()
def main() -> None:
    """Interact with the database and models."""
    return


main.add_command(database)
main.add_command(models)


if __name__ == '__main__':
    main()
