# Docker Usage

Build the image from the project root:

```bash
docker build -t tf2scanner .
```

Run the container, passing your `.env` file for API keys:

```bash
docker run --env-file .env -p 5000:5000 tf2scanner
```

The app will be available at `http://localhost:5000`.
