import svgwrite


dwg = svgwrite.Drawing('stamp.svg', size=('110', '110'))
dwg.embed_google_web_font(name='Song Myung', uri='https://fonts.googleapis.com/css2?family=Song+Myung')
dwg.add(dwg.circle((55, 55), r=53, fill='none', stroke=svgwrite.rgb(201, 0, 0), stroke_width=3))
dwg.add(dwg.text('블', insert=(13, 52), fill='#C90000', font_family="Song Myung", font_size="50"))
dwg.add(dwg.text('뭅', insert=(53, 52), fill='#C90000', font_family="Song Myung", font_size="50"))
dwg.add(dwg.text('닥', insert=(13, 92), fill='#C90000', font_family="Song Myung", font_size="50"))
dwg.add(dwg.text('스', insert=(53, 92), fill='#C90000', font_family="Song Myung", font_size="50"))
dwg.save()