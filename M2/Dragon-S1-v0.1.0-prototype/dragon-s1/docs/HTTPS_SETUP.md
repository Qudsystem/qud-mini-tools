# HTTPS Setup for Dragon S1

To secure the communication between the Dragon S1 Server and the Agents, it is highly recommended to run the server over HTTPS.

## 1. Generate Certificates

You can generate a self-signed TLS/SSL certificate using the provided Python script. Make sure your virtual environment is active and dependencies are installed.

```bash
python tools/generate_certs.py
```
This will generate `server.crt` and `server.key` in the current directory.

## 2. Run Uvicorn with HTTPS

Once you have the certificates, you can start the Uvicorn server with SSL enabled by adding the `--ssl-keyfile` and `--ssl-certfile` arguments.

### Via Command Line
```bash
uvicorn server.main:app --host 0.0.0.0 --port 3001 --ssl-keyfile server.key --ssl-certfile server.crt
```

### Programmatically
If you are running the server programmatically in Python, you can pass `ssl_keyfile` and `ssl_certfile` to `uvicorn.run()`:

```python
import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "server.main:app",
        host="0.0.0.0",
        port=3001,
        ssl_keyfile="server.key",
        ssl_certfile="server.crt"
    )
```

**Note:** Self-signed certificates may cause browser warnings (e.g., NET::ERR_CERT_AUTHORITY_INVALID) or require clients and agents to skip SSL verification or add the certificate to their trusted store. For production deployments exposed to the web, consider using a proper Certificate Authority (CA) such as Let's Encrypt.
