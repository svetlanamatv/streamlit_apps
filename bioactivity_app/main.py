# streamlit run main.py

import argparse
import json
import os
import time
from PIL import Image

import streamlit as st
from st_aggrid import AgGrid
from st_aggrid.grid_options_builder import GridOptionsBuilder

import data_processing as data
import visualizations as vis

SLEEP_TIME = 1

parser = argparse.ArgumentParser()
parser.add_argument("-images_path", type=str, default=os.getcwd())
parser.add_argument("-images_file", type=str, default="images.json")
args = parser.parse_args()

IMAGES_FILE_PATH = args.images_path + "/" + args.images_file

with open(IMAGES_FILE_PATH, "rt") as f:
    json_data = json.load(f)

BIOACTIVITY_CLASSES_IMG_PATH = (
        args.images_path + "/" + json_data["bioactivity_classes_img"])

DEFAULT_FLAGS = [
    "collected_target_data",
    "target_chembl_id",
    "collected_bioactivity_data",
    "finished_initial_preprocessing",
    "added_bioactivity_class",
    "converted_to_pIC50",
    "added_lipinski_descriptors",
    "finished_data_processing",
]

SUPPORTED_TARGETS = ["Alzheimer", "Diabetes"]

WELCOME_MESSAGE_HEADER = "Welcome to Bioactivity Data Analysis App!"
WELCOME_MESSAGE = '''This app lets you search for targets in the ChEMBL 
database and retrieve bioactivity data for compounds that have been tested on 
a chosen target. Then it performs data analysis tasks like data 
pre-processing, creating graphs, adding Lipinski descriptors, and running the 
Mann-Whitney U test. \\
*Please note that, as it's currently a demo version, 
you can only query targets related to Alzheimer's disease and Diabetes.*'''

MANN_WHITNEY_DESCRIPTORS = [
    "pIC50", "MW", "LogP", "NumHDonors", "NumHAcceptors"]
DESCRIPTORS = ["MW", "LogP", "NumHDonors", "NumHAcceptors"]


def no_compounds_found_error_message(class_name: str) -> str:
    return """
           ** Warning: no compounds were found for the {} class.** \\
           ** Data analysis results are unavailable.**
           """.format(class_name)


def attr_enabled(obj, name: str):
    return hasattr(obj, name) and getattr(obj, name)


def reset_flags():
    for flag in DEFAULT_FLAGS:
        st.session_state[flag] = False


def create_GridOptionsBuilder():
    builder = GridOptionsBuilder.from_dataframe(st.session_state["targets"])
    builder.configure_grid_options(alwaysShowHorizontalScroll=True)
    builder.configure_selection(selection_mode="multiple", use_checkbox=True)
    return builder.build()


def process_table_response(input_row):
    input_row_index = int(input_row[0]["_selectedRowNodeInfo"]["nodeId"])
    input_row = st.session_state["targets"].iloc[[input_row_index]]
    target_info_filter = {"target_name": "pref_name",
                          "target_type": "target_type",
                          "target_organism": "organism",
                          "target_chembl_id": "target_chembl_id",
                          }
    for target_info_item, name_in_df in target_info_filter.items():
        st.session_state[target_info_item] = input_row[name_in_df].iloc[0]


st.header(WELCOME_MESSAGE_HEADER)
st.markdown(WELCOME_MESSAGE)

# Get information for chosen target
target_input_form = st.form(key="target_input_form")
selected_target = target_input_form.selectbox(
    "Choose query for target search:", SUPPORTED_TARGETS)

target_submit_button = target_input_form.form_submit_button(label="Submit")

# step 1: query Chembl Database
if target_submit_button:
    reset_flags()
    try:
        if selected_target not in SUPPORTED_TARGETS:
            st.write("Sorry, currently only the following targets are "
                     "supported: " + ", ".join(SUPPORTED_TARGETS))
        else:
            targets = data.get_targets(selected_target)
            target_filter_fields = ["organism", "pref_name", "target_type",
                                    "target_chembl_id", "score"]
            st.session_state["targets"] = targets[target_filter_fields]
            st.session_state["collected_target_data"] = True
    except Exception:
        st.write("Sorry, we couldn't query the database")

