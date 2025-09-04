# Video Automation Pipeline

This project provides a Django-based API and command-line pipeline for watermarking, splitting, and combining videos with an intro.

## Prerequisites

- Python 3.8+
- FFmpeg installed and available in your PATH
- Google Drive API credentials (see `client_secrets.json` and `service_accounts.json`)

## Installation

1. **Clone the repository**  
   ```sh
   git clone <your-repo-url>
   cd videopipeline
   ```

2. **Install dependencies**  
   ```sh
   pip install -r requirements.txt
   ```

3. **Apply Django migrations**  
   ```sh
   python manage.py migrate
   ```

## Running the Server

Start the Django development server:

```sh
python manage.py runserver
```

The API will be available at:  
`http://localhost:8000/process/`

## Usage

### 1. **API Usage**

Send a POST request to `/process/` with JSON body:

```json