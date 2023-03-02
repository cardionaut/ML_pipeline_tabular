from loguru import logger
from sklearn.experimental import enable_halving_search_cv
from sklearn.model_selection import HalvingGridSearchCV, StratifiedKFold


class CrossValidation:
    def __init__(self, x_train, y_train, estimator, cross_validator, param_grid: dict, scoring: str, seed: int) -> None:
        self.x_train = x_train
        self.y_train = y_train
        self.estimator = estimator
        self.cross_validator = cross_validator
        self.param_grid = dict(param_grid)
        self.scoring = scoring
        self.seed = seed

    def __call__(self):
        selector = HalvingGridSearchCV(
            estimator=self.estimator,
            param_grid=self.param_grid,
            scoring=self.scoring,
            cv=self.cross_validator,
            max_resources=1000,
        )
        selector.fit(self.x_train, self.y_train)

        return selector
