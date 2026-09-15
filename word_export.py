"""Small HTML-to-Word exporter for lesson material, not arbitrary page chrome."""
from io import BytesIO
from bs4 import BeautifulSoup, NavigableString, Tag
from docx import Document
from docx.shared import Inches
from docx.oxml import OxmlElement
from docx.oxml.ns import qn


def export_html(html):
    document = Document()
    section = document.sections[0]
    section.page_width, section.page_height = Inches(8.5), Inches(11)
    soup = BeautifulSoup(html, 'html.parser')
    for unwanted in soup.select('script,style,form,nav,header,footer'):
        unwanted.decompose()

    def inline(node, paragraph):
        if isinstance(node, NavigableString):
            paragraph.add_run(str(node))
        elif node.name == 'br':
            paragraph.add_run().add_break()
        else:
            for child in node.children:
                before = len(paragraph.runs)
                inline(child, paragraph)
                for run in paragraph.runs[before:]:
                    if node.name in ('strong','b'):
                        run.bold=True
                    if node.name in ('em','i'):
                        run.italic=True

    def span(cell, name):
        try:
            value=int(cell.get(name,1))
        except (ValueError,TypeError):
            raise ValueError('Invalid table span; simplify the table before exporting.')
        if not 1<=value<=100:
            raise ValueError('Table span exceeds supported limits.')
        return value

    def table(node, target):
        rows=[row for row in node.find_all('tr') if row.find_parent('table') is node]
        if not rows:
            return
        occupied=set(); placements=[]; width=0
        if len(rows)>1000:
            raise ValueError('Table is too long to export.')
        for r,row in enumerate(rows):
            c=0
            for cell in row.find_all(['td','th'],recursive=False):
                while (r,c) in occupied:
                    c+=1
                rs,cs=span(cell,'rowspan'),span(cell,'colspan')
                if r+rs>len(rows) or c+cs>100:
                    raise ValueError('Invalid table geometry; simplify the table before exporting.')
                positions={(rr,cc) for rr in range(r,r+rs) for cc in range(c,c+cs)}
                if occupied & positions:
                    raise ValueError('Overlapping table cells cannot be exported.')
                occupied.update(positions)
                placements.append((r,c,rs,cs,cell));c+=cs;width=max(width,c)
        if not width:
            return
        result=target.add_table(rows=len(rows),cols=width)
        result.style='Table Grid'
        result.autofit=False
        weights=[22]*width
        for r,c,rs,cs,source in placements:
            if cs==1:
                weights[c]=max(weights[c],min(70,len(source.get_text(' ',strip=True))))
        available=getattr(target,'width',None) or (section.page_width-section.left_margin-section.right_margin)
        for c,weight in enumerate(weights):
            column_width=int(available*weight/sum(weights))
            result.columns[c].width=column_width
            for cell in result.columns[c].cells:
                cell.width=column_width
        borders=OxmlElement('w:tblBorders')
        for edge in ('top','left','bottom','right','insideH','insideV'):
            border=OxmlElement('w:'+edge)
            for key,value in (('val','single'),('sz','4'),('color','D9D9D9')):
                border.set(qn('w:'+key),value)
            borders.append(border)
        result._tbl.tblPr.append(borders)
        for r,c,rs,cs,source in placements:
            dest=result.cell(r,c)
            if rs>1 or cs>1:
                dest=dest.merge(result.cell(r+rs-1,c+cs-1))
            margins=OxmlElement('w:tcMar')
            for edge in ('top','bottom','left','right'):
                margin=OxmlElement('w:'+edge)
                margin.set(qn('w:w'),'100');margin.set(qn('w:type'),'dxa');margins.append(margin)
            dest._tc.get_or_add_tcPr().append(margins)
            render(source,dest)
            # Remove the initial empty cell paragraph when content added its own blocks.
            if len(dest.paragraphs)>1 and not dest.paragraphs[0].text:
                first=dest.paragraphs[0]._element
                first.getparent().remove(first)
            if source.name=='th':
                shading=OxmlElement('w:shd');shading.set(qn('w:fill'),'EAF0F4')
                dest._tc.get_or_add_tcPr().append(shading)
                for para in dest.paragraphs:
                    for run in para.runs:
                        run.bold=True
        if rows[0].find('th',recursive=False):
            properties=result.rows[0]._tr.get_or_add_trPr()
            repeat=OxmlElement('w:tblHeader');repeat.set(qn('w:val'),'true');properties.append(repeat)

    def render(node,target):
        pending=[]
        def flush():
            if pending and any(str(x).strip() for x in pending):
                paragraph=target.add_paragraph()
                for x in pending:
                    inline(x,paragraph)
            pending.clear()
        for child in node.children:
            if isinstance(child,NavigableString):
                if child.strip(): pending.append(child)
                elif pending: pending.append(child)
                continue
            if not isinstance(child,Tag): continue
            if child.name=='table':
                flush();table(child,target)
            elif child.name in ('h1','h2','h3','h4','h5','h6','p','pre','li'):
                flush()
                style=None
                if child.name.startswith('h'):
                    style='Heading '+child.name[1]
                elif child.name=='li':
                    style='List Number' if child.parent.name=='ol' else 'List Bullet'
                paragraph=target.add_paragraph(style=style)
                for item in child.children:
                    if isinstance(item,Tag) and item.name in ('table','ul','ol','p'):
                        if item.name=='table': table(item,target)
                        else: render(item,target)
                    else: inline(item,paragraph)
            elif child.name in ('div','section','article','main','body','html','ul','ol','thead','tbody'):
                flush();render(child,target)
            else:
                pending.append(child)
        flush()

    render(soup.body or soup,document)
    output=BytesIO();document.save(output);output.seek(0)
    return output
