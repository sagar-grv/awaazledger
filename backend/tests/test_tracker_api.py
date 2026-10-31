"""Unit tests for dispute multi-node verification tracker endpoints."""

from app.api.disputes import get_dispute_tracker, get_dispute_tracker_by_code
from app.models.dispute import Dispute
from app.agent.state_machine import AgentOrchestrator


def test_tracker_api_for_dispute(db_session):
    # Ensure dispute DISP-SCN-01 exists and run agent
    disp = db_session.query(Dispute).filter(Dispute.dispute_code == "DISP-SCN-01").first()
    assert disp is not None

    orchestrator = AgentOrchestrator(db_session)
    orchestrator.run_for_dispute(disp.id)

    # 1. Test GET /disputes/{id}/tracker endpoint function
    data = get_dispute_tracker(disp.id, db=db_session)

    assert data["dispute_id"] == disp.id
    assert data["dispute_code"] == "DISP-SCN-01"
    assert len(data["nodes"]) == 6

    # Verify nodes
    node_map = {n["label"]: n for n in data["nodes"]}
    assert "Remitter Bank" in node_map
    assert node_map["Remitter Bank"]["status"] == "SUCCESS"

    assert "NPCI Switch" in node_map
    assert node_map["NPCI Switch"]["status"] == "DELAYED"

    assert "Bridge Credit" in node_map
    assert node_map["Bridge Credit"]["status"] == "SUCCESS"

    # 2. Test GET /disputes/code/{dispute_code}/tracker endpoint function
    data_code = get_dispute_tracker_by_code(disp.dispute_code, db=db_session)
    assert data_code["dispute_code"] == "DISP-SCN-01"
    assert data_code["status"] in ["AUTO_CREDITED", "RESOLVED"]
