import time
import urllib.request

time.sleep(3)
try:
    response = urllib.request.urlopen('http://localhost:8000/docs')
    print('✓ Backend is running')
except Exception as e:
    print(f'✗ Backend is not running: {e}')
