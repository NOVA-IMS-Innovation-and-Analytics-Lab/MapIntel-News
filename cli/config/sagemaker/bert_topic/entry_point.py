"""SageMaker script to train and deploy UMAP."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from bertopic import BERTopic
from bertopic.representation import KeyBERTInspired


def model_fn(model_dir: str) -> BERTopic:
    """Load the model."""
    model = joblib.load(Path(model_dir) / 'model.joblib')
    return model


def predict_fn(input_data: np.typing.ArrayLike, model: BERTopic) -> np.typing.ArrayLike:
    """Use the model to predict."""
    return model.transform(input_data)


if __name__ == "__main__":
    # Parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--sm-model-dir", type=str, default=os.environ.get('SM_MODEL_DIR'))
    parser.add_argument("--model_dir", type=str)
    parser.add_argument("--train", type=str, default=os.environ.get('SM_CHANNEL_TRAIN'))
    args, _ = parser.parse_known_args()

    # Read in data
    bert_topic_data = pd.read_csv(args.train + "/train.csv").to_numpy().reshape(-1)

    # Fit and Save model
    bert_topic_model = BERTopic(representation_model=KeyBERTInspired()).fit(bert_topic_data)
    joblib.dump(bert_topic_model, Path(args.sm_model_dir) / 'model.joblib')
