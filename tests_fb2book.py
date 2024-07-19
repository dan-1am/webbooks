import unittest
from fb2book import Chapter,TableOfContents


class ChapterTest(unittest.TestCase):

    def test_chapter_creation(self):
        ch = Chapter('c1')
        self.assertEqual(ch.label, 'c1')
        self.assertEqual(ch.title, '')
        self.assertEqual(ch.number, '')
        self.assertEqual(ch.children, [])

    def test_chapter_is_named(self):
        ch = Chapter('c1')
        self.assertFalse(ch.named())
        ch.title = 'The Title'
        self.assertTrue(ch.named())

    def test_chapters_tree(self):
        root = Chapter('')
        children = [root.add_child(t) for t in ('c1', 'c2', 'c3')]
        child2 = children[1]
        child2_1 = child2.add_child('c2.1')
        self.assertEqual(root.number, '')
        self.assertEqual(root.children, children)
        self.assertEqual(child2.label, 'c2')
        self.assertEqual(child2_1.number, '2.1')


class TableOfContentsTest(unittest.TestCase):

    def test_toc_creation(self):
        toc = TableOfContents()
        self.assertEqual(toc.path[0], toc.tree)
        self.assertIsInstance(toc.tree, Chapter)
        self.assertEqual(toc.total, 0)

    def test_last_chapter_tracking(self):
        toc = TableOfContents()
        self.assertEqual(toc.last(), toc.tree)
        c1 = toc.new_chapter()
        c1_2 = toc.new_chapter()
        self.assertEqual(toc.last(), c1_2)
        toc.end_chapter()
        self.assertEqual(toc.last(), c1)

    def test_chapter_marker(self):
        toc = TableOfContents()
        toc.marker_template = "<!{label}!>"
        c1 = toc.new_chapter()
        self.assertEqual(toc.marker(c1), f"<!{c1.label}!>")

    def test_add_new_chapter(self):
        toc = TableOfContents()
        c1 = toc.new_chapter()
        c1_2 = toc.new_chapter()
        toc.end_chapter()
        toc.end_chapter()
        c2 = toc.new_chapter()
        self.assertEqual(toc.total, 3)
        self.assertEqual(toc.tree.children, [c1, c2])

    def test_new_chapter_marker(self):
        toc = TableOfContents()
        answer = toc.new_chapter_marker()
        marker = toc.marker(toc.last())
        self.assertEqual(answer, marker)

    def test_add_title(self):
        toc = TableOfContents()
        c1 = toc.new_chapter()
        marker1 = toc.add_title("t1")
        self.assertEqual(marker1, "", "First title don't need a marker")
        marker2 = toc.add_title("t2")
        c2 = toc.last()
        self.assertEqual(c1.title, "t1")
        self.assertEqual(c2.title, "t2", "We wrap extra titles in new chapters")
        self.assertEqual(toc.marker(c2), marker2)

    def test_toc_as_html(self):
        toc = TableOfContents()
        toc.line_template = "{label}|{number}|{title}\n"
        c1 = toc.new_chapter()
        toc.add_title("t1")
        c1_1 = toc.new_chapter()
        toc.add_title("t1_1")
        toc.end_chapter()
        toc.end_chapter()
        c2 = toc.new_chapter()
        toc.add_title("t2")
        result = toc.html()
        html = '''\
toc1|1|t1
toc2|1.1|t1_1
toc3|2|t2
'''
        self.assertEqual(result, html)
