import os
from os import path
import numpy as np
from PIL import Image
import pydicom
from pydicom.dataset import Dataset, FileDataset
import datetime

def png_to_dicom(png_folder, output_folder, patient_name="Test^Patient", patient_id="123456"):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    for filename in os.listdir(png_folder):
        if filename.lower().endswith('.png'):

            print("Converting:", filename)        
            png_path = os.path.join(png_folder, filename)
            img = Image.open(png_path).convert('L')  # Convert to grayscale
            np_img = np.array(img)

            # Create DICOM metadata
            file_meta = pydicom.Dataset()
            file_meta.MediaStorageSOPClassUID = pydicom.uid.generate_uid()
            file_meta.MediaStorageSOPInstanceUID = pydicom.uid.generate_uid()
            file_meta.ImplementationClassUID = pydicom.uid.PYDICOM_IMPLEMENTATION_UID
            file_meta.TransferSyntaxUID = pydicom.uid.ExplicitVRLittleEndian

            dt = datetime.datetime.now()
            ds = FileDataset(filename, {}, file_meta=file_meta, preamble=b"\0" * 128)

            # Set patient and image info
            ds.PatientName = patient_name
            ds.PatientID = patient_id
            ds.Modality = "OT"  # Other
            ds.StudyInstanceUID = pydicom.uid.generate_uid()
            ds.SeriesInstanceUID = pydicom.uid.generate_uid()
            ds.SOPInstanceUID = file_meta.MediaStorageSOPInstanceUID
            ds.SOPClassUID = file_meta.MediaStorageSOPClassUID

            ds.StudyDate = dt.strftime('%Y%m%d')
            ds.StudyTime = dt.strftime('%H%M%S')

            ds.Rows, ds.Columns = np_img.shape
            ds.SamplesPerPixel = 1
            ds.PhotometricInterpretation = "MONOCHROME2"
            ds.PixelRepresentation = 0
            ds.BitsStored = 8
            ds.BitsAllocated = 8
            ds.HighBit = 7
            ds.PixelData = np_img.tobytes()

            output_path = os.path.join(output_folder, filename.replace('.png', '.dcm'))
            ds.save_as(output_path)
            print(f"Saved {output_path}")

# iterate over subdirs
for i in range(1, 13):
    print(f"Processing subfolder images_{i}..")
    output_dir = path.join("XRay-Chest-NIH-dataset", "dicom", f"images_{i}")
    # Convert all PNGs in subdir
    png_to_dicom(path.join("XRay-Chest-NIH-dataset", "as_png", f"images_{i}"), output_dir)
    print(f"Finished subfolder images_{i}..")
    print("======================================")

print("All Done!")
