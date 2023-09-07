"""Configuration parameters."""

from pathlib import Path
from typing import Any

AWS_CONFIG: dict[str, Any] = {
    's3': {
        'bucket': 'mapintel-news',
        'key': 'data.json',
    },
    'cloudformation': {
        'stack_name': 'mapintel-news-stack',
        'template_path': str(Path(__file__).parent / 'cloudformation' / 'opensearch-index.yaml'),
    },
    'opensearch': {
        'port': 443,
        'domain': 'mapintel-news-domain',
        'username': 'admin',
        'instance_type': 't3.small.search',
        'instance_count': '3',
    },
    'sagemaker': {
        'role': 'SageMakerRole',
        'dimensionality_reductioner': {
            'training': {'instance_type': 'ml.m5.large'},
            'inference': {'instance_type': 'ml.t2.medium'},
            'framework_version': '1.2-1',
        },
        'generator': {'model_id': 'huggingface-llm-falcon-7b-instruct-bf16'},
    },
}
HAYSTACK_CONFIG: dict[str, dict[str, str | int]] = {
    'retriever': {
        'dim': 384,
        'model': 'sentence-transformers/all-MiniLM-L12-v2',
    },
}
SAMPLE_SIZE: int = 10000
