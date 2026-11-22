import unittest
from asma_core.aml_parser import AMLParser

class TestMedleyDeviceFormatter(unittest.TestCase):

    def setUp(self):
        self.aml = """{title: Mega Medley 80}
{artist: ASMA Band}

{start_of_song: Gloria | Umberto Tozzi | MI}
[INTRO]
| MI | LA | SI | MI |
{soc}
[MI]Gloria... [SI]manchi tu nell'aria
{eoc}
{end_of_song}

{start_of_song: Gente di Mare | Raf & Tozzi | DO}
[INTRO]
| DO | SOL | LAm | FA |
{sov}
[DO]A tutti i marinai...
{eov}
{end_of_song}

{start_of_song: Si Puo Dare Di Piu | Trio | RE}
[INTRO]
| RE | LA | SIm | SOL |
{soc}
[RE]Si puo dare di piu...
{eoc}
{end_of_song}"""

    def test_split_medley_fragments(self):
        header, fragments = AMLParser.split_medley_fragments(self.aml)
        self.assertIn("{title: Mega Medley 80}", header)
        self.assertEqual(len(fragments), 3)

        self.assertEqual(fragments[0]["title"], "Gloria")
        self.assertEqual(fragments[0]["artist"], "Umberto Tozzi")
        self.assertEqual(fragments[0]["key"], "MI")
        self.assertFalse(fragments[0]["has_page_break"])

        self.assertEqual(fragments[1]["title"], "Gente di Mare")
        self.assertEqual(fragments[1]["artist"], "Raf & Tozzi")
        self.assertEqual(fragments[1]["key"], "DO")

        self.assertEqual(fragments[2]["title"], "Si Puo Dare Di Piu")

    def test_format_one_per_page(self):
        out_one, frags_one = AMLParser.format_medley_pages(self.aml, strategy="one_per_page")
        self.assertEqual(len(frags_one), 3)
        self.assertEqual(frags_one[0]["page"], 1)
        self.assertEqual(frags_one[1]["page"], 2)
        self.assertEqual(frags_one[2]["page"], 3)
        self.assertIn("{np}\n{start_of_song: Gente di Mare", out_one)
        self.assertIn("{np}\n{start_of_song: Si Puo Dare Di Piu", out_one)

    def test_format_smart_fit_tablet(self):
        # 3 short fragments fit on a single tablet page
        out_tab, frags_tab = AMLParser.format_medley_pages(self.aml, strategy="smart_fit", target_device="Samsung Galaxy tab s8")
        self.assertEqual(frags_tab[0]["page"], 1)
        self.assertEqual(frags_tab[1]["page"], 1)
        self.assertEqual(frags_tab[2]["page"], 1)
        self.assertNotIn("{np}", out_tab)

    def test_format_smart_fit_smartphone(self):
        # Smartphone has smaller page height capacity, so 3 fragments split
        out_phone, frags_phone = AMLParser.format_medley_pages(self.aml, strategy="smart_fit", target_device="Pixel 8 pro")
        self.assertEqual(frags_phone[0]["page"], 1)
        self.assertEqual(frags_phone[1]["page"], 1)
        self.assertEqual(frags_phone[2]["page"], 2)
        self.assertIn("{np}\n{start_of_song: Si Puo Dare Di Piu", out_phone)

    def test_format_custom_breaks(self):
        # Explicit page break only before fragment 2
        out_cust, frags_cust = AMLParser.format_medley_pages(self.aml, strategy="custom", custom_breaks=[2])
        self.assertEqual(frags_cust[0]["page"], 1)
        self.assertEqual(frags_cust[1]["page"], 2)
        self.assertEqual(frags_cust[2]["page"], 2)
        self.assertIn("{np}\n{start_of_song: Gente di Mare", out_cust)
        self.assertNotIn("{np}\n{start_of_song: Si Puo Dare Di Piu", out_cust)

    def test_format_clear(self):
        out_one, _ = AMLParser.format_medley_pages(self.aml, strategy="one_per_page")
        out_clear, frags_clear = AMLParser.format_medley_pages(out_one, strategy="clear")
        self.assertNotIn("{np}", out_clear)
        self.assertEqual(frags_clear[0]["page"], 1)
        self.assertEqual(frags_clear[1]["page"], 1)
        self.assertEqual(frags_clear[2]["page"], 1)

if __name__ == "__main__":
    unittest.main()
