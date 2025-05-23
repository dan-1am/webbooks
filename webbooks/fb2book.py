#! /usr/bin/env python3

# https://github.com/gribuser/fb2
# https://github.com/genych/fb2-parser/
# www.fictionbook.org/index.php/Описание_формата_FB2_от_Sclex
# http://www.fictionbook.org/index.php/Eng:XML_Schema_Fictionbook_2.1

import xml.etree.ElementTree as ET
import re
import os
import zipfile


class BookParser:

    def __init__(self, text=None, file=None):
        if text is None:
            self.tree = self.parse_file(file)
        else:
            self.tree = ET.fromstring(text)
        self.strip_namespaces()

    def parse_file(self, file):
        handle = self.open(file)
        root = ET.parse(handle).getroot()
        return root

    def open_zip(self, file):
        with zipfile.ZipFile(file) as container:
            names = container.namelist()
            for name in names:
                if name.endswith(".fb2"):
                    return container.open(name)
            raise NameError("Unable to find .fb2 file inside .fb2.zip")

    def open(self, file):
        is_file_like = all(hasattr(file, attr)
            for attr in ('seek', 'close', 'read', 'write'))
        if is_file_like:
            handle = file
        elif str(file).endswith(".fb2.zip"):
            handle = self.open_zip(file)
        else:
            handle = open(file, "rb")
        return handle

    def strip_namespaces(self):
        """ Hack to not bother with namespaces """
        for element in self.tree.iter():
            element.tag = element.tag[element.tag.rfind('}')+1:]


class BookMetadata:

    def __init__(self, tree):
        self.tree = tree
        self.title_info = None
        self.authors = []
        self.genres = []
        self.sequence_name = ""
        self.sequence_number = 1

    def collect(self):
        if not self.title_info:
            meta_tree = self.tree.find("./description/title-info")
            self.title_info = self.extract_metadata(meta_tree)
            self.title = self.title_info.get("book-title", "")
            self.date = self.title_info.get("date", "")
            self.annotation = self.title_info.get("annotation", "")

    def extract_metadata(self, tree):
        metadata = {}
        if tree is None:
            tree = ET.Element("dummy")
        for child in tree:
            if child.tag == "author":
                self.collect_author_names(child)
            elif child.tag == "genre":
                self.collect_genre(child)
            elif child.tag == "sequence":
                self.collect_sequence_info(child)
            elif child.tag != "coverpage":
                metadata[child.tag] = child.text.strip()
        return metadata

    def annotation_to_text(self):
        raise NotImplementedError

    def collect_author_names(self, author):
        part_names = ("last-name", "first-name", "middle-name", "nickname")
        parts = filter(None, (author.findtext(p) for p in part_names) )
        name = ' '.join( (p.strip() for p in parts) )
        self.authors.append(name)

    def collect_genre(self, tag):
        genre_name = tag.text.strip()
        self.genres.append(genre_name)

    def collect_sequence_info(self, sequence):
        name = sequence.attrib.get("name", "").strip()
        number_text = sequence.attrib.get("number", None)
        try:
            number = int(number_text)
        except (TypeError, ValueError):
            number = 1
        self.sequence = name
        self.sequence_number = number


class Chapter:

    def __init__(self, label):
        self.title = ""
        self.label = label
        self.number = ""
        self.children = []

    def __repr__(self):
        number = self.number if self.number else "root"
        return f"<{self.__class__.__name__}_{number}>"

    def is_named(self):
        return bool(self.title)

    def new_child_number(self):
        next_number = 1+len(self.children)
        return (f"{self.number}.{next_number}" if self.number
            else f"{next_number}")

    def add_child(self, label):
        child = type(self)(label)
        child.number = self.new_child_number()
        self.children.append(child)
        return child


class TableOfChapters:

    def __init__(self):
        self.tree = Chapter("")
        self.path = [self.tree]
        self.total = 0

    def current(self):
        return self.path[-1]

    def add_chapter(self):
        self.total += 1
        chapter = self.current().add_child(f"toc{self.total}")
        self.path.append(chapter)
        return chapter

    def end_chapter(self):
        chapter = self.path.pop()
        return chapter

    def add_chapter_title(self, text):
        chapter = self.current()
        chapter.title = text

    def scan(self, actor, chapter=None):
        if chapter is None:
            chapter = self.tree
        for child in chapter.children:
            actor.toc_chapter(child)
            self.scan(actor, child)


