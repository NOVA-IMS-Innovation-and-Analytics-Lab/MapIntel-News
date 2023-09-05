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
from haystack.document_stores import OpenSearchDocumentStore
from haystack.nodes import EmbeddingRetriever
from sagemaker.jumpstart.model import JumpStartModel
from sagemaker.session import Session
from sagemaker.sklearn import SKLearn
from umap import UMAP
from utils import create_document_store, get_db_status_code

warnings.filterwarnings('ignore')


@click.group()
def models() -> None:
    """Interact with the models."""
    return


@models.command()
def show() -> None:
    """Show the status of the models."""
    sm_client = boto3.client('sagemaker')
    tags_models = []
    for info in sm_client.list_endpoints()['Endpoints']:
        tags = sm_client.list_tags(ResourceArn=info['EndpointArn'])['Tags']
        for tag in tags:
            if tag['Key'] == 'Model':
                tags_models.append(tag['Value'])
    if set(tags_models) != {'Generator', 'Dimensionality Reductioner', 'Topic Model'}:
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
    document_store = create_document_store(os_client, password)
    documents = document_store.get_all_documents()

    # Deploy generator model
    model_id = 'huggingface-llm-falcon-7b-instruct-bf16'
    JumpStartModel(model_id=model_id, role='SageMakerRole').deploy(tags=[{'Key': 'Model', 'Value': 'Generator'}])

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
        **AWS_CONFIG['sagemaker'],
    )
    umap_model.fit({'train': umap_data_path})
    umap_model.deploy(
        instance_type=AWS_CONFIG['sagemaker']['instance_type'],
        initial_instance_count=1,
        tags=[{'Key': 'Model', 'Value': 'Dimensionality Reductioner'}],
    )

    # Train and deploy topic model
    contents = [document.content for document in documents]
    contents_path = Path(mkdtemp()) / 'train.csv'
    pd.DataFrame(contents).to_csv(contents_path, index=False)
    bert_topic_data_path = sagemaker_session.upload_data(
        path=contents_path,
        bucket='mapintel-news',
        key_prefix='bert_topic_data',
    )
    bert_topic_model = SKLearn(
        entry_point='entry_point.py',
        script_mode=True,
        source_dir=str(Path(__file__).parent / 'config' / 'sagemaker' / 'bert_topic'),
        py_version='py3',
        **AWS_CONFIG['sagemaker'],
    )
    bert_topic_model.fit({'train': bert_topic_data_path})
    bert_topic_model.deploy(
        instance_type=AWS_CONFIG['sagemaker']['instance_type'],
        initial_instance_count=1,
        tags=[{'Key': 'Model', 'Value': 'Topic Model'}],
    )


@models.command()
def write() -> None:
    """Write the models predictions to the database."""
    password = click.prompt('Password', hide_input=True)
    os_client = boto3.client('opensearch')
    document_store = OpenSearchDocumentStore(
        host=os_client.describe_domain(DomainName=AWS_CONFIG['opensearch']['domain'])['DomainStatus']['Endpoint'],
        port=AWS_CONFIG['opensearch']['port'],
        username='admin',
        password=password,
        embedding_dim=HAYSTACK_CONFIG['retriever']['dim'],
    )
    retriever = EmbeddingRetriever(HAYSTACK_CONFIG['retriever']['model'], document_store)
    document_store.update_embeddings(retriever)
    documents = document_store.get_all_documents(return_embedding=True)
    umap = UMAP()
    embeddings2d = umap.fit_transform([document.embedding for document in documents])
    for document, embedding2d in zip(documents, embeddings2d, strict=True):
        document.meta['embedding2d'] = embedding2d
    document_store.write_documents(documents)
