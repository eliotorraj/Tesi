# Historical Qdrant inspection service

`compose.yaml` starts a local Qdrant service for inspecting a copied index with the official dashboard at `http://localhost:6333/dashboard/`. It requires a working Docker installation. The historical population/check command is `scripts/18_qdrant_dashboard.py` within the archived experiment workspace.

This service is optional. The standalone prototype uses its own local Qdrant storage and does not require Docker. Inspection copies and checks are stored under the archived RAG artifacts; they are not new training examples or Test outcomes.

[Parent directory](../README.md) · [Current repository guide](../../../../README.md)
