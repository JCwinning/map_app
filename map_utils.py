import os
import requests
import streamlit as st
from dotenv import load_dotenv
import time

# Load environment variables
load_dotenv()

# Constants
GAODE_API_KEY = os.getenv('GAODE_API_KEY')

def search_shops(keyword, city=None):
    """
    Search for shops using Gaode's place text search API.
    
    Args:
        keyword (str): The search keyword (e.g., shop name).
        city (str, optional): The city to restrict the search to.
        
    Returns:
        list: A list of dictionaries containing shop details (name, address, location, type).
    """
    url = 'https://restapi.amap.com/v3/place/text'
    params = {
        'key': GAODE_API_KEY,
        'keywords': keyword,
        'output': 'json'
    }
    if city:
        params['city'] = city
        
    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        if data.get('status') == '1' and data.get('pois'):
            results = []
            for poi in data['pois'][:10]:  # Increased to top 10 results
                location = poi.get('location', '').split(',')
                if len(location) == 2:
                    # Extract city from adname (administrative area name) or cityname
                    city = poi.get('cityname') or poi.get('adname', '')
                    results.append({
                        'name': poi.get('name', ''),
                        'address': poi.get('address', ''),
                        'longitude': float(location[0]),
                        'latitude': float(location[1]),
                        'type': poi.get('type', '').split(';')[0] if poi.get('type') else '',
                        'city': city
                    })
            return results
        return []
    except Exception as e:
        # Log error to Streamlit if running in that context, or just return empty
        if hasattr(st, 'error'):
            st.error(f"搜索出错: {str(e)}")
        return []

import hashlib
import re

def upload_shop_image(supabase, file, user_id, shop_id=None):
    """
    Upload an image to Supabase Storage and return the public URL.
    
    Args:
        supabase: The Supabase client object.
        file: The file object from st.file_uploader.
        user_id: The user's ID for folder organization.
        shop_id: Optional shop ID (or name hash) to organize files.
        
    Returns:
        str: Public URL of the uploaded image, or None if failed.
    """
    try:
        bucket_name = 'shopphoto'
        
        # Sanitize filename: ASCII only, remove spaces/special chars
        # Or even better, just keep extension + timestamp to be super safe
        file_ext = os.path.splitext(file.name)[1]
        if not file_ext:
            file_ext = ""
        # Create a safe filename with timestamp
        safe_filename = f"{int(time.time())}{file_ext}"

        # Construct path
        if shop_id:
            # Hash the shop name to create a safe folder name
            shop_folder = hashlib.md5(str(shop_id).encode('utf-8')).hexdigest()
            path = f"{user_id}/{shop_folder}/{safe_filename}"
        else:
            path = f"{user_id}/{safe_filename}"
            
        # Upload
        content = file.getvalue()
        # file.type is like 'image/jpeg'
        options = {"content-type": file.type}
        
        # Upsert=true in case of weird collision, though timestamp prevents it usually
        res = supabase.storage.from_(bucket_name).upload(
            path=path,
            file=content,
            file_options={"content-type": file.type, "upsert": "false"}
        )
        
        # Get Public URL
        public_url = supabase.storage.from_(bucket_name).get_public_url(path)
        return public_url
        
    except Exception as e:
        if hasattr(st, 'error'):
            st.error(f"图片上传失败: {str(e)}")
        return None

def delete_shop_image(supabase, image_url):
    """
    Delete an image from Supabase Storage given its public URL.
    
    Args:
        supabase: The Supabase client object.
        image_url: The full public URL of the image.
        
    Returns:
        bool: True if deletion request was sent successfully (or parsing succeeded), False otherwise.
    """
    try:
        bucket_name = 'shopphoto'
        
        # URL structure: https://<project>.supabase.co/storage/v1/object/public/<bucket>/<path>
        # We need the <path> part.
        
        # Check if URL belongs to our bucket
        target_segment = f"/public/{bucket_name}/"
        if target_segment not in image_url:
            # Maybe it's not hosted on Supabase or different bucket?
            return False
            
        file_path = image_url.split(target_segment)[1]
        
        # Decode URL encoding if necessary
        from urllib.parse import unquote
        file_path = unquote(file_path)

        supabase.storage.from_(bucket_name).remove([file_path])
        return True
        
    except Exception as e:
        if hasattr(st, 'error'):
            st.error(f"删除云端图片失败: {str(e)}")
        return False

def get_signed_image_url(supabase, image_url, expiration=3600):
    """
    Generate a temporary signed URL for a stored image.
    Works for both Public and Private buckets by signing the path extracted from the URL.
    
    Args:
        supabase: The Supabase client object.
        image_url: The stored public URL or path.
        expiration: Time in seconds for the link to remain valid.
        
    Returns:
        str: A valid signed URL, or the original URL if signing fails.
    """
    try:
        bucket_name = 'shopphoto'
        target_segment = f"/public/{bucket_name}/"
        
        # Extract path
        if target_segment in image_url:
            file_path = image_url.split(target_segment)[1]
            from urllib.parse import unquote
            file_path = unquote(file_path)
        else:
            # If it doesn't look like a standard public URL, maybe it's just a path? 
            # Or maybe it's already a different format. 
            # We assume if it's not matching our bucket pattern, we can't sign it easily from just the string.
            # But let's be safe: return original.
            return image_url
            
        # Create Signed URL
        # Supabase Python client returns a dict with 'signedURL' (camelCase) usually.
        # But we must treat the response carefully.
        res = supabase.storage.from_(bucket_name).create_signed_url(file_path, expiration)
        
        # Check response structure
        if isinstance(res, dict) and 'signedURL' in res:
            # The signedURL returned is usually a relative path "/storage/v1/object/sign/..." 
            # or a full URL depending on client version.
            s_url = res['signedURL']
            if s_url.startswith('/'):
               return f"{supabase.supabase_url}/storage/v1{s_url}"
            return s_url
        elif isinstance(res, str):
            return res
        else:
            return image_url
            
    except Exception:
        # If generation fails (e.g. offline, or auth error), return original so it might still work if public
        return image_url
