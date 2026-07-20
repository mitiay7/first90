import type { Page } from "@playwright/test";
import type { DemoTimelineScene } from "./demo-types";

type SceneContext = {
  page: Page;
  baseUrl: string;
  timelineStartedAt: number;
  scene: DemoTimelineScene;
};

export type RecordingState = {
  participantJourneyRecorded: boolean;
  coachResponseRecorded: boolean;
  endingCardShown: boolean;
};

export async function executeScene(
  execute: DemoTimelineScene["execute"],
  context: SceneContext,
  state: RecordingState,
): Promise<void> {
  const actions: Record<string, () => Promise<void>> = {
    showHook: () => showHook(context),
    showProductModel: () => showProductModel(context),
    showParticipantJourney: () => showParticipantJourney(context, state),
    showCoach: () => showCoach(context, state),
    showTailoredCapsules: () => showTailoredCapsules(context),
    showTelegram: () => showTelegram(context),
    showTeamStudio: () => showTeamStudio(context),
    showBuildEvidenceThenEnding: () => showBuildEvidenceThenEnding(context, state),
  };
  const action = actions[execute];
  if (!action) throw new Error(`Unknown demo action: ${execute}`);
  await action();
}

export async function waitUntilTimelineMs(
  timelineStartedAt: number,
  targetMs: number,
): Promise<void> {
  const remainingMs = timelineStartedAt + targetMs - Date.now();
  if (remainingMs > 0) await new Promise((resolve) => setTimeout(resolve, remainingMs));
}

async function showHook({ page }: SceneContext): Promise<void> {
  await visible(page, "presentation-hook");
}

async function showProductModel(context: SceneContext): Promise<void> {
  await gotoAndSettle(context, "/presentation?recording=true&scene=02");
  await visible(context.page, "product-model");
}

async function showParticipantJourney(
  context: SceneContext,
  state: RecordingState,
): Promise<void> {
  const { page, scene, timelineStartedAt } = context;
  await gotoAndSettle(context, "/journey?recording=true");
  await page.getByRole("heading", { name: "Good morning, Jordan." }).waitFor();

  await waitUntilTimelineMs(timelineStartedAt, contentPoint(scene, 0.18));
  await page.getByRole("button", { name: /Complete move/ }).click();
  await page.getByText("Move complete. Your journey is updated.").waitFor();
  await page.waitForTimeout(900);
  await page.waitForLoadState("domcontentloaded");
  await settleVisuals(page);

  await waitUntilTimelineMs(timelineStartedAt, contentPoint(scene, 0.52));
  await page.getByRole("button", { name: "Energy 4 of 5" }).click();
  await page.getByText("Energy signal saved privately.").waitFor();

  await waitUntilTimelineMs(timelineStartedAt, contentPoint(scene, 0.7));
  const journal = page.locator("#journal");
  await journal.scrollIntoViewIfNeeded();
  await journal.getByPlaceholder("Write one honest sentence…").fill(
    "One low-cost question exposed an assumption I can test tomorrow.",
  );
  await journal.getByRole("button", { name: "Save reflection" }).click();
  await page.getByText("Reflection saved. Only you can read it.").waitFor();
  state.participantJourneyRecorded = true;
}

async function showCoach(context: SceneContext, state: RecordingState): Promise<void> {
  const { page } = context;
  await gotoAndSettle(context, "/journey?recording=true#coach");
  const coach = page.locator("#coach");
  await coach.scrollIntoViewIfNeeded();
  await coach
    .getByPlaceholder("I keep getting conflicting priorities…")
    .fill("Two sponsors gave me conflicting priorities. What should I clarify first?");
  await coach.getByRole("button", { name: /Ask coach/ }).click();
  await page
    .locator("#coach-model")
    .filter({ hasText: "Live response" })
    .waitFor({ timeout: 25_000 });
  await page.locator("#coach-answer").scrollIntoViewIfNeeded();
  state.coachResponseRecorded = true;
}

