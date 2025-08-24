# Baernstormers

Full-stack solution for PostFinance's SpendCast challenge at the 2025 Bärnhäckt hackathon.

## Repository overview
- **SpendCast_BE/** – FastAPI backend with LangGraph AI agent and streaming or non-streaming chat endpoints for managing financial data backed by PostgreSQL.
- **SpendCast_FE/** – React + TypeScript + Vite front end.
- **data-extraction/** – Python scripts that query a GraphDB repository with SPARQL to produce spending summaries.

## Getting started

### Backend
```bash
cd SpendCast_BE
uv install
uvicorn main:app --reload
```

Run tests:
```bash
pytest
```

### Frontend
```bash
cd SpendCast_FE
npm install
npm run dev
```

### Data extraction scripts
Run individual scripts from the `data-extraction/scripts` directory, e.g.:
```bash
python data-extraction/scripts/transport_spend_calculator.py
```

## Testing
- Backend tests use `pytest`.
- The front end currently defines no test script.

## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## License
This project does not yet specify a license.
