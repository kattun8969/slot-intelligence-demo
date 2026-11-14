"""Static regressions for helmet cue gallery and source-safe popup."""
from pathlib import Path
import unittest

PAGE = Path(__file__).resolve().parents[1] / "docs" / "opportunities.html"

class CompoundCueGalleryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = PAGE.read_text(encoding="utf-8")

    def test_popup_and_all_helmet_variants(self):
        for marker in (
            'createElement("dialog")',
            'overlay.showModal()',
            'overlay.close()',
            'ロゴなし（デフォルト）',
            'ロゴあり',
            'ロゴ＋キラキラ',
            'Vロゴ',
            'ライバルヘルメット',
        ):
            self.assertIn(marker, self.html)

    def test_gallery_marks_illustrations_not_actual_machine_photos(self):
        self.assertIn("識別用の模式図（実機画像ではありません）", self.html)
        self.assertIn("実機画像の転載は許諾・引用要件の確認後", self.html)
        self.assertIn("解析出典：", self.html)
        self.assertIn("https://nana-press.com/kaiseki/machine/644/18217/", self.html)
        self.assertIn("https://1geki.jp/slot/l_monkeyturn5/47/", self.html)

    def test_profit_example_remains_hypothetical(self):
        self.assertIn("各狙い目の投資・利益予想ではありません", self.html)
        self.assertIn("renderProfitWorksheet()", self.html)

if __name__ == "__main__":
    unittest.main()
