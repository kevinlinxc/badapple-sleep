import XCTest

final class badapple_sleepUITests: XCTestCase {
    override func setUpWithError() throws { continueAfterFailure = true }

    @MainActor
    func testPhase1() throws {
        let app = XCUIApplication()
        app.launch()
        
        // Tap import
        let importBtn = app.buttons["Import All Sleep"]
        guard importBtn.waitForExistence(timeout: 10) else {
            snap(app, "no_import_btn"); return
        }
        importBtn.tap()
        
        // Poll for HealthKit permission dialog - OCR says it's "Turn On All" in our app
        for _ in 0..<20 {
            Thread.sleep(forTimeInterval: 1)
            // OCR revealed: dialog is in our app with "Turn On All" button
            for label in ["Turn On All", "Allow", "OK", "Don't Allow", "Continue"] {
                let btn = app.buttons[label]
                if btn.exists { btn.tap(); Thread.sleep(forTimeInterval: 1); break }
            }
            // Also check navigation bar (Allow might be top-right)
            let navAllow = app.navigationBars.buttons["Allow"]
            if navAllow.exists { navAllow.tap(); Thread.sleep(forTimeInterval: 1) }
            // Check SpringBoard too
            let sb = XCUIApplication(bundleIdentifier: "com.apple.springboard")
            for label in ["Allow", "OK"] {
                let b = sb.buttons[label]
                if b.exists { b.tap(); Thread.sleep(forTimeInterval: 1); break }
            }
            // Check if import completed
            if app.staticTexts.containing(NSPredicate(format: "label CONTAINS 'Import done'")).firstMatch.exists {
                break
            }
        }
        
        // Wait for import to complete
        Thread.sleep(forTimeInterval: 5)
        snap(app, "app_after_polling")  // show app state after polling
        let done = app.staticTexts.containing(NSPredicate(format: "label CONTAINS 'Import done'")).firstMatch
        guard done.waitForExistence(timeout: 20) else {
            snap(app, "import_timeout"); return
        }
        Thread.sleep(forTimeInterval: 2)

        // Open Health
        let health = XCUIApplication(bundleIdentifier: "com.apple.Health")
        health.activate()
        Thread.sleep(forTimeInterval: 5)

        // Dismiss Health app's own access screen (if any)
        for label in ["Turn On All", "Allow", "Continue", "Next", "Get Started", "Done"] {
            let hbtn = health.buttons[label]
            if hbtn.waitForExistence(timeout: 3) { hbtn.tap(); Thread.sleep(forTimeInterval: 0.5) }
        }

        // Browse tab
        let browse = health.tabBars.buttons["Browse"]
        if browse.waitForExistence(timeout: 10) { browse.tap(); Thread.sleep(forTimeInterval: 2) }

        // Find and tap Sleep
        var found = false
        for _ in 0..<15 {
            let c = health.cells.containing(NSPredicate(format: "label CONTAINS 'Sleep'")).firstMatch
            if c.exists && c.isHittable { c.tap(); found = true; break }
            health.swipeUp(); Thread.sleep(forTimeInterval: 0.5)
        }
        guard found else { snap(health, "sleep_not_found"); return }
        Thread.sleep(forTimeInterval: 2)

        // Scroll to stages chart
        for _ in 0..<5 { health.swipeUp(); Thread.sleep(forTimeInterval: 0.5) }
        Thread.sleep(forTimeInterval: 2)

        snap(health, "phase1")
    }

    func snap(_ app: XCUIApplication, _ name: String) {
        XCTContext.runActivity(named: name) { act in
            let shot = XCUIScreen.main.screenshot()
            let att = XCTAttachment(screenshot: shot)
            att.name = name; att.lifetime = .keepAlways; act.add(att)
        }
    }
}
