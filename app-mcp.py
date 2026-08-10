import os
import uuid
import base64
import httpx
from fastmcp import FastMCP

mcp = FastMCP(name="Face Recognizer MCP")

FACE_RECOGNIZER_URL = os.environ.get("FACE_RECOGNIZER_URL", "http://localhost:5000/facerecognizer")

@mcp.tool()
def detect_faces(image_base64: str) -> str:
    """Detect faces in an image and return their bounding box coordinates.

    Args:
        image_base64: A base64-encoded string representing the target image.
                      Accepts both raw base64 data and Data URL format
                      (e.g., 'data:image/jpeg;base64,...').

    Returns:
        JSON string containing detected face positions (top, right, bottom, left).
    """
    if "," in image_base64:
        image_base64 = image_base64.split(",", 1)[1]

    temp_filename = f"/tmp/{uuid.uuid4()}.jpg"
    
    try:
        image_data = base64.b64decode(image_base64)
        with open(temp_filename, "wb") as f:
            f.write(image_data)

        # Send POST to Flask API (localhost:5000)
        with open(temp_filename, "rb") as f:
            files = {"img": ("input.jpg", f, "image/jpeg")}
            response = httpx.post(FACE_RECOGNIZER_URL, files=files, timeout=30.0)
            response.raise_for_status()
            return response.text

    except Exception as e:
        return f"Error: {str(e)}"

    finally:
        if os.path.exists(temp_filename):
            os.remove(temp_filename)

if __name__ == "__main__":
    mcp.run(transport="sse", host="0.0.0.0", port=5001)
