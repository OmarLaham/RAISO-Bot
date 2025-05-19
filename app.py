import streamlit as st
import os
from os import path
import requests
from streamlit_modal import Modal

from PIL import Image
import pydicom
import tempfile
import os
from xray_classifier import classify_xray
from grad_cam import run_gradcam_on_xray
from xray_find_similar import find_similar_xrays
from xray_dicom_deidentify import de_id_dcm

def show_classification_result():
    st.success("✅ Classification Complete")
    # Print results
    n_diagnosis = 0
    dct_classification_result = st.session_state['dct_classification_result'] # get values from session_state
    classification_threshold = 0.55
    for label, prob in dct_classification_result.items():

        if prob >= classification_threshold: # Only show those with confidence >= classification_threshold
            n_diagnosis += 1

        col_class, col_confidence, col_operations = st.columns(3)
        with col_class:
            st.write(f"**{label}**")
        with col_confidence:
            st.write(f"Confidence: {prob:.2f}")
        with col_operations:
            if st.button("💡 Visual Explanaition", key=f"btn_explain_opinion_{label}"):
                st.session_state['action'] = "explain_opinion"
                st.session_state['explain_opinion_label'] = label
                modal.open()

            if st.button("🔍 Show Similar X-Rays", key=f"btn_show_similar_xrays_{label}"):
                st.session_state['action'] = "show_similar_xrays"
                st.session_state['explain_opinion_label'] = label
                modal.open()

        st.divider()

    st.write(f"**{n_diagnosis} labels / possible diagnosis** with confidence >= {classification_threshold} captured by the AI model.")


def show_example_dicoms():
    imgs = {
        "Cardiomegaly": path.join("example_dicoms","cardiomegaly_00004606_000.dcm"),
        "Hernia": path.join("example_dicoms","hernia_00007712_002.dcm"),
        "Nodule": path.join("example_dicoms","nodules_00004995_000.dcm"),
        "Infiltration": path.join("example_dicoms","infiltration_00018734_000.dcm")
    }

    with st.expander("**Example Chest X-Ray DICOMs**"):
        for label, img_path in imgs.items():
            col_img, col_operations = st.columns(2)

            with col_img:
                dicom_data = pydicom.dcmread(img_path)
                img = Image.fromarray(dicom_data.pixel_array)
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                st.image(img, caption=label)
                

            with col_operations:
                 btn_key = img_path.split("_")[-2]
                 if st.button("👉 Try this X-ray", key=f"btn_try_example_dicom_{btn_key}"):
                      st.session_state.example_dicom_path = img_path
                      st.experimental_rerun()

            st.divider()

# Set page config
st.set_page_config(page_title="Radiology AI Assistant", layout="centered")

# Title
st.title("🩻 RAISO - Radiology AI Second Opinion App")

def show_apim_form():

    st.write("🔐 Secure API Access")

    apim_url = st.secrets["RAISO_APIM_GATEWAY_URL"]

    # Store the subscription key in session state
    if "sub_key" not in st.session_state:
        #st.session_state.sub_key = ""

        # Step 1: Form to enter key
        with st.form("key_form"):
            key_input = st.text_input("Enter your API access key", type="password")
            submitted = st.form_submit_button("Use Key")

            if submitted:
                
                st.session_state.sub_key = key_input
                
                # Debugging
                print("> key input:", key_input)

                st.success("Key saved. Will now call the API and check if it's valid.")
                st.experimental_rerun()
                
                

                

    else:
        if st.session_state.sub_key != "":

            if 'apim_key_valid' not in st.session_state:
                # Check if key is valid
                print("> Validating key:", st.session_state.sub_key)
                headers = {
                    "Ocp-Apim-Subscription-Key": st.session_state.sub_key
                }
                
                response = requests.get(apim_url, headers=headers)

                if response.status_code == 200: # Valid subscription key
                    st.session_state.apim_key_valid = True
                    st.session_state.apim_header_added = True
                    st.success("🎉 Valid API key!")
                    st.experimental_rerun()
                    
                else: # Invalid subscription key

                    # Print for debugging
                    print("APIM validation request failed with status code:", response.status_code)
                    print(response.text)
                    # Reset the key
                    del st.session_state["sub_key"]

                    st.error("❌ Invalid API key. Please try again.")                
                    if st.button("🔄 Try Again"):
                        refresh_html = '''<meta http-equiv="refresh" content="0">'''
                        st.markdown(refresh_html, unsafe_allow_html=True)






# Use Azure API Management to limit usage. 
if 'apim_header_added' not in st.session_state: # If Ocp-Apim-Subscription-Key header is still not added, show form to enter key
    show_apim_form()
