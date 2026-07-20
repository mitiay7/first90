import { execFileSync } from "node:child_process";
import { mkdirSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

export const projectRoot = resolve(dirname(fileURLToPath(import.meta.url)), "../..");
export const artifactDir = resolve(projectRoot, "artifacts/video");
export const debugDir = resolve(artifactDir, "debug");
export const rawVideoDir = resolve(artifactDir, "raw");
export const normalizedAudioDir = resolve(artifactDir, "audio-normalized");
export const backgroundMusicSource = resolve(projectRoot, "demo/music/one-cool-minute.mp3");

export const artifactPaths = {
  audioInspection: resolve(artifactDir, "audio-inspection.json"),
  timeline: resolve(artifactDir, "demo-timeline.json"),
  timingReport: resolve(artifactDir, "timing-report.json"),
  recordingReport: resolve(artifactDir, "recording-report.json"),
  browserVideo: resolve(artifactDir, "browser-demo.webm"),
  assembledVoiceover: resolve(artifactDir, "assembled-voiceover.wav"),
  backgroundMusic: resolve(artifactDir, "background-music.wav"),
  finalVideo: resolve(artifactDir, "first90-demo.mp4"),
  validation: resolve(artifactDir, "validation.json"),
  trace: resolve(debugDir, "trace.zip"),
  failureScreenshot: resolve(debugDir, "failure.png"),
  browserConsole: resolve(debugDir, "browser-console.log"),
  browserNetwork: resolve(debugDir, "browser-network.log"),
  ffmpegCommand: resolve(debugDir, "ffmpeg-command.txt"),
  ffmpegLog: resolve(debugDir, "ffmpeg.log"),
};

export function ensureArtifactDirectories(): void {
  for (const directory of [artifactDir, debugDir, rawVideoDir, normalizedAudioDir]) {
    mkdirSync(directory, { recursive: true });
  }
}

export function fromProjectRoot(path: string): string {
  return resolve(projectRoot, path);
}

export function runBinary(binary: string, args: string[], capture = false): string {
  return execFileSync(binary, args, {
    cwd: projectRoot,
    encoding: "utf8",
    stdio: capture ? ["ignore", "pipe", "pipe"] : ["ignore", "inherit", "inherit"],
    maxBuffer: 20 * 1024 * 1024,
  });
}
