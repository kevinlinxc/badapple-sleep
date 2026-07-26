import Foundation

enum CSVParser {

    static func load(named filename: String) throws -> [SleepSegment] {

        guard let url = Bundle.main.url(forResource: filename, withExtension: "csv") else {
            throw NSError(domain: "CSV", code: 1, userInfo: [
                NSLocalizedDescriptionKey: "CSV not found: \(filename).csv"
            ])
        }

        let text = try String(contentsOf: url)

        let formatter = DateFormatter()
        formatter.dateFormat = "yyyy-MM-dd'T'HH:mm:ss"
        formatter.locale = Locale(identifier: "en_US_POSIX")
        formatter.timeZone = TimeZone.current

        var segments: [SleepSegment] = []

        let lines = text
            .split(whereSeparator: \.isNewline)
            .dropFirst()

        for line in lines {

            let cols = line.split(separator: ",")

            guard cols.count == 3 else { continue }

            guard
                let start = formatter.date(from: String(cols[0])),
                let end = formatter.date(from: String(cols[1]))
            else {
                continue
            }

            let stage: SleepStage

            switch cols[2].trimmingCharacters(in: .whitespaces).lowercased() {
            case "awake":
                stage = .awake
            case "core":
                stage = .core
            case "deep":
                stage = .deep
            case "rem":
                stage = .rem
            default:
                continue
            }

            segments.append(
                SleepSegment(
                    start: start,
                    end: end,
                    stage: stage
                )
            )
        }

        return segments
    }
}
