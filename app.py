from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import subprocess
import json

app = Flask(__name__)
CORS(app)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/get_info', methods=['POST'])
def get_info():
    data = request.json
    url = data.get('url')
    
    if not url:
        return jsonify({'error': 'URL প্রদান করা প্রয়োজন'}), 400

    try:
        # yt-dlp কমান্ড রান করে JSON ফরম্যাটে তথ্য নেওয়া
        result = subprocess.run(
            ['yt-dlp', '-J', '--no-warnings', url],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode != 0:
            return jsonify({'error': 'ভিডিও তথ্য পাওয়া যায়নি। লিংকটি সঠিক কিনা চেক করুন।'}), 400

        info = json.loads(result.stdout)
        formats = info.get('formats', [])
        
        best_video = None
        best_audio = None

        # সেরা ভিডিও এবং অডিও ফরম্যাট খোঁজা
        for f in formats:
            if f.get('vcodec') != 'none' and f.get('acodec') == 'none' and f.get('url'):
                best_video = f
            elif f.get('acodec') != 'none' and f.get('vcodec') == 'none' and f.get('url'):
                best_audio = f

        # যদি আলাদা ভিডিও/অডিও না পাওয়া যায়, তবে ডিফল্ট ফরম্যাট নেওয়া
        if not best_video:
            best_video = info

        response = {
            'title': info.get('title', 'Unknown Title'),
            'thumbnail': info.get('thumbnail', ''),
            'uploader': info.get('uploader', 'Unknown'),
            'platform': info.get('extractor', 'Unknown').capitalize(),
            'video_url': best_video.get('url') if best_video else None,
            'audio_url': best_audio.get('url') if best_audio else None
        }
        return jsonify(response)

    except subprocess.TimeoutExpired:
        return jsonify({'error': 'রিquest টাইমআউট হয়েছে। আবার চেষ্টা করুন।'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # লোকালি রান করার জন্য
    app.run(host='0.0.0.0', port=5000, debug=True)
