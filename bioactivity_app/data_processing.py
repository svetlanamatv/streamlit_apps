import streamlit as st

import numpy as np
from numpy.random import seed
import time
from typing import List, Optional

import pandas as pd

from chembl_webresource_client.new_client import new_client

from rdkit import Chem
from rdkit.Chem import Descriptors, Lipinski

from scipy.stats import mannwhitneyu

SLEEP_TIME = 1
IC50_MAX_VALUE = 100_000_000
SEED = 1

DATAFRAME_COLUMNS_FILTER = [
    "activity_id", "molecule_chembl_id", "canonical_smiles", "standard_value"]

DESCRIPTOR_FUNCTIONS = {
    "MW": Descriptors.MolWt,
    "LogP": Descriptors.MolLogP,
    "NumHDonors": Lipinski.NumHDonors,
    "NumHAcceptors": Lipinski.NumHAcceptors
}
DEFAULT_DESCRIPTORS = list(DESCRIPTOR_FUNCTIONS.keys())


@st.cache_data
def convert_df(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8")


@st.cache_data(show_spinner=False)
def get_targets(user_query: str) -> pd.DataFrame:
    with st.spinner("Getting data..."):
        time.sleep(SLEEP_TIME)
        target = new_client.target
        target_search_result = target.search(user_query)

        return pd.DataFrame.from_dict(target_search_result)


@st.cache_data(show_spinner=False)
def get_target_bioactivity_data(target_chembl_id: str) -> pd.DataFrame:
    with st.spinner("Getting data for {}...".format(target_chembl_id)):
        time.sleep(SLEEP_TIME)
        activity = new_client.activity
        activity_search_result = activity.filter(
            target_chembl_id=target_chembl_id).filter(standard_type="IC50")

        return pd.DataFrame.from_dict(activity_search_result)


@st.cache_data(show_spinner=False)
def preprocess_bioactivity_df(df: pd.DataFrame) -> pd.DataFrame:
    with st.spinner("Preprocessing Bioactivity Data..."):
        time.sleep(SLEEP_TIME)

        df["standard_value"] = df["standard_value"].astype(float)

        # remove nans, negative IC50 values, remove unused fields
        df = df[df.standard_value.notna()]
        df = df[df.standard_value >= 0]
        df = df[DATAFRAME_COLUMNS_FILTER]
        return df.reset_index(drop=True)


@st.cache_data(show_spinner=False)
def convert_to_pIC50(df: pd.DataFrame) -> pd.DataFrame:
    pIC50_values = []
    for value in df["standard_value"]:
        value = min(value, IC50_MAX_VALUE)  # filter out big IC50 values
        value *= (10 ** -9)  # nM to M
        pIC50_values.append(-np.log10(value))

    df["pIC50"] = pIC50_values
    return df.drop(labels="standard_value", axis=1)


@st.cache_data(show_spinner=False)
def mannwhitney_u_test(df: pd.DataFrame, descriptor: str) -> pd.DataFrame:
    seed(SEED)

    active = df[df.bioactivity_class == "active"][descriptor]
    inactive = df[df.bioactivity_class == "inactive"][descriptor]

    statistic, p_value = mannwhitneyu(active, inactive)

    alpha = 0.05
    if p_value > alpha:
        interpretation = "Same distribution (fail to reject H0)"
    else:
        interpretation = "Different distribution (reject H0)"

    return pd.DataFrame.from_dict({"Descriptor": [descriptor],
                                   "Statistics": [statistic],
                                   "P-value": [p_value],
                                   "α": [alpha],
                                   "Interpretation": [interpretation]})


@st.cache_data(show_spinner=False)
def add_bioactivity_class(df: pd.DataFrame, remove_intermediate: bool = True
                          ) -> pd.DataFrame:
    with st.spinner("Adding bioactivity class..."):
        time.sleep(SLEEP_TIME)

        bioactivity_class = []
        for value in df["standard_value"]:
            if value >= 10000:
                bioactivity_class.append("inactive")
            elif value <= 1000:
                bioactivity_class.append("active")
            else:
                bioactivity_class.append("intermediate")

        df["bioactivity_class"] = bioactivity_class

        if remove_intermediate:
            df = df[df.bioactivity_class != "intermediate"]

        return df.reset_index(drop=True)


@st.cache_data(show_spinner=False)
def add_lipinski_descriptors(df: pd.DataFrame,
                             descriptor_names: Optional[List[str]]
                             ) -> pd.DataFrame:
    with st.spinner("Adding Lipinski Descriptors.."):
        time.sleep(SLEEP_TIME)

        if not descriptor_names:
            descriptor_names = DEFAULT_DESCRIPTORS
        descriptors = {name: [] for name in descriptor_names}

        for smile in df["canonical_smiles"]:
            molecule = Chem.MolFromSmiles(smile)
            for descriptor_name in descriptor_names:
                descriptors[descriptor_name].append(
                    DESCRIPTOR_FUNCTIONS[descriptor_name](molecule))

        for descriptor_name in descriptor_names:
            df[descriptor_name] = descriptors[descriptor_name]

    return df.reset_index(drop=True)
