"""Preprocessing for the Customer Spending project.

Contains the custom transformers and make_pipeline(). The saved model pipeline
references these classes, so this file must be importable (same folder or on
PYTHONPATH) wherever model_pipeline.pkl is loaded (Gradio, FastAPI, ...).
"""
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

SPEND_COLS = ["MntWines", "MntFruits", "MntMeatProducts", "MntFishProducts", "MntSweetProducts", "MntGoldProds"]
PURCHASE_COLS = ["NumDealsPurchases", "NumWebPurchases", "NumCatalogPurchases", "NumStorePurchases"]
CHANNEL_PURCHASE_COLS = ["NumWebPurchases", "NumCatalogPurchases", "NumStorePurchases"]
CAMPAIGN_COLS = ["AcceptedCmp1", "AcceptedCmp2", "AcceptedCmp3", "AcceptedCmp4", "AcceptedCmp5", "Response"]


class MarketingFeatureEngineer(BaseEstimator, TransformerMixin):
    """Create features using only the data passed to fit/transform.

    scenario="all"          -> use every non-leaking feature
    scenario="pre_campaign" -> drop everything that is only known after purchases / campaigns,
                               including the features derived from those columns.
    """
    def __init__(self, scenario="all"):
        self.scenario = scenario

    def fit(self, X, y=None):
        dates = pd.to_datetime(X["Dt_Customer"], dayfirst=True, errors="coerce")
        self.reference_date_ = dates.max()
        return self

    def transform(self, X):
        X = X.copy()
        X["Income"] = X["Income"].replace({0: np.nan, 666666: np.nan})
        X.loc[X["Year_Birth"] < 1900, "Year_Birth"] = np.nan
        X["Education"] = X["Education"].replace({"2n Cycle": "Master"})
        X["Marital_Status"] = X["Marital_Status"].replace({
            "Together": "Married", "Absurd": "Single", "YOLO": "Single", "Alone": "Single"
        })

        dt = pd.to_datetime(X["Dt_Customer"], dayfirst=True, errors="coerce")
        X["Customer_Tenure_Days"] = (self.reference_date_ - dt).dt.days
        X["Age"] = self.reference_date_.year - X["Year_Birth"]
        X.loc[~X["Age"].between(18, 100), "Age"] = np.nan

        X["Total_Children"] = X["Kidhome"] + X["Teenhome"]
        X["Has_Children"] = (X["Total_Children"] > 0).astype(int)
        adult_count = X["Marital_Status"].isin(["Married", "Together"]).astype(int) + 1
        X["Household_Size"] = adult_count + X["Total_Children"]
        X["Total_Purchases"] = X[PURCHASE_COLS].sum(axis=1)
        for col in CHANNEL_PURCHASE_COLS:
            short = col.replace("Num", "").replace("Purchases", "")
            X[f"{short}_Purchase_Share"] = X[col] / X["Total_Purchases"].replace(0, np.nan)
        X["Total_Accepted_Campaigns"] = X[[c for c in CAMPAIGN_COLS if c != "Response"]].sum(axis=1)
        X["Income_per_Person"] = X["Income"] / X["Household_Size"].replace(0, np.nan)
        X["Customer_Year"] = dt.dt.year
        X["Customer_Month"] = dt.dt.month

        X = X.drop(columns=["Dt_Customer", "Year_Birth", "Kidhome", "Teenhome"], errors="ignore")
        if self.scenario == "pre_campaign":
            derived = ["Total_Purchases", "Total_Accepted_Campaigns"] + [c for c in X.columns if c.endswith("_Purchase_Share")]
            X = X.drop(columns=[*PURCHASE_COLS, "NumWebVisitsMonth", *CAMPAIGN_COLS, *derived], errors="ignore")
        return X


class IQRClipper(BaseEstimator, TransformerMixin):
    """Clip numeric columns using IQR limits learned on the training data."""
    def fit(self, X, y=None):
        X = np.asarray(X, dtype=float)
        self.q1_ = np.nanpercentile(X, 25, axis=0)
        self.q3_ = np.nanpercentile(X, 75, axis=0)
        iqr = self.q3_ - self.q1_
        self.lower_ = self.q1_ - 1.5 * iqr
        self.upper_ = self.q3_ + 1.5 * iqr
        return self

    def transform(self, X):
        X = np.asarray(X, dtype=float)
        return np.clip(X, self.lower_, self.upper_)

    def get_feature_names_out(self, input_features=None):
        return np.asarray(input_features, dtype=object)


def make_pipeline(X_fit, scenario, model):
    """raw customer columns -> feature engineering -> impute/clip/scale/encode -> model."""
    engineer = MarketingFeatureEngineer(scenario=scenario)
    engineered_train = engineer.fit_transform(X_fit)
    categorical = [c for c in engineered_train.columns if not pd.api.types.is_numeric_dtype(engineered_train[c])]
    numeric = [c for c in engineered_train.columns if c not in categorical]
    binary = [c for c in numeric if set(pd.Series(engineered_train[c].dropna().unique())).issubset({0, 1})]
    continuous = [c for c in numeric if c not in binary]

    try:
        encoder = OneHotEncoder(drop="first", handle_unknown="ignore", sparse_output=False)
    except TypeError:
        encoder = OneHotEncoder(drop="first", handle_unknown="ignore", sparse=False)

    continuous_pipe = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("iqr_clip", IQRClipper()),
        ("scaler", StandardScaler()),
    ])
    binary_pipe = Pipeline([("imputer", SimpleImputer(strategy="most_frequent"))])
    categorical_pipe = Pipeline([
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("onehot", encoder),
    ])
    preprocessor = ColumnTransformer([
        ("continuous", continuous_pipe, continuous),
        ("binary", binary_pipe, binary),
        ("categorical", categorical_pipe, categorical),
    ], remainder="drop")
    return Pipeline([
        ("feature_engineering", engineer),
        ("preprocessing", preprocessor),
        ("model", model),
    ])
