from datetime import timedelta
import os
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "karma-chain")

ROLE_SEQUENCE = ["learner", "volunteer", "seva", "guru"]

ACTIONS = [
    "completing_lessons",
    "helping_peers",
    "solving_doubts",
    "selfless_service",
    "cheat"
]

INTENT_MAP = {
    "completing_lessons": "learn",
    "helping_peers": "assist",
    "solving_doubts": "assist",
    "selfless_service": "extra_service",
    "cheat": "malicious_or_greedy"
}

# Base rewards for actions
REWARD_MAP = {
    "completing_lessons": {"token": "DharmaPoints", "value": 5},
    "helping_peers": {"token": "SevaPoints", "value": 10},
    "solving_doubts": {"token": "SevaPoints", "value": 8},
    "selfless_service": {"token": "PunyaTokens", "value": 25}
}

# Progressive punishment system for cheating
CHEAT_PUNISHMENT_LEVELS = {
    1: {"token": "DharmaPoints", "value": -2, "name": "first_offense"},
    2: {"token": "DharmaPoints", "value": -5, "name": "second_offense"},
    3: {"token": "DharmaPoints", "value": -10, "name": "third_offense"},
    4: {"token": "DharmaPoints", "value": -20, "name": "fourth_offense"},
    5: {"token": "DharmaPoints", "value": -40, "name": "fifth_offense"},
    "default": {"token": "DharmaPoints", "value": -100, "name": "repeat_offender"}
}

# Number of days after which cheat count resets to zero
CHEAT_PUNISHMENT_RESET_DAYS = 30

TOKEN_ATTRIBUTES = {
    "DharmaPoints": {"expiry_days": 365, "stackable": True, "daily_decay": 0.0},
    "SevaPoints": {"expiry_days": 365, "stackable": True, "daily_decay": 0.0005},
    "PunyaTokens": {"expiry_days": 730, "stackable": True, "daily_decay": 0.0001},
    "PaapTokens": {
        "minor": {"expiry_days": 180, "stackable": True, "daily_decay": 0.0, "multiplier": 1.0},
        "medium": {"expiry_days": 365, "stackable": True, "daily_decay": 0.0, "multiplier": 2.5},
        "maha": {"expiry_days": 730, "stackable": True, "daily_decay": 0.0, "multiplier": 5.0}
    },
    "DridhaKarma": {"weight": 0.8, "expiry_days": 1095, "stackable": True, "daily_decay": 0.00005},
    "AdridhaKarma": {"weight": 0.3, "expiry_days": 365, "stackable": True, "daily_decay": 0.001},
    "SanchitaKarma": {"weight": 1.0, "expiry_days": None, "stackable": True, "daily_decay": 0.0},
    "PrarabdhaKarma": {"weight": 1.0, "expiry_days": None, "stackable": True, "daily_decay": 0.0},
    "Rnanubandhan": {
        "minor": {"expiry_days": 365, "stackable": True, "daily_decay": 0.0, "multiplier": 1.0},
        "medium": {"expiry_days": 730, "stackable": True, "daily_decay": 0.0, "multiplier": 2.0},
        "major": {"expiry_days": 1460, "stackable": True, "daily_decay": 0.0, "multiplier": 4.0}
    }
}

# Paap classification for different actions
PAAP_CLASSES = {
    "cheat": "medium",
    "disrespect_guru": "medium",
    "break_promise": "minor",
    "harm_others": "maha",
    "false_speech": "minor",
    "theft": "medium",
    "violence": "maha"
}

# Mapping from Paap severity to recommended atonements
PRAYASCHITTA_MAP = {
    "minor": {
        "Jap": 108,
        "Tap": 1,
        "Bhakti": 1,
        "Daan": 10
    },
    "medium": {
        "Jap": 1008,
        "Tap": 3,
        "Bhakti": 3,
        "Daan": 50
    },
    "maha": {
        "Jap": 10008,
        "Tap": 7,
        "Bhakti": 7,
        "Daan": 100
    }
}

# Loka thresholds for rebirth assignment
LOKA_THRESHOLDS = {
    "Swarga": {"min_karma": 500, "max_karma": float('inf'), "description": "Heavenly realm of light and bliss"},
    "Mrityuloka": {"min_karma": 0, "max_karma": 499, "description": "Middle realm (human world) of learning and growth"},
    "Antarloka": {"min_karma": -200, "max_karma": -1, "description": "Intermediate realm of reflection and transition"},
    "Naraka": {"min_karma": float('-inf'), "max_karma": -201, "description": "Lower realm of purification through suffering"}
}

# Rewards for completing atonement - add to PaapTokens based on severity
ATONEMENT_REWARDS = {
    "minor": {"token": "PaapTokens.minor", "value": 2},
    "medium": {"token": "PaapTokens.medium", "value": 5},
    "maha": {"token": "PaapTokens.maha", "value": 10}
}

LEVEL_THRESHOLDS = {
    "learner": 0,
    "volunteer": 50,
    "seva": 200,
    "guru": 500
}

# Q-learning hyperparameters
ALPHA = float(os.getenv("ALPHA", "0.15"))
GAMMA = float(os.getenv("GAMMA", "0.9"))
EPSILON = float(os.getenv("EPSILON", "0.2"))

# Configurable karma factors and guidance weights
KARMA_FACTORS = {
    "purushartha_modifiers": {
        "Dharma": 1.2,
        "Artha": 1.0,
        "Kama": 0.8,
        "Moksha": 1.5
    },
    "positive_distribution": {
        "sanchita": 0.5,
        "prarabdha": 0.3,
        "dridha": 0.6,
        "adridha": 0.4
    },
    "negative_distribution": {
        "adridha": 0.7
    },
    "net_weights": {
        "dridha": 0.8,
        "adridha": 0.3
    }
}

CORRECTIVE_GUIDANCE_WEIGHTS = {
    "Seva": 1.2,
    "Meditation": 1.3,
    "Daan": 1.1,
    "Tap": 1.4,
    "Bhakti": 1.25
}
