"""SageMaker script to train and deploy UMAP."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from umap import UMAP


def model_fn(model_dir: str) -> UMAP:
    """Load the model."""
    model = joblib.load(Path(model_dir) / 'model.joblib')
    return model


def predict_fn(input_data: np.typing.ArrayLike, model: UMAP) -> np.typing.ArrayLike:
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
    umap_data = pd.read_csv(args.train + '/train.csv')

    # Fit and Save model
    umap_model = UMAP().fit(umap_data)
    joblib.dump(umap_model, Path(args.sm_model_dir) / 'model.joblib')
