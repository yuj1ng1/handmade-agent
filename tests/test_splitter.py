from docx.text.paragraph import Paragraph
from docx.table import Table
from docx.oxml.text.paragraph import CT_P
from docx.oxml.table import CT_Tbl 
from docx import Document as Docxdocument
from pathlib import Path

base_path=Path(__file__).resolve().parents[1]
file_path=(
    base_path
    /"rag_text"
    /"程序设计实训完整报告.docx"
) 

document=Docxdocument(file_path)

def iter_blocks(document):
    for child in document.element.body.iterchildren():
        if isinstance(child,CT_P):
            yield Paragraph(
                child,
                document
            )
        elif isinstance(child,CT_Tbl):
            yield Table(
                child,
                document
            )
blocks=[]

for block in iter_blocks(document):

    if isinstance(block,Paragraph):
        para_text=block.text.strip()
        if para_text:
            blocks.append(
                {
                    "type":"paragraph",
                    "text":para_text
                }
            )

    elif isinstance(block,Table):
        table_lines=[]
        for row in block.rows:
            cells=[]
            for cell in row.cells:
                text=cell.text.strip()
                cells.append(text)
            row_text=" | ".join(cells)
            if row_text:
                table_lines.append(row_text)
        if table_lines:
            table_text="\n".join(
                table_lines
            )
            blocks.append(
                {
                    "type":"table",
                    "text":table_text
                }
            )

print(blocks)