import Foundation
import PDFKit
let document = PDFDocument(url: URL(fileURLWithPath: "main.pdf"))!
precondition(document.pageCount == 47)
for index in [41, 42, 46] {
    let page = document.page(at: index)!
    print("PAGE \(index + 1)")
    print(page.string ?? "")
    if index == 46 {
        let urls = Array(Set(page.annotations.compactMap { $0.url?.absoluteString })).sorted()
        precondition(urls.count == 15)
        for url in urls { print("LINK \(url)") }
        precondition(urls.contains("https://github.com/realsenseai/librealsense/wiki/Troubleshooting-Q%26A"))
    }
}
print("47 PDF pages; table and reference text extracted; 15 reference links present.")
