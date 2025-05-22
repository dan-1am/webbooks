from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock,call
import xml.etree.ElementTree as ET
import zipfile

from webbooks.fb2book import (Chapter,TableOfChapters,ImageProcessor,
    BookScanner,DocWriter,BookProcessor)


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

    def test_toc_creation(self):
        toc = TableOfChapters()
        self.assertIsInstance(toc.tree, Chapter)
        self.assertEqual(toc.path, [toc.tree])
        self.assertEqual(toc.total, 0)

    def test_current_chapter_tracking(self):
        toc = TableOfChapters()
        self.assertEqual(toc.current(), toc.tree)
        c1 = toc.add_chapter()
        c1_2 = toc.add_chapter()
        self.assertEqual(toc.total, 2)
        self.assertEqual(toc.current(), c1_2)
        toc.end_chapter()
        self.assertEqual(toc.current(), c1)

    def test_add_new_chapter(self):
        toc = TableOfChapters()
        c1 = toc.add_chapter()
        c1_2 = toc.add_chapter()
        toc.end_chapter()
        toc.end_chapter()
        c2 = toc.add_chapter()
        self.assertEqual(toc.total, 3)
        self.assertEqual(toc.tree.children, [c1, c2])

    def test_add_chapter_title(self):
        toc = TableOfChapters()
        c = toc.add_chapter()
        toc.add_chapter_title("t1")
        self.assertEqual(c.title, "t1")

    def test_toc_scan(self):
        toc = TableOfChapters()
        c1 = toc.add_chapter()
        c1_1 = toc.add_chapter()
        toc.end_chapter()
        toc.end_chapter()
        c2 = toc.add_chapter()
        toc.end_chapter()
        actor = Mock()
        toc.scan(actor)
        calls = [call(c1), call(c1_1), call(c2)]
        actor.toc_chapter.assert_has_calls(calls)


class ImageProcessorTest(unittest.TestCase):

    def test_creation(self):
        ip = ImageProcessor("root", "actor", False)
        self.assertEqual(ip.root, "root")
        self.assertEqual(ip.actor, "actor")
        self.assertEqual(ip.embed, False)

    def mock_add_image(self, link):
        ip = ImageProcessor()
        ip.get_image_link = Mock(return_value=link)
        ip.add_internal_image = Mock()
        ip.link_image = Mock()
        ip.add_image("tree")
        ip.get_image_link.assert_called_once_with("tree")
        return ip

    def test_add_image_embedded_in_fb2(self):
        ip = self.mock_add_image("#lnk")
        ip.add_internal_image.assert_called_once()
        ip.link_image.assert_not_called()

    def test_add_image_with_external_link(self):
        ip = self.mock_add_image("lnk")
        ip.add_internal_image.assert_not_called()
        ip.link_image.assert_called_once()

    def test_add_internal_image(self):
        ip = ImageProcessor()
        ei = ip.embed_image = Mock()
        ip.add_internal_image("#lnk")
        ei.assert_called_once_with("lnk")

    def test_embed_image(self):
        ip = ImageProcessor()
        ip.get_image_data = Mock(return_value=("data", "type"))
        ip.actor = Mock()
        ip.embed_image("n1")
        ip.actor.embed_image.assert_called_once_with("n1", "data", "type")

    def test_link_image(self):
        ip = ImageProcessor()
        ip.actor = Mock()
        ip.link_image("lnk")
        ip.actor.link_image.assert_called_once_with("lnk")

    def test_get_image_link(self):
        ip = ImageProcessor()
        tree = ET.fromstring('<image href="lnk"/>')
        link = ip.get_image_link(tree)
        self.assertEqual(link, "lnk")

    def test_get_image_list(self):
        fb2 = """<body>
        <binary id="lnk" content-type="image/png">123</binary>
        </body>"""
        root = ET.fromstring(fb2)
        ip = ImageProcessor(root)
        data,type = ip.get_image_data("#lnk")
        self.assertEqual(data, "123")
        self.assertEqual(type, "image/png")


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


html_sample = """\
<p><a href='#toc1'>1. </a></p>
<p><a href='#toc2'>1.1. First title.</a></p>
<hr>
<hr><h2 id='toc1'>Chapter 1</h2>
<hr><h2 id='toc2'>Chapter 1.1</h2>
<h2>First title.</h2>
<p>Beginning.</p>
<img src="http://example.com/external.jpg"><p>External image.</p>
<img src="data:image/png;base64, efgh"><p>Internal image.</p>
<div style="text-align: center;"><p>
poem1<br>
poem2<br>
</p></div>
<p>End...</p>


"""


class BookProcessorTest(unittest.TestCase):

    def test_book_processor_creation(self):
        book = BookProcessor("<body></body>")
        self.assertEqual(book.scanner.tree.tag, "body")

    def test_display(self):
        book = BookProcessor(sample_fb2)
        text,toc = book.get_content()
        full = toc + text
        if full != html_sample:
            with open("bad_book.txt", "w") as f:
                f.write(full)
        self.assertEqual(full, html_sample)
