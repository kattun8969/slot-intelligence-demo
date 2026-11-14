"""Static checks for attributed image popups and transparent fallback."""
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

    def test_source_images_and_attribution(self):
        for marker in (
            "https://chonborista.com/wp-content/uploads/2023/09/l_monkey_heru1.jpg",
            "https://chonborista.com/wp-content/uploads/2023/09/l_monkey_heru2.jpg",
            'img.referrerPolicy="no-referrer"',
            'img.addEventListener("error"',
            "出典：",
            "画像・解析出典：",
            "ちょんぼりすた掲載",
            "画像を表示できませんでした",
        ):
            self.assertIn(marker, self.html)

    def test_profit_example_remains_hypothetical(self):
        self.assertIn("各狙い目の投資・利益予想ではありません", self.html)
        self.assertIn("renderProfitWorksheet()", self.html)

if __name__ == "__main__":
    unittest.main()
