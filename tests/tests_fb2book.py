from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock,call
import xml.etree.ElementTree as ET
import zipfile

from webbooks.fb2book import (Chapter,TableOfChapters,BookScanner,DocWriter)


sample_fb2 = """\
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
    <title>First title.</title>
    <p>Beginning.</p>
    <image l:href="http://example.com/external.jpg"/>
    <p>External image.</p>
    <image l:href="#i_127.png"/>
    <p>Internal image.</p>
    <poem><stanza>
    <v>poem1</v>
    <v>poem2</v>
    </stanza></poem>
    <p>End...</p>
</section>
</body>
<binary id="cover.jpg" content-type="image/jpg">abcd
</binary>
<binary id="i_127.png" content-type="image/png">efgh
</binary>
</FictionBook>
"""


class ChapterTest(unittest.TestCase):

    def test_chapter_creation(self):
        ch = Chapter('c1')
        self.assertEqual(ch.label, 'c1')
        self.assertEqual(ch.title, '')
        self.assertEqual(ch.number, '')

    def test_chapter_is_named(self):
        ch = Chapter('c1')
        self.assertFalse(ch.is_named())
        ch.title = 'The Title'
        self.assertTrue(ch.is_named())

    def test_new_child_number(self):
        root = Chapter('r')
        self.assertEqual(root.new_child_number(), "1")
        child = root.add_child('c1')
        child.add_child('c1-1')
        self.assertEqual(child.new_child_number(), "1.2")

    def test_chapters_tree(self):
        root = Chapter('')
        children = [root.add_child(t) for t in ('c1', 'c2', 'c3')]
        child2 = children[1]
        child2_1 = child2.add_child('c2-1')
        self.assertEqual(root.number, '')
        self.assertEqual(root.children, children)
        self.assertEqual(child2.label, 'c2')
        self.assertEqual(child2_1.number, '2.1')


class TableOfChaptersTest(unittest.TestCase):

    def setUp(self):
        self.actor = Mock()
        self.toc = TableOfChapters(self.actor)

    def test_toc_creation(self):
        toc = self.toc
        self.assertEqual(toc.actor, self.actor)
        self.assertIsInstance(toc.tree, Chapter)
        self.assertEqual(toc.path, [toc.tree])
        self.assertEqual(toc.total, 0)

    def test_current_chapter_tracking(self):
        toc = self.toc
        self.assertEqual(toc.current(), toc.tree)
        c1 = toc.add_chapter()
        c1_2 = toc.add_chapter()
        toc.actor.add_chapter.assert_called_with(c1_2)
        self.assertEqual(toc.total, 2)
        self.assertEqual(toc.current(), c1_2)
        toc.end_chapter()
        self.assertEqual(toc.current(), c1)

    def test_add_new_chapter(self):
        toc = self.toc
        c1 = toc.add_chapter()
        c1_2 = toc.add_chapter()
        toc.end_chapter()
        toc.end_chapter()
        c2 = toc.add_chapter()
        self.assertEqual(toc.total, 3)
        self.assertEqual(toc.tree.children, [c1, c2])

    def test_add_chapter_title(self):
        toc = self.toc
        c = toc.add_chapter()
        toc.add_chapter_title("t1")
        self.assertEqual(c.title, "t1")

    def test_toc_get_result(self):
        toc = self.toc
        c1 = toc.add_chapter()
        c1_1 = toc.add_chapter()
        toc.end_chapter()
        toc.end_chapter()
        c2 = toc.add_chapter()
        toc.end_chapter()
        toc.get_result()
        calls = [call(c1), call(c1_1), call(c2)]
        toc.actor.toc_chapter.assert_has_calls(calls)


@unittest.skip
class FB2BookTest(unittest.TestCase):

    fb2 = sample_fb2
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

    def test_open_zip(self):
        with tempfile.TemporaryDirectory() as dirname:
            bookname = "book.fb2"
            zippath = Path(dirname, bookname+".zip")
            with zipfile.ZipFile(zippath, "w") as archive:
                archive.writestr(bookname, self.fb2)
            book = FB2Book(file=zippath)
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
            found,bracket,_ = piece.partition("]")
            if not bracket:
                raise SyntaxError()
            parts.append(found)
        return "\n".join(parts)

    def test_text_in_brackets(self):
        text = "[a1]abc[b2]de\nfg[c3]hi[d4]"
        result = self.text_in_brackets(text)
        self.assertEqual(result, "a1\nb2\nc3\nd4")
        self.assertRaises(SyntaxError, self.text_in_brackets, "[a1][b2[c3]")

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


class BookScannerTest(unittest.TestCase):

    def test_scanner_creation(self):
        scanner = BookScanner("<body></body>")
        self.assertEqual(scanner.parser.root.tag, "body")

    def test_display(self):
        scanner = BookScanner(sample_fb2)
        writer = DocWriter(output="html")
        scanner.scan(writer)
        with open("test.txt", "w") as f:
            f.write( writer.get_result() )
