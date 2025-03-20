from main import app
import uvicorn
import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))  # Changed default port to 8000
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)