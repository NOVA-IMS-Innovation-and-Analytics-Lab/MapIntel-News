"""Configuration parameters."""

from pathlib import Path

AWS_CONFIG: dict[str, dict[str, str | int]] = {
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
        'instance_type': 'r5.large.search',
        'instance_count': '3',
    },
    'sagemaker': {
        'role': 'SageMakerRole',
        'instance_type': 'ml.c5.xlarge',
        'framework_version': '1.2-1',
        'generator': 'huggingface-llm-falcon-7b-instruct-bf16',
    },
}
HAYSTACK_CONFIG: dict[str, dict[str, str | int]] = {
    'retriever': {
        'dim': 384,
        'model': 'sentence-transformers/all-MiniLM-L12-v2',
    },
}
SAMPLE_SIZE: int = 1000
