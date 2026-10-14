import Foundation
import PDFKit

let arguments = CommandLine.arguments
let document = PDFDocument(url: URL(fileURLWithPath: arguments[1]))!
var pages: [[String: Any]] = []
for index in 0..<document.pageCount {
    let page = document.page(at: index)!
    pages.append(["page": index + 1, "text": page.string ?? ""])
}
let data = try JSONSerialization.data(withJSONObject: pages, options: [.prettyPrinted, .sortedKeys])
try data.write(to: URL(fileURLWithPath: arguments[2]))
print("Extracted \(document.pageCount) pages for document QA only.")
