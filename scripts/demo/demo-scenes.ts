export type DemoSceneDefinition = {
  id: string;
  audioFile: string;
  description: string;
  leadInMs: number;
  trailingHoldMs: number;
  minimumVisualDurationMs: number;
  execute:
    | "showHook"
    | "showProductModel"
    | "showParticipantJourney"
    | "showCoach"
    | "showTailoredCapsules"
    | "showTelegram"
    | "showTeamStudio"
    | "showBuildEvidenceThenEnding";
};

export const demoScenes: readonly DemoSceneDefinition[] = [
  {
    id: "01-hook",
    audioFile: "demo/voiceover/01.mp3",
    description: "New-role noise and the First 90 promise",
    leadInMs: 450,
    trailingHoldMs: 650,
    minimumVisualDurationMs: 4_000,
    execute: "showHook",
  },
  {
    id: "02-product-model",
    audioFile: "demo/voiceover/02.mp3",
    description: "Ninety days, 270 touchpoints, and contextual personalization",
    leadInMs: 300,
    trailingHoldMs: 650,
    minimumVisualDurationMs: 5_000,
    execute: "showProductModel",
  },
  {
    id: "03-participant-journey",
    audioFile: "demo/voiceover/03.mp3",
    description: "Real fictional participant flow on day eighteen",
    leadInMs: 300,
    trailingHoldMs: 750,
    minimumVisualDurationMs: 8_000,
    execute: "showParticipantJourney",
  },
  {
    id: "04-gpt-coach",
    audioFile: "demo/voiceover/04.mp3",
    description: "GPT-5.6-ready coaching, deterministic fallback, and privacy boundary",
    leadInMs: 300,
    trailingHoldMs: 750,
    minimumVisualDurationMs: 10_000,
    execute: "showCoach",
  },
  {
    id: "05-tailored-capsules",
    audioFile: "demo/voiceover/05.mp3",
    description: "Enhanced Days 1-3 manager content and learning resources",
    leadInMs: 300,
    trailingHoldMs: 650,
    minimumVisualDurationMs: 7_000,
    execute: "showTailoredCapsules",
  },
  {
    id: "06-telegram",
    audioFile: "demo/voiceover/06.mp3",
    description: "Telegram onboarding and reviewer group commands",
    leadInMs: 300,
    trailingHoldMs: 650,
    minimumVisualDurationMs: 8_000,
    execute: "showTelegram",
  },
  {
    id: "07-team-studio",
    audioFile: "demo/voiceover/07.mp3",
    description: "Aggregate Team Studio and explicit admin privacy guidance",
    leadInMs: 300,
    trailingHoldMs: 750,
    minimumVisualDurationMs: 8_000,
    execute: "showTeamStudio",
  },
  {
    id: "08-build-impact-ending",
    audioFile: "demo/voiceover/08.mp3",
    description: "Codex, GPT-5.6, live architecture, and ending card",
    leadInMs: 300,
    trailingHoldMs: 1_800,
    minimumVisualDurationMs: 10_000,
    execute: "showBuildEvidenceThenEnding",
  },
] as const;

// Official rules require less than three minutes. Keep a two-second safety margin.
export const competitionLimitMs = 178_000;
export const warningThresholdMs = 175_000;

export const expectedAudioFileNames = demoScenes.map((scene) =>
  scene.audioFile.split("/").at(-1),
) as string[];
