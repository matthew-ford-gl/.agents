import pathlib
import unittest


SKILL = pathlib.Path(__file__).parents[1] / "SKILL.md"
FIXER = pathlib.Path(__file__).parents[2] / ".." / "agents" / "pr-fixer" / "AGENT.md"


class LandPrContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.skill = SKILL.read_text(encoding="utf-8")
        cls.fixer = FIXER.resolve().read_text(encoding="utf-8")

    def test_converges_without_arbitrary_cycle_limit(self):
        self.assertIn("Continue until APPROVED", self.skill)
        self.assertIn("Never stop merely because a correction count", self.skill)
        self.assertNotIn("allow exactly one correction", self.skill)
        self.assertNotIn("If that would exceed 4", self.skill)

    def test_new_validation_failures_return_to_remediation(self):
        self.assertIn("A newly exposed failure", self.skill)
        self.assertIn("return to step 1", self.skill)
        self.assertIn("derive the pre-push suite", self.skill)

    def test_delivery_is_required_before_terminal_reporting(self):
        self.assertIn("Never emit a success-like verdict", self.skill)
        self.assertIn("uncommitted intended change", self.skill)
        self.assertIn("addressed-but-open thread", self.skill)
        self.assertIn("DELIVERED — remote gates pending", self.skill)

    def test_fixer_accepts_repeated_evidence_driven_corrections(self):
        self.assertIn("failed validation fingerprint", self.fixer)
        self.assertIn("materially distinct root-cause correction", self.fixer)
        self.assertNotIn("single correction allowed", self.fixer)


if __name__ == "__main__":
    unittest.main()
