import os
from io import BytesIO
import json
from datetime import datetime
import requests
import streamlit as st
import pydicom
from pydicom.uid import generate_uid
from pydicom.tag import Tag
from pydicom.dataelem import DataElement
from pydicom.datadict import dictionary_VR
#from dicom_anonymizer import anonymize_dataset
from azure.identity import ClientSecretCredential
#from azure.healthcareapis import DicomServiceClient  # hypothetical, replace with actual client if exists


def load_rules(rules_path):
    with open(rules_path, 'r') as f:
        return json.load(f)

def anonymize_dataset(ds, rules):
    # Remove tags
    for tag_str in rules.get("remove", {}).get("tags", []):
        try:
            # if isinstance(tag_str, str) and "," in tag_str:
            tag_tuple = tuple(int(x.strip(), 16) for x in tag_str.strip("()").split(","))
            #print("tage:", tag_str, " - tag_tuple:", tag_tuple)
            tag = Tag(tag_tuple)

            if tag in ds:
                del ds[tag]
        except Exception as e:
            print(f"Could not remove tag {tag_str}: {e}")

    # Replace values
    for tag, value in rules.get("replace", {}).get("tags", {}).items():
        try:

            #if isinstance(tag, str) and "," in tag:
            tag_tuple = tuple(int(x.strip(), 16) for x in tag.strip("()").split(","))
            tag = Tag(tag_tuple)

            # Determine value
            if value == "auto":
                new_value = generate_uid()
            elif value == "ANON":
                new_value = "ANON"
            else:
                new_value = value # Keep it as it's

            # Determine VR (Value Representation) from existing tag if possible
            if tag in ds:
                vr = ds[tag].VR
            else:
                # Fallback: use 'LO' (Long String) for general text
                vr = 'LO'

            # Create proper DataElement
            ds[tag] = DataElement(tag, vr, new_value)

        except Exception as e:
            print(f"Could not replace tag {tag}: {e}")

    ## Force SOP Class UID to X-ray (CR)
    #ds[(0x0008, 0x0016)] = "1.2.840.10008.5.1.4.1.1.1" # SOP Class UID = Computed Radiography Image Storage

    return ds

def de_id_dcm_on_premise(dicom_data):

    # Load rules
    rules = load_rules(os.path.join("config", "xray_deidentification_rules.json"))

    # Apply anonymization
    deidentified_ds = anonymize_dataset(dicom_data, rules)

    return deidentified_ds

# Get Azure access token and cache it
@st.cache_resource
def get_token():
        
        # Authenticate securely
        credential = ClientSecretCredential(  # Azure AD authentication is required for DICOM de-identification service for compliance and GDPR, ...
            tenant_id = st.secrets["AZURE_TENANT_ID"],
            client_id = st.secrets["AZURE_CLIENT_ID"],
            client_secret = st.secrets["AZURE_CLIENT_SECRET"]
        )

        token = credential.get_token("https://dicom.healthcareapis.azure.com/.default")
        return token.token
        

def de_id_dcm_on_azure(dicom_data):

    # Get Azure access token
    access_token = get_token()
    # Check if token is None
    if access_token is None:
        raise Exception("Failed to obtain Azure access token.")

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/octet-stream",  # Sending binary DICOM
        "Accept": "application/dicom"
    }
    

    # Convert pydicom dataset to binary
    buffer = BytesIO()
    dicom_data.save_as(buffer)
    buffer.seek(0)
    
    # Call de-ID API (inline, real-time)
    azure_de_id_endpoint = st.secrets['AZURE_DEID_ENDPOINT']
    url = f"{azure_de_id_endpoint}/v1/de-identify"
    response = requests.post(url, headers=headers, data=buffer.getvalue())

    if response.status_code != 200:
        raise Exception(f"De-identification failed: {response.status_code} - {response.text}")
    

    # Convert response DICOM to pydicom dataset
    de_id_dcm = pydicom.dcmread(BytesIO(response.content))
    return de_id_dcm


def de_id_dcm(dicom_data):

    # Deidentify DICOM using on-premise de-identification (for on-premises use)
    with st.spinner("🔐 De-identifying DICOM before uploading for advanced de-identification on the cloud.."):
        dicom_data = de_id_dcm_on_premise(dicom_data)
        st.success("✅ DICOM on-premise de-identification complete.")
        
    st.write("**De-identification on Azure**")

    # Deidentify DICOM using Azure DICOM De-identification service (advanced on cloud)
    with st.spinner("🛡️ De-identifying DICOM using Azure DICOM De-identification service..."):
        dicom_data = de_id_dcm_on_azure(dicom_data)
        st.success("✅ DICOM on Azure de-identification complete.")
        
    return dicom_data