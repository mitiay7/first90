import { createHash } from "node:crypto";
import { existsSync, readFileSync, rmSync } from "node:fs";
import {
  artifactPaths,
  backgroundMusicSource,
  ensureArtifactDirectories,
  runBinary,
} from "./demo-files";
import type { DemoTimeline } from "./demo-types";

const expectedMusicSha256 = "8778d1e095ab7c6793d10ce9bbe1d9783c9ec6d558f11302ced2202b2c039a0c";

/** Prepares the selected CC0 track as a deterministic 48 kHz stereo mix source. */
export function generateBackgroundMusic(): void {
  ensureArtifactDirectories();
  if (!existsSync(backgroundMusicSource)) {
    throw new Error(`Licensed background track is missing: ${backgroundMusicSource}`);
  }
  const actualSha256 = createHash("sha256")
    .update(readFileSync(backgroundMusicSource))
    .digest("hex");
  if (actualSha256 !== expectedMusicSha256) {
    throw new Error(`Background track checksum mismatch: ${actualSha256}`);
  }
  const timeline = JSON.parse(readFileSync(artifactPaths.timeline, "utf8")) as DemoTimeline;
  const durationSeconds = timeline.totalDurationMs / 1000;
  const duration = durationSeconds.toFixed(3);
  const fadeOutStart = Math.max(0, durationSeconds - 0.8).toFixed(3);
  rmSync(artifactPaths.backgroundMusic, { force: true });
  runBinary("ffmpeg", [
    "-hide_banner",
    "-loglevel",
    "error",
    "-y",
    "-i",
    backgroundMusicSource,
    "-map",
    "0:a:0",
    "-vn",
    "-af",
    `aresample=48000,afade=t=in:st=0:d=0.2,afade=t=out:st=${fadeOutStart}:d=0.8,atrim=duration=${duration}`,
    "-ar",
    "48000",
    "-ac",
    "2",
    "-c:a",
    "pcm_s16le",
    artifactPaths.backgroundMusic,
  ]);
  console.log(`CC0 background track prepared: ${artifactPaths.backgroundMusic}`);
}

if (import.meta.url === `file://${process.argv[1]}`) generateBackgroundMusic();
