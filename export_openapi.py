import json
import yaml
from app.main import app

# Export OpenAPI JSON
openapi_data = app.openapi()

# Save as YAML
with open("openapi.yaml", "w") as f:
    yaml.dump(openapi_data, f, sort_keys=False)

print("Generated openapi.yaml")
