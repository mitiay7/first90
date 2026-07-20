import { spawnSync } from "node:child_process";
import { existsSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { artifactPaths, ensureArtifactDirectories, fromProjectRoot } from "./demo-files";
import type { DemoTimeline } from "./demo-types";

type RecordingReport = { videoTrimStartMs: number };

export function renderVideo(options: { captions: boolean }): void {
  ensureArtifactDirectories();
  const timeline = JSON.parse(readFileSync(artifactPaths.timeline, "utf8")) as DemoTimeline;
  const recording = JSON.parse(
    readFileSync(artifactPaths.recordingReport, "utf8"),
  ) as RecordingReport;
  const durationSeconds = timeline.totalDurationMs / 1000;
  const duration = durationSeconds.toFixed(3);
  const trimStart = Math.max(0, recording.videoTrimStartMs / 1000).toFixed(3);
  const louderOutroStart = Math.max(0, durationSeconds - 4).toFixed(3);
  const outroRampStart = Math.max(0, durationSeconds - 5).toFixed(3);
  const captionsFile = fromProjectRoot("demo/voiceover/captions.srt");
  if (options.captions && !existsSync(captionsFile)) {
    throw new Error("--captions was requested but demo/voiceover/captions.srt does not exist");
  }

  const subtitleFilter = options.captions
    ? `,subtitles=${escapeFilterPath(captionsFile)}:force_style='FontName=Arial,FontSize=19,PrimaryColour=&H00FFFFFF,OutlineColour=&H90000000,BorderStyle=3,Outline=1,Shadow=0,MarginV=52,Alignment=2'`
    : "";
  const filter = [
    `[0:v]trim=start=${trimStart},setpts=PTS-STARTPTS,tpad=stop_mode=clone:stop_duration=2,trim=duration=${duration},fps=30,scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,format=yuv420p${subtitleFilter}[video]`,
    `[2:a]volume='if(lt(t,4),0.58,if(lt(t,5),0.58-(t-4)*0.43,if(lt(t,${outroRampStart}),0.15,if(lt(t,${louderOutroStart}),0.15+(t-${outroRampStart})*0.43,0.58))))':eval=frame[music-level]`,
    `[music-level][1:a]sidechaincompress=threshold=0.018:ratio=6:attack=25:release=450[ducked-music]`,
    `[1:a][ducked-music]amix=inputs=2:weights='1 1':normalize=0,alimiter=limit=0.95,atrim=duration=${duration}[audio]`,
  ].join(";");
  const args = [
    "-hide_banner",
    "-y",
    "-i",
    artifactPaths.browserVideo,
    "-i",
    artifactPaths.assembledVoiceover,
    "-i",
    artifactPaths.backgroundMusic,
    "-filter_complex",
    filter,
    "-map",
    "[video]",
    "-map",
    "[audio]",
    "-t",
    duration,
    "-c:v",
    "libx264",
    "-preset",
    "slow",
    "-crf",
    "18",
    "-profile:v",
    "high",
    "-level",
    "4.1",
    "-pix_fmt",
    "yuv420p",
    "-c:a",
    "aac",
    "-b:a",
    "192k",
    "-movflags",
    "+faststart",
    artifactPaths.finalVideo,
  ];

  rmSync(artifactPaths.finalVideo, { force: true });
  writeFileSync(artifactPaths.ffmpegCommand, `ffmpeg ${args.map(shellQuote).join(" ")}\n`);
  const result = spawnSync("ffmpeg", args, { encoding: "utf8", maxBuffer: 30 * 1024 * 1024 });
  writeFileSync(artifactPaths.ffmpegLog, `${result.stdout ?? ""}${result.stderr ?? ""}`);
  if (result.status !== 0) throw new Error(`FFmpeg render failed; see ${artifactPaths.ffmpegLog}`);
  console.log(`Final MP4: ${artifactPaths.finalVideo}`);
}

function escapeFilterPath(path: string): string {
  return path.replaceAll("\\", "\\\\").replaceAll(":", "\\:").replaceAll("'", "\\'");
}

function shellQuote(value: string): string {
  return `'${value.replaceAll("'", "'\\''")}'`;
}

if (import.meta.url === `file://${process.argv[1]}`) {
  renderVideo({
    captions: process.argv.includes("--captions") && !process.argv.includes("--no-captions"),
  });
}
