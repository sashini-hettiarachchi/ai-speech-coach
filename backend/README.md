# Speech Coach Flask App

## Setup Instructions

1. **Create and activate a virtual environment:**
   use python 3.11
   ```zsh
   python3 -m venv venv
   source venv/bin/activate
   ```

2. **Install dependencies:**
   ```zsh
   pip install -r requirements.txt
   ```

3. **Set environment variables:**
   - Edit the `.env` file to set your `SECRET_KEY` and other settings as needed.

4. **Run the Flask app:**
   ```zsh
   flask run
   ```
   ```zsh
   python3 app.py
   ```
   The app will be available at http://127.0.0.1:5005/

## Project Structure

- `app.py`: Main Flask application
- `utils/`: Utility modules for speech analysis
- `uploads/`: Uploaded audio files
- `test_data/`: Test audio files

## Sample Request

To analyze an audio file, use the following sample `curl` command:

```bash
curl -X POST http://localhost:5005/api/v1/analyze \
  -F "file=@/path/to/your/audiofile.wav"
```
Replace `/path/to/your/audiofile.wav` with the path to your audio file.

## Notes

- Do not commit your `.env` file or `venv/` folder to version control.
- For development, the app runs in debug mode by default.

---

## Running LLaMA Model with Docker

If you want to run a LLaMA model as an API server, you can use Ollama.

### Using Ollama

1. **Start Ollama in Docker:**
   ```bash
   docker run -d --name ollama -p 11434:11434 ollama/ollama
   ```

2. **Pull a LLaMA model:**
   ```bash
   docker exec -it ollama ollama pull llama2
   ```

This will set up an HTTP endpoint for LLaMA at port `11434`.

