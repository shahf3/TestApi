# TestApi

# AI-Powered API Auto-Tester

**AI-Powered API Auto-Tester** is a Python tool that leverages OpenAI GPT to automatically generate, execute, and validate test cases for any API described by an OpenAPI (Swagger) specification. It produces detailed reports in HTML, JSON, or Markdown, making API quality assurance fast, intelligent, and easy.

---

## Features

- **OpenAPI/Swagger Support**: Parse OpenAPI 3.x (YAML/JSON) specs.
- **AI Test Generation**: Uses GPT to generate realistic, valid, invalid, and boundary test cases for each endpoint.
- **Automated Execution**: Runs all test cases against your API, handling authentication and custom headers.
- **Response Validation**: Validates responses against OpenAPI schemas and expected status codes.
- **Comprehensive Reporting**: Generates beautiful HTML, JSON, or Markdown reports with pass/fail/error breakdowns.
- **Spec Discovery**: Can auto-generate a basic OpenAPI spec from a live API URL (best effort).

---

## Installation

1. **Clone the repository:**
   ```bash
   git clone <your-repo-url>
   cd Test APi
   ```

2. **Install dependencies:**
   ```bash
   python -m pip install -r requirements.txt
   ```

3. **Set your OpenAI API key:**
   - Create a `.env` file in the project root:
     ```
     OPENAI_API_KEY=sk-...
     ```
   - Or set the environment variable directly.

---

## Usage

### 1. Run API Tests

```bash
python cli.py test --spec examples/petstore.yaml --base-url https://petstore3.swagger.io/api/v3 --output html
```

- `--spec` (`-s`): Path to your OpenAPI spec (YAML or JSON).
- `--base-url` (`-u`): (Optional) Override the base URL in the spec.
- `--output` (`-o`): Report format (`html`, `json`, or `markdown`). Default: `html`.
- `--model` (`-m`): (Optional) OpenAI model (default: `gpt-3.5-turbo`).

**Reports** are saved in the `reports/` directory.

### 2. Generate Test Cases Only

```bash
python cli.py generate --spec examples/petstore.yaml --output test_cases.json
```

- Saves all generated test cases to a JSON file (no execution).

### 3. Discover API Spec from URL

```bash
python cli.py discover --url https://your.api.url --output my_api.yaml
```

- Attempts to auto-generate an OpenAPI spec from a live API (best effort, may require manual editing).

---

## Example Specs

Sample OpenAPI specs are provided in the `examples/` folder:
- `petstore.yaml` / `petstore.json`
- `github_api.yaml`
- `local_api.yaml`
- `sample_openapi.yaml`

---

## Reports

After running tests, find your reports in the `reports/` directory. HTML reports provide a visual summary, including:
- Total, passed, failed, and error test counts
- Success rate
- Per-endpoint and per-test details
- Validation errors and response bodies

---

## Troubleshooting

- **404/405 Errors**: Ensure the `servers` URL in your OpenAPI spec matches the actual API base URL.
- **Schema Validation Issues**: Check that your spec's response schemas match the real API responses.
- **OpenAI API Key Errors**: Make sure your key is set in `.env` or as an environment variable.

---

**Happy Testing!** 
