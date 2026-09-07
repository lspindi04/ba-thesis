from pathlib import Path
from docx import Document
from docx.shared import Pt
path = Path(r"C:\zenlab-Projects\ba-thesis\implementation-concept\DeviceIntegrationPlugin_Kurzkonzept_kompakt.docx")
doc = Document(path)
count = 0
for paragraph in doc.paragraphs:
    if paragraph.text.startswith("Die Modulnamen beschreiben Verantwortungs- und Abhängigkeitsgrenzen."):
        paragraph.paragraph_format.space_before = Pt(6)
        paragraph.paragraph_format.space_after = Pt(6)
        count += 1
if count != 1:
    raise RuntimeError(count)
doc.save(path)
print(path)