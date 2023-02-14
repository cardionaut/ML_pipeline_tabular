import os

from loguru import logger
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.inspection import permutation_importance
from sklearn.feature_selection import RFECV
from sklearn.model_selection import StratifiedKFold

from excel.analysis.utils.helpers import save_tables, split_data


class AnalyseVariables:
    def __init__(self) -> None:
        self.job_dir = None
        self.metadata = None
        self.seed = None
        self.target_label = None
        self.corr_thresh = None

    def univariate_analysis(self, data: pd.DataFrame):
        """
        Perform univariate analysis (box plots and distributions)
        """
        # split data and metadata but keep hue column
        if self.target_label in self.metadata:
            self.metadata.remove(self.target_label)
        to_analyse, _, _ = split_data(data, self.metadata, self.target_label, remove_mdata=True)

        # box plot for each feature w.r.t. target_label
        data_long = to_analyse.melt(id_vars=[self.target_label])
        sns.boxplot(
            data=data_long,
            x='value',
            y='variable',
            hue=self.target_label,
            orient='h',
            meanline=True,
            showmeans=True,
        )
        plt.axvline(x=0, alpha=0.7, color='grey', linestyle='--')
        plt.tight_layout()
        plt.savefig(os.path.join(self.job_dir, f'box_plot_{self.target_label}.pdf'))
        plt.clf()

        to_analyse = to_analyse.drop(self.target_label, axis=1)  # now remove hue column

        # box plot for each feature
        sns.boxplot(data=to_analyse, orient='h', meanline=True, showmeans=True, whis=1.5)
        plt.axvline(x=0, alpha=0.7, color='grey', linestyle='--')
        plt.tight_layout()
        plt.savefig(os.path.join(self.job_dir, 'box_plot.pdf'))
        plt.clf()

        # plot distribution for each feature
        sns.displot(data=to_analyse, kind='kde')
        plt.tight_layout()
        plt.savefig(os.path.join(self.job_dir, 'dis_plot.pdf'))
        plt.clf()
        return data

    def bivariate_analysis(self, data):
        """
        Perform bivariate analysis
        """
        pass

    def pearson_correlation(self, data: pd.DataFrame):
        """
        Compute correlation between features and optionally drop highly correlated ones
        """
        matrix = data.corr(method='pearson').round(2)
        plt.figure(figsize=(50, 50))
        sns.heatmap(matrix, annot=True, xticklabels=True, yticklabels=True, cmap='viridis')
        plt.xticks(rotation=90)
        plt.savefig(os.path.join(self.job_dir, 'corr_plot.pdf'))
        plt.clf()
        return data

    def drop_by_pearson_correlation(self, data: pd.DataFrame):
        """
        Compute correlation between features and optionally drop highly correlated ones
        """
        matrix = data.corr(method='pearson').round(2)
        abs_corr = matrix.abs()
        upper_tri = abs_corr.where(np.triu(np.ones(abs_corr.shape), k=1).astype(bool))
        cols_to_drop = [col for col in upper_tri.columns if any(upper_tri[col] > self.corr_thresh)]
        metadata = [col for col in self.metadata if col not in cols_to_drop]
        to_analyse = data.drop(cols_to_drop, axis=1)
        logger.info(
            f'Removed {len(cols_to_drop)} redundant features with correlation above {self.corr_thresh}, '
            f'number of remaining features: {len(to_analyse.columns)}'
        )
        matrix = to_analyse.corr(method='pearson').round(2)

        # plot correlation heatmap
        plt.figure(figsize=(50, 50))
        sns.heatmap(matrix, annot=True, xticklabels=True, yticklabels=True, cmap='viridis')
        plt.xticks(rotation=90)
        plt.savefig(os.path.join(self.job_dir, 'corr_plot.pdf'))
        plt.clf()
        return data

    def forest_reduction(self, data: pd.DataFrame):
        """
        Calculate feature importance and remove features with low importance
        """
        X = data.drop(self.target_label, axis=1)  # split data
        y = data[self.target_label]
        estimator = RandomForestClassifier(random_state=self.seed)
        min_features = 1
        selector = RFECV(
            estimator=estimator, step=1, min_features_to_select=min_features, scoring='average_precision', n_jobs=4
        )
        selector.fit(X, y)
        logger.info(f'Optimal number of features: {selector.n_features_}')

        n_scores = len(selector.cv_results_["mean_test_score"])
        plt.figure()
        plt.xlabel("Number of features selected")
        plt.ylabel("Mean average precision")
        plt.xticks(range(min_features, n_scores + 1))
        plt.grid()
        plt.errorbar(
            range(min_features, n_scores + min_features),
            selector.cv_results_["mean_test_score"],
            yerr=selector.cv_results_["std_test_score"],
        )
        plt.title("Recursive Feature Elimination")
        plt.savefig(os.path.join(self.job_dir, 'RFECV.pdf'))
        plt.clf()

        # Plot importances
        # fig, ax = plt.subplots()
        # importances.plot.bar(yerr=std, ax=ax)
        # ax.set_title("Feature importances using mean decrease in impurity")
        # ax.set_ylabel("Mean decrease in impurity")
        # fig.tight_layout()
        # plt.savefig(os.path.join(job_dir, 'feature_importance_impurity.pdf'))
        # plt.clf()

    min_features = 1
    cross_validator = StratifiedKFold(n_splits=10, shuffle=True, random_state=seed)
    selector = RFECV(
        estimator=estimator,
        step=1,
        min_features_to_select=min_features,
        cv=cross_validator,
        scoring='average_precision',
        n_jobs=4,
    )
    selector.fit(X, y)

        # Plot correlation heatmap
        # figsize = to_keep * 1.5
        # matrix = to_analyse.corr(method='pearson').round(2)
        # plt.figure(figsize=(figsize, figsize))
        # sns.heatmap(matrix, annot=True, xticklabels=True, yticklabels=True, cmap='viridis')
        # plt.xticks(rotation=90)
        # fig.tight_layout()
        # plt.savefig(os.path.join(out_dir, 'corr_plot_after_reduction.pdf'))
        # plt.clf()

    # Plot performance for increasing number of features
    n_scores = len(selector.cv_results_['mean_test_score'])
    plt.figure()
    plt.xlabel('Number of features selected')
    plt.ylabel('Mean average precision')
    plt.xticks(range(min_features, n_scores + 1, 5))
    plt.grid(alpha=0.5)
    plt.errorbar(
        range(min_features, n_scores + min_features),
        selector.cv_results_['mean_test_score'],
        yerr=selector.cv_results_['std_test_score'],
    )
    plt.title(f'Recursive Feature Elimination for {method} estimator')
    plt.savefig(os.path.join(out_dir, f'RFECV_{method}.pdf'))
    plt.clf()

    to_analyse = pd.concat((X.loc[:, selector.support_], to_analyse[label]), axis=1)
    metadata = [col for col in metadata if col in to_analyse.columns]
    importances = pd.Series(selector.estimator_.feature_importances_, index=X.columns[selector.support_])
    importances = importances.sort_values(ascending=False)

    # Plot importances
    fig, ax = plt.subplots()
    importances.plot.bar(ax=ax)
    ax.set_title(f'Feature importances using {method} estimator')
    fig.tight_layout()
    plt.savefig(os.path.join(out_dir, f'feature_importance_{method}.pdf'))
    plt.clf()

    # Plot patient/feature value heatmap
    # plt.figure(figsize=(figsize, figsize))
    # sns.heatmap(to_analyse.transpose(), annot=False, xticklabels=False, yticklabels=True, cmap='viridis')
    # plt.xticks(rotation=90)
    # fig.tight_layout()
    # plt.savefig(os.path.join(out_dir, 'heatmap_after_reduction.pdf'))
    # plt.clf()
    def drop_outliers(self, data: pd.DataFrame):
        """Detect outliers in the data, optionally removing or further investigating them

        Args:
            data (pd.DataFrame): data
            whiskers (float, optional): determines reach of the whiskers. Defaults to 1.5 (matplotlib default)
            remove (bool, optional): whether to remove outliers. Defaults to True.
            investigate (bool, optional): whether to investigate outliers. Defaults to False.
        """
        # Split data and metadata
        mdata = data[self.metadata]
        whiskers = 1.5
        to_analyse = data.drop(self.metadata, axis=1, errors='ignore')

        # Calculate quartiles, interquartile range and limits
        q1, q3 = np.percentile(to_analyse, [25, 75], axis=0)
        iqr = q3 - q1
        lower_limit = q1 - whiskers * iqr
        upper_limit = q3 + whiskers * iqr
        # logger.debug(f'\nlower limit: {lower_limit}\nupper limit: {upper_limit}')

        to_analyse = to_analyse.mask(to_analyse.le(lower_limit) | to_analyse.ge(upper_limit))
        to_analyse.to_excel(os.path.join(self.job_dir, 'outliers_removed.xlsx'), index=True)

        # Add metadata again
        data = pd.concat((to_analyse, mdata), axis=1)

        # TODO: deal with removed outliers (e.g. remove patient)
        return data

    def detect_outliers(self, data: pd.DataFrame):
        """Detect outliers in the data, optionally removing or further investigating them

        Args:
            data (pd.DataFrame): data
            whiskers (float, optional): determines reach of the whiskers. Defaults to 1.5 (matplotlib default)
            remove (bool, optional): whether to remove outliers. Defaults to True.
            investigate (bool, optional): whether to investigate outliers. Defaults to False.
        """
        # Split data and metadata
        mdata = data[self.metadata]
        whiskers = 1.5
        to_analyse = data.drop(self.metadata, axis=1, errors='ignore')

        # Calculate quartiles, interquartile range and limits
        q1, q3 = np.percentile(to_analyse, [25, 75], axis=0)
        iqr = q3 - q1
        lower_limit = q1 - whiskers * iqr
        upper_limit = q3 + whiskers * iqr
        # logger.debug(f'\nlower limit: {lower_limit}\nupper limit: {upper_limit}')

        high_data = to_analyse.copy(deep=True)
        # Remove rows without outliers
        # high_data = high_data.drop(high_data.between(lower_limit, upper_limit).all(), axis=0)
        # Add metadata again
        high_data = pd.concat((high_data, mdata), axis=1).sort_values(by=['subject'])

        # Highlight outliers in table
        high_data.style.apply(
            lambda _: highlight(df=high_data, lower_limit=lower_limit, upper_limit=upper_limit), axis=None
        ).to_excel(os.path.join(self.job_dir, 'investigate_outliers.xlsx'), index=True)
        return data


def highlight(df: pd.DataFrame, lower_limit: np.array, upper_limit: np.array):
    """Highlight outliers in a dataframe"""
    style_df = pd.DataFrame('', index=df.index, columns=df.columns)
    mask = pd.concat(
        [~df.iloc[:, i].between(lower_limit[i], upper_limit[i], inclusive='neither') for i in range(lower_limit.size)],
        axis=1,
    )
    style_df = style_df.mask(mask, 'background-color: red')
    style_df.iloc[:, lower_limit.size :] = ''  # uncolor metadata
    return style_df
