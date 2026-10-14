import Foundation
import PDFKit
let document = PDFDocument(url: URL(fileURLWithPath: "main.pdf"))!
precondition(document.pageCount == 49)
for index in [1, 8, 9, 10, 11, 48] {
    let page = document.page(at: index)!
    print("PAGE \(index + 1)")
    print(page.string ?? "")
    if index == 48 {
        let urls = Array(Set(page.annotations.compactMap { $0.url?.absoluteString })).sorted()
        precondition(urls.count == 16)
        precondition(urls.contains("https://dev.realsenseai.com/docs/projectors/"))
        for url in urls { print("LINK \(url)") }
    }
}
print("49 PDF pages; changed text extracted; 16 clickable reference links present.")
