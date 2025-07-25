# Testing OPA within container

The containerized instance of OPA needs the policies (`opa/example-policy.rego`) and the data (`opa/example-data.json`) used to evaluate the input.

The following docker-compose file:
- copies in the `/orchestrator` folder the `../opa/data` folder contained in this repository.
- starts opa in server mode
- loads the `orchestrator` package and serves it on `localhost:8181/v1/data/orchestrator`.

Once OPA is up and running we can interrogate its endpoints to evaluate if a token has the correct access rights.

Here we give an example of the input to provide to the OPA REST API.

```bash
curl -X POST http://localhost:8181/v1/data/orchestrator/allow \
-H 'Content-Type: application/javascript' \
-d '{
  "input": {
    "user_info": {
      "iss": "https://iam.cloud.infn.it/",
      "groups": ["test_admin"]
    },   
    "path": "/api/v1/users",
    "method": "GET",
    "has_body": "false"
  }
}'
```

The expected result should be: `{"result":true}`
