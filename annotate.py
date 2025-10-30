import streamlit as st
import pandas as pd
import json

st.set_page_config(layout="wide")

def fetch_non_annotated(df: pd.DataFrame, annot_index: int) -> tuple:
    
    """Provide the dataframe and an index and get the corresponding column fields for said index as a tuple."""
    
    curr_row = df.iloc[annot_index]
    sentence = curr_row["sent"]
    cont_og = curr_row["original_cont_label"]
    det_og = curr_row["original_det_label"]
    auto_cont = curr_row["annotated_cont_labels"]
    auto_det = curr_row["annotated_det_labels"]
    tuple_info = (sentence, cont_og, det_og, auto_cont, auto_det)
    
    return tuple_info

def generate_category_explanation(explanations:dict, category:str) -> str:
    
    """Constructs the explanation for the labels in a category form the explanations dictionary."""
    
    expl_cat = explanations[category]
    explanation_string = ""
    for key, value in expl_cat.items():
        explanation_string = explanation_string + key + ": " + value + "\n\n"
    
    return explanation_string

def load_annotation_data(df: pd.DataFrame, i:int, annot_indexes, tuple_indexes:tuple):
    
    """
    Loads the annotation data for the index, gets the category information from the fetch_non_annotated function and displays it in the app.
    """
    
    curr_tuple = fetch_non_annotated(df, annot_indexes[i])
        
    st.text("SENTENCE")
    text_cont = st.container(border=True).write(curr_tuple[0])
    
    st.text("Generated from Label")
    index_reference = tuple_indexes[0]
    text_cont = st.container(border=True).write(curr_tuple[index_reference])

    st.text("Automatic Annotation")
    index_automatic_annot = tuple_indexes[1]
    text_cont = st.container(border=True).write(curr_tuple[index_automatic_annot])

@st.cache_data
def convert_df(df: pd.DataFrame):
    """
    Converts a dataframe to a csv for download.
    """
    return df.to_csv(index=False).encode("utf-8")


def main():

    st.title("ANNOTATE!")

    # we will use the side to upload and download files
    with st.sidebar:
        st.header("File Management")
        df_loader = st.file_uploader("Upload the CSV you want to annotate.", type=["csv"])
        explanations_loader = st.file_uploader("Upload the JSON file containing annotation guidelines.", type=["json"])

    # set the index as part of the session state so that we can update it with a button to go back and forth between sentences
    if "df_index" not in st.session_state: 
        st.session_state["df_index"] = 0
    
    # need to load the csvs and explanations before starting the annotation process
    while not df_loader or not explanations_loader:
        st.info("Upload a CSV file and annotation guide to start annotating.")
        
        if not df_loader:
            st.warning("Please upload a CSV file.")
    
        if not explanations_loader:
            st.warning("Please upload a JSON file with annotation guidelines.")
            
        # streamlit will no do anything until both files are uploaded
        st.stop()
    
    # the state of the app will change so that the tools are displayed once the df and explanations are loaded
    if df_loader and explanations_loader:
        # loading the files
        df = pd.read_csv(df_loader)
        explanations = json.load(explanations_loader)
        
        validation_columns =  ["Validated Content", "Validated Content Label", 
                            "Validated Determinant", "Validated Determinant Label"]
        
        if validation_columns[0] not in list(df.columns): # first time that you load a csv, these will be created automatically
        
            df["Validated Content"] = "NO"
            df["Validated Content Label"] = "NA"
            df["Validated Determinant"] = "NO"
            df["Validated Determinant Label"] = "NA"
            
        
            
        # blocked columns won't be able to be edited in the st.data_editor obj
        blocked_columns = ["sent", "original_cont_label", 
                        "original_det_label", "annotated_cont_labels",
                        "annotated_det_labels", "Validated_Content", 
                        "Validated Determinant"]
        
        annotations_not_validated_yet_df = df[(df["Validated Content"]=="NO") | (df["Validated Determinant"]=="NO")]
        number_annot_left = annotations_not_validated_yet_df.shape[0]
        annot_indexes = annotations_not_validated_yet_df.index
        
        # creating two columns, one for the explanations and one for the annotation process
        col1, col2 = st.columns(2)
        
        # the column that holds the cateogry to annotate and the explanation of that category
        with col1:
            
            # select which category to annotate first
            cateogry_to_annotate = st.radio("Select which category you'd like to annotate first.", ["Contents", "Determinants"])

            expl_conts = generate_category_explanation(explanations, "conts")
            expl_dets = generate_category_explanation(explanations, "dets")

            if cateogry_to_annotate == "Contents":
                cont_descriptions = st.text_area("Content Labels Explanations", expl_conts, height=400)
                cols_view = ["original_cont_label", "annotated_cont_labels", "Validated Content Label"]
                tuple_indexes = [1, 3]
                annot_indexes = df[df["Validated Content"]=="NO"].index
                
            elif cateogry_to_annotate == "Determinants":
                det_descriptions = st.text_area("Determinant Labels Explanations", expl_dets, height=400)
                cols_view = ["original_det_label", "annotated_det_labels", "Validated Determinant Label"]
                tuple_indexes = [2, 4]
                annot_indexes = df[df["Validated Determinant"]=="NO"].index
                
                # (sentence, cont_og, det_og, auto_cont, auto_det) order ot the tuple

        # the column that holds the data to annotate and the input for the validated label
        with col2:
            
            load_annotation_data(df, st.session_state["df_index"], annot_indexes, tuple_indexes)
            
            validated_annotation = st.text_input(label="Validated annotation", placeholder="Enter your annotation.")
            
            # log when there is a validated annotation
            if validated_annotation:
                
                df[cols_view[2]].loc[annot_indexes[st.session_state["df_index"]]] = validated_annotation # input the validated label in the df
                df[cols_view[1]].loc[annot_indexes[st.session_state["df_index"]]] = "YES" # change the validation to status to YES
            
            # submit = st.form_submit_button("Next Sentence", on_click=my_callback, args=[df_index])
            
            
            subcol1, subcol2, _ = st.columns([1, 1, 3])
            
            # buttons to go to the next and previous sentence
            with subcol1:
                button_next = st.button("Next sentence")
            with subcol2: 
                button_back = st.button("Prev. sentence")
            
            if button_next:
                st.session_state["df_index"] += 1
        
            if button_back:
                st.session_state["df_index"] -= 1
                
        with st.sidebar:
            csv = convert_df(df)
            st.download_button(label="Download Annotated CSV", data=csv, file_name="validated.csv")

if __name__ == "__main__":
    main()