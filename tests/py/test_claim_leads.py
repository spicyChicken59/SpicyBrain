"""The claim blocker report is generated from the claim ledger and stays in step with it."""
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("claim_leads", ROOT / "scripts" / "academy-claim-leads.py")
claim_leads = importlib.util.module_from_spec(spec)
spec.loader.exec_module(claim_leads)


class ClaimLeadsTest(unittest.TestCase):
    def test_the_committed_report_matches_the_ledger(self):
        self.assertEqual((ROOT / "docs/academy/CLAIM-LEADS.md").read_text(), claim_leads.build())

    def test_every_open_claim_with_a_decision_is_listed_with_its_gap(self):
        report = claim_leads.build()
        ledger = json.loads((ROOT / "docs/academy/CLAIM-REVIEW.json").read_text())
        decided = {d["id"] for d in json.loads((ROOT / "docs/academy/CLAIM-REVIEWS.json").read_text())["claims"]}
        for claim in ledger["claims"]:
            listed = f"`{claim['id']}`" in report
            open_with_decision = claim["status"] == "partial" or (
                claim["status"] == "pending-claim-review" and claim["id"] in decided)
            with self.subTest(claim=claim["id"]):
                self.assertEqual(listed, open_with_decision)


if __name__ == "__main__":
    unittest.main()
