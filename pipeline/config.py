"""Versioned deterministic analytics policy for the first live CSV run."""

RULES_VERSION = "v0"
LOUVAIN_SEED = 42
LOUVAIN_RESOLUTION = 1

ROLE_ORDER = ("consolidator", "distributor", "transit", "terminal", "coordinator")
ROLE_SUPPORT = {
    "consolidator": 0.85,
    "distributor": 0.85,
    "transit": 0.60,
    "terminal": 0.50,
    "coordinator": 0.55,
}
SINGLE_TX_CAP = 0.40
PERIPHERAL_SCORE = 0.15
ISOLATE_SCORE = 0.05
MIXED_ROLE_DELTA = 0.10

CONSOLIDATOR_MIN_IN_DEGREE = 3
DISTRIBUTOR_MIN_OUT_DEGREE = 10
TRANSIT_MIN_TX = 2
TRANSIT_RATIO_MIN = 0.8
TRANSIT_RATIO_MAX = 1.2
TERMINAL_RATIO_MAX = 0.1
TERMINAL_MIN_IN_DATES = 2
TERMINAL_LAST_IN_DAY_MAX = 29
COORDINATOR_MIN_SEED_REACH = 2
COORDINATOR_BETWEENNESS_QUANTILE = 0.9
COORDINATOR_MIN_CROSS_CLUSTER_VOLUME = 0.2

PRIORITY_WEIGHTS = {
    "direct_seed_senders": 0.175,
    "seed_reach_4": 0.175,
    "in_degree": 0.25,
    "flow_volume": 0.20,
    "betweenness": 0.10,
    "out_degree": 0.10,
}
