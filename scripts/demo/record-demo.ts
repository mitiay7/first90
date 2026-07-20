import { copyFileSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { chromium, type BrowserContext, type Page } from "@playwright/test";
import { artifactPaths, ensureArtifactDirectories, rawVideoDir } from "./demo-files";
import {
  executeScene,
  settleVisuals,
  waitUntilTimelineMs,
  type RecordingState,
} from "./demo-actions";
import type { DemoTimeline } from "./demo-types";

const defaultBaseUrl = "https://first90.hub.lea-dev.site";

export async function recordDemo(): Promise<void> {
  ensureArtifactDirectories();
  const timeline = JSON.parse(readFileSync(artifactPaths.timeline, "utf8")) as DemoTimeline;
  const baseUrl = (process.env.DEMO_BASE_URL ?? defaultBaseUrl).replace(/\/$/, "");
  const browser = await chromium.launch({ headless: true });
  const consoleLines: string[] = [];
  const networkLines: string[] = [];
  let context: BrowserContext | null = null;
  let page: Page | null = null;

  try {
    const setupContext = await browser.newContext({
      viewport: { width: 1920, height: 1080 },
      reducedMotion: "reduce",
    });
    const setupPage = await setupContext.newPage();
    const setupReset = await setupContext.request.post(`${baseUrl}/api/v1/demo/reset`);
    if (!setupReset.ok()) throw new Error(`Demo reset failed with ${setupReset.status()}`);
    await setupPage.goto(`${baseUrl}/presentation?recording=true&scene=01`);
    await setupPage.getByTestId("presentation-hook").waitFor();
    const storageState = await setupContext.storageState();
    await setupContext.close();

    context = await browser.newContext({
      storageState,
      viewport: { width: 1920, height: 1080 },
      recordVideo: { dir: rawVideoDir, size: { width: 1920, height: 1080 } },
      reducedMotion: "reduce",
      colorScheme: "light",
      locale: "en-GB",
      deviceScaleFactor: 1,
    });
    await context.tracing.start({ screenshots: true, snapshots: true, sources: false });
    page = await context.newPage();
    page.on("console", (message) =>
      consoleLines.push(`${message.type().toUpperCase()} ${message.text()}`),
    );
    page.on("pageerror", (error) => consoleLines.push(`PAGEERROR ${error.message}`));
    page.on("response", (response) => {
      const responseUrl = new URL(response.url());
      if (
        responseUrl.origin === new URL(baseUrl).origin &&
        responseUrl.pathname.startsWith("/api/")
      ) {
        networkLines.push(
          `${response.request().method()} ${response.status()} ${responseUrl.pathname}`,
        );
      }
    });

    const video = page.video();
    const pageCreatedAt = Date.now();
    await page.goto(`${baseUrl}/presentation?recording=true&scene=01`);
    await page.getByTestId("presentation-hook").waitFor();
    await settleVisuals(page);
    const timelineStartedAt = Date.now();
    const recordingState: RecordingState = {
      participantJourneyRecorded: false,
      coachResponseRecorded: false,
      coachMode: null,
      endingCardShown: false,
    };
    const scenesCompleted: string[] = [];

    for (const scene of timeline.scenes) {
      await waitUntilTimelineMs(timelineStartedAt, scene.startMs);
      await executeScene(
        scene.execute,
        { page, baseUrl, timelineStartedAt, scene },
        recordingState,
      );
      await waitUntilTimelineMs(timelineStartedAt, scene.endMs);
      const overrunMs = Date.now() - (timelineStartedAt + scene.endMs);
      if (overrunMs > 1_000) throw new Error(`${scene.id} overran its timeline by ${overrunMs}ms`);
      scenesCompleted.push(scene.id);
    }

    if (!recordingState.participantJourneyRecorded)
      throw new Error("Participant journey actions were not recorded");
    if (!recordingState.coachResponseRecorded)
      throw new Error("Coach response was not recorded");
    if (!recordingState.coachMode) throw new Error("Coach mode was not recorded");
    if (!recordingState.endingCardShown) throw new Error("Ending card was not recorded");
    const finalReset = await context.request.post(`${baseUrl}/api/v1/demo/reset`);
    if (!finalReset.ok()) throw new Error(`Final demo reset failed with ${finalReset.status()}`);
    await context.tracing.stop({ path: artifactPaths.trace });
    await context.close();
    context = null;
    if (!video) throw new Error("Playwright did not create a browser video");
    const sourceVideo = await video.path();
    rmSync(artifactPaths.browserVideo, { force: true });
    copyFileSync(sourceVideo, artifactPaths.browserVideo);

    writeFileSync(artifactPaths.browserConsole, `${consoleLines.join("\n")}\n`);
    writeFileSync(artifactPaths.browserNetwork, `${networkLines.join("\n")}\n`);
    writeFileSync(
      artifactPaths.recordingReport,
      `${JSON.stringify(
        {
          version: 1,
          baseUrl,
          timelineDurationMs: timeline.totalDurationMs,
          videoTrimStartMs: timelineStartedAt - pageCreatedAt,
          scenesCompleted,
          ...recordingState,
        },
        null,
        2,
      )}\n`,
    );
    console.log(`Browser recording: ${artifactPaths.browserVideo}`);
  } catch (error) {
    if (page)
      await page
        .screenshot({ path: artifactPaths.failureScreenshot, fullPage: false })
        .catch(() => undefined);
    if (context) await context.tracing.stop({ path: artifactPaths.trace }).catch(() => undefined);
    writeFileSync(artifactPaths.browserConsole, `${consoleLines.join("\n")}\n`);
    writeFileSync(artifactPaths.browserNetwork, `${networkLines.join("\n")}\n`);
    throw error;
  } finally {
    if (context) await context.request.post(`${baseUrl}/api/v1/demo/reset`).catch(() => undefined);
    if (context) await context.close().catch(() => undefined);
    await browser.close();
  }
}

if (import.meta.url === `file://${process.argv[1]}`) void recordDemo();
