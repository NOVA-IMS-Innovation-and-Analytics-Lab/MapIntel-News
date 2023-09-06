"""Utilities for CLI."""

# Author: Georgios Douzas <gdouzas@icloud.com>
# License: MIT

import os

import click
from config.params import AWS_CONFIG, HAYSTACK_CONFIG
from haystack.document_stores import OpenSearchDocumentStore
from mypy_boto3_opensearch.client import OpenSearchServiceClient


def create_document_store(os_client: OpenSearchServiceClient, password: str) -> OpenSearchDocumentStore:
    """Create an OpenSearch document store."""
    endpoint = os_client.describe_domain(DomainName=AWS_CONFIG['opensearch']['domain'])['DomainStatus']['Endpoint']
    return OpenSearchDocumentStore(
        host=endpoint,
        port=AWS_CONFIG['opensearch']['port'],
        username=AWS_CONFIG['opensearch']['username'],
        password=password,
        embedding_dim=HAYSTACK_CONFIG['retriever']['dim'],
    )


def db_created(os_client: OpenSearchServiceClient) -> bool:
    """Check if database is created."""
    domain_names = os_client.list_domain_names()['DomainNames']
    return AWS_CONFIG['opensearch']['domain'] in [info['DomainName'] for info in domain_names]


def db_processing(os_client: OpenSearchServiceClient) -> bool:
    """Check if database is processing."""
    domain_status = os_client.describe_domain(DomainName=AWS_CONFIG['opensearch']['domain'])['DomainStatus']
    return (domain_status['Created'] or domain_status['Deleted']) and domain_status['Processing']


def db_empty(os_client: OpenSearchServiceClient, password: str) -> bool:
    """Check if database is empty."""
    document_store = create_document_store(os_client, password)
    return not document_store.get_all_documents()


def db_ready(os_client: OpenSearchServiceClient, password: str) -> bool:
    """Check if database is ready."""
    document_store = create_document_store(os_client, password)
    documents = document_store.get_all_documents(return_embedding=True)
    return all(
        document.embedding is not None
        and document.meta.get('embedding2d') is not None
        and document.meta.get('topic') is not None
        for document in documents
    )


def get_db_status_code(os_client: OpenSearchServiceClient) -> tuple[int, str]:
    """Get the status code of the database."""
    if not db_created(os_client):
        return 0, ''
    elif db_processing(os_client):
        return 1, ''
    password = os.environ.get('OPENSEARCH_PASSWORD')
    if password is None:
        password = click.prompt('OpenSearch password', hide_input=True)
    if db_empty(os_client, password):
        return 2, password
    elif not db_ready(os_client, password):
        return 3, password
    return 4, password
