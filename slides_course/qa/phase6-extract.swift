import Foundation
import PDFKit
let d = PDFDocument(url: URL(fileURLWithPath: CommandLine.arguments[1]))!
for i in 0..<d.pageCount {
 let p=d.page(at:i)!, b=p.bounds(for:.mediaBox)
 precondition(abs(b.width/b.height-16.0/9.0)<0.001)
 precondition(!(p.string ?? "").isEmpty)
 print("PAGE \(i+1)\n\(p.string ?? "")\n")
}
