import Foundation
import PDFKit
let doc = PDFDocument(url: URL(fileURLWithPath: "main.pdf"))!
precondition(doc.pageCount == 20, "Expected 16 main slides plus 4 backups")
var output = ""
for i in 0..<doc.pageCount {
    let page = doc.page(at: i)!
    let rect = page.bounds(for: .mediaBox)
    precondition(abs(rect.width / rect.height - 16.0 / 9.0) < 0.001)
    let content = page.string ?? ""
    precondition(!content.isEmpty, "Empty slide")
    output += "PAGE \(i + 1)\n\(content)\n\n"
}
try output.write(toFile: "qa/pdf-text.txt", atomically: true, encoding: .utf8)
print("20 nonempty 16:9 pages; text extraction complete")
