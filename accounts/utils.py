import base64
import binascii

def decode_base64(data):
    """Decode Base64 string to bytes, fixing padding if needed."""
    try:
        data += "=" * (-len(data) % 4)
        return base64.b64decode(data)
    except binascii.Error:
        return None