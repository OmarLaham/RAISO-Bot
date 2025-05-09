import streamlit as st
from PIL import Image
import pydicom
import tempfile
import os
from xray_classifier import classify_xray
from grad_cam import run_gradcam_on_xray

def show_classification_result():
    st.success("✅ Classification Complete")
    # Print results
    dct_classification_result = st.session_state['dct_classification_result'] # get values from session_state
    for label, prob in dct_classification_result.items():
                        col_class, col_confidence, col_operations = st.columns(3)
                        with col_class:
                            st.write(f"Class: {label}")
                        with col_confidence:
                            st.write(f"Confidence: {prob:.2f}")
                        with col_operations:
                            if st.button("💡 Visual Explanation", key=f"btn_explain_opinion_{label}"):
                                st.session_state['action'] = "explain_opinion"
                                st.session_state['explain_opinion_label'] = label

# Set page config
st.set_page_config(page_title="Radiology AI Assistant", layout="centered")

# Title
st.title("🧠 Radiology AI Assistant")

# File uploader
uploaded_file = st.file_uploader("Upload a DICOM file (Max 5MB)", type=["dcm"])

if uploaded_file:
    if uploaded_file.size > 5 * 1024 * 1024:
        st.error("⚠️ File too large! Please upload a file smaller than 5MB.")
    else:
        # Save to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".dcm") as tmp:
            tmp.write(uploaded_file.read())
            tmp_path = tmp.name

        # Show basic DICOM info or image preview
        try:
            dicom_data = pydicom.dcmread(tmp_path)
            st.success("✅ File uploaded and read successfully.")
            st.write("**Patient ID:**", dicom_data.get("PatientID", "N/A"))
            st.write("**Modality:**", dicom_data.get("Modality", "N/A"))
            st.write("**Study Date:**", dicom_data.get("StudyDate", "N/A"))

            # # Optional: Convert pixel data to image
            # if hasattr(dicom_data, "pixel_array"):
            #     st.image(dicom_data.pixel_array, caption="DICOM Preview", use_column_width=True)
        except Exception as e:
            st.error(f"❌ Failed to process DICOM file: {e}")
            os.remove(tmp_path)

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

                # Post-classification options
                st.markdown("---")
                st.subheader("Next Steps")

                col1, col2 = st.columns(2)

                with col1:
                    if st.button("📝 Generate Report"):
                        st.session_state['action'] = "generate_report"

                with col2:
                    if st.button("🔍 Show Top 3 Similar X-rays"):
                        st.session_state['action'] = "show_similar"


        else:
            # Show classification results
            show_classification_result()

            # Drive logic based on session state
            if 'action' in st.session_state:
                print("action in state")
                if st.session_state['action'] == "explain_opinion":
                    print("explain opinion in state")
                    with st.spinner("Generating explanation using Grad-CAM..."):
                        # Generate Grad-CAM image
                        heatmap = run_gradcam_on_xray(dicom_data.pixel_array, label=st.session_state['explain_opinion_label'])
                        st.success("✅ Explanation generated")
                        st.image(heatmap, caption=f"Grad-CAM Heatmap - {st.session_state['explain_opinion_label']}", use_column_width=True)

                if st.session_state['action'] == "generate_report":
                    with st.spinner("Generating report using ML..."):
                        # Placeholder
                        st.success("✅ Report generated")
                        st.text_area("Radiology Report", "Findings indicate signs of pneumonia...", height=200)

                elif st.session_state['action'] == "show_similar":
                    with st.spinner("Fetching similar X-rays from Azure..."):
                        # Placeholder images or results
                        st.success("✅ Similar X-rays Found")
                        for i in range(1, 4):
                            st.image(f"https://via.placeholder.com/300x300.png?text=Similar+X-ray+{i}",
                                        caption=f"Top {i} Similar X-ray")