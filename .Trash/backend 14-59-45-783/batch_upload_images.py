# optimize_uploaded_images.py - 전체 코드
import boto3
import os
from dotenv import load_dotenv
from PIL import Image
import io
import requests

load_dotenv()

class ImageOptimizer:
    def __init__(self):
        self.s3 = boto3.client(
            's3',
            aws_access_key_id=os.getenv('NCP_ACCESS_KEY'),
            aws_secret_access_key=os.getenv('NCP_SECRET_KEY'),
            endpoint_url='https://kr.object.ncloudstorage.com',
            region_name='kr-standard'
        )
        self.bucket = 'recipu-bucket'
        self.base_url = f"https://kr.object.ncloudstorage.com/{self.bucket}"
    
    def optimize_image(self, image_key):
        """Object Storage의 이미지를 WebP로 변환"""
        try:
            # 이미 WebP면 스킵
            if image_key.endswith('.webp'):
                print(f"⏭️  Already WebP: {image_key}")
                return None
            
            # 원본 다운로드
            image_url = f"{self.base_url}/{image_key}"
            print(f"⬇️  Downloading: {image_key}")
            
            response = requests.get(image_url)
            img = Image.open(io.BytesIO(response.content))
            original_size = len(response.content)
            
            # RGB 변환
            if img.mode == 'RGBA':
                background = Image.new('RGB', img.size, (255, 255, 255))
                background.paste(img, mask=img.split()[3])
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            
            # 리사이징 (1920px 이하)
            if max(img.size) > 1920:
                img.thumbnail((1920, 1920), Image.Resampling.LANCZOS)
            
            # WebP 변환
            webp_output = io.BytesIO()
            img.save(webp_output, format='WEBP', quality=85, method=6)
            webp_size = len(webp_output.getvalue())
            webp_output.seek(0)
            
            # 새 파일명 생성
            webp_key = image_key.rsplit('.', 1)[0] + '.webp'
            
            # 업로드
            self.s3.upload_fileobj(
                webp_output,
                self.bucket,
                webp_key,
                ExtraArgs={
                    'ACL': 'public-read',
                    'ContentType': 'image/webp',
                    'CacheControl': 'max-age=31536000, immutable'
                }
            )
            
            webp_url = f"{self.base_url}/{webp_key}"
            reduction = (1 - webp_size/original_size) * 100
            
            print(f"✅ {image_key}")
            print(f"   {original_size/1024:.1f}KB → {webp_size/1024:.1f}KB ({reduction:.1f}% 감소)")
            print(f"   {webp_url}\n")
            
            return {
                'original': image_key,
                'webp': webp_key,
                'url': webp_url,
                'original_size_kb': original_size / 1024,
                'webp_size_kb': webp_size / 1024,
                'reduction_percent': reduction
            }
            
        except Exception as e:
            print(f"❌ {image_key}: {e}\n")
            return None
    
    def optimize_all(self, prefix='assets/'):
        """버킷의 모든 PNG/JPG를 WebP로 변환"""
        response = self.s3.list_objects_v2(
            Bucket=self.bucket,
            Prefix=prefix
        )
        
        if 'Contents' not in response:
            print("❌ 파일이 없습니다!")
            return []
        
        files = [obj['Key'] for obj in response['Contents'] 
                 if not obj['Key'].endswith('/')]
        
        print(f"📁 총 {len(files)}개 파일 발견\n")
        
        results = []
        for file_key in files:
            result = self.optimize_image(file_key)
            if result:
                results.append(result)
        
        # 통계
        if results:
            total_original = sum(r['original_size_kb'] for r in results)
            total_webp = sum(r['webp_size_kb'] for r in results)
            total_reduction = (1 - total_webp/total_original) * 100
            
            print(f"\n{'='*60}")
            print(f"🎉 최적화 완료!")
            print(f"총 {len(results)}개 파일")
            print(f"원본: {total_original:.1f}KB")
            print(f"WebP: {total_webp:.1f}KB")
            print(f"절감: {total_reduction:.1f}% ({total_original - total_webp:.1f}KB)")
            print(f"{'='*60}")
        
        return results

if __name__ == '__main__':
    optimizer = ImageOptimizer()
    results = optimizer.optimize_all('assets/')
    
    if results:
        print("\n=== WebP 이미지 URL ===")
        print("export const RECIPE_IMAGES = {")
        for r in results:
            name = r['webp'].split('/')[-1].rsplit('.', 1)[0]
            print(f"  '{name}': '{r['url']}',")
        print("};")