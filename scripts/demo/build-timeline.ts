import { readFileSync, writeFileSync } from "node:fs";
import { artifactPaths, ensureArtifactDirectories } from "./demo-files";
import { competitionLimitMs, demoScenes, warningThresholdMs } from "./demo-scenes";
import type { AudioInspection, DemoTimeline } from "./demo-types";

export function calculateTimeline(inspection: AudioInspection): DemoTimeline {
  let cursorMs = 0;
  const scenes = demoScenes.map((definition) => {
    const audio = inspection.audioFiles.find((file) => file.relativePath === definition.audioFile);
    if (!audio) throw new Error(`Audio inspection is missing ${definition.audioFile}`);
    const contentDurationMs = Math.max(audio.durationMs, definition.minimumVisualDurationMs);
    const startMs = cursorMs;
    const audioStartMs = startMs + definition.leadInMs;
    const audioEndMs = audioStartMs + audio.durationMs;
    const endMs = startMs + definition.leadInMs + contentDurationMs + definition.trailingHoldMs;
    cursorMs = endMs;
    return {
      id: definition.id,
      audioFile: definition.audioFile,
      description: definition.description,
      execute: definition.execute,
      audioDurationMs: audio.durationMs,
      contentDurationMs,
      startMs,
      audioStartMs,
      audioEndMs,
      endMs,
      leadInMs: definition.leadInMs,
      trailingHoldMs: definition.trailingHoldMs,
    };
  });

  for (let index = 0; index < scenes.length - 1; index += 1) {
    const current = scenes[index]!;
    const next = scenes[index + 1]!;
    if (current.audioEndMs > next.audioStartMs) {
      throw new Error(`Narration overlap: ${current.id} ends after ${next.id} starts`);
    }
    if (current.endMs !== next.startMs)
      throw new Error(`Non-sequential scene boundary at ${next.id}`);
  }

  const totalNarrationDurationMs = scenes.reduce(
    (total, scene) => total + scene.audioDurationMs,
    0,
  );
  const timeline: DemoTimeline = {
    version: 1,
    competitionLimitMs,
    totalDurationMs: cursorMs,
    totalNarrationDurationMs,
    totalSilenceAndHoldMs: cursorMs - totalNarrationDurationMs,
    scenes,
  };
  if (timeline.totalDurationMs >= competitionLimitMs) {
    throw new Error(
      `Expected video duration ${(timeline.totalDurationMs / 1000).toFixed(3)}s violates the strict ${(competitionLimitMs / 1000).toFixed(0)}s competition limit.`,
    );
  }
  return timeline;
}

export function buildTimeline(): DemoTimeline {
  ensureArtifactDirectories();
  const inspection = JSON.parse(
    readFileSync(artifactPaths.audioInspection, "utf8"),
  ) as AudioInspection;
  const timeline = calculateTimeline(inspection);
  const timingReport = {
    version: 1,
    table: timeline.scenes.map((scene) => ({
      scene: scene.id,
      audioFile: scene.audioFile,
      audioDurationMs: scene.audioDurationMs,
      leadInMs: scene.leadInMs,
      visualHoldMs: scene.trailingHoldMs,
      sceneDurationMs: scene.endMs - scene.startMs,
    })),
    totalNarrationDurationMs: timeline.totalNarrationDurationMs,
    totalSilenceAndVisualHoldMs: timeline.totalSilenceAndHoldMs,
    totalFinalVideoDurationMs: timeline.totalDurationMs,
    remainingBeforeCompetitionLimitMs: competitionLimitMs - timeline.totalDurationMs,
  };
  writeFileSync(artifactPaths.timeline, `${JSON.stringify(timeline, null, 2)}\n`);
  writeFileSync(artifactPaths.timingReport, `${JSON.stringify(timingReport, null, 2)}\n`);
  return timeline;
}

if (import.meta.url === `file://${process.argv[1]}`) {
  const timeline = buildTimeline();
  console.table(
    timeline.scenes.map((scene) => ({
      Scene: scene.id,
      Audio: `${(scene.audioDurationMs / 1000).toFixed(3)}s`,
      Start: `${(scene.startMs / 1000).toFixed(3)}s`,
      End: `${(scene.endMs / 1000).toFixed(3)}s`,
    })),
  );
  const totalSeconds = timeline.totalDurationMs / 1000;
  if (timeline.totalDurationMs >= warningThresholdMs) {
    console.warn(`Timing warning: ${totalSeconds.toFixed(3)}s is close to the 178s limit.`);
  }
  console.log(`Shared timeline: ${artifactPaths.timeline}`);
}