async function showTailoredCapsules(context: SceneContext): Promise<void> {
  const { page, scene, timelineStartedAt } = context;
  await gotoAndSettle(context, "/guide?recording=true#first-days");
  const cards = page.locator(".first-days-grid > article");
  if ((await cards.count()) !== 3) throw new Error("Expected three tailored day cards");
  await cards.nth(0).scrollIntoViewIfNeeded();
  await waitUntilTimelineMs(timelineStartedAt, contentPoint(scene, 0.47));
  await cards.nth(1).scrollIntoViewIfNeeded();
  await waitUntilTimelineMs(timelineStartedAt, contentPoint(scene, 0.76));
  await cards.nth(2).scrollIntoViewIfNeeded();
}

async function showTelegram(context: SceneContext): Promise<void> {
  const { page, scene, timelineStartedAt } = context;
  await gotoAndSettle(context, "/guide?recording=true#telegram");
  const onboarding = page.locator("#telegram");
  await onboarding.scrollIntoViewIfNeeded();
  await onboarding.getByRole("heading", { name: "Start your adaptation in Telegram" }).waitFor();

  await waitUntilTimelineMs(timelineStartedAt, contentPoint(scene, 0.55));
  await gotoAndSettle(context, "/reviewers?recording=true#admin-chat");
  const adminChat = page.locator("#admin-chat");
  await adminChat.scrollIntoViewIfNeeded();
  await adminChat.getByRole("heading", { name: "Add the bot to a reviewer admin chat" }).waitFor();
}

async function showTeamStudio(context: SceneContext): Promise<void> {
  const { page, scene, timelineStartedAt } = context;
  await gotoAndSettle(context, "/studio?recording=true");
  await page.getByRole("heading", { name: "Transition pulse" }).waitFor();

  await waitUntilTimelineMs(timelineStartedAt, contentPoint(scene, 0.5));
  await gotoAndSettle(context, "/studio/guide?recording=true#privacy");
  const privacy = page.locator("#privacy");
  await privacy.scrollIntoViewIfNeeded();
  await privacy.getByRole("heading", { name: "Know what admins can see" }).waitFor();

  await waitUntilTimelineMs(timelineStartedAt, contentPoint(scene, 0.8));
  await gotoAndSettle(context, "/reviewers?recording=true#studio");
  const reviewerStudio = page.locator("#studio");
  await reviewerStudio.scrollIntoViewIfNeeded();
  await reviewerStudio.getByRole("heading", { name: "What works in Team Studio" }).waitFor();
}

async function showBuildEvidenceThenEnding(
  context: SceneContext,
  state: RecordingState,
): Promise<void> {
  const { page, scene, timelineStartedAt } = context;
  await gotoAndSettle(context, "/presentation?recording=true&scene=08&phase=evidence");
  await visible(page, "build-evidence");

  await waitUntilTimelineMs(timelineStartedAt, contentPoint(scene, 0.73));
  await gotoAndSettle(context, "/presentation?recording=true&scene=08&phase=ending");
  await visible(page, "ending-card");
  state.endingCardShown = true;
}

function contentPoint(scene: DemoTimelineScene, fraction: number): number {
  return scene.startMs + scene.leadInMs + Math.round(scene.contentDurationMs * fraction);
}

function url(context: SceneContext, path: string): string {
  return new URL(path, context.baseUrl).toString();
}

async function gotoAndSettle(context: SceneContext, path: string): Promise<void> {
  await context.page.goto(url(context, path), { waitUntil: "domcontentloaded" });
  await settleVisuals(context.page);
}

async function visible(page: Page, testId: string): Promise<void> {
  await page.getByTestId(testId).waitFor({ state: "visible", timeout: 15_000 });
}

export async function settleVisuals(page: Page): Promise<void> {
  await page.evaluate(async () => {
    await document.fonts.ready;
    await new Promise<void>((resolve) => {
      requestAnimationFrame(() => requestAnimationFrame(() => resolve()));
    });
  });
}
