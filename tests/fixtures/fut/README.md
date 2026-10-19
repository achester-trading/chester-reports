# Fixtures for altdata/sources/fut.py

Captured on 17 Oct 2026 from the laptop with the project's User-Agent
(`chester-reports/1.0`), each one a venue's real response:

- `okx_*.json`: www.okx.com/api/v5.
- `deribit_*.json`: www.deribit.com/api/v2.

The `bybit_*.json` files are NOT captured. api.bybit.com answers US addresses 403
("configured to block access from your country"). They follow the response shapes
in Bybit's v5 API documentation (retCode, retMsg, result.list), with synthetic
figures. The Bybit venue is switched off in config/crypto_sources.yaml.
