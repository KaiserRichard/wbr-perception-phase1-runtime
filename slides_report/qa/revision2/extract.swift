import Foundation
import PDFKit
let doc = PDFDocument(url: URL(fileURLWithPath: "main.pdf"))!
precondition(doc.pageCount == 22, "Expected 17 main slides, 4 backups and references")
var output = ""
for i in 0..<doc.pageCount {
    let page = doc.page(at: i)!
    let rect = page.bounds(for: .mediaBox)
    precondition(abs(rect.width / rect.height - 16.0 / 9.0) < 0.001)
    let content = page.string ?? ""
    precondition(!content.isEmpty, "Empty slide")
    for forbidden in ["Source:", "experiments/", "REPORT.md", "provenance.txt", "SDK"] {
        precondition(!content.contains(forbidden), "Unexpected source/path/unexplained SDK on slide")
    }
    output += "PAGE \(i + 1)\n\(content)\n\n"
}
try output.write(toFile: "qa/revision2/pdf-text.txt", atomically: true, encoding: .utf8)
print("22 nonempty 16:9 pages; no source lines, evidence paths or unexplained SDK")