# step 2: show targets dataset and get the response from the user
if attr_enabled(st.session_state, "collected_target_data"):
    st.write("✔️ Loaded target data for query: ", selected_target)

    try:
        st.write("Please choose one target from the table:")
        go = create_GridOptionsBuilder()
        response = AgGrid(st.session_state["targets"], gridOptions=go,
                          use_checkbox=True, reload_data=False)
        selected_row = response["selected_rows"]
    except Exception:
        st.write("Sorry, we couldn't show the dataset or get the response "
                 "from the table")
    else:
        compound_select_button = st.button("Submit", key="b1")

        if compound_select_button:
            reset_flags()
            st.session_state["collected_target_data"] = True

            if selected_row and len(selected_row) == 1:
                try:
                    process_table_response(selected_row)
                except Exception:
                    st.write("Sorry, we couldn't process the response from "
                             "the table")
            elif selected_row and len(selected_row) > 1:
                st.write("Please select only one row")
            else:
                st.write("Please select a row")

# step 3: query Chembl for target data by target_chembl_id
if attr_enabled(st.session_state, "target_chembl_id"):
    try:
        st.session_state["bioactivity_df"] = data.get_target_bioactivity_data(
            st.session_state["target_chembl_id"])
        if st.session_state["bioactivity_df"].shape[0] != 0:
            st.session_state["collected_bioactivity_data"] = True
        else:
            st.session_state["collected_bioactivity_data"] = False
            st.write("Sorry, we couldn't find bioactivity data for the chosen "
                     "target")
    except Exception:
        st.write("Sorry, we couldn't get data for ", str(
            st.session_state["target_chembl_id"]))

# step 4.1: initial data preprocessing
if attr_enabled(st.session_state, "collected_bioactivity_data"):
    try:
        st.divider()
        st.header("Data Processing", anchor=False)
        st.divider()
        st.markdown("""
                        ✔️ Loaded bioactivity data for target **{}**\\
                           Type: {}\\
                           Organism: {}\\
                           ChEMBL id: {}
                    """.format(st.session_state["target_name"],
                               st.session_state["target_type"].lower(),
                               st.session_state["target_organism"].lower(),
                               st.session_state["target_chembl_id"])
                    )

        st.write("    Dataset preview: ")
        st.dataframe(st.session_state["bioactivity_df"].head(3))
        st.write("    Dataset size: ", st.session_state["bioactivity_df"].shape)

        csv = data.convert_df(st.session_state["bioactivity_df"])
        target_name = st.session_state["target_name"].lower().replace(" ", "_")
        st.download_button("Download Original Dataset", csv,
                           "bioactivity_dataset_" + target_name + ".csv",
                           "text/csv", key="download-csv")

        st.session_state["df"] = data.preprocess_bioactivity_df(
            st.session_state["bioactivity_df"])
        if st.session_state["df"].shape[0] != 0:
            st.session_state["finished_initial_preprocessing"] = True
        else:
            st.write("Sorry, dataframe became empty after preprocessing")
    except Exception:
        st.write("Sorry, couldn't finish initial preprocessing")

# step 4.2: add bioactivity class
if attr_enabled(st.session_state, "finished_initial_preprocessing"):
    st.markdown("✔️ **Preprocessed dataset**")
    st.markdown(""" 
            - Removed NaNs
            - Removed negative IC50 values
                    """)

    try:
        st.session_state["df"] = data.add_bioactivity_class(
            st.session_state["df"])
        st.session_state["added_bioactivity_class"] = True
    except Exception:
        st.write("Sorry, couldn't add bioactivity class")

# step 4.3: covert to pIC50
if attr_enabled(st.session_state, "added_bioactivity_class"):
    st.markdown("✔️ **Added Bioactivity Class**")
    st.write("All compounds have been categorized into three classes based on "
             "their standard values:")

    image = Image.open(BIOACTIVITY_CLASSES_IMG_PATH)
    st.image(image)
    st.markdown("""
    *Please be aware that we have excluded all records with 
    intermediate bioactivity classifications from the dataset.*
    """
                )
    try:
        st.session_state["df"] = data.convert_to_pIC50(st.session_state["df"])

        st.markdown("""
                ✔️ **Converted IC50 to pIC50**\\
                   (the negative log of the IC50 value when converted to molar)
                """)

        st.session_state["df"] = st.session_state["df"].reset_index(drop=True)
        st.session_state["converted_to_pIC50"] = True
    except Exception:
        st.write("Sorry, couldn't convert to pIC50")