class ImageProcessor:

    def __init__(self, root=None, actor=None, embed=True):
        self.root = root
        self.actor = actor
        self.embed = embed

    def add_image(self, image_node):
        link = self.get_image_link(image_node)
        if not link:
            return
        if link[0] == "#":
            self.add_internal_image(link)
        else:
            self.link_image(link)

    def add_internal_image(self, link):
        name = link.removeprefix("#")
        if self.embed:
            self.embed_image(name)
        else:
            new_link = self.extracted_link(name)
            self.link_image(new_link)

    def embed_image(self, name):
        data, content_type  = self.get_image_data(name)
        if data:
            self.actor.embed_image(name, data, content_type)
        else:
            link_code = f"(Missing image: {name})"

    def link_image(self, link):
        self.actor.link_image(link)

    def get_image_link(self, image_node):
        for k,v in image_node.attrib.items():
            if k.endswith("href"):
                return v

    def get_image_data(self, link):
        name = link.removeprefix('#')
        for binary in self.root.findall("binary"):
            if binary.attrib['id'] == name:
                content_type = binary.attrib.get("content-type", "image/jpg")
                return binary.text, content_type
        return None, None


class BookScanner:

    def __init__(self, tree):
        self.tree = tree
        self.actor = None

    def scan_inner(self, tree):
        if tree.text:
            self.actor.add_text(tree.text)
        for child in tree:
            self.scan_tree(child)
            if child.tail != None:
                self.actor.add_text(child.tail)

    def add_chapter_for_extra_title(self):
        self.toc.end_chapter()
        chapter = self.toc.add_chapter()
        self.actor.add_chapter(chapter)

    def handle_new_title(self):
        chapter = self.toc.current()
        if chapter.is_named():
            self.add_chapter_for_extra_title()

    def wrap_chapter(self, tree):
        is_chapter = tree.tag in ("body","section")
        if is_chapter:
            chapter = self.toc.add_chapter()
            self.actor.add_chapter(chapter)
        self.scan_inner(tree)
        if is_chapter:
            chapter = self.toc.end_chapter()
            self.actor.end_chapter(chapter)

    def text_tag(self, tree):
        if tree.tag == "title":
            self.handle_new_title()
        self.actor.add_tag(tree.tag)
        self.wrap_chapter(tree)
        if tree.tag == "title":
            text = self.actor.fragments.copy_tag_text()
            self.toc.add_chapter_title(text)
        self.actor.end_tag(tree.tag)

    def scan_tree(self, tree):
        if tree.tag == "image":
            self.add_image(tree)
        else:
            self.text_tag(tree)

    def scan(self, actor):
        self.actor = actor
        self.toc = TableOfChapters()
        parts = self.add_coverpage()
        for body in self.tree.findall('body'):
            self.scan_tree(body)
        self.toc.scan(self.actor)

    def add_coverpage(self):
        cover = self.tree.find("./description/title-info/coverpage/image")
        if cover is not None:
            return self.add_image(cover)

    def add_image(self, image_node):
        ImageProcessor(self.tree, self.actor).add_image(image_node)


class FragmentKeeper:

    def __init__(self):
        self.data = []
        self.positions = []

    def append(self, text):
        self.data.append(text)

    def position(self):
        return len(self.data)

    def push_tag_position(self):
        position = self.position()
        self.positions.append(position)
        return position

    def pop_tag_position(self):
        return self.positions.pop()

    def cut_from(self, position):
        pieces = self.data[position:]
        del self.data[position:]
        return "".join(pieces)

    def copy_from(self, position):
        pieces = self.data[position:]
        text = "".join(pieces)
        self.data[position:] = (text,)
        return text

    def cut_tag_text(self):
        tag_position = self.positions[-1]
        return self.cut_from(tag_position)

    def copy_tag_text(self):
        tag_position = self.positions[-1]
        return self.copy_from(tag_position)

    def get_result(self):
        self.data = [ "".join(self.data) ]
        return self.data[0]


