import Foundation
import PDFKit
let d = PDFDocument(url: URL(fileURLWithPath: CommandLine.arguments[1]))!
for i in 0..<d.pageCount { print("PAGE \(i+1)\n\(d.page(at:i)!.string ?? "")\n") }
