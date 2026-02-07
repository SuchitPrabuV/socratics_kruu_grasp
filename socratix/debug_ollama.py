import urllib3
import json

def test_ollama():
    url = "http://localhost:11434/api/generate"
    payload = {
        "model": "llama3",
        "prompt": "Hi",
        "stream": False
    }
    
    print(f"Sending request to {url}...")
    http = urllib3.PoolManager(timeout=5.0)
    try:
        resp = http.request(
            'POST',
            url,
            body=json.dumps(payload).encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )
        print("Response Status:", resp.status)
        print("Response Body:", resp.data.decode('utf-8'))
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_ollama()
