# Mock Banking & Payment Switch Services

This folder contains lightweight mock servers representing external financial institutions:
- **cbs_mock.py**: Mock Remitter and Beneficiary Core Banking System (HDFC / SBI / ICICI).
- **npci_mock.py**: Mock NPCI UDIR (Unified Dispute and Issue Resolution) gateway.
- **paytm_ledger_mock.py**: Mock internal Paytm Payments Bank / Gateway ledger.

These mock services can either be invoked in-process via Python service clients or started as independent HTTP servers during multi-process testing.
