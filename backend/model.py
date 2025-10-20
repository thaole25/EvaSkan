from pydantic import BaseModel
from typing import List, Dict, Any
import sys
import os

import numpy as np
import torch
from torchvision.transforms import v2

# Add parent directory to path so we can import ice, woe, etc.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import params

# ============================================================================
# MODEL CONFIGURATION AND LOADING
# ============================================================================

INPUT_MEAN = params.INPUT_MEAN
INPUT_STD = params.INPUT_STD

if params.ALGO == "ICE":
    LAYER_NAME = params.ICE_CONCEPT_LAYER[params.MODEL]
elif params.ALGO == "PCBM":
    LAYER_NAME = params.PCBM_CONCEPT_LAYER[params.MODEL]

NORMALIZED_NO_AUGMENTED_TRANS = v2.Compose(
    [
        v2.Resize((params.INPUT_RESIZE, params.INPUT_RESIZE)),
        v2.ToImage(),
        v2.ToDtype(torch.float32, scale=True),
        v2.Normalize(INPUT_MEAN, INPUT_STD),
    ]
)

EXP_PATH = "{}/{}_Exp_{}_ncomp{}_seed{}_{}_{}_clf{}_{}.sav".format(
    params.SAVE_FOLDER,
    params.ALGO,
    params.MODEL,
    params.NO_CONCEPTS,
    params.SEED,
    params.REDUCER,
    params.FEATURE_TYPE,
    params.IS_TRAIN_CLF,
    params.ICE_CLF,
)
WOE_EXPLAINER = "{}/{}_woeexplainer_{}_ncomp{}_seed{}_{}_{}_{}.sav".format(
    params.SAVE_FOLDER,
    params.ALGO,
    params.MODEL,
    params.NO_CONCEPTS,
    params.SEED,
    params.REDUCER,
    params.FEATURE_TYPE,
    params.WOE_CLF,
)
CONCEPT_MODEL = "{}/{}_concept_{}_ncomp{}_seed{}_{}_{}_clf{}_{}.sav".format(
    params.SAVE_FOLDER,
    params.ALGO,
    params.MODEL,
    params.NO_CONCEPTS,
    params.SEED,
    params.REDUCER,
    params.FEATURE_TYPE,
    params.IS_TRAIN_CLF,
    params.ICE_CLF,
)

Exp = torch.load(EXP_PATH, map_location=torch.device(params.DEVICE), weights_only=False)
woeexplainer = torch.load(WOE_EXPLAINER, map_location=torch.device(params.DEVICE), weights_only=False)
concept_model = torch.load(CONCEPT_MODEL, map_location=torch.device(params.DEVICE), weights_only=False)

class FeatureArea(BaseModel):
    feature_id: int
    area_coordinates: Dict[str, Any]


class FeatureResponse(BaseModel):
    features: List[FeatureArea]


def woe_input_image(image):
    original_x = NORMALIZED_NO_AUGMENTED_TRANS(
        image
    ).numpy()  # .to(device=params.DEVICE)
    if Exp is None:
        x = concept_model.get_feature(original_x, layer_name=LAYER_NAME)
    else:
        x = Exp.reducer.transform(
            concept_model.get_feature(original_x, layer_name=LAYER_NAME)
        )
    h = x[0]
    x_feature = x.mean(axis=(1, 2))
    x_feature = np.squeeze(x_feature)
    x_feature = torch.tensor(x_feature).to(device=params.DEVICE)
    return original_x, h, x_feature


def predict_image(image, container_width, container_height):
    feature_areas = []
    if image is not None:
        original_x, original_h, x_feature = woe_input_image(image)
        num_features = x_feature.shape[0]

        for feat_idx in range(num_features):
            _, img_test_feat = Exp.get_feature_area_on_image(
                original_x, original_h, feat_idx
            )
            rows = len(img_test_feat)
            cols = len(img_test_feat[0])
            min_x, min_y = cols, rows
            max_x, max_y = -1, -1
            for y in range(rows):
                for x in range(cols):
                    if img_test_feat[y][x] == 1:
                        min_x = min(min_x, x)
                        max_x = max(max_x, x)
                        min_y = min(min_y, y)
                        max_y = max(max_y, y)

            if max_x == -1 or max_y == -1:
                continue

            min_x = min_x / params.INPUT_RESIZE * container_width
            max_x = max_x / params.INPUT_RESIZE * container_width
            min_y = min_y / params.INPUT_RESIZE * container_height
            max_y = max_y / params.INPUT_RESIZE * container_height

            height = max_y - min_y + 1
            width = max_x - min_x + 1

            feature_areas.append(
                {
                    "feature_id": feat_idx,
                    "feature_name": params.FEATURE_ID_TO_LABEL[feat_idx],
                    "area_coordinates": {
                        "x": min_x,
                        "y": min_y,
                        "width": width,
                        "height": height,
                    },
                }
            )

        hypotheses_woes = []
        probs = []
        for hypothesis_index, hypothesis_name in enumerate(params.DXLABELS):
            explain = woeexplainer.explain_for_human(
                x=x_feature,
                hypothesis=hypothesis_index,
                units="features",
                show_bayes=False,
                plot=False,
            )

            evidence = []
            for i, attwoe in enumerate(explain.attwoes):
                evidence_type = "zero"
                if attwoe < 0:
                    evidence_type = "negative"
                elif attwoe > 0:
                    evidence_type = "positive"

                if 0 <= abs(attwoe) < params.WOE_THRESHOLDS["Neutral"]:
                    soe = "Not worth mentioning"
                elif params.WOE_THRESHOLDS["Neutral"] < abs(attwoe) <= params.WOE_THRESHOLDS["Substantial"]:
                    soe = "Substantial"
                elif params.WOE_THRESHOLDS["Substantial"] < abs(attwoe) <= params.WOE_THRESHOLDS["Strong"]:
                    soe = "Strong"
                elif abs(attwoe) > params.WOE_THRESHOLDS["Strong"]:
                    soe = "Decisive"

                evidence.append(
                    {
                        "feature_id": i,
                        "feature_name": params.FEATURE_ID_TO_LABEL[i],
                        "evidence_type": evidence_type,
                        "soe": soe,
                    }
                )

            posterior_log_odd = (
                explain.total_woe + explain.base_lods
            )  # get posterior log odd
            post_odd = torch.exp(posterior_log_odd).item()  # get posterior odd
            prob = post_odd / (1 + post_odd)
            prob = round(prob, 2)  # convert odd to probability
            probs.append(prob)

            hypotheses_woes.append(
                {
                    "hypothesis_id": hypothesis_index,
                    "hypothesis_name": "{} ({})".format(
                        params.LABEL_FULLNAMES[hypothesis_index], hypothesis_name
                    ),
                    "evidence": evidence,
                    "probability": prob,
                }
            )
        best_class_index = probs.index(max(probs))
        best_class_name = params.LABEL_FULLNAMES[best_class_index]

    result = {
        "recommendation": best_class_name,
        "hypotheses": hypotheses_woes,
        "features": feature_areas,
    }
    return result
