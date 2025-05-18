import os
from io import BytesIO
import json
import requests
import streamlit as st
import pydicom
from pydicom.uid import generate_uid
from dicom_anonymizer import anonymize_dataset
from azure.identity import ClientSecretCredential
from azure.healthcareapis import DicomServiceClient  # hypothetical, replace with actual client if exists


def load_rules(rules_path):
    with open(rules_path, 'r') as f:
        return json.load(f)

def anonymize_dataset(ds, rules):
    # Remove tags
    for tag in rules.get("remove", []):
        if tag in ds:
            del ds[tag]

    # Replace values
    for tag, value in rules.get("replace", {}).items():
        if value == "auto":
            # Generate a new UID
            ds[tag] = generate_uid()
        else:
            ds[tag] = value

    return ds

def dicom_deidentify_on_premise(dicom_data):

    # Load rules
    rules = load_rules(os.path.join("config", "xray_deidentification_rules.json"))

    # Apply anonymization
    deidentified_ds = anonymize_dataset(dicom_data, rules)

    return deidentified_ds

def dicom_deidentify_on_azure(dicom_data):

    # Authenticate securely
    credential = ClientSecretCredential(  # Azure AD authentication is required for DICOM de-identification service for compliance and GDPR, ...
        tenant_id = st.secrets("TENANT_ID"),
        client_id = st.secrets("CLIENT_ID"),
        client_secret = st.secrets("CLIENT_SECRET")
    )

    # Get access token for DICOM service
    token = credential.get_token("https://dicom.healthcareapis.azure.com/.default").token
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/dicom"
    }

    # Convert pydicom dataset to binary
    buffer = BytesIO()
    dicom_data.save_as(buffer)
    buffer.seek(0)
    
    # Call de-ID API (inline, real-time)
    azure_dicom_endpoint = st.secrets('AZURE_DICOM_ENDPOINT')
    url = f"{azure_dicom_endpoint}/v1/de-identify"
    response = requests.post(url, headers=headers, data=buffer.getvalue())

    if response.status_code != 200:
        raise Exception(f"De-identification failed: {response.status_code} - {response.text}")

    # Convert response DICOM to pydicom dataset
    deidentified_ds = pydicom.dcmread(BytesIO(response.content))
    return deidentified_ds