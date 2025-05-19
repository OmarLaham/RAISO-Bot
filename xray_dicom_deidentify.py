import os
from io import BytesIO
import json
from datetime import datetime
import requests
import streamlit as st
import pydicom
#from deid.dicom import DicomCleaner
from pydicom.uid import generate_uid
from pydicom.tag import Tag
from pydicom.dataelem import DataElement


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


def de_id_dcm(dicom_data):

    # Deidentify DICOM using on-premise de-identification (for on-premises use)
    with st.spinner("🔐 De-identifying DICOM metadata before uploading for advanced de-identification on the cloud.."):
        dicom_data = de_id_dcm_on_premise(dicom_data)
        st.success("✅ On-premise metadata de-identification complete.")

    # # Deidentify DICOM using Azure DICOM De-identification service (advanced on cloud)
    # with st.spinner("🛡️ De-identifying DICOM using Azure DICOM De-identification service..."):
    #     dicom_data = de_id_dcm_on_azure(dicom_data)
    #     st.success("✅ Azure de-identification complete.")
        
    return dicom_data