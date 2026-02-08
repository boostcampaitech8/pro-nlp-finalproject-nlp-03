# convert_png_to_transparent_webp.py
import hashlib
import hmac
import base64
import requests
from email.utils import formatdate
import os
from PIL import Image
import io
from dotenv import load_dotenv

load_dotenv()

class NCPObjectStorageV1:
    def __init__(self, access_key, secret_key, bucket_name):
        self.access_key = access_key
        self.secret_key = secret_key
        self.bucket_name = bucket_name
        self.endpoint = "https://kr.object.ncloudstorage.com"
    
    def _make_signature_v1(self, method, path, content_type=''):
        timestamp = formatdate(timeval=None, localtime=False, usegmt=True)
        string_to_sign = f"{method}\n\n{content_type}\n{timestamp}\n/{self.bucket_name}{path}"
        signature = base64.b64encode(
            hmac.new(
                self.secret_key.encode('utf-8'),
                string_to_sign.encode('utf-8'),
                hashlib.sha1
            ).digest()
        ).decode('utf-8')
        return signature, timestamp
    
    def list_objects(self, prefix=''):
        """버킷의 파일 목록 조회"""
        url = f"{self.endpoint}/{self.bucket_name}/"
        if prefix:
            url += f"?prefix={prefix}"
        
        response = requests.get(url)
        if response.status_code == 200:
            # XML 파싱 간단하게
            import xml.etree.ElementTree as ET
            root = ET.fromstring(response.content)
            
            files = []
            for content in root.findall('.//{http://s3.amazonaws.com/doc/2006-03-01/}Contents'):
                key = content.find('{http://s3.amazonaws.com/doc/2006-03-01/}Key').text
                files.append(key)
            return files
        return []
    
    def download_file(self, object_key):
        url = f"{self.endpoint}/{self.bucket_name}/{object_key}"
        response = requests.get(url)
        if response.status_code == 200:
            return response.content
        return None
    
    def upload_file(self, file_data, object_key, content_type='image/webp'):
        path = f"/{object_key}"
        signature, timestamp = self._make_signature_v1('PUT', path, content_type)
        
        headers = {
            'Host': f'{self.bucket_name}.kr.object.ncloudstorage.com',
            'Date': timestamp,
            'Authorization': f'AWS {self.access_key}:{signature}',
            'Content-Type': content_type,
        }
        
        url = f"https://{self.bucket_name}.kr.object.ncloudstorage.com{path}"
        response = requests.put(url, headers=headers, data=file_data)
        
        if response.status_code in [200, 201]:
            return f"{self.endpoint}/{self.bucket_name}/{object_key}"
        return None
    
    def delete_file(self, object_key):
        path = f"/{object_key}"
        signature, timestamp = self._make_signature_v1('DELETE', path)
        
        headers = {
            'Host': f'{self.bucket_name}.kr.object.ncloudstorage.com',
            'Date': timestamp,
            'Authorization': f'AWS {self.access_key}:{signature}',
        }
        
        url = f"https://{self.bucket_name}.kr.object.ncloudstorage.com{path}"
        response = requests.delete(url, headers=headers)
        return response.status_code == 204

def convert_to_webp_with_transparency(image_data):
    """이미지를 WebP로 변환 (투명 배경 유지)"""
    img = Image.open(io.BytesIO(image_data))
    
    # 투명도 유지
    # if img.mode == 'P':
    #     img = img.convert('RGBA')
    # elif img.mode not in ['RGB', 'RGBA']:
    #     img = img.convert('RGBA' if 'transparency' in img.info else 'RGB')
    
    # 리사이징
    if max(img.size) > 1920:
        img.thumbnail((1920, 1920), Image.Resampling.LANCZOS)
    
    # WebP로 저장 (투명도 유지)
    output = io.BytesIO()
    img.save(output, format='WEBP', quality=85, method=6, lossless=False)
    return output.getvalue(), img.mode

def main():
    ACCESS_KEY = os.getenv('NCP_ACCESS_KEY')
    SECRET_KEY = os.getenv('NCP_SECRET_KEY')
    BUCKET_NAME = 'recipu-bucket'
    
    storage = NCPObjectStorageV1(ACCESS_KEY, SECRET_KEY, BUCKET_NAME)
    
    print("🔍 PNG 파일 검색 중...\n")
    
    # assets/ 폴더의 모든 PNG 파일 찾기
    all_files = storage.list_objects('assets/')
    png_files = [f for f in all_files if f.endswith('.png')]
    
    if not png_files:
        print("❌ PNG 파일이 없습니다!")
        return
    
    print(f"📁 총 {len(png_files)}개 PNG 파일 발견\n")
    
    results = []
    
    for idx, png_key in enumerate(png_files, 1):
        try:
            print(f"[{idx}/{len(png_files)}] {png_key}")
            
            # PNG 다운로드
            print(f"  ⬇️  다운로드 중...")
            image_data = storage.download_file(png_key)
            
            if not image_data:
                print(f"  ❌ 다운로드 실패\n")
                continue
            
            original_size = len(image_data)
            
            # 투명 배경 유지하면서 WebP 변환
            print(f"  🔄 투명 WebP 변환 중...")
            webp_data, img_mode = convert_to_webp_with_transparency(image_data)
            webp_size = len(webp_data)
            
            # WebP 업로드
            webp_key = png_key.rsplit('.', 1)[0] + '.webp'
            print(f"  ⬆️  업로드 중... ({webp_key})")
            url = storage.upload_file(webp_data, webp_key, 'image/webp')
            
            if url:
                # 원본 PNG 삭제
                print(f"  🗑️  원본 PNG 삭제 중...")
                storage.delete_file(png_key)
                
                reduction = (1 - webp_size/original_size) * 100
                has_transparency = img_mode == 'RGBA'
                
                print(f"  ✅ 완료: {original_size/1024:.1f}KB → {webp_size/1024:.1f}KB ({reduction:.1f}% 감소)")
                print(f"  투명도: {'✓' if has_transparency else '✗'} (모드: {img_mode})")
                print(f"  📎 {url}\n")
                
                results.append({
                    'name': webp_key.split('/')[-1].rsplit('.', 1)[0],
                    'url': url,
                    'has_transparency': has_transparency,
                    'original_size_kb': original_size / 1024,
                    'webp_size_kb': webp_size / 1024,
                    'reduction_percent': reduction
                })
            
        except Exception as e:
            print(f"  ❌ 오류: {e}\n")
    
    # 통계
    if results:
        transparent_count = sum(1 for r in results if r['has_transparency'])
        total_original = sum(r['original_size_kb'] for r in results)
        total_webp = sum(r['webp_size_kb'] for r in results)
        total_reduction = (1 - total_webp/total_original) * 100
        
        print(f"\n{'='*60}")
        print(f"🎉 변환 완료!")
        print(f"총 {len(results)}개 파일")
        print(f"투명 배경: {transparent_count}개 / {len(results)}개")
        print(f"원본 PNG: {total_original:.1f}KB")
        print(f"WebP: {total_webp:.1f}KB")
        print(f"절감: {total_reduction:.1f}% ({total_original - total_webp:.1f}KB)")
        print(f"원본 PNG {len(results)}개 삭제 완료")
        print(f"{'='*60}")
        
        print("\n=== 투명 WebP 이미지 URL ===")
        print("export const RECIPE_IMAGES = {")
        for r in results:
            transparency = "✓" if r['has_transparency'] else "✗"
            print(f"  '{r['name']}': '{r['url']}',  // 투명도: {transparency}")
        print("};")

if __name__ == '__main__':
    main()