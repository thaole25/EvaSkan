import torch
import numpy as np
from pathlib import Path
import random

# ============================================================================
# MODEL AND ALGORITHM CONFIGURATION
# ============================================================================

ALGO = "ICE"
MODEL = "resnext50"
NO_CONCEPTS = 7
SEED = 445
REDUCER = "NMF"
FEATURE_TYPE = "mean"
ICE_CLF= "gnb"
WOE_CLF= "original"
IS_TRAIN_CLF = True

# ============================================================================
# DEVICE CONFIGURATION
# ============================================================================

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# ============================================================================
# IMAGE PREPROCESSING
# ============================================================================

INPUT_RESIZE = 224
INPUT_MEAN = [0.76303977, 0.5456458, 0.57004434]
INPUT_STD = [0.14092788, 0.1526127, 0.1699702]

# ============================================================================
# MODEL LAYERS
# ============================================================================

ICE_CONCEPT_LAYER = {
    "resnet50": "layer4",
    "resnet152": "layer4",
    "resnext50": "layer4",
}

PCBM_CONCEPT_LAYER = {
    "resnet50": "backbone.features.7",
    "resnet152": "backbone.features.7",
    "resnext50": "backbone.features.7",
}

# ============================================================================
# PATHS
# ============================================================================

PROJECT_ROOT = Path(__file__).parent.resolve()
SAVE_FOLDER = PROJECT_ROOT / "save_model"
DATA_PATH = Path("../datasets/HAM10000")
EXP_PATH = Path("ExplainersLight")
EXAMPLE_PATH = Path("Example_Image")
RESULT_PATH = Path("results")

# ============================================================================
# LABELS AND FEATURES
# ============================================================================

DXLABELS = ["AKIEC", "BCC", "BKL", "DF", "MEL", "NV", "VASC"]
LABEL_FULLNAMES = [
    "Actinic keratoses/intraepithelial carcinoma",
    "Basal cell carcinoma",
    "Benign keratosis-like lesions",
    "Dermatofibroma",
    "Melanoma",
    "Melanocytic nevi",
    "Vascular lesions",
]

FEATURE_ID_TO_LABEL = {
    0: "Reddish\n Structures",
    1: "Medium Irregular\n Pigmentation",
    2: "Irregular\n Dots and Globules",
    3: "Whitish Veils",
    4: "Light Irregular\n Pigmentation",
    5: "Dark Irregular\n Pigmentation",
    6: "Lines (Hair)",
}

LESION_TYPE_DICT = {
    "akiec": "Actinic keratoses and intraepithelial carcinoma",
    "bcc": "basal cell carcinoma",
    "bkl": "benign keratosis-like lesions",
    "df": "dermatofibroma",
    "mel": "melanoma",
    "nv": "melanocytic nevi",
    "vasc": "vascular lesions",
}

# ============================================================================
# TRAINING CONFIGURATION
# ============================================================================

BATCH_SIZE = 128
NUM_WORKERS = 8 if torch.cuda.is_available() else 0
NUM_TEST_PER_CLASS = 20
NUM_VAL_PER_CLASS = 20
NUM_SAMPLES_TRAIN_EACH_CLASS = 1000

# ============================================================================
# VISUALIZATION AND PROCESSING
# ============================================================================

FONT_SIZE = 70
DPI = 500
CALC_LIMIT = 1e9
SLEEP_TIME_PARALLEL = 0

# ============================================================================
# WEIGHT OF EVIDENCE THRESHOLDS
# ============================================================================

WOE_THRESHOLDS = {
    "Neutral": 1.15,
    "Substantial": 2.3,
    "Strong": 4.61,
    "Decisive": np.inf,
}


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def set_seed(seed):
    torch.manual_seed(seed)
    torch.cuda.manual_seed(seed)
    np.random.seed(seed)
    random.seed(seed)
    torch.backends.cudnn.deterministic = True
