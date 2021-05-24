from svgpathtools import wsvg, Line, QuadraticBezier, Path
from freetype import Face
from bs4 import BeautifulSoup
from wand.api import library
import wand.color
import wand.image


def tuple_to_imag(t):
    return t[0] + t[1] * 1j


letter = ['김', '블', '루', '인']

face = Face('HJHanjeonseoB.ttf')
face.set_char_size(48 * 64)
dValueList = []
for i in letter:
    face.load_char(i)
    outline = face.glyph.outline
    y = [t[1] for t in outline.points]
    outline_points = [(p[0], max(y) - p[1]) for p in outline.points]
    start, end = 0, 0
    paths = []

    for i in range(len(outline.contours)):
        end = outline.contours[i]
        points = outline_points[start:end + 1]
        points.append(points[0])
        tags = outline.tags[start:end + 1]
        tags.append(tags[0])

        segments = [[points[0], ], ]
        for j in range(1, len(points)):
            segments[-1].append(points[j])
            if tags[j] and j < (len(points) - 1):
                segments.append([points[j], ])
        for segment in segments:
            if len(segment) == 2:
                paths.append(Line(start=tuple_to_imag(segment[0]),
                                end=tuple_to_imag(segment[1])))
            elif len(segment) == 3:
                paths.append(QuadraticBezier(start=tuple_to_imag(segment[0]),
                                            control=tuple_to_imag(segment[1]),
                                            end=tuple_to_imag(segment[2])))
            elif len(segment) == 4:
                C = ((segment[1][0] + segment[2][0]) / 2.0,
                    (segment[1][1] + segment[2][1]) / 2.0)

                paths.append(QuadraticBezier(start=tuple_to_imag(segment[0]),
                                            control=tuple_to_imag(segment[1]),
                                            end=tuple_to_imag(C)))
                paths.append(QuadraticBezier(start=tuple_to_imag(C),
                                            control=tuple_to_imag(segment[2]),
                                            end=tuple_to_imag(segment[3])))
        start = end + 1

    path = Path(*paths)
    wsvg(path, filename="stamp.html")

    with open('stamp.html') as stampRaw:
        soup = BeautifulSoup(stampRaw.read(), features='html.parser')
        dValue = soup.find('path')['d']
        dValueList.append(dValue)

stampTemp = \
"""<svg xmlns="http://www.w3.org/2000/svg" xmlns:ev="http://www.w3.org/2001/xml-events" xmlns:xlink="http://www.w3.org/1999/xlink" baseProfile="full" width="180px" height="180px" version="1.1" viewBox="0 0 3500 3500">
    <svg width="3500" height="3500" viewBox="0 0 3500 3500" xmlns="http://www.w3.org/2000/svg">
        <circle cx="1750" cy="1750" fill="none" stroke="#C90000" stroke-width="100" r="1700"></circle>
        <svg x="500" y="530">
            <path id='stamp01' transform="scale(0.4, 0.435)" fill="#C90000" stroke="none" d='""" + dValueList[0] + """'/>
        </svg>
        <svg x="1750" y="530">
            <path id='stamp02' transform="scale(0.4, 0.435)" fill="#C90000" stroke="none" d='""" + dValueList[1] + """'/>
        </svg>
        <svg x="500" y="1780">
            <path id='stamp03' transform="scale(0.4, 0.435)" fill="#C90000" stroke="none" d='""" + dValueList[2] + """'/>
        </svg>
        <svg x="1750" y="1780">
            <path id='stamp04' transform="scale(0.4, 0.435)" fill="#C90000" stroke="none" d='""" + dValueList[3] + """'/>
        </svg>
    </svg>
</svg>"""

with open('stamp.svg', 'w') as stampSVG:
    stampSVG.write(stampTemp)

with open('stamp.svg', "r") as stampSVG:
    with wand.image.Image() as stampPNG:
        with wand.color.Color('transparent') as background_color:
            library.MagickSetBackgroundColor(stampPNG.wand,
                                            background_color.resource)
        svg_blob = stampSVG.read().encode('utf-8')
        stampPNG.read(blob=svg_blob, resolution = 72)
        png_image = stampPNG.make_blob("png32")

with open('stamp.png', "wb") as out:
    out.write(png_image)