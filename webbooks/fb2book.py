#! /usr/bin/env python3

# https://github.com/gribuser/fb2
# https://github.com/genych/fb2-parser/
# www.fictionbook.org/index.php/Описание_формата_FB2_от_Sclex

import xml.etree.ElementTree as ET
import re
import os
import zipfile


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


class TableOfContents:

    line_template = "<a href='#{label}'>{number}. {title}</a><br>\n"
    marker_template = "<div id='{label}'></div>"

    def clear(self):
        self.tree = Chapter("")
        self.path = [self.tree]
        self.total = 0

    def __init__(self):
        self.clear()

    def last(self):
        return self.path[-1]

    def marker(self, chapter):
        return self.marker_template.format(label=chapter.label)

    def new_chapter(self):
        last = self.last()
        self.total += 1
        new = last.add_child(f"toc{self.total}")
        self.path.append(new)
        return new

    def new_chapter_marker(self):
        return self.marker(self.new_chapter())

    def end_chapter(self):
        self.path.pop()

    def add_title(self, text):
        chapter = self.last()
        if chapter.is_named():  # several <title> tags in one section
            self.end_chapter()
            chapter = self.new_chapter()
            marker = self.marker(chapter)
        else:
            marker = ""
        chapter.title = text
        return marker

    def html(self, chapter=None, parts=None):
        if chapter is None:
            chapter = self.tree
        if parts is None:
            parts = []
        for child in chapter.children:
            line = self.line_template.format(label=child.label,
                number=child.number, title=child.title)
            parts.append(line)
            self.html(child, parts)
        return "".join(parts)


class FB2Book:

    htmlmap = {
        'body': ("<hr><hr>\n", ""),
        'section': ("<hr>\n", ""),
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
        'stanza': ('<div style="text-align: center;"><p>', "</p></div>"),
        'v': ("", "<br>"),
        'cite': ("<cite>", "</cite>"),
        'text-author': ('<div style="text-align: right">', "</div>"),
        'empty-line': ("<br>", ""),
    }

    def __init__(self, text=None, file=None):
        if text is None:
            handle = self.open(file)
            self.root = ET.parse(handle).getroot()
        else:
            self.root = ET.fromstring(text)
        self.strip_namespaces()
        self.toc = TableOfContents()

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


# it is possible to omit ns stripping - {*} is any namespace since python 3.8
# tree.findall(".//{*}description")
# or include ns separately:
# tree.findall("xmlns:DEAL_LEVEL/xmlns:PAID_OFF", namespaces={'xmlns': 'http://www.test.com'})

    def strip_namespaces(self):
        for element in self.root.iter():
            element.tag = element.tag[element.tag.rfind('}')+1:]

    def author_name(self, author):
        partnames = ("last-name", "first-name", "middle-name", "nickname")
        parts = filter(None, ( author.findtext(p) for p in partnames ) )
        name = ' '.join( (p.strip() for p in parts) )
        return name

    def get_authors(self, info):
        return [self.author_name(a) for a in info.findall("author")]

    def get_annotation(self, info):
        element = info.find('annotation')
        if element is not None:
            return "".join( self.inner_to_html(element) )
        return ""

    def get_sequence_info(self, info):
        sequence = info.find("sequence")
        name = sequence is not None and sequence.attrib.get("name", None)
        if not name:
            return ("", 1)
        name = name.strip()
        number = sequence.attrib.get("number", None)
        try:
            number = int(number)
        except (TypeError, ValueError):
            number = 1
        return (name, number)

    def get_values(self, info, **tags):
        for name,tag in tags.items():
            value = info.findtext(tag)
            if value is not None:
                value = value.strip()
            else:
                value = ""
            setattr(self, name, value)

    def describe(self):
        info = self.root.find("./description/title-info")
        if info is None:
            info = ET.Element("dummy")
        self.get_values(info, date='date', title="book-title")
        self.authors = self.get_authors(info)
        self.genres = [g.text.strip() for g in info.findall("genre") if g.text]
        self.sequence, self.sequence_number = self.get_sequence_info(info)
        self.annotation = self.get_annotation(info)

    def image_link(self, tree):
        for k,v in tree.attrib.items():
            if k.endswith("href"):
                return v

    def image_data(self, link):
        link = link.removeprefix('#')
        for binary in self.root.findall("binary"):
            if binary.attrib['id'] == link:
                content_type = binary.attrib.get("content-type", "image/jpg")
                return binary.text, content_type
        return None, None

    def embed_image(self, link, parts):
        data, content_type  = self.image_data(link)
        if data:
            parts.extend(['<img src="data:', content_type,';base64, ', data, '">\n' ])
        else:
            parts.append(f"<p>Missing image: {link}</p>")

    def external_image(self, link, parts):
        parts.append(f'<img src="{link}">\n')

    def html_image(self, tree, parts=None):
        if parts is None:
            parts = []
        link = self.image_link(tree)
        if not link:
            return parts
        if link[0] == "#":
            self.embed_image(link, parts)
        else:
            self.external_image(link, parts)
        return parts

    def html_coverpage(self, parts=None):
        if parts is None:
            parts = []
        cover = self.root.find("./description/title-info/coverpage/image")
        if cover is not None:
            self.html_image(cover, parts)
        return parts

    def inner_to_html(self, tree, parts=None):
        if parts is None:
            parts = []
        if tree.text:
            parts.append(tree.text)
        for child in tree:
            self.tree_to_html(child, parts)
            if child.tail != None:
                parts.append(child.tail)
        return parts

    def tree_to_text(self, tree):
        text = "".join( self.inner_to_html(tree) )
        text = re.sub(r'<[^<]+?>', '', text)
        return text

    def text_tag(self, tree, parts):
        tag = tree.tag
        is_section = tag in ("body","section")
        if is_section:
            parts.append( self.toc.new_chapter_marker() )
        elif tag == "title":
            marker = self.toc.add_title( self.tree_to_text(tree) )
            parts.append(marker)
        self.inner_to_html(tree, parts)
        if is_section:
            self.toc.end_chapter()

    def tree_to_html(self, tree, parts=None):
        if parts is None:
            parts = []
        tag = tree.tag
        template = self.htmlmap.get(tag, None) or (f"[Unknown: {tag}]", "[Unknown end]")
        parts.append(template[0])
        if tag == "image":
            self.html_image(tree, parts)
        else:
            self.text_tag(tree, parts)
        parts.append( template[1] )
        return parts

    def to_html(self):
        self.toc.clear()
        parts = self.html_coverpage()
        for body in self.root.findall('body'):
            self.tree_to_html(body, parts)
        return "".join(parts)

    def get_toc(self):
        return self.toc.html()
