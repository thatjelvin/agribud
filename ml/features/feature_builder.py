def build_features(snapshot: dict, farm: dict) -> dict:
    return {
        'vegetation_health_score': snapshot.get('vegetation_health_score', 55.0),
        'rainfall_mm': snapshot.get('rainfall_mm', 30.0),
        'temperature_c': snapshot.get('temperature_c', 30.0),
        'farm_size_ha': farm.get('farm_size_ha', 1.0),
        'crop_type': farm.get('crop_type', 'unknown'),
    }
