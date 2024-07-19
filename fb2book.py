#! /usr/bin/env python3

# https://github.com/gribuser/fb2
# https://github.com/genych/fb2-parser/
# www.fictionbook.org/index.php/Описание_формата_FB2_от_Sclex

import xml.etree.ElementTree as ET
import re
import os


class Chapter:
    def __init__(self, label):
        self.title = ""
        self.label = label
        self.number = ""
        self.children = []

    def named(self):
        return self.title

    def add_child(self, label):
        child = type(self)(label)
        last_count = 1+len(self.children)
        child.number = (f"{self.number}.{last_count}" if self.number
            else f"{last_count}")
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
        if chapter.named():  # several <title> tags in one section
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
        if text:
            self.root = ET.fromstring(text)
        else:
            self.root = ET.parse(file).getroot()
        self.strip_namespaces()
        self.toc = TableOfContents()

# it is possible to omit ns stripping - {*} is any namespace since python 3.8
# tree.findall(".//{*}description")
# or include ns separately:
# tree.findall("xmlns:DEAL_LEVEL/xmlns:PAID_OFF", namespaces={'xmlns': 'http://www.test.com'})

    def strip_namespaces(self):
        for element in self.root.iter():
            element.tag = element.tag.partition('}')[-1]

    def author_name(self, author):
        partnames = ("last-name", "first-name", "middle-name", "nickname")
        parts = filter(None, ( author.findtext(p) for p in partnames ) )
        name = ' '.join( (p.strip() for p in parts) )
        return name

    def get_authors(self, info):
        return [self.author_name(a) for a in info.findall("author")]

    def get_annotation(self, info):
        element = info.find('annotation')
        if element:
            return "".join( self.html_inside(element) )
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

    def describe(self):
        info = self.root.find("./description/title-info")
        data = dict(date='date', title="book-title")
        for name,tag in data.items():
            value = info.findtext(tag)
            if value:
                value = value.strip()
            else:
                value = ""
            setattr(self, name, value)
        self.authors = self.get_authors(info)
        self.genres = [g.text.strip() for g in info.findall("genre") if g.text]
        self.sequence, self.sequence_number = self.get_sequence_info(info)
        self.annotation = self.get_annotation(info)

    def html_picture(self, tree, parts=None):
        if parts is None:
            parts = []
        for k,v in tree.attrib.items():
            if k.endswith("href"):
                link = v
                break
        else:
            return parts
        if link[0] != "#":
            parts.append(f'<img src="{link}">\n')
            return parts
        link = link[1:]
        for binary in self.root.findall("binary"):
            if binary.attrib['id'] == link:
                content_type = binary.attrib.get("content-type","text/plain")
                parts.extend(['<img src="data:', content_type,';base64, ', binary.text, '">\n' ])
                return parts
        parts.append(f"<p>Missing image: {link}</p>")
        return parts
#      <image l:href="#cover.jpg"/>
#  <binary id="cover.jpg" content-type="image/jpeg">/9j/4AAQSkZJRgABAQAAAQABAAD/wAARCARgArwDASIAAhEBAxEB/9sAQwALCAgKCAcLCgkK

    def html_coverpage(self, parts=None):
        if parts is None:
            parts = []
        cover = self.root.find("./description/title-info/coverpage/image")
        if cover is not None:
            self.html_picture(cover, parts)
        return parts

    def html_inside(self, tree, parts=None):
        if parts is None:
            parts = []
        if tree.text:
            parts.append(tree.text)
        for child in tree:
            self.html_tag(child, parts)
            if child.tail != None:
                parts.append(child.tail)
        return parts

    def html_tag(self, tree, parts=None):
        if parts is None:
            parts = []
        tag = tree.tag
        if tag == "image":
            self.html_picture(tree, parts)
            return parts
        template = self.htmlmap.get(tag, None) or (f"[Unknown: {tag}]", "[Unknown end]")
        parts.append(template[0])
        is_section = tag in ("body","section")
        if is_section:
            parts.append( self.toc.new_chapter_marker() )
        elif tag == "title":
            text = "".join( self.html_inside(tree) )
            text = re.sub(r'<[^<]+?>', '', text)
            parts.append( self.toc.add_title(text) )
        self.html_inside(tree, parts)
        parts.append( template[1] )
        if is_section:
            self.toc.end_chapter()
        return parts

    def html(self):
        self.toc.clear()
        parts = self.html_coverpage()
        for body in self.root.findall('body'):
            self.html_tag(body, parts)
        return "".join(parts)

    def get_toc(self):
        return self.toc.html()


if __name__ == '__main__':
    name="example.fb2"
    FB2Book(file=name).describe()
