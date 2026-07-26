import Foundation
import HealthKit

final class HealthKitManager {

    static let shared = HealthKitManager()

    let store = HKHealthStore()

    func requestPermissions() async throws {
        guard HKHealthStore.isHealthDataAvailable() else { return }
        guard let sleepType = HKObjectType.categoryType(forIdentifier: .sleepAnalysis) else { return }
        try await store.requestAuthorization(toShare: [sleepType], read: [sleepType])
    }

    func importCSV(named filename: String) async throws {
        guard let sleepType = HKObjectType.categoryType(forIdentifier: .sleepAnalysis) else { return }
        let segments = try CSVParser.load(named: filename)
        let samples = segments.map {
            HKCategorySample(type: sleepType, value: value(for: $0.stage), start: $0.start, end: $0.end)
        }
        guard !samples.isEmpty else {
            throw NSError(domain: "HK", code: 2, userInfo: [NSLocalizedDescriptionKey: "No samples in \(filename)"])
        }
        try await store.save(samples)
    }

    func importAllNights(onProgress: @escaping (Int, Int) -> Void) async throws {
        guard let sleepType = HKObjectType.categoryType(forIdentifier: .sleepAnalysis) else { return }
        let files = discoverCSVFiles().files
        guard !files.isEmpty else { return }
        var batch = [HKSample]()
        for (i, file) in files.enumerated() {
            let segments = try CSVParser.load(named: file)
            let samples: [HKSample] = segments.map {
                HKCategorySample(type: sleepType, value: value(for: $0.stage), start: $0.start, end: $0.end)
            }
            batch.append(contentsOf: samples)
            if batch.count >= 5 * 240 {
                try await store.save(batch)
                batch.removeAll()
            }
            onProgress(i + 1, files.count)
        }
        if !batch.isEmpty { try await store.save(batch) }
    }

    func discoverCSVFiles() -> (files: [String], debug: String) {
        let urls = Bundle.main.urls(forResourcesWithExtension: "csv", subdirectory: nil) ?? []
        let sleepURLs = urls.filter { $0.lastPathComponent.hasPrefix("sleep_") }
        let files = sleepURLs.map { $0.deletingPathExtension().lastPathComponent }.sorted()
        return (files, "\(files.count) files")
    }

    func deleteAllSleepData() async throws {
        guard let sleepType = HKObjectType.categoryType(forIdentifier: .sleepAnalysis) else { return }
        let predicate = HKQuery.predicateForSamples(withStart: .distantPast, end: .distantFuture)
        try await store.deleteObjects(of: sleepType, predicate: predicate)
    }

    private func value(for stage: SleepStage) -> Int {
        switch stage {
        case .awake: return HKCategoryValueSleepAnalysis.awake.rawValue
        case .rem:   return HKCategoryValueSleepAnalysis.asleepREM.rawValue
        case .core:  return HKCategoryValueSleepAnalysis.asleepCore.rawValue
        case .deep:  return HKCategoryValueSleepAnalysis.asleepDeep.rawValue
        }
    }
}
