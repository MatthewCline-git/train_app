# NYC Subway Times API

A FastAPI-based REST API that provides real-time NYC subway arrival times and route information using the MTA's GTFS feeds.

## Features

- Real-time train arrival times for all NYC subway stations
- Complete route and station listings
- Station name fuzzy matching
- CORS support for web applications
- Docker support for easy deployment

## Prerequisites

- Python 3.10 or higher
- Docker (optional)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/mta-api.git
cd mta-api
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
```

## Running the API

### Local Development

```bash
uvicorn mta_api.main:app --reload
```

### Using Docker

```bash
docker compose up
```

The API will be available at `http://localhost:8000`.

## API Documentation

Once running, visit `http://localhost:8000/docs` for the interactive API documentation.

### Key Endpoints

- `GET /api/v1/routes` - List all subway routes and their stops
- `GET /api/v1/routes/{route}` - Get stops for a specific route
- `GET /api/v1/arrivals/{route}/{station}` - Get real-time arrivals for a station
- `GET /api/v1/health` - Health check endpoint

### Example Request

```bash
curl "http://localhost:8000/api/v1/arrivals/4/Grand%20Central-42%20St"
```

Example Response:
```json
{
  "downtowns": "3:42 PM, 3:57 PM, 4:12 PM",
  "uptowns": "3:45 PM, 4:00 PM, 4:15 PM"
}
```

## Project Structure

```
mta_api/
├── src/
│   └── mta_api/
│       ├── api/          # API route definitions
│       ├── data/         # Data processing and storage
│       └── services/     # Business logic and external services
├── tests/                # Test suite
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── setup.py
```

## Testing

```bash
pytest
```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

The fact that this API is public is sick. Thanks to the good folks in local government who made it happen. 