from pathlib import Path
from docx import Document
path = Path(r"C:\zenlab-Projects\ba-thesis\implementation-concept\DeviceIntegrationPlugin_Kurzkonzept_kompakt.docx")
doc = Document(path)
old = "Gerätespezifische Protokolle und TreeNode-Logik bleiben in den bestehenden DeviceAgents. Für den MVP gilt YAGNI: eine In-Memory-Registry, kein Gateway, kein neuer WebAPI-Adapter und keine zusätzlichen Manager-Schichten. Interfaces werden nur an echten Prozess- oder Modulgrenzen verwendet; interne Helper werden erst bei einer klaren eigenen Verantwortung extrahiert. Abhängigkeiten werden im Composition Root verdrahtet, nicht über Service-Locator oder globale Zustände."
new = "Gerätespezifische Protokolle und TreeNode-Logik bleiben in den bestehenden DeviceAgents. Für den MVP gilt YAGNI: eine In-Memory-Registry, kein Gateway, kein WebAPI-Adapter im Kernumfang und keine generischen zusätzlichen Manager- oder Repository-Schichten. Interfaces werden nur an echten Prozess- oder Modulgrenzen verwendet; interne Helper werden erst bei einer klaren eigenen Verantwortung extrahiert. Abhängigkeiten werden im Composition Root verdrahtet, nicht über Service-Locator oder globale Zustände."
count = 0
for paragraph in doc.paragraphs:
    if paragraph.text == old:
        paragraph.runs[0].text = new
        for run in paragraph.runs[1:]:
            run.text = ""
        count += 1
if count != 1:
    raise RuntimeError(f"Expected one replacement, found {count}")
doc.save(path)
print(path)