else: # Drive logic to show the main app
        
    # Cite model and dataset
    nih_dataset_link = "<a target='_blank' style='font-size: bold;' href='https://www.kaggle.com/datasets/nih-chest-xrays/data'>NIH Chest X-rays Dataset</a>"
    citation_html = f"<div style='padding: 5px; margin-bottom: 10px; background-color: #e0ffff'>This app is using a pre-trained <b>EfficientNetB0</b> model for X-Ray image classification. All X-Rays used as example imaging data and for similarity search are de-identified X-rays from the {nih_dataset_link}).</div>"

    st.markdown(citation_html, unsafe_allow_html=True)

    # Popup to use for extra content
    modal = Modal("RAISO - Radiology AI Assistant", key="modal")

    if 'example_dicom_path' not in st.session_state:
        st.session_state.example_dicom_path = False

    # File uploader

    uploaded_file = None
    if st.session_state.example_dicom_path == False:
        uploaded_file = st.file_uploader("Upload a DICOM file (Max 5MB)", type=["dcm"])
        st.write("🔒 Uploaded file will be de-identified before passing to ML model.")



    # Experiment restarter
    if uploaded_file or st.session_state.example_dicom_path:
        if st.button("🔄 Try another image"):

            refresh_html = '''<meta http-equiv="refresh" content="0">'''
            st.markdown(refresh_html, unsafe_allow_html=True)


    # Show Example images
    if not uploaded_file and not st.session_state.example_dicom_path:
        show_example_dicoms()     

    # If file is uploaded or selected from example dataset
    if uploaded_file or st.session_state.example_dicom_path:
        dicom_data = None
        if uploaded_file: # only check file size if uploading. Avoid if using example DICOM
            if uploaded_file.size > 5 * 1024 * 1024:
                st.error("⚠️ File too large! Please upload a file smaller than 5MB.")
            else:

                # Save to temporary file
                with tempfile.NamedTemporaryFile(delete=False, suffix=".dcm") as tmp:
                    tmp.write(uploaded_file.read())
                    tmp_path = tmp.name

                # Drive DICOM logic
                try:

                    if 'deidentified_dicom' not in st.session_state:
                        dicom_data = pydicom.dcmread(tmp_path)
                        st.success("✅ File loaded successfully.")
                        st.session_state['deidentified_dicom'] = de_id_dcm(dicom_data)
                    else :
                        dicom_data = st.session_state['deidentified_dicom']

                    

                    # Display DICOM image with metadata after de-identification
                    img = Image.fromarray(dicom_data.pixel_array)
                    if img.mode != "RGB":
                        img = img.convert("RGB")
                    st.image(img)
                    
                    st.write("**Patient ID:**", dicom_data.get("PatientID", "N/A"))
                    st.write("**Modality:**", dicom_data.get("Modality", "N/A"))
                    st.write("**Study Date:**", dicom_data.get("StudyDate", "N/A"))

                except Exception as e:
                    st.error(f"❌ Failed to process DICOM file: {e}")
                    os.remove(tmp_path)

        if  st.session_state.example_dicom_path:
            example_dicom_path = st.session_state["example_dicom_path"]
            try:
                #dicom_data = pydicom.dcmread(example_dicom_path)

                if 'deidentified_dicom' not in st.session_state:
                        dicom_data = pydicom.dcmread(example_dicom_path)
                        st.success("✅ File loaded successfully.")
                        st.write("💡 No De-identification will be applied on example DICOMs. To test De-identification feature, please upload your DICOM file (.dcm).")
                        st.session_state['deidentified_dicom'] = dicom_data # No need to de-identify example DICOMs
                else :
                    dicom_data = st.session_state['deidentified_dicom']

                img = Image.fromarray(dicom_data.pixel_array)
                if img.mode != "RGB":
                    img = img.convert("RGB")
                st.image(img)

                st.success("✅ Example file read successfully.")
                st.write("**Patient ID:**", "N/A")
                st.write("**Modality:**", "N/A")
                st.write("**Study Date:**", "N/A")
                
            except Exception as e:
                st.error(f"❌ Failed to process DICOM file: {e}")



        if 'xray_classified' not in st.session_state:
            # Button to classify
            if st.button("Run AI Classification"):
                # Placeholder for backend response
                with st.spinner("Processing with AI model..."):
                    # Simulated classification result
                    dct_classification_result = classify_xray(dicom_data.pixel_array)
                    st.session_state['dct_classification_result'] = dct_classification_result
                    show_classification_result()

                    # Set session state to to drive logic
                    st.session_state['xray_classified'] = True


        else:
            # Show classification results
            show_classification_result()

            # Drive logic based on session state
            if 'action' in st.session_state:

                # Visual explanation logic
                if st.session_state['action'] == "explain_opinion":
                        if modal.is_open():
                            with modal.container():
                                with st.spinner("Generating explanation using Grad-CAM..."):
                                    # Generate Grad-CAM image
                                    heatmap = run_gradcam_on_xray(dicom_data.pixel_array, label=st.session_state['explain_opinion_label'])
                                    st.success("✅ Explanation generated")
                                    st.write("Grad-CAM Heatmap sets highlights on the part(s) of the image on which the model had the highest focus while making the classification dicision.")
                                    st.image(heatmap, caption=f"Grad-CAM Heatmap - {st.session_state['explain_opinion_label']}", use_column_width=True)

                # Find similiar X-rays logic
                if st.session_state['action'] == "show_similar_xrays":
                    if modal.is_open():
                        with modal.container():
                            with st.spinner("🔍 Fetching similar X-rays from NIH Chest X-ray Dataset..."):
                                # Get the image from the DICOM file as PiL Image
                                img = Image.fromarray(dicom_data.pixel_array)
                                if img.mode != "RGB":
                                    img = img.convert("RGB")
                                # Get filenames of similar X-rays using Azure Search AI
                                filenames = find_similar_xrays(st.session_state['explain_opinion_label'], img)
                                st.success("✅ Top similar X-rays Found")
                                for i in range(len(filenames)):
                                    filename = filenames[i]
                                    st.image(f"https://raisobotstorage.blob.core.windows.net/xray-nih-images-container/images/{filename}",
                                            caption=f"Top {i + 1} Similar X-ray | ID: {filename.split('.')[0]}")
                                    st.divider()

    
