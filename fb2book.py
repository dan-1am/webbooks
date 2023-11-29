#! /usr/bin/env python3

# https://github.com/genych/fb2-parser/
# www.fictionbook.org/index.php/Описание_формата_FB2_от_Sclex

import xml.etree.ElementTree as ET
import os



class FB2Book:

    htmlmap = {
        'body': ("<hr><hr>\n", ""),
        'section': ("<hr>\n", ""),
        'title': ("<h2>", "</h2>\n"),
        'subtitle': ("<h3>", "</h3>\n"),
        'epigraph': ('<div style="text-align: right; font-style: italic">', "</div>\n"),
        'a': ("", ""),
        'p': ("<p>", "</p>\n"),
        'table': ('<table border="1">\n', "</table>\n"),
        'tr': ("<tr>\n", "</tr>\n"),
        'th': ("<th>\n", "</th>\n"),
        'td': ("<td>", "</td>\n"),
        'emphasis': ("<em>", "</em>\n"),
        'strong': ("<strong>", "</strong>\n"),
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
        partnames = ("last-name","first-name","middle-name", "nickname")
        parts = filter(None, ( author.findtext(t) for t in partnames ) )
        name = ' '.join( (p.strip() for p in parts) )
        return name

    def get_authors(self, info):
        return [self.author_name(a) for a in info.findall("author")]

    def get_annotation(self, info):
        tagged = info.find('annotation')
        if tagged:
            return "".join( self.html_inside(tagged) )
        return None

    def get_sequence_info(self, info):
        sequence = info.find("sequence")
        name = sequence is not None and sequence.attrib.get("name", None)
        if not name:
            return (None, None)
        number = sequence.attrib.get("number", None)
        if number:
            number = number.strip()
            if number.isdecimal():
                number = int(number)
        return (name.strip(), number)

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
        if tree.tag == "image":
            self.html_picture(tree, parts)
            return parts
        template = self.htmlmap.get(tree.tag, None) or (f"[Unknown: {tree.tag}]", "[Unknown end]")
        parts.append( template[0] )
        self.html_inside(tree, parts)
        parts.append( template[1] )
        return parts

    def html(self):
        parts = self.html_coverpage()
        for body in self.root.findall('body'):
            self.html_tag(body, parts)
        return "".join(parts)



if __name__ == '__main__':
    name="example.fb2"
    FB2Book(file=name).describe()
