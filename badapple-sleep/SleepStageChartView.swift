import SwiftUI

struct SleepStageChartView: View {
    let segments: [SleepSegment]
    let date: Date

    private let startHour = 21
    private let endHour = 7
    private let stageOrder: [SleepStage] = [.awake, .rem, .core, .deep]

    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            Text("Sleep")
                .font(.largeTitle)
                .fontWeight(.bold)
                .foregroundColor(.white)
            Text(date.formatted(date: .abbreviated, time: .omitted))
                .font(.subheadline)
                .foregroundColor(.secondary)
            chartView.padding(.top, 8)
        }
        .padding(20)
        .background(Color(red: 0.11, green: 0.11, blue: 0.12))
    }

    private var chartView: some View {
        let barH: CGFloat = 22
        let barGap: CGFloat = 10
        let labelW: CGFloat = 52
        let chartH = CGFloat(stageOrder.count) * (barH + barGap) + 30

        return GeometryReader { geo in
            let x0: CGFloat = labelW
            let chartW = geo.size.width - x0 - 8
            let sleepMinutes = CGFloat(((endHour - startHour + 24) % 24) * 60)

            ZStack(alignment: .topLeading) {
                ForEach(Array(stageOrder.enumerated()), id: \.offset) { i, stage in
                    let y = CGFloat(i) * (barH + barGap)
                    Text(label(stage))
                        .font(.system(size: 13, weight: .medium))
                        .foregroundColor(color(stage))
                        .position(x: labelW / 2, y: y + barH / 2)
                }

                ForEach(Array(segments.enumerated()), id: \.offset) { _, seg in
                    if let si = stageOrder.firstIndex(of: seg.stage) {
                        let x1 = ttx(seg.start, chartW: chartW, x0: x0)
                        let x2 = ttx(seg.end, chartW: chartW, x0: x0)
                        let y = CGFloat(si) * (barH + barGap)
                        if x2 > x1 {
                            RoundedRectangle(cornerRadius: barH / 2)
                                .fill(color(seg.stage))
                                .frame(width: x2 - x1, height: barH)
                                .position(x: (x1 + x2) / 2, y: y + barH / 2)
                        }
                    }
                }

                let hrs = Int(sleepMinutes / 60)
                if hrs > 0 {
                    ForEach(0...hrs, id: \.self) { h in
                        let x = x0 + CGFloat(h) / CGFloat(hrs) * chartW
                        Path { p in
                            p.move(to: CGPoint(x: x, y: 0))
                            p.addLine(to: CGPoint(x: x, y: chartH - 30))
                        }
                        .stroke(Color.white.opacity(0.12), lineWidth: 0.5)

                        Text(hourText((startHour + h) % 24))
                            .font(.system(size: 9))
                            .foregroundColor(.secondary)
                            .position(x: x, y: chartH - 14)
                    }
                }
            }
            .frame(height: chartH)
        }
        .frame(height: chartH)
    }

    private func ttx(_ date: Date, chartW: CGFloat, x0: CGFloat) -> CGFloat {
        let h = Calendar.current.component(.hour, from: date)
        let m = Calendar.current.component(.minute, from: date)
        let total = CGFloat(((h - startHour + 24) % 24) * 60 + m)
        let duration = CGFloat(((endHour - startHour + 24) % 24) * 60)
        return x0 + total / duration * chartW
    }

    private func label(_ s: SleepStage) -> String {
        switch s { case .awake: "Awake"; case .rem: "REM"; case .core: "Core"; case .deep: "Deep" }
    }

    private func color(_ s: SleepStage) -> Color {
        switch s {
        case .awake: Color(red: 1, green: 0.62, blue: 0.18)
        case .rem:   Color(red: 0.39, green: 0.82, blue: 1)
        case .core:  Color(red: 0.23, green: 0.51, blue: 0.96)
        case .deep:  Color(red: 0.37, green: 0.36, blue: 0.90)
        }
    }

    private func hourText(_ h: Int) -> String {
        let s = h < 12 ? "AM" : "PM"
        var v = h; if v == 0 { v = 12 } else if v > 12 { v -= 12 }
        return "\(v)\(s)"
    }
}
