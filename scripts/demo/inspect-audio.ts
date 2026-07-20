import { accessSync, constants, readFileSync, statSync, writeFileSync } from "node:fs";
import { relative } from "node:path";
import {
  artifactPaths,
  ensureArtifactDirectories,
  fromProjectRoot,
  projectRoot,
  runBinary,
} from "./demo-files";
import { demoScenes, expectedAudioFileNames } from "./demo-scenes";
import type { AudioFileInspection, AudioInspection } from "./demo-types";

type Probe = {
  streams?: Array<{
    codec_type?: string;
    codec_name?: string;
    sample_rate?: string;
    channels?: number;
    bit_rate?: string;
  }>;
  format?: { duration?: string; bit_rate?: string };
};

export function validateAudioFileNames(fileNames: string[]): void {
  const expected = [...expectedAudioFileNames];
  if (
    fileNames.length !== expected.length ||
    fileNames.some((name, index) => name !== expected[index])
  ) {
    throw new Error(
      `Expected audio files in order: ${expected.join(", ")}. Received: ${fileNames.join(", ")}`,
    );
  }
}

export function inspectAudioFiles(): AudioInspection {
  ensureArtifactDirectories();
  validateAudioFileNames(demoScenes.map((scene) => scene.audioFile.split("/").at(-1)!));

  const audioFiles = demoScenes.map((scene, index): AudioFileInspection => {
    const absolutePath = fromProjectRoot(scene.audioFile);
    return inspectAudioPath(absolutePath, relative(projectRoot, absolutePath), index + 1);
  });

  const inspection: AudioInspection = {
    version: 1,
    audioFiles,
    totalNarrationDurationMs: audioFiles.reduce((total, file) => total + file.durationMs, 0),
  };
  writeFileSync(artifactPaths.audioInspection, `${JSON.stringify(inspection, null, 2)}\n`);
  return inspection;
}

export function inspectAudioPath(
  absolutePath: string,
  relativePath: string,
  index: number,
): AudioFileInspection {
  accessSync(absolutePath, constants.R_OK);
  const file = statSync(absolutePath);
  if (!file.isFile() || file.size === 0) throw new Error(`${relativePath} is missing or empty`);
  readFileSync(absolutePath, { encoding: null, flag: "r" });

  const probe = JSON.parse(
    runBinary(
      "ffprobe",
      ["-v", "error", "-show_streams", "-show_format", "-of", "json", absolutePath],
      true,
    ),
  ) as Probe;
  const stream = probe.streams?.find((candidate) => candidate.codec_type === "audio");
  if (!stream) throw new Error(`${relativePath} does not contain an audio stream`);
  const durationSeconds = Number(probe.format?.duration);
  if (!Number.isFinite(durationSeconds) || durationSeconds <= 0) {
    throw new Error(`${relativePath} has an invalid duration`);
  }

  return {
    index,
    fileName: relativePath.split("/").at(-1)!,
    relativePath,
    durationSeconds,
    durationMs: Math.round(durationSeconds * 1000),
    codec: stream.codec_name ?? "unknown",
    sampleRate: Number(stream.sample_rate ?? 0),
    channels: Number(stream.channels ?? 0),
    bitRate: Number(stream.bit_rate ?? probe.format?.bit_rate ?? 0) || null,
    sizeBytes: file.size,
  };
}

if (import.meta.url === `file://${process.argv[1]}`) {
  const inspection = inspectAudioFiles();
  for (const file of inspection.audioFiles) {
    console.log(
      `${file.fileName.padEnd(8)} ${file.durationSeconds.toFixed(3)}s  ${file.codec}  ${file.sampleRate}Hz  ${file.channels}ch`,
    );
  }
  console.log(`Audio inspection: ${artifactPaths.audioInspection}`);
}