# step 4.4: add Lipinski descriptors
if attr_enabled(st.session_state, "converted_to_pIC50"):
    try:
        st.session_state["df"] = data.add_lipinski_descriptors(
            st.session_state["df"], DESCRIPTORS)
        st.session_state["added_lipinski_descriptors"] = True
    except Exception:
        st.write("Sorry, couldn't add Lipinski Descriptors")

# step 5: Mann-Whitney U test
if attr_enabled(st.session_state, "added_lipinski_descriptors"):
    st.markdown("✔️ **Added Lipinski Descriptors**")
    st.markdown("""
        * MV - Molecular mass
        * logP - Partition coefficient
        * NumHDonors - Hydrogen bond donors
        * NumHAcceptors - Hydrogen bond acceptors
        """)

    st.write("Dataset preview:")
    st.dataframe(st.session_state["df"].head(3), hide_index=True)
    st.write("Dataset size: ", st.session_state["df"].shape)

    csv_preprocessed = data.convert_df(st.session_state["df"])
    target_name = st.session_state["target_name"].lower().replace(" ", "_")
    st.download_button("Download Pre-processed Dataset", csv_preprocessed,
                       "bioactivity_preprocessed_dataset_" + target_name +
                       ".csv", "text/csv", key="download-preprocessed-csv")

    active = st.session_state["df"][
        st.session_state["df"].bioactivity_class == "active"]
    inactive = st.session_state["df"][
        st.session_state["df"].bioactivity_class == "inactive"]

    if active.shape[0] == 0:
        st.markdown(no_compounds_found_error_message(class_name="active"))
    elif inactive.shape[0] == 0:
        st.markdown(no_compounds_found_error_message(class_name="inactive"))
    else:
        try:
            st.session_state["mannwhitney_dict"] = dict()
            with st.spinner("Running Mann-Whitney U test..."):
                time.sleep(SLEEP_TIME)
                for descriptor in MANN_WHITNEY_DESCRIPTORS:
                    descriptor_result = data.mannwhitney_u_test(
                        st.session_state["df"], descriptor)
                    st.session_state["mannwhitney_dict"].update(
                        {descriptor: descriptor_result})
            st.session_state["finished_data_processing"] = True
            st.markdown("✔️ **Finished Mann-Whitney U test**")
        except Exception:
            st.write("Sorry, couldn't run Mann-Whitney U test")

# step 6: visualizations
if attr_enabled(st.session_state, "finished_data_processing"):
    st.divider()
    st.header("Data Analysis Result", anchor=False)
    st.divider()

    col_frequency, col_pIC50 = st.columns(spec=[0.5, 0.5])
    with col_frequency:
        vis.plot_bioactivity_class_frequency_px(st.session_state["df"])
    with col_pIC50:
        vis.plot_pIC50_px(st.session_state["df"])

    default_x_axis = MANN_WHITNEY_DESCRIPTORS[1]
    default_y_axis = MANN_WHITNEY_DESCRIPTORS[2]

    with st.form(key="scatter_plot_input_form"):
        col_x_axis, col4_y_axis = st.columns(spec=[0.5, 0.5])
        with col_x_axis:
            plot_x_axis = st.selectbox(
                "Choose argument for X axis", list(MANN_WHITNEY_DESCRIPTORS),
                index=1, key=123)
        with col4_y_axis:
            plot_y_axis = st.selectbox(
                "Choose argument Y axis", list(MANN_WHITNEY_DESCRIPTORS),
                index=2, key=124)

        scatter_plot_submit_button = st.form_submit_button(label="Plot")

    if scatter_plot_submit_button:
        vis.scatterplot_px(st.session_state["df"], plot_x_axis, plot_y_axis,
                           "bioactivity_class", "pIC50")
    else:
        vis.scatterplot_px(st.session_state["df"], default_x_axis,
                           default_y_axis, "bioactivity_class", "pIC50")

    st.markdown("""
        *pIC50 is used as point size*
        """)

    st.divider()

    if len(st.session_state["mannwhitney_dict"]) != 0:
        st.header("Mann-Whitney U Test Result", anchor=False)
        st.divider()

        for descriptor in MANN_WHITNEY_DESCRIPTORS:
            st.markdown("""
                **Descriptor: {}**
                """.format(descriptor))
            vis.boxplot_bioactivity_class_px(st.session_state["df"],
                                             descriptor)

            st.dataframe(st.session_state["mannwhitney_dict"][descriptor],
                         hide_index=True)
            st.divider()
    else:
        st.write("Sorry, no results to show")
