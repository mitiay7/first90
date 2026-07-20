import { existsSync, readFileSync, statSync, writeFileSync } from "node:fs";
import {
  artifactPaths,
  backgroundMusicSource,
  ensureArtifactDirectories,
  runBinary,
} from "./demo-files";
import { competitionLimitMs, expectedAudioFileNames } from "./demo-scenes";
import type { DemoTimeline } from "./demo-types";

type Probe = {
  streams?: Array<{
    codec_type?: string;
    codec_name?: string;
    width?: number;
    height?: number;
    r_frame_rate?: string;
    duration?: string;
  }>;
  format?: { duration?: string };
};

type RecordingReport = {
  participantJourneyRecorded: boolean;
  coachResponseRecorded: boolean;
  coachMode: "live" | "fallback" | null;
  endingCardShown: boolean;
  scenesCompleted: string[];
};

export function validateVideo(): Record<string, unknown> {
  ensureArtifactDirectories();
  if (!existsSync(artifactPaths.finalVideo) || statSync(artifactPaths.finalVideo).size === 0) {
    throw new Error("Final MP4 is missing or empty");
  }
  const timeline = JSON.parse(readFileSync(artifactPaths.timeline, "utf8")) as DemoTimeline;
  const recording = JSON.parse(
    readFileSync(artifactPaths.recordingReport, "utf8"),
  ) as RecordingReport;
  const probe = JSON.parse(
    runBinary(
      "ffprobe",
      ["-v", "error", "-show_streams", "-show_format", "-of", "json", artifactPaths.finalVideo],
      true,
    ),
  ) as Probe;
  const video = probe.streams?.find((stream) => stream.codec_type === "video");
  const audio = probe.streams?.find((stream) => stream.codec_type === "audio");
  const durationSeconds = Number(probe.format?.duration ?? 0);
  const frameRate = parseFrameRate(video?.r_frame_rate ?? "0/1");
  const audioDuration = Number(audio?.duration ?? durationSeconds);
  const audioFilesUsed = timeline.scenes.map((scene) => scene.audioFile.split("/").at(-1)!);
  const checks = {
    durationBelowCompetitionLimit: durationSeconds * 1000 < competitionLimitMs,
    width: video?.width === 1920,
    height: video?.height === 1080,
    frameRate: Math.abs(frameRate - 30) < 0.05,
    h264: video?.codec_name === "h264",
    aac: audio?.codec_name === "aac",
    audioDurationMatches: Math.abs(audioDuration - durationSeconds) < 0.25,
    allAudioFilesUsed:
      audioFilesUsed.length === expectedAudioFileNames.length &&
      audioFilesUsed.every((name, index) => name === expectedAudioFileNames[index]),
    allScenesRecorded: recording.scenesCompleted.length === timeline.scenes.length,
    participantJourneyRecorded: recording.participantJourneyRecorded,
    coachResponseRecorded: recording.coachResponseRecorded,
    coachModeRecorded: recording.coachMode === "live" || recording.coachMode === "fallback",
    endingCardShown: recording.endingCardShown,
    licensedBackgroundMusicSource: existsSync(backgroundMusicSource),
    preparedBackgroundMusic: existsSync(artifactPaths.backgroundMusic),
  };
  const validation = {
    valid: Object.values(checks).every(Boolean),
    durationSeconds,
    width: video?.width ?? null,
    height: video?.height ?? null,
    frameRate,
    videoCodec: video?.codec_name ?? null,
    audioCodec: audio?.codec_name ?? null,
    audioDurationSeconds: audioDuration,
    fileSizeBytes: statSync(artifactPaths.finalVideo).size,
    audioFilesUsed,
    coachMode: recording.coachMode,
    checks,
  };
  writeFileSync(artifactPaths.validation, `${JSON.stringify(validation, null, 2)}\n`);
  if (!validation.valid)
    throw new Error(`Final video validation failed: ${artifactPaths.validation}`);
  console.log(`Validation passed: ${artifactPaths.validation}`);
  return validation;
}

function parseFrameRate(value: string): number {
  const [numerator, denominator] = value.split("/").map(Number);
  return denominator ? numerator! / denominator : 0;
}

if (import.meta.url === `file://${process.argv[1]}`) validateVideo();
