from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
base = Path(r"C:\zenlab-Projects\ba-thesis\implementation-concept")
docx = base / "DeviceIntegrationPlugin_Kurzkonzept_kompakt.docx"
tmp = base / ".render" / "compact_image_refresh.docx"
image = base / "diagrams" / "07_gesamtklassendiagramm_implementierung.png"
with ZipFile(docx, "r") as zin, ZipFile(tmp, "w", ZIP_DEFLATED) as zout:
    for info in zin.infolist():
        data = image.read_bytes() if info.filename == "word/media/image3.png" else zin.read(info.filename)
        zout.writestr(info, data)
tmp.replace(docx)
print(docx)