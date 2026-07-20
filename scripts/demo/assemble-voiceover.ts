import { readFileSync, rmSync, writeFileSync } from "node:fs";
import {
  artifactPaths,
  ensureArtifactDirectories,
  fromProjectRoot,
  normalizedAudioDir,
  runBinary,
} from "./demo-files";
import type { DemoTimeline } from "./demo-types";

export function assembleVoiceover(): void {
  ensureArtifactDirectories();
  const timeline = JSON.parse(readFileSync(artifactPaths.timeline, "utf8")) as DemoTimeline;
  const normalizedFiles = timeline.scenes.map((scene, index) => {
    const output = `${normalizedAudioDir}/${String(index + 1).padStart(2, "0")}.wav`;
    rmSync(output, { force: true });
    runBinary("ffmpeg", [
      "-hide_banner",
      "-loglevel",
      "error",
      "-y",
      "-i",
      fromProjectRoot(scene.audioFile),
      "-vn",
      "-af",
      "loudnorm=I=-18:TP=-2:LRA=7",
      "-ar",
      "48000",
      "-ac",
      "2",
      "-c:a",
      "pcm_s16le",
      output,
    ]);
    return output;
  });

  const inputArgs = normalizedFiles.flatMap((file) => ["-i", file]);
  const filters = timeline.scenes.map(
    (scene, index) =>
      `[${index}:a]adelay=${scene.audioStartMs}|${scene.audioStartMs}[voice${index}]`,
  );
  const voiceInputs = timeline.scenes.map((_, index) => `[voice${index}]`).join("");
  const durationSeconds = (timeline.totalDurationMs / 1000).toFixed(3);
  filters.push(
    `${voiceInputs}amix=inputs=${timeline.scenes.length}:normalize=0:dropout_transition=0,alimiter=limit=0.95,apad=whole_dur=${durationSeconds},atrim=duration=${durationSeconds}[voiceout]`,
  );
  rmSync(artifactPaths.assembledVoiceover, { force: true });
  runBinary("ffmpeg", [
    "-hide_banner",
    "-loglevel",
    "error",
    "-y",
    ...inputArgs,
    "-filter_complex",
    filters.join(";"),
    "-map",
    "[voiceout]",
    "-ar",
    "48000",
    "-ac",
    "2",
    "-c:a",
    "pcm_s16le",
    artifactPaths.assembledVoiceover,
  ]);
  writeFileSync(
    `${normalizedAudioDir}/README.txt`,
    "Generated 48 kHz stereo PCM intermediates. Source MP3 files are never modified.\n",
  );
  console.log(`Assembled narration: ${artifactPaths.assembledVoiceover}`);
}

if (import.meta.url === `file://${process.argv[1]}`) assembleVoiceover();
