Option Explicit
Dim word, doc, inputPath, outputPath
inputPath = WScript.Arguments(0)
outputPath = WScript.Arguments(1)
Set word = CreateObject("Word.Application")
word.Visible = False
word.DisplayAlerts = 0
Set doc = word.Documents.Open(inputPath, False, True)
doc.ExportAsFixedFormat outputPath, 17
doc.Close False
word.Quit
Set doc = Nothing
Set word = Nothing
