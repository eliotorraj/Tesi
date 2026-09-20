"""Limiti operativi richiesti per le prove; non sono specifiche del produttore."""
DEFAULT_BATCH = 512
DEFAULT_MICRO_BATCH = 128
DEFAULT_GUARDS = {
    "minimum_available_bytes": 1610612736,
    "memory_consecutive_samples": 3,
    "maximum_edge_c": 95,
    "maximum_hotspot_c": 108,
    "pause_hotspot_c": 105,
    "resume_hotspot_c": 100,
    "missing_sensor_consecutive_samples": 3,
    "thresholds_are": "User-requested experimental operating limits, not vendor specifications or a diagnosis",
}
GUARD_FLAGS = {
    "minimum_available_bytes": "-MinimumAvailableBytes",
    "maximum_edge_c": "-MaximumEdgeC",
    "maximum_hotspot_c": "-MaximumHotspotC",
    "pause_hotspot_c": "-PauseHotspotC",
    "resume_hotspot_c": "-ResumeHotspotC",
}

def server_arguments(profile):
    """Usa i valori del profilo, anche dopo il congelamento della validation."""
    batch, micro = profile["batch"], profile["micro_batch"]
    if not 0 < micro <= batch:
        raise ValueError("Require 0 < micro_batch <= batch")
    guards = profile["guards"]
    if not 0 < guards["resume_hotspot_c"] < guards["pause_hotspot_c"] < guards["maximum_hotspot_c"] <= 110:
        raise ValueError("Require 0 < resume < pause < maximum hotspot <= 110 C")
    if not 0 < guards["maximum_edge_c"] <= 95 or guards["minimum_available_bytes"] <= 0:
        raise ValueError("Invalid edge or available RAM limit")
    if guards["memory_consecutive_samples"] != 3 or guards["missing_sensor_consecutive_samples"] != 3:
        raise ValueError("Monitor requires three consecutive memory/missing-sensor samples")
    result = ["-Context", profile["context"], "-CacheType", profile["cache_type"],
              "-GpuLayers", profile["gpu_layers"], "-Batch", batch, "-MicroBatch", micro]
    for key, flag in GUARD_FLAGS.items():
        result.extend([flag, guards[key]])
    return list(map(str, result))
