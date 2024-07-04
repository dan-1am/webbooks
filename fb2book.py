#! /usr/bin/env python3

# https://github.com/genych/fb2-parser/
# www.fictionbook.org/index.php/Описание_формата_FB2_от_Sclex

import xml.etree.ElementTree as ET
import re
import os


class TableOfContents:

    def __init__(self):
        self.tree = []
        self.counts = [0]

    def new_chapter(self):
        self.counts[-1] += 1
        chapter = dict(
            title="untitled",
            named=False,
            level=len(self.counts),
            label=f"toc{len(self.tree)}",
            number=".".join( map(str, self.counts) ),
        )
        self.tree.append(chapter)
        return chapter

    def marker(self, chapter):
        return f"<div id='{chapter['label']}'></div>"

    def subsection(self):
        chapter = self.new_chapter()
        self.counts.append(0)
        return self.marker(chapter)

    def endsection(self):
        self.counts.pop()

    def title(self, text):
        chapter = self.tree[-1]
        if chapter['named']:  # several <title> tags in one section
            chapter = self.new_chapter()
            marker = self.marker(chapter)
        else:
            marker = ""
        chapter['title'] = text
        chapter['named'] = True
        return marker

    def html(self):
        parts = []
        for ch in self.tree:
            label = ch['label']
            parts.append(f"<a href='#{label}'>{ch['number']}. {ch['title']}</a><br>\n")
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
        data = dict( date = info.findtext('date'), title = info.findtext("book-title") )
        for k,v in data.items():
            setattr(self, k, v and v.strip())
        self.authors = self.get_authors(info)
        self.genres = [g.text.strip() for g in info.findall("genre") if g.text is not None]
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
            parts.append( self.toc.subsection() )
        elif tag == "title":
            text = "".join( self.html_inside(tree) )
            text = re.sub(r'<[^<]+?>', '', text)
            parts.append( self.toc.title(text) )
        self.html_inside(tree, parts)
        parts.append( template[1] )
        if is_section:
            self.toc.endsection()
        return parts

    def html(self):
        self.toc = TableOfContents()
        parts = self.html_coverpage()
        for body in self.root.findall('body'):
            self.html_tag(body, parts)
        return "".join(parts)

    def get_toc(self):
        return self.toc.html()


if __name__ == '__main__':
    name="example.fb2"
    FB2Book(file=name).describe()
