"""GET /comparisons/{id}: 저장된 대조 결과 조회."""

from pathlib import Path

SAMPLES = Path(__file__).resolve().parents[2] / "samples"


def upload(client, url, name):
    data = (SAMPLES / name).read_bytes()
    return client.post(url, files={"file": (name, data, "image/png")}).json()


def test_reads_saved_comparison(client):
    posting = upload(client, "/postings/extract", "case3_posting.png")
    created = upload(client, f"/postings/{posting['id']}/compare", "case3_contract.png")

    r = client.get(f"/comparisons/{created['id']}")
    assert r.status_code == 200
    assert r.json() == created


def test_missing_comparison_returns_404(client):
    assert client.get("/comparisons/999").status_code == 404
