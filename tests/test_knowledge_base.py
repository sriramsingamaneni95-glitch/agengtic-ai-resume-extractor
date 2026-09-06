
import knowledge_base


def test_verify_known_company(tmp_path, monkeypatch):
    monkeypatch.setattr(knowledge_base, "KB_FILE", tmp_path / "kb.json")
    result = knowledge_base.verify_entity("Googl", "company") 
    assert result["verified"] is True
    assert result["matched_to"] == "Google"


def test_verify_unknown_company(tmp_path, monkeypatch):
    monkeypatch.setattr(knowledge_base, "KB_FILE", tmp_path / "kb.json")
    result = knowledge_base.verify_entity("Totally Made Up Corp Inc", "company")
    assert result["verified"] is False


def test_teach_entity_persists(tmp_path, monkeypatch):
    monkeypatch.setattr(knowledge_base, "KB_FILE", tmp_path / "kb.json")
    knowledge_base.teach_entity("Acme Robotics", "company")
    result = knowledge_base.verify_entity("Acme Robotics", "company")
    assert result["verified"] is True
    assert result["matched_to"] == "Acme Robotics"


def test_teach_entity_is_idempotent(tmp_path, monkeypatch):
    monkeypatch.setattr(knowledge_base, "KB_FILE", tmp_path / "kb.json")
    knowledge_base.teach_entity("Acme Robotics", "company")
    knowledge_base.teach_entity("Acme Robotics", "company")
    kb = knowledge_base._load_kb()
    assert kb["companies"].count("Acme Robotics") == 1