decorations = {
"text": {
    'toc_chapter': ("{number}. {title} [{label}]\n", ""),
    'chapter': ("\n* * *\nChapter {number} [{label}]\n\n", "\n\n"),
    'image': ("", "", '(image {url})'),
    'body': ("-"*40+"\n", ""),
    'section': ("", ""),
    'title': ("", "\n\n"),
    'subtitle': ("", "\n\n"),
    'epigraph': (" "*10, "\n"),
    'a': ("", ""),
    'p': ("", "\n\n"),
    'br': ("", "\n"),
    'table': ("\n", "\n"),
    'tr': ("", "\n"),
    'th': ("", "-"*72 + "\n"),
    'td': (" ", " |"),
    'emphasis': ("_", "_"),
    'strong': ("*", "*"),
    'sub':("^(", ")"),
    'sup':("_(", ")"),
    'strikethrough':("--(", ")--"),
    'code':("\n", "\n"),
    'poem': ("", ""),
    'stanza': ("", "\n"),
    'v': (" "*10, "\n"),
    'cite': (" "*10, "\n"),
    'text-author': (" "*10, "\n"),
    'empty-line': ("-"*72, "\n"),
},
"html": {
    'toc_chapter': ("<p><a href='#{label}'>{number}. {title}</a></p>\n", ""),
    'chapter': ("<hr><h2 id='{label}'>Chapter {number}</h2>\n", "\n"),
    'image': ("", "", '<img src="{url}">'),
    'body': ("<hr>\n", ""),
    'section': ("", ""),
    'title': ("<h2>", "</h2>\n"),
    'subtitle': ("<h3>", "</h3>\n"),
    'epigraph': ('<div style="text-align: right; font-style: italic">', "</div>\n"),
    'a': ("", ""),
    'p': ("<p>", "</p>\n"),
    'br': ("<br>\n", ""),
    'table': ('<table border="1">\n', "</table>\n"),
    'tr': ("<tr>\n", "</tr>\n"),
    'th': ("<th>\n", "</th>\n"),
    'td': ("<td>", "</td>\n"),
    'emphasis': ("<em>", "</em>"),
    'strong': ("<strong>", "</strong>"),
    'sub':("<sub>", "</sub>"),
    'sup':("<sup>", "</sup>"),
    'strikethrough':("<s>", "</s>"),
    'code':("<pre>", "</pre>"),
    'poem': ("", ""),
    'stanza': ('<div style="text-align: center;"><p>\n', "</p></div>\n"),
    'v': ("", "<br>\n"),
    'cite': ("<cite>", "</cite>"),
    'text-author': ('<div style="text-align: right">', "</div>"),
    'empty-line': ("<br>", ""),
},
}


class DocWriter:

    no_strip_tags = ("p", "title", "subtitle", "v")

    def __init__(self, output="html"):
        self.decorations = decorations[output]
        self.fragments = FragmentKeeper()
        self.toc_fragments = FragmentKeeper()
        self.strip_areas = [True]

    def get_result(self):
        return self.fragments.get_result()

    def get_toc(self):
        return self.toc_fragments.get_result()

    def toc_chapter(self, chapter):
        template = self.decorations["toc_chapter"][0]
        title = self.simplify_title(chapter.title)
        text = template.format(
            label=chapter.label,
            number=chapter.number,
            title=title,
        )
        self.toc_fragments.append(text)

    def simplify_title(self, title):
        title = title.strip()
        title = title.replace("\n", " ").replace("<br>", " ")
        title = title.replace("</p>", "").replace("<p>", "")
        return title

    def strip_needed(self):
        return self.strip_areas[-1]

    def add_strip_area(self, mode):
        self.strip_areas.append(mode)

    def end_strip_area(self):
        self.strip_areas.pop()

    def add_text(self, text):
        if self.strip_needed():
            text = text.strip()
        self.fragments.append(text)

    def call_if_exists(self, method):
        call = getattr(self, method, None)
        if call:
            call()

    def add_tag(self, tag):
        prefix = self.decorations[tag][0]
        self.fragments.append(prefix)
        self.call_if_exists("add_"+tag)
        self.fragments.push_tag_position()
        if tag in self.no_strip_tags:
            self.add_strip_area(False)

    def end_tag(self, tag):
        if tag in self.no_strip_tags:
            self.end_strip_area()
        self.fragments.pop_tag_position()
        self.call_if_exists("end_"+tag)
        self.fragments.append( self.decorations[tag][1] )

    def add_chapter(self, chapter):
        template = self.decorations['chapter'][0]
        text = template.format(label=chapter.label, number=chapter.number)
        self.fragments.append(text)

    def end_chapter(self, chapter):
        template = self.decorations['chapter'][1]
        text = template.format(label=chapter.label, number=chapter.number)
        self.fragments.append(text)

    def embed_image(self, name, data, content_type):
        single_line = "".join( data.split() )
        url = "data:{0};base64, {1}".format(content_type, single_line)
        self.link_image(url)

    def link_image(self, url):
        template = self.decorations['image'][2]
        text = template.format(url=url)
        self.fragments.append(text)


class BookProcessor:

    def __init__(self, text=None, file=None):
        if text or file:
            self.load(text, file)

    def load(self, text=None, file=None):
        parser = BookParser(text, file)
        tree = parser.tree
        self.metadata = BookMetadata(tree)
        self.scanner = BookScanner(tree)
        self.content = dict()

    def get_format_writer(self, format):
        writer = self.content.get(format, None)
        if not writer:
            writer = DocWriter(format)
            self.scanner.scan(writer)
            self.content[format] = writer
        return writer

    def get_content(self, format="html"):
        writer = self.get_format_writer(format)
        content = writer.get_result()
        toc = writer.get_toc()
        return content, toc

    def get_metadata(self):
        self.metadata.collect()
        return self.metadata
