# ML Service Structure

This module is organized for extensible training and inference:

- `models/`: model classes and registries
- `features/`: feature engineering
- `pipelines/`: training and batch workflows
- `inference/`: real-time and batch inference entrypoints
- `training/`: training jobs and experiment configs

Current MVP uses a lightweight statistical baseline while preserving contracts for future CNN/LSTM integration.
