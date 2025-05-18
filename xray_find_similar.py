import streamlit as st
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
from xray_embedder import embed_xray

def find_similar_xrays(label: str, img, k:int=3):
    """
    Find similar X-ray images based on the provided label and DICOM pixel array using Azure AI Search.

    Args:
        label (str): The label of the X-ray image.
        img (Image): The Image that represents the pixel array of the DICOM image.
        k (int): The number of similar images to retrieve. Default is 3.

    Returns:
        list: A list of filenames of top similar X-ray images.
    """

    # Embed X-ray
    embedding_vector = embed_xray(img)

    # Connect to Azure Search AI using SDK
    client = SearchClient(
        endpoint = st.secrets["AZURE_AI_SEARCH_ENDPOINT"],
        index_name = st.secrets["AZURE_AI_SEARCH_INDEX_NAME"],
        credential = AzureKeyCredential(st.secrets["AZURE_API_KEY"])
    )

    
    results = client.search(
        search_text = "",  # Required, even if you're only using vector search
        vector_queries = [
            {
                "vector": embedding_vector,
                "fields": "embedding",
                "k": k,
                "kind": "vector"
            }
        ],
        filter = f"labels/any(t: t eq '{label}')", # filter for documents where labels field contains the label
        select=["filename"]
    )

    print("FUFU")
    print(results)

    filenames = [doc['filename'] for doc in results]
    return filenames



