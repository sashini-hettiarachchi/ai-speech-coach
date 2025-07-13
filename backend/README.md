# Speech Coach Flask App

## Setup Instructions

1. **Create and activate a virtual environment:**
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
   The app will be available at http://127.0.0.1:5000/

## Project Structure
- `app.py`: Main Flask application
- `utils/`: Utility modules for speech analysis
- `uploads/`: Uploaded audio files
- `test_data/`: Test audio files

## Sample Request

To analyze an audio file, use the following sample `curl` command:

```bash
curl -X POST http://localhost:5000/analyze \
  -F "file=@/path/to/your/audiofile.wav"
```
```bash
curl -X POST http://localhost:5000/api/v1/analyze
```
Replace `/path/to/your/audiofile.wav` with the path to your audio file.

## Notes
- Do not commit your `.env` file or `venv/` folder to version control.
- For development, the app runs in debug mode by default.

---

