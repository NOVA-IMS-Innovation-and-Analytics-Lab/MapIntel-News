"""Module that contains the database functionality of the CLI."""

# Author: Georgios Douzas <gdouzas@icloud.com>
# License: MIT

import warnings
from json import load
from pathlib import Path
from random import sample
from tempfile import NamedTemporaryFile
from typing import cast

import boto3
import botocore
import click
from config.params import AWS_CONFIG, SAMPLE_SIZE
from haystack import Document
from utils import create_document_store, get_db_status_code

warnings.filterwarnings('ignore')


@click.group()
def database() -> None:
    """Interact with the database."""
    return


@database.command()
def describe() -> None:
    """Describe the status of the database."""
    os_client = boto3.client('opensearch')
    status_code, _ = get_db_status_code(os_client)
    msg_mapping = {
        0: 'Not created',
        1: 'Created but is processing',
        2: 'Created but empty',
        3: 'Created, populated with documents but predictions missing',
        4: 'Ready',
    }
    click.echo(f'Database status: {msg_mapping[status_code]}.')


@database.command()
def delete() -> None:
    """Delete the database."""
    cf_client = boto3.client('cloudformation')
    cf_client.delete_stack(StackName=AWS_CONFIG['cloudformation']['stack_name'])


@database.command()
def create() -> None:
    """Create a database."""
    password = click.prompt('Password', hide_input=True)
    cf_client = boto3.client('cloudformation')
    parameters = [
        {'ParameterKey': 'InstanceType', 'ParameterValue': AWS_CONFIG['opensearch']['instance_type']},
        {'ParameterKey': 'InstanceCount', 'ParameterValue': AWS_CONFIG['opensearch']['instance_count']},
        {'ParameterKey': 'OSPassword', 'ParameterValue': password},
    ]
    with Path.open(AWS_CONFIG['cloudformation']['template_path']) as file:
        try:
            cf_client.create_stack(
                StackName=AWS_CONFIG['cloudformation']['stack_name'],
                TemplateBody=file.read(),
                Parameters=parameters,
            )
        except botocore.errorfactory.ClientError as error:
            click.echo(error)


@database.command()
def write() -> None:
    """Write the documents to the database."""
    empty_status_code = 2
    os_client = boto3.client('opensearch')
    status_code, password = get_db_status_code(os_client)
    msg_mapping = {
        0: 'Database has not been created.',
        1: 'Database is created but is processing. Try again when processing is finished.',
        3: 'Database is not empty. No documents were written.',
        4: 'Database is not empty. No documents were written.',
    }
    if status_code != empty_status_code:
        click.echo(msg_mapping[status_code])
        return
    s3_client = boto3.client('s3')
    with NamedTemporaryFile('wb') as temp_file:
        s3_client.download_fileobj(cast(str, AWS_CONFIG['s3']['bucket']), cast(str, AWS_CONFIG['s3']['key']), temp_file)
        with Path.open(Path(temp_file.name), mode='rb') as data_file:
            documents = [Document(**data) for data in sample(load(data_file), SAMPLE_SIZE)]
    document_store = create_document_store(os_client, password)
    document_store.write_documents(documents)
