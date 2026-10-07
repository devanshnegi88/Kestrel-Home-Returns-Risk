# Model comparison

All models below are evaluated on the same **unique-order chronological 80/20 validation split**. No downstream service/pickup fields are used.

| Model | Accuracy @ 0.50 | Precision | Recall | F1 | ROC-AUC | PR-AUC | Brier |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| CatBoost | 89.15% | 81.82% | 7.44% | 13.64% | 0.775 | 0.398 | 0.087 |
| Logistic Regression | 89.43% | 70.00% | 14.46% | 23.97% | 0.777 | 0.400 | 0.086 |
| **50/50 blend** | **89.34%** | **78.12%** | **10.33%** | **18.25%** | **0.779** | **0.407** | **0.086** |

## Why keep the blend?

The logistic component provides the strongest standalone AUC of the two in this split, while CatBoost captures nonlinear/categorical interactions. The blend improves the overall ranking metrics and gives the best Brier score of the three candidates in the selected comparison. That makes it a better all-around scoring model than simply choosing one component by a single metric.
