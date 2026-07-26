import SwiftUI

struct ContentView: View {
    @State private var status = "Ready"
    @State private var task: Task<Void, Never>?

    var body: some View {
        VStack(spacing: 12) {
            Text(status).font(.headline).foregroundColor(.white)
            Button("Import All Sleep") { startImport() }.buttonStyle(.borderedProminent)
            Button("Delete All Sleep") { startDelete() }.buttonStyle(.bordered).tint(.red)
        }
        .padding()
        .background(Color(red: 0.11, green: 0.11, blue: 0.12))
        .preferredColorScheme(.dark)
    }

    private func startImport() {
        task?.cancel(); status = "Importing..."
        task = Task {
            do {
                try await HealthKitManager.shared.requestPermissions()
                try await HealthKitManager.shared.importAllNights { done, total in
                    status = "\(done)/\(total)"
                }
                status = "Import done"
            } catch { status = "Err: \(error)" }
        }
    }

    private func startDelete() {
        task?.cancel(); status = "Deleting..."
        task = Task {
            do {
                try await HealthKitManager.shared.requestPermissions()
                try await HealthKitManager.shared.deleteAllSleepData()
                status = "Deleted"
            } catch { status = "Err: \(error)" }
        }
    }
}
