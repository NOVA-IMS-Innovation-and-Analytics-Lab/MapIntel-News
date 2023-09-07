"""Module that contains the models functionality of the CLI."""

# Author: Georgios Douzas <gdouzas@icloud.com>
# License: MIT

import warnings
from pathlib import Path
from tempfile import mkdtemp

import boto3
import click
import pandas as pd
from config.params import AWS_CONFIG, HAYSTACK_CONFIG
from haystack.nodes import EmbeddingRetriever
from sagemaker.jumpstart.model import JumpStartModel
from sagemaker.session import Session
from sagemaker.sklearn import SKLearn, SKLearnPredictor
from utils import create_document_store, get_db_status_code

warnings.filterwarnings('ignore')


@click.group()
def models() -> None:
    """Interact with the models."""
    return


@models.command()
def describe() -> None:
    """Describe the status of the models."""
    sm_client = boto3.client('sagemaker')
    tags_models = []
    for info in sm_client.list_endpoints()['Endpoints']:
        tags = sm_client.list_tags(ResourceArn=info['EndpointArn'])['Tags']
        for tag in tags:
            if tag['Key'] == 'Model':
                tags_models.append(tag['Value'])
    if set(tags_models) != {'Generator', 'Dimensionality Reductioner'}:
        click.echo('Models status: Not created.')
        return
    click.echo('Models status: Ready.')


@models.command()
def delete() -> None:
    """Delete the models."""
    sm_client = boto3.client('sagemaker')
    for info in sm_client.list_endpoints()['Endpoints']:
        sm_client.delete_endpoint(EndpointName=info['EndpointName'])
    for info in sm_client.list_endpoint_configs()['EndpointConfigs']:
        sm_client.delete_endpoint_config(EndpointConfigName=info['EndpointConfigName'])


@models.command()
def create() -> None:
    """Create the models on S3."""

    sagemaker_session = Session()

    # Get documents
    missing_predictions_status_code = 3
    os_client = boto3.client('opensearch')
    status_code, password = get_db_status_code(os_client)
    if status_code != missing_predictions_status_code:
        click.echo('Models can not be created. Check the status of the database.')
        return
    document_store = create_document_store(os_client, password)
    documents = document_store.get_all_documents()

    # Deploy generator model
    JumpStartModel(model_id=AWS_CONFIG['sagemaker']['generator']['model_id'], role='SageMakerRole').deploy(
        tags=[{'Key': 'Model', 'Value': 'Generator'}],
    )

    # Train and deploy dimensionality reduction model
    retriever = EmbeddingRetriever(HAYSTACK_CONFIG['retriever']['model'], document_store)
    embeddings = retriever.embed_documents(documents)
    embeddings_path = Path(mkdtemp()) / 'train.csv'
    pd.DataFrame(embeddings).to_csv(embeddings_path, index=False)
    umap_data_path = sagemaker_session.upload_data(path=embeddings_path, bucket='mapintel-news', key_prefix='umap_data')
    umap_model = SKLearn(
        entry_point='entry_point.py',
        script_mode=True,
        source_dir=str(Path(__file__).parent / 'config' / 'sagemaker' / 'umap'),
        py_version='py3',
        role=AWS_CONFIG['sagemaker']['role'],
        instance_type=AWS_CONFIG['sagemaker']['dimensionality_reductioner']['training']['instance_type'],
        framework_version=AWS_CONFIG['sagemaker']['dimensionality_reductioner']['framework_version'],
    )
    umap_model.fit({'train': umap_data_path})
    umap_model.deploy(
        instance_type=AWS_CONFIG['sagemaker']['dimensionality_reductioner']['inference']['instance_type'],
        initial_instance_count=1,
        tags=[{'Key': 'Model', 'Value': 'Dimensionality Reductioner'}],
    )


@models.command()
def write() -> None:
    """Write the models predictions to the database."""

    sm_client = boto3.client('sagemaker')

    # Get document store
    missing_predictions_status_code = 3
    os_client = boto3.client('opensearch')
    status_code, password = get_db_status_code(os_client)
    if status_code < missing_predictions_status_code:
        click.echo('Models predictions can not be written to the database. Check the status of the database.')
        return
    document_store = create_document_store(os_client, password)

    # Check models
    tags_models = []
    for info in sm_client.list_endpoints()['Endpoints']:
        tags = sm_client.list_tags(ResourceArn=info['EndpointArn'])['Tags']
        for tag in tags:
            if tag['Key'] == 'Model':
                tags_models.append(tag['Value'])
    if 'Dimensionality Reductioner' not in tags_models:
        click.echo('Models predictions can not be written to the database. Dimensionality reductioner is missing.')
        return

    # Write embeddings
    retriever = EmbeddingRetriever(HAYSTACK_CONFIG['retriever']['model'], document_store)
    document_store.update_embeddings(retriever)

    # Write 2D embeddings
    documents = document_store.get_all_documents(return_embedding=True)
    for info in sm_client.list_endpoints()['Endpoints']:
        tags = sm_client.list_tags(ResourceArn=info['EndpointArn'])['Tags']
        if {'Key': 'Model', 'Value': 'Dimensionality Reductioner'} in tags:
            break
    embeddings2d = SKLearnPredictor(info['EndpointName']).predict([document.embedding for document in documents])
    for document, embedding2d in zip(documents, embeddings2d, strict=True):
        document.meta['embedding2d'] = embedding2d
    document_store.write_documents(documents)
