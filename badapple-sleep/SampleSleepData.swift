import Foundation

struct SleepSegment {

    let start: Date
    let end: Date
    let stage: SleepStage

}

enum SleepStage {
    case awake
    case core
    case rem
    case deep
}

struct SampleSleepData {

    static func july23() -> [SleepSegment] {

        let cal = Calendar.current

        func make(_ hour: Int,
                  _ minute: Int,
                  _ hour2: Int,
                  _ minute2: Int,
                  stage: SleepStage) -> SleepSegment {

            let start = cal.date(
                from: DateComponents(
                    year: 2026,
                    month: 7,
                    day: 23,
                    hour: hour,
                    minute: minute
                ))!

            let end = cal.date(
                from: DateComponents(
                    year: 2026,
                    month: 7,
                    day: 23,
                    hour: hour2,
                    minute: minute2
                ))!

            return SleepSegment(
                start: start,
                end: end,
                stage: stage
            )
        }

        return [

            make(0,00,0,30, stage: .core),
            make(0,30,1,00, stage: .deep),
            make(1,00,1,20, stage: .rem),
            make(1,20,1,25, stage: .awake),
            make(1,25,2,00, stage: .core),

        ]

    }

}
