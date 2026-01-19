import re
import requests
import gdown
import os

class GoogleDriveDownloader:
    """Helper to download files from Google Drive"""
    
    @staticmethod
    def extract_file_id(url: str) -> str:
        """
        Extract file ID from Google Drive URL
        
        Args:
            url: Google Drive URL (view or share link)
            
        Returns:
            extracted file ID or None
        """
        # Patterns for different Drive URL formats
        patterns = [
            r'/file/d/([a-zA-Z0-9_-]+)',
            r'id=([a-zA-Z0-9_-]+)',
            r'/open\?id=([a-zA-Z0-9_-]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
                
        return None

    @staticmethod
    def download_file(url: str, output_path: str) -> bool:
        """
        Download file from Google Drive URL
        
        Args:
            url: Google Drive URL
            output_path: Path to save the downloaded file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            file_id = GoogleDriveDownloader.extract_file_id(url)
            
            if not file_id:
                print(f"❌ Could not extract file ID from URL: {url}")
                return False
                
            # Construct download URL
            download_url = f'https://drive.google.com/uc?id={file_id}'
            
            print(f"  Downloading from Drive (ID: {file_id})...")
            
            # Using gdown for robust drive downloading
            try:
                # Silent gdown is preferred usually but we want logs here
                gdown.download(id=file_id, output=output_path, quiet=False, fuzzy=True)
                
                if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                    return True
                else:
                     print("❌ Download extracting failed (empty file)")
                     return False
                     
            except Exception as e:
                print(f"⚠️ gdown failed ({str(e)}), trying direct requests...")
                
                # Fallback to requests (often restricted for large files without confirm token)
                response = requests.get(download_url, stream=True)
                if response.status_code == 200:
                    with open(output_path, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)
                    return True
                else:
                     print(f"❌ HTTP Download failed: {response.status_code}")
                     return False

        except Exception as e:
            print(f"❌ Download error: {str(e)}")
            return False
