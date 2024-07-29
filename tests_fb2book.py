import unittest
from fb2book import Chapter,TableOfContents,FB2Book
import xml.etree.ElementTree as ET


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


class FB2BookTest(unittest.TestCase):

    fb2 = """\
<FictionBook xmlns="http://www.gribuser.ru/xml/fictionbook/2.0" xmlns:l="http://www.w3.org/1999/xlink">
<description>
<title-info>
    <genre>prose_classic</genre>
    <author>
      <first-name>Bob</first-name>
      <middle-name>Jr</middle-name>
      <last-name>Doe</last-name>
      <nickname>Tester</nickname>
    </author>
    <book-title>Title</book-title>
    <annotation>
      <p>Annotation.</p>
    </annotation>
    <date>2001</date>
    <sequence name="Sequence." number="2"/>
    <coverpage><image l:href="#cover.jpg"/></coverpage>
</title-info>
</description>
<body>
<section>
    <image l:href="http://example.com/external.jpg"/>
    <image l:href="#i_127.png"/>
</section>
</body>
<binary id="cover.jpg" content-type="image/jpg">abcd
</binary>
<binary id="i_127.png" content-type="image/png">efgh
</binary>
</FictionBook>
"""

    def check_description(self, book):
        book.describe()
        sample = dict(
            genres=['prose_classic'],
            authors=['Doe Bob Jr Tester'],
            title='Title',
            annotation='<p>Annotation.</p>',
            date='2001',
            sequence='Sequence.',
            sequence_number=2,
        )
        book.annotation = book.annotation.strip()
        for key,value in sample.items():
            with self.subTest(key=key):
                parsed = getattr(book, key, None)
                self.assertEqual(parsed, value)

    def test_describe_with_namespaces(self):
        book = FB2Book(self.fb2)
        self.check_description(book)

    def test_describe_without_namespaces(self):
        tail = self.fb2.partition('\n')[2]
        tail = tail.replace("l:href", "href")
        self.assertNotIn(tail, "<FictionBook")
        fb2 = "<FictionBook>\n" + tail
        book = FB2Book(fb2)
        self.check_description(book)

    def test_external_image_link(self):
        book = FB2Book(self.fb2)
        images = book.root.findall(".//image")
        ext_link = book.image_link(images[1])
        self.assertEqual(ext_link, "http://example.com/external.jpg")

    def test_internal_image_handling(self):
        book = FB2Book(self.fb2)
        image = book.root.find(".//image")
        link = book.image_link(image)
        self.assertEqual(link, "#cover.jpg")
        data, type = book.image_data(link)
        self.assertEqual(type, "image/jpg")
        self.assertEqual(data.strip(), "abcd")

    def test_image_embedding(self):
        """Weak test for presence of image signature."""
        book = FB2Book(self.fb2)
        image = book.root.find(".//image")
        link = book.image_link(image)
        parts = []
        book.embed_image(link, parts)
        result = "".join(parts)
        self.assertIn("abcd", result)
        self.assertIn("image/jpg", result)

    def test_coverpage(self):
        """Weak test for presence of cover signature."""
        book = FB2Book(self.fb2)
        parts = book.html_coverpage()
        result = "".join(parts)
        cover = book.root.find("./description/title-info/coverpage/image")
        link = book.image_link(cover)
        data, type = book.image_data(link)
        self.assertIn(data, result)
        self.assertIn(type, result)

    structured_fb2 = """\
<FictionBook>
<body>
[first_text]
<section>
[section1_text]
    <section>
    [section1_1_text]
    </section>
[section1_end]
</section>
[last_text]
</body>
</FictionBook>
"""

    def text_in_brackets(self, text):
        parts = []
        for piece in text.split('[')[1:]:
            found = piece.partition("]")[0]
            parts.append(found)
        return "\n".join(parts)

    def test_tree_to_text(self):
        fb2 = self.structured_fb2
        book = FB2Book(fb2)
        text = book.tree_to_text(book.root)
        text = text.replace('[', '').replace(']', '')
        text = text.replace(' ','')
        tags = filter(None, text.splitlines())
        result = "\n".join(tags)
        source = self.text_in_brackets(fb2)
        self.assertEqual(result, source)

    def test_to_html(self):
        fb2 = self.structured_fb2
        book = FB2Book(fb2)
        html = book.to_html()
        result = self.text_in_brackets(html)
        source = self.text_in_brackets(fb2)
        self.assertEqual(result, source)
