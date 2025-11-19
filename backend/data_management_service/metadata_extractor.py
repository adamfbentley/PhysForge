import h5py
import json
import logging
from typing import Dict, Any
from fastapi import UploadFile
import os
import io
import hashlib

logger = logging.getLogger(__name__)

async def extract_metadata(file: UploadFile) -> Dict[str, Any]:
    metadata = {
        "filename": file.filename,
        "size_bytes": file.size,
        "mime_type": file.content_type,
        "extracted_data": {}
    }

    file_content = await file.read()
    file.file.seek(0) # Reset file pointer for subsequent reads if any

    # Attempt to extract HDF5 metadata
    if file.filename and (file.filename.endswith('.h5') or file.filename.endswith('.hdf5')):
        try:
            # h5py requires a file-like object that supports seek and read
            # For in-memory bytes, we can use io.BytesIO
            with h5py.File(io.BytesIO(file_content), 'r') as f:
                h5_data = {}
                def visitor_func(name, obj):
                    if isinstance(obj, h5py.Dataset):
                        h5_data[name] = {
                            "shape": obj.shape,
                            "dtype": str(obj.dtype),
                            "attributes": dict(obj.attrs)
                        }
                    elif isinstance(obj, h5py.Group):
                        h5_data[name] = {"attributes": dict(obj.attrs)}
                f.visititems(visitor_func)
                metadata["extracted_data"]["hdf5_structure"] = h5_data
                logger.info(f"Extracted HDF5 metadata for {file.filename}")
        except Exception as e:
            logger.warning(f"Could not extract HDF5 metadata from {file.filename}: {e}")
            metadata["extracted_data"]["error"] = f"HDF5 parsing failed: {e}"
    elif file.content_type == "application/json":
        try:
            json_string = file_content.decode('utf-8')
            json_data = json.loads(json_string)

            # SEC-DMS-001: Sanitize/truncate JSON content preview to prevent data exposure
            MAX_PREVIEW_LENGTH = 500 # characters
            truncated = False
            if len(json_string) > MAX_PREVIEW_LENGTH:
                json_preview = json_string[:MAX_PREVIEW_LENGTH] + "..."
                truncated = True
            else:
                json_preview = json_string

            metadata["extracted_data"]["json_content_preview"] = json_preview
            metadata["extracted_data"]["json_content_preview_truncated"] = truncated
            metadata["extracted_data"]["json_content_hash_sha256"] = hashlib.sha256(file_content).hexdigest()
            
            logger.info(f"Extracted JSON metadata for {file.filename}")
        except json.JSONDecodeError as e:
            logger.warning(f"Could not extract JSON metadata from {file.filename}: {e}")
            metadata["extracted_data"]["error"] = f"JSON parsing failed: {e}"
    else:
        # Generic metadata for other file types
        metadata["extracted_data"]["file_type_info"] = f"No specific metadata extractor for {file.content_type}"
        logger.info(f"No specific metadata extractor for {file.content_type} for {file.filename}")

    return metadata
